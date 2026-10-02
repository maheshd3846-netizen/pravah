"""Pydantic Schemas for Early Warning Alerts."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class AlertItemResponse(BaseModel):
    alert_id: str
    severity: str  # INFO, WARNING, HIGH, CRITICAL
    node_id: str
    node_code: str
    item: str
    alert_type: str
    time_horizon_hours: Optional[int]
    probability: Optional[float]
    causes: List[str]
    evidence: Dict[str, Any]
    explanation: str


class AlertsListResponse(BaseModel):
    total_alerts: int
    critical_count: int
    high_count: int
    warning_count: int
    alerts: List[AlertItemResponse]
