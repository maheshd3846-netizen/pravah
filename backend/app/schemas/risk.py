"""Pydantic Schemas for Risk Intelligence, Criticality, and Network Propagation."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class RiskComponentsSchema(BaseModel):
    inventory: float
    demand: float
    route: float
    transport: float
    environment: float


class NodeRiskDetailResponse(BaseModel):
    node_id: str
    node_code: str
    overall_risk: float
    level: str
    components: RiskComponentsSchema
    raw_indicators: Dict[str, Any]
    criticality: Optional[Dict[str, Any]] = None
    propagated_risk: Optional[Dict[str, Any]] = None


class RiskOverviewResponse(BaseModel):
    total_nodes_assessed: int
    high_risk_nodes_count: int
    high_risk_nodes: List[str]
    blocked_routes_count: int
    blocked_routes: List[str]
    total_active_alerts: int
    critical_alerts_count: int
    nodes: List[NodeRiskDetailResponse]
