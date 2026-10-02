"""FastAPI Integration Tests for Intelligence, Forecasting, and Risk Endpoints."""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_risk_overview_and_recalculate():
    # Test recalculation
    recalc_resp = client.post("/api/risk/recalculate?seed=42")
    assert recalc_resp.status_code == 200
    data = recalc_resp.json()
    assert data["total_nodes_assessed"] == 15
    assert len(data["nodes"]) == 15

    # Test overview
    overview_resp = client.get("/api/risk/overview")
    assert overview_resp.status_code == 200
    assert overview_resp.json()["total_nodes_assessed"] == 15


def test_api_risk_nodes_and_single_node():
    nodes_resp = client.get("/api/risk/nodes")
    assert nodes_resp.status_code == 200
    nodes = nodes_resp.json()
    assert len(nodes) == 15

    first_node = nodes[0]
    nid = first_node["node_id"]

    # Query single node
    single_resp = client.get(f"/api/risk/{nid}")
    assert single_resp.status_code == 200
    s_data = single_resp.json()
    assert s_data["node_id"] == nid
    assert "components" in s_data
    assert "inventory" in s_data["components"]


def test_api_alerts():
    alerts_resp = client.get("/api/alerts")
    assert alerts_resp.status_code == 200
    a_data = alerts_resp.json()
    assert "total_alerts" in a_data
    assert isinstance(a_data["alerts"], list)


def test_api_forecast_run():
    payload = {
        "node_id": "NODE_FP_01",
        "item_id": "FUEL",
        "horizon_hours": 24,
        "model_type": "xgboost",
        "include_stockout_simulation": True,
    }
    resp = client.post("/api/forecast/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["p50"]) == 24
    assert len(data["p80"]) == 24
    assert len(data["p95"]) == 24
    assert data["p50"][0] <= data["p80"][0] <= data["p95"][0]
    assert data["model_version"] == "xgb-demand-v1"
    assert data["feature_version"] == "demand-features-v1"


def test_api_forecast_get():
    resp = client.get("/api/forecast/NODE_FP_01/FOOD")
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_id"] == "NODE_FP_01"
    assert data["item_id"] == "FOOD"
    assert len(data["p50"]) == 24
