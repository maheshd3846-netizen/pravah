"""Inventory Overview API Router."""

from __future__ import annotations
from fastapi import APIRouter
from simulation.world_generator import WorldGenerator
from simulation.inventory_engine import InventoryEngine
from backend.app.schemas.inventory import (
    InventoryOverviewResponse,
    NodeInventoryStatus,
    StockoutEventResponse,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=InventoryOverviewResponse)
async def get_inventory(seed: int = 42) -> InventoryOverviewResponse:
    """Returns baseline inventory snapshot, stock levels, and days-of-supply across all 15 nodes."""
    world_gen = WorldGenerator(seed=seed)
    nodes = world_gen.generate_nodes()
    inv_engine = InventoryEngine(nodes)

    node_statuses = []
    critical_count = 0

    for nid, node in nodes.items():
        stock_levels = inv_engine.current_inventory[nid]
        days_of_supply = {}
        is_node_critical = False

        for item, stock in stock_levels.items():
            daily_burn = node.reorder_point.get(item, 50.0) / max(1, node.safety_stock_days)
            dos = round(stock / max(0.1, daily_burn), 1)
            days_of_supply[item] = dos
            if dos < 3.0:
                is_node_critical = True

        if is_node_critical:
            critical_count += 1

        node_statuses.append(
            NodeInventoryStatus(
                node_id=node.id,
                node_code=node.code,
                node_name=node.name,
                node_type=node.type.value,
                priority=node.priority,
                stock_levels=stock_levels,
                days_of_supply=days_of_supply,
                is_critical=is_node_critical,
            )
        )

    return InventoryOverviewResponse(
        total_nodes=len(node_statuses),
        critical_nodes_count=critical_count,
        stockout_events_count=len(inv_engine.stockout_events),
        node_inventories=node_statuses,
        recent_stockouts=[],
    )
