"""Tests for Risk Engine, Categorical Thresholds, and Network Propagation."""

import networkx as nx
from backend.app.risk.evaluator import (
    RiskEvaluator,
    RiskWeightsConfig,
    RiskThresholdsConfig,
)
from backend.app.risk.propagation import (
    NetworkRiskPropagator,
    PropagationConfig,
)
from backend.app.risk.criticality import NodeCriticalityCalculator


def test_risk_components_normalization_and_weights():
    weights = RiskWeightsConfig(
        inventory_weight=0.30,
        demand_weight=0.25,
        route_weight=0.20,
        transport_weight=0.15,
        environment_weight=0.10,
    )
    evaluator = RiskEvaluator(weights=weights)

    # Test normalization bounds
    inv_r = evaluator.evaluate_inventory_risk(
        stockout_probability=0.75,
        time_to_zero_hours=12,
        time_to_safety_stock_hours=4,
        current_inventory=300.0,
        safety_stock=600.0,
    )
    dem_r = evaluator.evaluate_demand_risk(
        demand_growth_ratio=1.4,
        demand_volatility_cv=0.3,
        forecast_spread_ratio=0.5,
    )
    route_r = evaluator.evaluate_route_risk(
        inflow_routes_status=["BLOCKED", "DEGRADED"],
        alternate_routes_count=0,
        mean_route_reliability=0.7,
    )
    trans_r = evaluator.evaluate_transport_risk(
        vehicle_availability_ratio=0.5,
        active_delays_count=2,
    )
    env_r = evaluator.evaluate_environment_risk(
        weather_severity="SEVERE",
        wind_speed=70.0,
        visibility=1.0,
        temperature=-20.0,
    )

    for r in [inv_r, dem_r, route_r, trans_r, env_r]:
        assert 0.0 <= r <= 1.0, f"Component risk {r} must be in [0, 1]"

    overall = evaluator.calculate_overall_risk(
        node_id="NODE_FP_01",
        node_code="FP-01",
        inventory_risk=inv_r,
        demand_risk=dem_r,
        route_risk=route_r,
        transport_risk=trans_r,
        environment_risk=env_r,
    )

    assert 0.0 <= overall.overall_risk <= 1.0
    assert overall.level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]


def test_risk_threshold_levels():
    evaluator = RiskEvaluator()

    # Low risk
    low = evaluator.calculate_overall_risk("N1", "C1", 0.1, 0.1, 0.1, 0.1, 0.1)
    assert low.level == "LOW"

    # Moderate risk
    mod = evaluator.calculate_overall_risk("N2", "C2", 0.5, 0.45, 0.45, 0.4, 0.4)
    assert mod.level in ["MODERATE", "HIGH"]

    # Critical risk
    crit = evaluator.calculate_overall_risk("N3", "C3", 0.95, 0.9, 0.85, 0.8, 0.8)
    assert crit.level == "CRITICAL"


def test_network_risk_propagation_decay_and_depth():
    # Build a 4-node linear supply chain: Depot -> Hub -> Staging -> Forward
    # Edge A -> B -> C -> D
    nodes = {"DEPOT": {}, "HUB": {}, "STAGING": {}, "FORWARD": {}}
    routes = {
        "R1": {"source_node_id": "DEPOT", "destination_node_id": "HUB", "max_capacity": 10000.0},
        "R2": {"source_node_id": "HUB", "destination_node_id": "STAGING", "max_capacity": 5000.0},
        "R3": {"source_node_id": "STAGING", "destination_node_id": "FORWARD", "max_capacity": 2000.0},
    }

    config = PropagationConfig(
        propagation_factor=0.50,
        propagation_decay=0.70,
        max_depth=3,
    )
    propagator = NetworkRiskPropagator(config=config)
    graph = propagator.build_dependency_graph(nodes, routes)

    # Depot experiences severe shock (risk = 1.0), others have 0 local risk
    base_risks = {"DEPOT": 1.0, "HUB": 0.0, "STAGING": 0.0, "FORWARD": 0.0}
    results = propagator.propagate_risk(graph, base_risks)

    # Propagated risk should decay strictly down the chain
    # Depth 1: HUB
    hub_risk = results["HUB"]["propagated_risk"]
    # Depth 2: STAGING
    staging_risk = results["STAGING"]["propagated_risk"]
    # Depth 3: FORWARD
    forward_risk = results["FORWARD"]["propagated_risk"]

    assert hub_risk > staging_risk > forward_risk > 0.0
    assert forward_risk < 1.0


def test_node_criticality_decoupling():
    calc = NodeCriticalityCalculator()

    # Forward Combat Post (Priority 5, high altitude, low alternate routes)
    fp_crit = calc.calculate_node_criticality(
        node_priority=5,
        daily_demand_volume=500.0,
        inflow_routes_count=1,
        outflow_routes_count=0,
        elevation_meters=4700.0,
    )

    # Staging Base (Priority 3, low altitude, multiple routes)
    sb_crit = calc.calculate_node_criticality(
        node_priority=3,
        daily_demand_volume=600.0,
        inflow_routes_count=3,
        outflow_routes_count=2,
        elevation_meters=2200.0,
    )

    assert fp_crit["criticality_score"] > sb_crit["criticality_score"]
    assert fp_crit["criticality_tier"] in ["STRATEGIC_CRITICAL", "OPERATIONAL_HIGH"]
