"""FastAPI Endpoint Integration Tests for PRAVAH Backend."""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "subsystems" in data


def test_network_endpoint():
    response = client.get("/api/network")
    assert response.status_code == 200
    data = response.json()
    assert data["total_nodes"] == 15
    assert 20 <= data["total_routes"] <= 40
    assert 10 <= data["total_vehicles"] <= 12


def test_inventory_endpoint():
    response = client.get("/api/inventory")
    assert response.status_code == 200
    data = response.json()
    assert data["total_nodes"] == 15
    assert len(data["node_inventories"]) == 15


def test_demand_endpoint():
    response = client.get("/api/demand?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["total_requested"] > 0
    assert "FOOD" in data["by_category"]


def test_scenarios_list_and_create():
    # List scenarios
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    names = [s["name"] for s in scenarios]
    assert "NORMAL" in names
    assert "COMPOUND_DISRUPTION" in names

    # Create new scenario
    new_scen = {
        "name": "TEST_DYNAMIC_SURGE",
        "description": "API test scenario",
        "horizon_hours": 48,
        "disruptions": [
            {
                "id": "DISR_TEST_01",
                "type": "DEMAND_SURGE",
                "target": "ALL_FORWARD_POSTS",
                "severity": 0.5,
                "start_time": 10,
                "duration": 20,
                "impact_factor": 0.4,
                "description": "Test surge",
            }
        ],
    }
    create_resp = client.post("/api/scenarios", json=new_scen)
    assert create_resp.status_code == 200
    assert create_resp.json()["name"] == "TEST_DYNAMIC_SURGE"


def test_simulation_run_and_state():
    run_payload = {
        "scenario_name": "NORMAL",
        "seed": 42,
        "start_hour": 0,
        "horizon_hours": 48,
        "auto_replenish": True,
    }
    response = client.post("/api/simulation/run", json=run_payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "run_id" in res_data
    assert res_data["total_requested_demand"] > 0
    assert res_data["fulfillment_rate_percent"] > 0

    run_id = res_data["run_id"]

    # Query state of run
    state_resp = client.get(f"/api/simulation/{run_id}/state")
    assert state_resp.status_code == 200
    state_data = state_resp.json()
    assert state_data["run_id"] == run_id
    assert state_data["is_completed"] is True
