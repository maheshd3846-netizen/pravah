"""PRAVAH Backend Server — Module alias for backend.main.

Enables both `uvicorn backend.main:app` and `uvicorn backend.app.main:app`.
"""

from backend.main import app

__all__ = ["app"]
