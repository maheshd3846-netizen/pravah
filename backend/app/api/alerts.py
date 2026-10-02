"""Early Warning Alerts API Endpoints."""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter

from backend.app.api.risk import risk_service, _ensure_evaluated
from backend.app.schemas.alerts import AlertsListResponse, AlertItemResponse

router = APIRouter(prefix="/alerts", tags=["Early Warnings"])


@router.get("", response_model=AlertsListResponse)
async def list_alerts(
    severity: Optional[str] = None,
    node_id: Optional[str] = None,
) -> AlertsListResponse:
    """Lists structured operational alerts with causes, evidence, and deterministic explanations."""
    _ensure_evaluated()
    alerts = risk_service._cached_alerts

    if severity:
        alerts = [a for a in alerts if a.severity.upper() == severity.upper()]
    if node_id:
        alerts = [a for a in alerts if a.node_id == node_id or a.node_code == node_id]

    items = [
        AlertItemResponse(
            alert_id=a.alert_id,
            severity=a.severity,
            node_id=a.node_id,
            node_code=a.node_code,
            item=a.item,
            alert_type=a.alert_type,
            time_horizon_hours=a.time_horizon_hours,
            probability=a.probability,
            causes=a.causes,
            evidence=a.evidence,
            explanation=a.explanation,
        )
        for a in alerts
    ]

    return AlertsListResponse(
        total_alerts=len(items),
        critical_count=sum(1 for a in items if a.severity == "CRITICAL"),
        high_count=sum(1 for a in items if a.severity == "HIGH"),
        warning_count=sum(1 for a in items if a.severity == "WARNING"),
        alerts=items,
    )
