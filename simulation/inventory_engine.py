"""Inventory Engine for PRAVAH Logistics System.

Implements non-negative discrete-event balance equations:
I[t+1] = I[t] + receipts + transfer_in - transfer_out - demand
Tracks fulfilled vs unmet demand, stockouts, and days-of-supply metrics.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from simulation.world_generator import (
    Node,
    SupplyCategory,
    Shipment,
)
from simulation.demand_generator import HourlyDemand


@dataclass
class StockoutEvent:
    event_id: str
    node_id: str
    node_code: str
    item: str
    timestamp_hour: int
    shortage_amount: float
    duration_hours: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "node_id": self.node_id,
            "node_code": self.node_code,
            "item": self.item,
            "timestamp_hour": self.timestamp_hour,
            "shortage_amount": self.shortage_amount,
            "duration_hours": self.duration_hours,
        }


@dataclass
class InventorySnapshot:
    timestamp_hour: int
    node_id: str
    node_code: str
    item: str
    starting_inventory: float
    receipts: float
    transfers_in: float
    transfers_out: float
    requested_demand: float
    fulfilled_demand: float
    unmet_demand: float
    ending_inventory: float
    days_of_supply: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp_hour": self.timestamp_hour,
            "node_id": self.node_id,
            "node_code": self.node_code,
            "item": self.item,
            "starting_inventory": self.starting_inventory,
            "receipts": self.receipts,
            "transfers_in": self.transfers_in,
            "transfers_out": self.transfers_out,
            "requested_demand": self.requested_demand,
            "fulfilled_demand": self.fulfilled_demand,
            "unmet_demand": self.unmet_demand,
            "ending_inventory": self.ending_inventory,
            "days_of_supply": self.days_of_supply,
        }


class InventoryEngine:
    """Manages multi-echelon stock levels, arrivals, dispatches, and consumption."""

    def __init__(self, nodes: Dict[str, Node]):
        self.nodes = nodes
        # Current inventory state: current_inventory[node_id][item] = float
        self.current_inventory: Dict[str, Dict[str, float]] = {}
        for nid, node in nodes.items():
            self.current_inventory[nid] = {}
            for item in SupplyCategory:
                self.current_inventory[nid][item.value] = float(node.initial_inventory.get(item.value, 0.0))

        self.stockout_events: List[StockoutEvent] = []
        self.history: List[InventorySnapshot] = []

    def get_stock(self, node_id: str, item: str) -> float:
        """Returns current available stock for given node and supply category."""
        return self.current_inventory.get(node_id, {}).get(item, 0.0)

    def process_step(
        self,
        timestamp_hour: int,
        demands: List[HourlyDemand],
        arrived_shipments: List[Shipment],
        dispatched_shipments: List[Shipment],
    ) -> Tuple[List[HourlyDemand], List[InventorySnapshot]]:
        """Executes inventory state transition equation for simulation timestep t."""
        # 1. Aggregate receipts from delivered shipments
        receipts: Dict[Tuple[str, str], float] = {}
        for s in arrived_shipments:
            key = (s.destination_node_id, s.item)
            receipts[key] = receipts.get(key, 0.0) + s.quantity

        # 2. Aggregate transfers out from newly dispatched shipments
        dispatches: Dict[Tuple[str, str], float] = {}
        for s in dispatched_shipments:
            key = (s.source_node_id, s.item)
            dispatches[key] = dispatches.get(key, 0.0) + s.quantity

        step_snapshots: List[InventorySnapshot] = []
        processed_demands: List[HourlyDemand] = []

        # Index demand by (node_id, item)
        demand_map: Dict[Tuple[str, str], HourlyDemand] = {
            (d.node_id, d.item): d for d in demands
        }

        for nid, node in self.nodes.items():
            daily_burn_dict = node.reorder_point

            for item_cat in SupplyCategory:
                item = item_cat.value
                start_stock = self.current_inventory[nid][item]
                inflow = receipts.get((nid, item), 0.0)
                outflow_transfers = dispatches.get((nid, item), 0.0)

                # Available stock after transfers and receipts
                # Transfers out cannot exceed existing stock; if attempted, clamped
                actual_transfer_out = min(start_stock, outflow_transfers)
                stock_after_transfers = start_stock - actual_transfer_out + inflow

                # Obtain demand for this hour
                d_record = demand_map.get((nid, item))
                if d_record is None:
                    req_demand = 0.0
                else:
                    req_demand = d_record.requested_demand

                # Inventory cannot become negative
                if stock_after_transfers >= req_demand:
                    fulfilled = req_demand
                    unmet = 0.0
                    end_stock = stock_after_transfers - fulfilled
                else:
                    fulfilled = max(0.0, stock_after_transfers)
                    unmet = req_demand - fulfilled
                    end_stock = 0.0

                    # Record stockout event
                    event = StockoutEvent(
                        event_id=f"SO_{nid}_{item}_{timestamp_hour}",
                        node_id=nid,
                        node_code=node.code,
                        item=item,
                        timestamp_hour=timestamp_hour,
                        shortage_amount=round(unmet, 2),
                    )
                    self.stockout_events.append(event)

                self.current_inventory[nid][item] = round(end_stock, 2)

                # Update demand record
                if d_record is not None:
                    d_record.fulfilled_demand = round(fulfilled, 2)
                    d_record.unmet_demand = round(unmet, 2)
                    processed_demands.append(d_record)

                # Calculate days of supply
                daily_burn = (daily_burn_dict.get(item, 50.0) / max(1, node.safety_stock_days))
                days_of_supply = round(end_stock / max(0.1, daily_burn), 1)

                snapshot = InventorySnapshot(
                    timestamp_hour=timestamp_hour,
                    node_id=nid,
                    node_code=node.code,
                    item=item,
                    starting_inventory=round(start_stock, 2),
                    receipts=round(inflow, 2),
                    transfers_in=0.0,
                    transfers_out=round(actual_transfer_out, 2),
                    requested_demand=round(req_demand, 2),
                    fulfilled_demand=round(fulfilled, 2),
                    unmet_demand=round(unmet, 2),
                    ending_inventory=round(end_stock, 2),
                    days_of_supply=days_of_supply,
                )
                self.history.append(snapshot)
                step_snapshots.append(snapshot)

        return processed_demands, step_snapshots
