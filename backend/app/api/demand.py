"""Tactical Demand History and Forecast API Router."""

from __future__ import annotations
from typing import Dict
from fastapi import APIRouter
from simulation.world_generator import WorldGenerator, SupplyCategory
from simulation.demand_generator import DemandGenerator
from simulation.weather_generator import WeatherGenerator
from backend.app.schemas.demand import (
    DemandOverviewResponse,
    DemandPointResponse,
)

router = APIRouter(prefix="/demand", tags=["Demand"])


@router.get("", response_model=DemandOverviewResponse)
async def get_demand(seed: int = 42, hours: int = 48) -> DemandOverviewResponse:
    """Returns sample synthetic demand time series and category aggregation."""
    world_gen = WorldGenerator(seed=seed)
    nodes = world_gen.generate_nodes()
    demand_gen = DemandGenerator(seed=seed)
    weather_gen = WeatherGenerator(seed=seed)

    records = []
    category_totals: Dict[str, Dict[str, float]] = {
        c.value: {"requested": 0.0, "fulfilled": 0.0, "unmet": 0.0}
        for c in SupplyCategory
    }

    total_req = 0.0

    for h in range(min(hours, 72)):
        for node in nodes.values():
            weather = weather_gen.generate_weather(node, h)
            for item in SupplyCategory:
                d = demand_gen.calculate_hourly_demand(
                    node=node,
                    item=item.value,
                    timestamp_hour=h,
                    weather=weather,
                )
                total_req += d.requested_demand
                category_totals[item.value]["requested"] = round(
                    category_totals[item.value]["requested"] + d.requested_demand, 1
                )

                if len(records) < 50:
                    records.append(
                        DemandPointResponse(
                            node_id=node.id,
                            node_code=node.code,
                            item=item.value,
                            timestamp_hour=h,
                            requested_demand=d.requested_demand,
                            fulfilled_demand=d.requested_demand,
                            unmet_demand=0.0,
                        )
                    )

    return DemandOverviewResponse(
        total_requested=round(total_req, 1),
        total_fulfilled=round(total_req, 1),
        total_unmet=0.0,
        overall_fulfillment_rate=100.0,
        by_category=category_totals,
        recent_sample=records,
    )
