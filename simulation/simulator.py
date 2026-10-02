"""Discrete-Time Simulator for PRAVAH Logistics & Supply Chain.

Advances world state hour-by-hour over a configurable horizon (default 14 days / 336 hours).
Coordinates weather generation, disruptions, vehicle fleet movement, dynamic shipment
transit times, demand fulfillment, and inventory balance.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import uuid
from typing import Dict, List, Optional, Tuple, Any
import networkx as nx
from simulation.world_generator import (
    NodeType,
    SupplyCategory,
    RouteStatus,
    VehicleStatus,
    WeatherSeverity,
    Node,
    Route,
    Vehicle,
    Shipment,
    WorldGenerator,
    WorldState,
)
from simulation.demand_generator import DemandGenerator, HourlyDemand
from simulation.weather_generator import WeatherGenerator
from simulation.inventory_engine import InventoryEngine, InventorySnapshot, StockoutEvent
from simulation.disruption_engine import DisruptionEngine, Disruption


@dataclass
class SimulationConfig:
    seed: int = 42
    start_hour: int = 0
    horizon_hours: int = 336  # 14 days
    scenario_name: str = "NORMAL"
    auto_replenish: bool = True
    disruptions: List[Disruption] = field(default_factory=list)


@dataclass
class SimulationResult:
    run_id: str
    scenario_name: str
    seed: int
    horizon_hours: int
    total_requested_demand: float
    total_fulfilled_demand: float
    total_unmet_demand: float
    fulfillment_rate_percent: float
    total_stockout_events: int
    stockout_hours_total: int
    critical_nodes: List[Dict[str, Any]]
    earliest_stockout_hour: Optional[int]
    active_disruptions_count: int
    summary_metrics: Dict[str, Any]
    snapshots: List[InventorySnapshot] = field(default_factory=list)
    stockout_events: List[StockoutEvent] = field(default_factory=list)
    shipments: List[Shipment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_name": self.scenario_name,
            "seed": self.seed,
            "horizon_hours": self.horizon_hours,
            "total_requested_demand": self.total_requested_demand,
            "total_fulfilled_demand": self.total_fulfilled_demand,
            "total_unmet_demand": self.total_unmet_demand,
            "fulfillment_rate_percent": self.fulfillment_rate_percent,
            "total_stockout_events": self.total_stockout_events,
            "stockout_hours_total": self.stockout_hours_total,
            "critical_nodes": self.critical_nodes,
            "earliest_stockout_hour": self.earliest_stockout_hour,
            "active_disruptions_count": self.active_disruptions_count,
            "summary_metrics": self.summary_metrics,
            "shipment_count": len(self.shipments),
            "stockout_events_count": len(self.stockout_events),
        }


class Simulator:
    """Core discrete-event simulation engine executing 1-hour timesteps."""

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.run_id = f"SIM_{uuid.uuid4().hex[:8]}"

        # Initialize world components deterministically
        world_gen = WorldGenerator(seed=self.config.seed)
        self.world: WorldState = world_gen.generate_world()

        self.weather_gen = WeatherGenerator(seed=self.config.seed)
        self.demand_gen = DemandGenerator(seed=self.config.seed)
        self.inventory_engine = InventoryEngine(self.world.nodes)
        self.disruption_engine = DisruptionEngine(self.config.disruptions)

        self.current_hour = self.config.start_hour
        self.all_shipments: List[Shipment] = []
        self.shipment_counter = 0

        # Build NetworkX graph representation for routing
        self._build_graph()

    def _build_graph(self) -> None:
        """Constructs directional multigraph for shortest-path route resolution."""
        self.graph = nx.DiGraph()
        for nid, node in self.world.nodes.items():
            self.graph.add_node(nid, **node.to_dict())

        for rid, route in self.world.routes.items():
            self.graph.add_edge(
                route.source_node_id,
                route.destination_node_id,
                route_id=rid,
                base_hours=route.base_travel_hours,
                status=route.status,
                distance_km=route.distance_km,
                obj=route,
            )

    def find_best_route(self, source_id: str, dest_id: str) -> Optional[Route]:
        """Finds shortest available route or fallback alternate path avoiding blocked routes."""
        valid_routes = []
        for rid, route in self.world.routes.items():
            if route.source_node_id == source_id and route.destination_node_id == dest_id:
                if route.status != RouteStatus.BLOCKED:
                    valid_routes.append(route)

        if valid_routes:
            # Sort by base travel hours
            valid_routes.sort(key=lambda r: r.base_travel_hours)
            return valid_routes[0]

        # Multi-hop search via NetworkX excluding blocked edges
        try:
            def edge_weight(u, v, d):
                route_obj: Route = d["obj"]
                if route_obj.status == RouteStatus.BLOCKED:
                    return 1e9  # impassable
                elif route_obj.status == RouteStatus.DEGRADED:
                    return route_obj.base_travel_hours * 2.0
                return route_obj.base_travel_hours

            path = nx.shortest_path(self.graph, source_id, dest_id, weight=edge_weight)
            if len(path) >= 2:
                # Return first leg
                first_hop_src = path[0]
                first_hop_dst = path[1]
                for rid, r in self.world.routes.items():
                    if r.source_node_id == first_hop_src and r.destination_node_id == first_hop_dst:
                        if r.status != RouteStatus.BLOCKED:
                            return r
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        return None

    def _dispatch_replenishment(self, current_hour: int) -> List[Shipment]:
        """Automated tactical replenishment dispatch heuristic based on reorder points."""
        if not self.config.auto_replenish:
            return []

        new_shipments: List[Shipment] = []

        # Tiered replenishment upstream suppliers
        supply_hierarchy = {
            NodeType.FORWARD_POST: ["NODE_SB_02", "NODE_SB_03", "NODE_SB_04", "NODE_SB_05", "NODE_RH_01", "NODE_RH_02", "NODE_RH_03"],
            NodeType.TRANSIT_POINT: ["NODE_RH_01", "NODE_RH_02", "NODE_RH_03", "NODE_CD_01", "NODE_SB_01"],
            NodeType.REGIONAL_HUB: ["NODE_CD_01", "NODE_SB_01"],
        }

        # Check nodes needing resupply
        # Priority order: Forward Posts (Priority 5) first!
        sorted_nodes = sorted(self.world.nodes.values(), key=lambda n: n.priority, reverse=True)

        for dest_node in sorted_nodes:
            if dest_node.type == NodeType.CENTRAL_DEPOT:
                # Depot gets external production batches every 72 hours
                if current_hour % 72 == 0:
                    for item in SupplyCategory:
                        refill = dest_node.reorder_quantity.get(item.value, 5000.0) * 1.2
                        self.inventory_engine.current_inventory[dest_node.id][item.value] += refill
                continue

            possible_suppliers = supply_hierarchy.get(dest_node.type, [])

            for item_cat in SupplyCategory:
                item = item_cat.value
                current_stock = self.inventory_engine.get_stock(dest_node.id, item)
                reorder_threshold = dest_node.reorder_point.get(item, 500.0)

                # Check if stock is below reorder threshold
                # Also check that we don't already have excessive in-transit shipments for this item
                in_transit_quantity = sum(
                    s.quantity for s in self.world.active_shipments
                    if s.destination_node_id == dest_node.id and s.item == item
                )

                if (current_stock + in_transit_quantity) < reorder_threshold:
                    req_qty = dest_node.reorder_quantity.get(item, 1000.0)

                    # Look for supplier with stock and route
                    for src_id in possible_suppliers:
                        src_stock = self.inventory_engine.get_stock(src_id, item)
                        if src_stock < req_qty * 0.3:
                            continue

                        # Find best available route
                        route = self.find_best_route(src_id, dest_node.id)
                        if route is None or route.status == RouteStatus.BLOCKED:
                            continue

                        # Find available vehicle stationed at supplier or depot
                        available_vehicle = None
                        for v in self.world.vehicles.values():
                            if (v.status == VehicleStatus.AVAILABLE and v.availability and
                                v.current_node_id in [src_id, "NODE_CD_01"]):
                                available_vehicle = v
                                break

                        if available_vehicle is None:
                            continue

                        # Allocate quantity clamped to vehicle capacity and source stock
                        alloc_qty = min(req_qty, available_vehicle.capacity, src_stock * 0.8)
                        if alloc_qty < 10.0:
                            continue

                        # Calculate dynamic travel time based on current weather at destination
                        w_state = self.weather_gen.generate_weather(dest_node, current_hour)
                        eff_hours = self.weather_gen.calculate_effective_travel_time(route, w_state)
                        if route.status == RouteStatus.DEGRADED:
                            eff_hours = round(eff_hours * 1.8, 2)

                        transit_steps = max(1, int(round(eff_hours)))
                        expected_arr = current_hour + transit_steps

                        self.shipment_counter += 1
                        shipment = Shipment(
                            shipment_id=f"SHIP_{self.shipment_counter:04d}",
                            source_node_id=src_id,
                            destination_node_id=dest_node.id,
                            item=item,
                            quantity=round(alloc_qty, 1),
                            route_id=route.id,
                            vehicle_id=available_vehicle.id,
                            departure_time=current_hour,
                            expected_arrival=expected_arr,
                            actual_arrival=expected_arr,
                            status="IN_TRANSIT",
                        )

                        # Reserve vehicle
                        available_vehicle.status = VehicleStatus.IN_TRANSIT
                        available_vehicle.availability = False
                        available_vehicle.current_node_id = dest_node.id  # Destination after transit

                        new_shipments.append(shipment)
                        self.world.active_shipments.append(shipment)
                        self.all_shipments.append(shipment)
                        break  # Fulfilled this replenishment request

        return new_shipments

    def step(self) -> Tuple[List[HourlyDemand], List[InventorySnapshot]]:
        """Advances simulation by exactly one hour."""
        current_hour = self.current_hour

        # 1. Apply active route & vehicle disruptions
        self.disruption_engine.apply_route_disruptions(self.world.routes, current_hour)
        self.disruption_engine.apply_vehicle_disruptions(self.world.vehicles, current_hour)

        # 2. Update weather state for each node
        for nid, node in self.world.nodes.items():
            forced_sev = self.disruption_engine.get_weather_override(nid, current_hour)
            self.world.weather_by_node[nid] = self.weather_gen.generate_weather(
                node, current_hour, forced_severity=forced_sev
            )

        # 3. Process arriving shipments
        arrived_shipments: List[Shipment] = []
        remaining_shipments: List[Shipment] = []

        for s in self.world.active_shipments:
            # Check route status during transit; if route became blocked, add delay
            route = self.world.routes.get(s.route_id)
            if route and route.status == RouteStatus.BLOCKED and s.actual_arrival <= current_hour:
                # Shipment delayed by blockage
                s.actual_arrival = current_hour + 2
                s.status = "DELAYED"

            if s.actual_arrival <= current_hour:
                s.status = "DELIVERED"
                arrived_shipments.append(s)
                self.world.completed_shipments.append(s)
                # Release vehicle
                veh = self.world.vehicles.get(s.vehicle_id)
                if veh:
                    veh.status = VehicleStatus.AVAILABLE
                    veh.availability = True
                    veh.current_node_id = s.destination_node_id
            else:
                remaining_shipments.append(s)

        self.world.active_shipments = remaining_shipments

        # 4. Trigger automated replenishment dispatches
        new_dispatches = self._dispatch_replenishment(current_hour)

        # 5. Generate hourly demand for all nodes & items
        hourly_demands: List[HourlyDemand] = []
        for nid, node in self.world.nodes.items():
            weather = self.world.weather_by_node.get(nid)
            surge_mult = self.disruption_engine.get_demand_surge_multiplier(
                node.id, node.type.value, current_hour
            )
            for item in SupplyCategory:
                d = self.demand_gen.calculate_hourly_demand(
                    node=node,
                    item=item.value,
                    timestamp_hour=current_hour,
                    weather=weather,
                    surge_multiplier=surge_mult,
                    total_hours=self.config.horizon_hours,
                )
                hourly_demands.append(d)

        # 6. Process inventory transitions & demand fulfillment
        processed_demands, snapshots = self.inventory_engine.process_step(
            timestamp_hour=current_hour,
            demands=hourly_demands,
            arrived_shipments=arrived_shipments,
            dispatched_shipments=new_dispatches,
        )

        self.current_hour += 1
        return processed_demands, snapshots

    def run(self) -> SimulationResult:
        """Executes full simulation run across configured horizon and returns calculated metrics."""
        all_snapshots: List[InventorySnapshot] = []

        for _ in range(self.config.horizon_hours):
            _, snapshots = self.step()
            all_snapshots.extend(snapshots)

        # Calculate exact results
        total_requested = sum(s.requested_demand for s in all_snapshots)
        total_fulfilled = sum(s.fulfilled_demand for s in all_snapshots)
        total_unmet = sum(s.unmet_demand for s in all_snapshots)

        fulfillment_rate = (
            round((total_fulfilled / total_requested) * 100.0, 2)
            if total_requested > 0
            else 100.0
        )

        stockout_events = self.inventory_engine.stockout_events
        stockout_hours_total = len(stockout_events)

        earliest_stockout_hour = (
            min((e.timestamp_hour for e in stockout_events), default=None)
            if stockout_events
            else None
        )

        # Identify critical nodes (nodes with stockouts or lowest remaining safety stock)
        node_unmet_counts: Dict[str, float] = {}
        for e in stockout_events:
            node_unmet_counts[e.node_code] = node_unmet_counts.get(e.node_code, 0.0) + e.shortage_amount

        critical_nodes = [
            {"node_code": ncode, "unmet_demand": round(unmet, 1)}
            for ncode, unmet in sorted(node_unmet_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        summary_metrics = {
            "total_nodes": len(self.world.nodes),
            "total_routes": len(self.world.routes),
            "total_vehicles": len(self.world.vehicles),
            "total_shipments_dispatched": len(self.all_shipments),
            "total_shipments_delivered": len(self.world.completed_shipments),
            "active_shipments_end": len(self.world.active_shipments),
            "fulfillment_rate_percent": fulfillment_rate,
            "total_unmet_units": round(total_unmet, 1),
            "total_stockout_events": len(stockout_events),
        }

        return SimulationResult(
            run_id=self.run_id,
            scenario_name=self.config.scenario_name,
            seed=self.config.seed,
            horizon_hours=self.config.horizon_hours,
            total_requested_demand=round(total_requested, 1),
            total_fulfilled_demand=round(total_fulfilled, 1),
            total_unmet_demand=round(total_unmet, 1),
            fulfillment_rate_percent=fulfillment_rate,
            total_stockout_events=len(stockout_events),
            stockout_hours_total=stockout_hours_total,
            critical_nodes=critical_nodes,
            earliest_stockout_hour=earliest_stockout_hour,
            active_disruptions_count=len(self.config.disruptions),
            summary_metrics=summary_metrics,
            snapshots=all_snapshots,
            stockout_events=stockout_events,
            shipments=self.all_shipments,
        )
