"""Scenario Management API Router."""

from __future__ import annotations
from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.schemas.scenarios import (
    ScenarioResponse,
    ScenarioCreateRequest,
    DisruptionSchema,
)
from backend.app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])
scenario_service = ScenarioService()


@router.get("", response_model=List[ScenarioResponse])
async def list_scenarios() -> List[ScenarioResponse]:
    """Lists all configured standard operational and disruption scenarios."""
    scenarios = scenario_service.list_scenarios()
    results = []
    for sc in scenarios:
        disruptions = [
            DisruptionSchema(
                id=d["id"],
                type=d["type"],
                target=d["target"],
                severity=float(d["severity"]),
                start_time=int(d["start_time"]),
                duration=int(d["duration"]),
                impact_factor=float(d["impact_factor"]),
                description=d.get("description", ""),
            )
            for d in sc.get("disruptions", [])
        ]
        results.append(
            ScenarioResponse(
                name=sc["name"],
                description=sc.get("description", ""),
                horizon_hours=sc.get("horizon_hours", 336),
                disruptions=disruptions,
            )
        )
    return results


@router.post("", response_model=ScenarioResponse)
async def create_scenario(request: ScenarioCreateRequest) -> ScenarioResponse:
    """Registers a new custom operational disruption scenario."""
    scenario_dict = request.model_dump()
    saved = scenario_service.create_scenario(scenario_dict)
    return ScenarioResponse(**saved)
