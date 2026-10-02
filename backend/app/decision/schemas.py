"""Data Contracts, Schemas, and Enums for PRAVAH Decision & Recommendation Layer."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Deterministic military logistics decision-support action categories."""
    MOVE = "MOVE"
    REROUTE = "REROUTE"
    REALLOCATE = "REALLOCATE"
    PRIORITIZE = "PRIORITIZE"
    HOLD = "HOLD"
    DEFER = "DEFER"


class RecommendationStatus(str, Enum):
    """Lifecycle status of a generated decision recommendation."""
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    MIXED = "MIXED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class ConfidenceLevel(str, Enum):
    """Evidence-derived confidence rating."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DataQualityState(str, Enum):
    """Operational readiness of upstream telemetry and sensor data."""
    READY = "READY"
    DEGRADED = "DEGRADED"
    INSUFFICIENT = "INSUFFICIENT"


class EvidenceType(str, Enum):
    """Categorization of verifiable operational facts."""
    STOCKOUT_PROBABILITY = "STOCKOUT_PROBABILITY"
    TIME_TO_ZERO = "TIME_TO_ZERO"
    DEMAND_SURGE = "DEMAND_SURGE"
    ROUTE_STATUS = "ROUTE_STATUS"
    ROUTE_RISK = "ROUTE_RISK"
    SOURCE_INVENTORY = "SOURCE_INVENTORY"
    VEHICLE_CAPACITY = "VEHICLE_CAPACITY"
    COUNTERFACTUAL_DELTA = "COUNTERFACTUAL_DELTA"
    WEATHER_SEVERITY = "WEATHER_SEVERITY"


class DecisionEvidenceItem(BaseModel):
    """Atomic verifiable fact supporting a recommendation."""
    type: str
    value: Any
    source: str
    description: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


class DecisionConfidence(BaseModel):
    """Measurable confidence rating with supporting factors."""
    level: str  # HIGH, MEDIUM, LOW
    score: float
    factors: List[str] = Field(default_factory=list)


class RouteAlternative(BaseModel):
    """Comparison of selected route vs alternative network options."""
    route_id: str
    status: str
    distance_km: float
    risk_score: float
    travel_time_hours: float
    is_selected: bool
    selection_reason: str = ""


class RecommendationSchema(BaseModel):
    """Auditable, structured decision-support recommendation."""
    recommendation_id: str
    scenario_id: str
    optimization_run_id: str
    evaluation_id: Optional[str] = None
    priority: int = 3  # 1 (Highest) to 5 (Lowest)
    action_type: str
    source_node: str
    destination_node: str
    item: str
    quantity: float
    route: str
    vehicle: str
    planned_departure: int
    expected_arrival: int
    title: str
    reason: str
    evidence: List[DecisionEvidenceItem] = Field(default_factory=list)
    tradeoffs: Dict[str, Any] = Field(default_factory=dict)
    expected_effect: str = ""
    verified_effect: str = ""
    status: str
    confidence: DecisionConfidence
    validation_state: Dict[str, str] = Field(default_factory=dict)
    conflict_detected: bool = False
    conflict_details: List[str] = Field(default_factory=list)
    alternatives: List[RouteAlternative] = Field(default_factory=list)
    audit_trail: Dict[str, str] = Field(default_factory=dict)
    created_at: str


class RecommendationGenerateRequest(BaseModel):
    """Request payload for recommendation generation."""
    scenario_id: str = "COMPOUND_DISRUPTION"
    optimization_run_id: Optional[str] = None
    evaluation_id: Optional[str] = None
    demand_policy: str = "P80"
    data_quality_state: str = "READY"
    horizon_hours: int = 72
    seed: int = 42


class RecommendationListResponse(BaseModel):
    """Collection response of decision recommendations with summary metrics."""
    total_recommendations: int
    status_counts: Dict[str, int]
    action_counts: Dict[str, int]
    recommendations: List[RecommendationSchema]


class DecisionSummaryResponse(BaseModel):
    """Executive decision dashboard summary for command-center display."""
    readiness: str
    data_quality: str
    critical_nodes: List[Dict[str, Any]]
    active_risks: List[Dict[str, Any]]
    recommendations_count: int
    verified_actions_count: int
    top_recommendations: List[RecommendationSchema]
    overall_tradeoffs: Dict[str, Any]
    last_updated: str
