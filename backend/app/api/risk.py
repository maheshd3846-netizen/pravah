"""Risk Intelligence API Endpoints."""

from __future__ import annotations
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException

from simulation.world_generator import WorldGenerator
from backend.app.risk.service import RiskIntelligenceService
from backend.app.schemas.risk import (
    RiskOverviewResponse,
    NodeRiskDetailResponse,
    RiskComponentsSchema,
)

router = APIRouter(prefix="/risk", tags=["Risk Intelligence"])
risk_service = RiskIntelligenceService()


def _ensure_evaluated():
    if not risk_service._cached_assessments:
        world = WorldGenerator(seed=42).generate_world()
        risk_service.evaluate_world_risk(world)


@router.get("/overview", response_model=RiskOverviewResponse)
async def get_risk_overview() -> RiskOverviewResponse:
    """Returns whole-network risk telemetry, critical nodes, blocked corridors, and active alert counts."""
    _ensure_evaluated()
    summary = {
        "total_nodes_assessed": len(risk_service._cached_assessments),
        "high_risk_nodes_count": sum(1 for a in risk_service._cached_assessments.values() if a.level in ["HIGH", "CRITICAL"]),
        "high_risk_nodes": [a.node_code for a in risk_service._cached_assessments.values() if a.level in ["HIGH", "CRITICAL"]],
        "blocked_routes_count": 0,
        "blocked_routes": [],
        "total_active_alerts": len(risk_service._cached_alerts),
        "critical_alerts_count": sum(1 for a in risk_service._cached_alerts if a.severity == "CRITICAL"),
    }

    nodes_detail = []
    for nid, a in risk_service._cached_assessments.items():
        nodes_detail.append(
            NodeRiskDetailResponse(
                node_id=a.node_id,
                node_code=a.node_code,
                overall_risk=a.overall_risk,
                level=a.level,
                components=RiskComponentsSchema(**a.components),
                raw_indicators=a.raw_indicators,
                criticality=risk_service._cached_criticalities.get(nid),
                propagated_risk=risk_service._cached_propagated.get(nid),
            )
        )

    return RiskOverviewResponse(
        total_nodes_assessed=summary["total_nodes_assessed"],
        high_risk_nodes_count=summary["high_risk_nodes_count"],
        high_risk_nodes=summary["high_risk_nodes"],
        blocked_routes_count=summary["blocked_routes_count"],
        blocked_routes=summary["blocked_routes"],
        total_active_alerts=summary["total_active_alerts"],
        critical_alerts_count=summary["critical_alerts_count"],
        nodes=nodes_detail,
    )


@router.get("/nodes", response_model=List[NodeRiskDetailResponse])
async def list_node_risks() -> List[NodeRiskDetailResponse]:
    """Lists risk assessments, component breakdown, and criticality for all 15 nodes."""
    _ensure_evaluated()
    return [
        NodeRiskDetailResponse(
            node_id=a.node_id,
            node_code=a.node_code,
            overall_risk=a.overall_risk,
            level=a.level,
            components=RiskComponentsSchema(**a.components),
            raw_indicators=a.raw_indicators,
            criticality=risk_service._cached_criticalities.get(nid),
            propagated_risk=risk_service._cached_propagated.get(nid),
        )
        for nid, a in risk_service._cached_assessments.items()
    ]


@router.get("/{node_id}", response_model=NodeRiskDetailResponse)
async def get_node_risk(node_id: str) -> NodeRiskDetailResponse:
    """Returns detailed risk components, propagation sources, and criticality for a specific node."""
    _ensure_evaluated()
    target_nid = node_id
    if target_nid not in risk_service._cached_assessments:
        # Search by code
        for nid, a in risk_service._cached_assessments.items():
            if a.node_code == node_id:
                target_nid = nid
                break

    a = risk_service._cached_assessments.get(target_nid)
    if not a:
        raise HTTPException(status_code=404, detail=f"Risk profile for node '{node_id}' not found.")

    return NodeRiskDetailResponse(
        node_id=a.node_id,
        node_code=a.node_code,
        overall_risk=a.overall_risk,
        level=a.level,
        components=RiskComponentsSchema(**a.components),
        raw_indicators=a.raw_indicators,
        criticality=risk_service._cached_criticalities.get(target_nid),
        propagated_risk=risk_service._cached_propagated.get(target_nid),
    )


@router.post("/recalculate", response_model=RiskOverviewResponse)
async def recalculate_risk(seed: int = 42) -> RiskOverviewResponse:
    """Forces fresh risk recalculation across nodes, routes, weather state, and inventory."""
    world = WorldGenerator(seed=seed).generate_world()
    risk_service.evaluate_world_risk(world)
    return await get_risk_overview()
