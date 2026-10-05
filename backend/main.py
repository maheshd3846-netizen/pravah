"""PRAVAH Backend Server — FastAPI Application Entry Point.

Predictive Logistics & Forward Supply Chain Resilience Engine
Smart India Hackathon PS 26251.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

# Add project root directory to sys.path to enable clean imports
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database tables on application startup."""
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization deferred or failed: {e}")
    yield

app = FastAPI(
    title="PRAVAH — Predictive Logistics Intelligence & Resilience Engine",
    description=(
        "Production-oriented discrete-time simulation, demand forecasting, "
        "and logistics decision support system for forward military supply networks."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware
from backend.app.api import api_router
from backend.app.models.database import init_db

# Configure CORS for frontend access
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
frontend_origins_raw = os.getenv("FRONTEND_ORIGIN", os.getenv("CORS_ORIGINS", ""))
allowed_origins = list(default_origins)
if frontend_origins_raw:
    for origin in frontend_origins_raw.split(","):
        cleaned = origin.strip().rstrip("/")
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

allow_all_origins = os.getenv("ALLOW_ALL_ORIGINS", "false").lower() in ("true", "1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else allowed_origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$" if not allow_all_origins else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes under /api
app.include_router(api_router)


@app.get("/")
def root_endpoint():
    """Welcome and API documentation link."""
    return {
        "engine": "PRAVAH",
        "description": "Predictive Logistics & Forward Supply Chain Intelligence",
        "status": "online",
        "docs_url": "/docs",
        "api_v1": "/api",
    }


@app.get("/health")
def health_endpoint():
    """Root health check probe for platform orchestrators (e.g. Render)."""
    return {
        "status": "healthy",
        "engine": "PRAVAH",
    }



if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))
    host = os.getenv("API_HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
    reload_flag = os.getenv("ENVIRONMENT", "development").lower() == "development"
    uvicorn.run("backend.main:app", host=host, port=port, reload=reload_flag)

