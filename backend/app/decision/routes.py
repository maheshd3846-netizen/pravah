"""FastAPI Routes for Decision Support and Recommendation Engine."""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.decision.schemas import (
    RecommendationGenerateRequest,
    RecommendationListResponse,
    RecommendationSchema,
    DecisionSummaryResponse,
)
from backend.app.decision.service import get_decision_service

router = APIRouter(tags=["Decision & Recommendations"])


@router.post("/recommendations/generate", response_model=RecommendationListResponse)
def generate_recommendations(request: RecommendationGenerateRequest):
    """Generates prioritized, fact-grounded recommendations from current intelligence and optimization."""
    try:
        service = get_decision_service()
        return service.generate_recommendations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.get("/recommendations", response_model=RecommendationListResponse)
def list_recommendations(
    scenario_id: Optional[str] = Query(None, description="Filter by operational scenario"),
    status: Optional[str] = Query(None, description="Filter by status (PROPOSED, VERIFIED, MIXED, REJECTED, INCONCLUSIVE)"),
    priority: Optional[int] = Query(None, description="Filter by priority tier (1 to 5)"),
    node: Optional[str] = Query(None, description="Filter by source or destination node"),
    item: Optional[str] = Query(None, description="Filter by commodity item"),
):
    """Lists generated recommendations with optional multi-attribute filtering."""
    try:
        service = get_decision_service()
        return service.list_recommendations(
            scenario_id=scenario_id,
            status=status,
            priority=priority,
            node=node,
            item=item,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recommendations: {str(e)}")


@router.get("/recommendations/{recommendation_id}", response_model=RecommendationSchema)
def get_recommendation(recommendation_id: str):
    """Retrieves an individual recommendation with its full evidence, audit trail, and alternatives."""
    service = get_decision_service()
    rec = service.get_recommendation(recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation '{recommendation_id}' not found")
    return rec


@router.get("/decision/summary", response_model=DecisionSummaryResponse)
def get_decision_summary():
    """Retrieves tactical readiness overview, critical nodes, active risks, and top verified actions."""
    try:
        service = get_decision_service()
        return service.get_decision_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve decision summary: {str(e)}")
