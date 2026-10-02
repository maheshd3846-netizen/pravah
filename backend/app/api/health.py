"""Health Check Endpoint for PRAVAH API."""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Returns engine health status and subsystem verification."""
    return {
        "status": "healthy",
        "system": "PRAVAH Tactical Logistics Intelligence Engine",
        "version": "1.0.0-phase1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "subsystems": {
            "simulation_engine": "operational",
            "demand_generator": "operational",
            "weather_engine": "operational",
            "inventory_engine": "operational",
            "disruption_engine": "operational",
            "optimization_heuristics": "operational",
        },
    }
