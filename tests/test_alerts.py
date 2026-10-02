"""Tests for Early Warning Engine and Factual Explanation Synthesis."""

from backend.app.risk.alerts import EarlyWarningEngine
from backend.app.risk.explanations import ExplanationEngine


def test_alerts_triggering_under_critical_stress():
    engine = EarlyWarningEngine()

    # Extreme conditions: current inventory 50, safety stock 300, time to zero 6 hours
    alerts = engine.evaluate_inventory_alerts(
        node_id="NODE_FP_04",
        node_code="FP-04",
        item="FUEL",
        current_inventory=50.0,
        safety_stock=300.0,
        time_to_ss_hours=1,
        time_to_zero_hours=6,
        stockout_prob=0.95,
        p95_cumulative_demand=450.0,
        lead_time_hours=24.0,
        route_status="BLOCKED",
        weather_severity="SEVERE",
        demand_surge_percent=30.0,
    )

    assert len(alerts) >= 1
    crit_alerts = [a for a in alerts if a.severity == "CRITICAL"]
    assert len(crit_alerts) == 1
    assert crit_alerts[0].alert_type == "CRITICAL_STOCKOUT_IMMINENT"
    assert "FP-04" in crit_alerts[0].explanation
    assert "FUEL" in crit_alerts[0].explanation
    assert len(crit_alerts[0].causes) > 0


def test_no_false_alerts_when_conditions_are_safe():
    engine = EarlyWarningEngine()

    # Completely safe conditions: abundant inventory, no stockout risk, no surge
    alerts = engine.evaluate_inventory_alerts(
        node_id="NODE_CD_01",
        node_code="CD-01",
        item="FOOD",
        current_inventory=50000.0,
        safety_stock=10000.0,
        time_to_ss_hours=None,
        time_to_zero_hours=None,
        stockout_prob=0.0,
        p95_cumulative_demand=5000.0,
        lead_time_hours=24.0,
        route_status="AVAILABLE",
        weather_severity="NORMAL",
        demand_surge_percent=0.0,
    )

    # Must NOT produce false positive alerts
    assert len(alerts) == 0


def test_route_alerts_on_blockage():
    engine = EarlyWarningEngine()

    # High dependency blocked route
    route_alerts = engine.evaluate_route_alerts(
        route_id="ROUTE_R_01",
        route_code="R-01",
        source_code="CD-01",
        dest_code="RH-01",
        status="BLOCKED",
        weather_severity="NORMAL",
        dependency_factor=0.65,
    )

    assert len(route_alerts) == 1
    assert route_alerts[0].severity == "CRITICAL"
    assert route_alerts[0].alert_type == "SUPPLY_CORRIDOR_BLOCKED"
    assert "R-01" in route_alerts[0].explanation


def test_deterministic_explanation_synthesis():
    expl_engine = ExplanationEngine()

    text = expl_engine.explain_stockout_risk(
        node_code="FP-02",
        item="WATER",
        current_inventory=120.0,
        safety_stock=400.0,
        time_to_ss_hours=3,
        time_to_zero_hours=18,
        stockout_prob=0.82,
        route_status="DEGRADED",
        weather_severity="MODERATE",
        demand_surge_percent=25.0,
    )

    # Explanation must be factual and contain real parameters
    assert "WATER at FP-02" in text
    assert "18 hours" in text
    assert "DEGRADED" in text
    assert "82.0%" in text
