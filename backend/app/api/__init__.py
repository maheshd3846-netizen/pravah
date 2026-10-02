"""Unified API router configuration for PRAVAH backend."""

from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.simulation import router as simulation_router
from backend.app.api.network import router as network_router
from backend.app.api.inventory import router as inventory_router
from backend.app.api.demand import router as demand_router
from backend.app.api.scenarios import router as scenarios_router
from backend.app.api.forecast import router as forecast_router
from backend.app.api.risk import router as risk_router
from backend.app.api.alerts import router as alerts_router

api_router = APIRouter(prefix="/api")

api_router.include_router(health_router)
api_router.include_router(simulation_router)
api_router.include_router(network_router)
api_router.include_router(inventory_router)
api_router.include_router(demand_router)
api_router.include_router(scenarios_router)
api_router.include_router(forecast_router)
api_router.include_router(risk_router)
api_router.include_router(alerts_router)

__all__ = ["api_router"]
