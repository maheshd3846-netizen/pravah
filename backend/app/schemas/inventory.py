"""Pydantic Schemas for Inventory and Stockout Events."""

from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel


class StockoutEventResponse(BaseModel):
    event_id: str
    node_id: str
    node_code: str
    item: str
    timestamp_hour: int
    shortage_amount: float
    duration_hours: int


class NodeInventoryStatus(BaseModel):
    node_id: str
    node_code: str
    node_name: str
    node_type: str
    priority: int
    stock_levels: Dict[str, float]
    days_of_supply: Dict[str, float]
    is_critical: bool


class InventoryOverviewResponse(BaseModel):
    total_nodes: int
    critical_nodes_count: int
    stockout_events_count: int
    node_inventories: List[NodeInventoryStatus]
    recent_stockouts: List[StockoutEventResponse]
