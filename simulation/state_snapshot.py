"""Deterministic Simulation State Snapshot & Cloning Architecture for PRAVAH.

Provides bitwise reproducible state capture, serializable hashing, and isolated
cloning to ensure paired counterfactual experiments start from the identical initial world.
"""

from __future__ import annotations
import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from simulation.world_generator import (
    Node,
    Route,
    Vehicle,
    Shipment,
    WorldState,
    WorldGenerator,
    RouteStatus,
    VehicleStatus,
)


@dataclass
class StateSnapshot:
    """Serializable, immutable snapshot of the simulation world state."""
    snapshot_id: str
    seed: int
    current_hour: int
    scenario_name: str
    nodes_data: Dict[str, Dict[str, Any]]
    routes_data: Dict[str, Dict[str, Any]]
    vehicles_data: Dict[str, Dict[str, Any]]
    inventory_data: Dict[str, Dict[str, float]]
    active_shipments_data: List[Dict[str, Any]]
    disruptions_data: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def hash(self) -> str:
        """Computes a deterministic SHA-256 fingerprint of the initial state."""
        # Normalize and serialize core physical state in deterministic key order
        state_repr = {
            "seed": self.seed,
            "current_hour": self.current_hour,
            "scenario": self.scenario_name,
            "nodes": {
                nid: {
                    "type": str(n.get("type")),
                    "priority": n.get("priority"),
                    "initial_inventory": n.get("initial_inventory", {}),
                }
                for nid, n in sorted(self.nodes_data.items())
            },
            "routes": {
                rid: {
                    "src": r.get("source_node_id"),
                    "dst": r.get("destination_node_id"),
                    "status": str(r.get("status")),
                    "distance_km": r.get("distance_km"),
                    "capacity": r.get("max_capacity"),
                }
                for rid, r in sorted(self.routes_data.items())
            },
            "inventory": {
                nid: {k: round(v, 2) for k, v in sorted(items.items())}
                for nid, items in sorted(self.inventory_data.items())
            },
            "vehicles": {
                vid: {
                    "status": str(v.get("status")),
                    "capacity": v.get("capacity"),
                    "node": v.get("current_node_id"),
                }
                for vid, v in sorted(self.vehicles_data.items())
            },
        }
        serialized = json.dumps(state_repr, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def clone(self) -> StateSnapshot:
        """Deep copy returning an independent snapshot."""
        return copy.deepcopy(self)

    @classmethod
    def capture(cls, simulator: Any) -> StateSnapshot:
        """Captures complete operational state from an active Simulator instance."""
        world: WorldState = simulator.world
        sim_id = getattr(simulator, "run_id", "SNAPSHOT")

        nodes_dict = {nid: n.to_dict() for nid, n in world.nodes.items()}
        routes_dict = {rid: r.to_dict() for rid, r in world.routes.items()}
        vehicles_dict = {vid: v.to_dict() for vid, v in world.vehicles.items()}

        inv_data = {
            nid: dict(items)
            for nid, items in simulator.inventory_engine.current_inventory.items()
        }

        active_ships = [s.to_dict() for s in world.active_shipments]
        disruptions = [d.to_dict() for d in simulator.disruption_engine.disruptions]

        return cls(
            snapshot_id=f"SNAP_{sim_id}",
            seed=simulator.config.seed,
            current_hour=simulator.current_hour,
            scenario_name=simulator.config.scenario_name,
            nodes_data=nodes_dict,
            routes_data=routes_dict,
            vehicles_data=vehicles_dict,
            inventory_data=inv_data,
            active_shipments_data=active_ships,
            disruptions_data=disruptions,
            metadata={"horizon_hours": simulator.config.horizon_hours},
        )

    def restore_into(self, simulator: Any) -> None:
        """Restores snapshot data directly into an instantiated simulator without pointer aliasing."""
        simulator.current_hour = self.current_hour
        simulator.config.seed = self.seed
        simulator.config.scenario_name = self.scenario_name

        # Restore inventory
        simulator.inventory_engine.current_inventory = copy.deepcopy(self.inventory_data)

        # Restore route statuses
        for rid, r_dict in self.routes_data.items():
            if rid in simulator.world.routes:
                r_obj = simulator.world.routes[rid]
                r_status_str = r_dict.get("status", "AVAILABLE")
                r_obj.status = RouteStatus(r_status_str) if isinstance(r_status_str, str) else r_status_str

        # Restore vehicle statuses
        for vid, v_dict in self.vehicles_data.items():
            if vid in simulator.world.vehicles:
                v_obj = simulator.world.vehicles[vid]
                v_status_str = v_dict.get("status", "AVAILABLE")
                v_obj.status = VehicleStatus(v_status_str) if isinstance(v_status_str, str) else v_status_str
                v_obj.availability = (v_obj.status == VehicleStatus.AVAILABLE)
                v_obj.current_node_id = v_dict.get("current_node_id", v_obj.current_node_id)

        # Clear shipments
        simulator.world.active_shipments = []
        simulator.world.completed_shipments = []
        simulator.all_shipments = []
