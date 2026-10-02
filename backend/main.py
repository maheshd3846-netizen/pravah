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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
