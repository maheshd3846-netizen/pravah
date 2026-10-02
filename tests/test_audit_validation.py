"""Comprehensive Phase 2.5 Validation and Audit Regression Test Suite for PRAVAH.

Covers:
1. Forecasting Data-Leakage Audit
2. Forecast Target Integrity Audit (Requested vs Fulfilled)
3. Temporal Cross-Validation Audit
4. XGBoost Quantile Forecast Audit (Monotonicity & Non-negativity across seeds)
5. Metric Edge Cases Audit
6. Monte Carlo Stockout & Uncertainty Audit
7. Inventory Conservation Audit
8. Safety Stock Edge Cases Audit
9. Risk Engine & Threshold Audit
10. Network Risk Propagation Directionality & Cycle Safety Audit
11. Strategic Criticality vs Transient Operational Risk Decoupling
12. Alert & Explanation Fact-Grounding Audit
13. Scenario Monotonicity Tests (Inventory, Demand, Route, Transport, Weather)
14. End-to-End Deterministic Reproducibility Audit
15. Data Quality Gate Verification
"""

import math
import numpy as np
import pandas as pd
import pytest
import networkx as nx

from ml.features.feature_pipeline import FeaturePipeline
from ml.xgboost.forecaster import DemandXGBForecaster, XGBForecastConfig
from ml.baselines.moving_average import MovingAverageForecaster
from ml.evaluation.temporal_cv import TemporalCrossValidator
from ml.evaluation.metrics import evaluate_forecast, evaluate_quantile_forecast
from backend.app.forecasting.inventory_projection import (
    InventoryProjectionEngine,
    DynamicSafetyStockConfig,
)
from backend.app.forecasting.quality_gate import DataQualityGate, QualityStatus
from backend.app.risk.evaluator import (
    RiskEvaluator,
    RiskWeightsConfig,
    RiskThresholdsConfig,
)
from backend.app.risk.propagation import NetworkRiskPropagator, PropagationConfig
from backend.app.risk.criticality import NodeCriticalityCalculator
from backend.app.risk.alerts import EarlyWarningEngine
from backend.app.risk.explanations import ExplanationEngine
from simulation.world_generator import WorldGenerator
from simulation.demand_generator import DemandGenerator


# ==============================================================================
# 1. FORECASTING DATA-LEAKAGE AUDIT
# ==============================================================================

def test_data_leakage_future_demand_mutation_invariant():
    """Regression test: mutating demand[t+1:] MUST NOT change features generated at t."""
    pipeline = FeaturePipeline()
    hours = 300
    timestamps = list(range(hours))
    base_demand = [float(10 + (h % 24)) for h in timestamps]

    df_a = pd.DataFrame({
        "timestamp_hour": timestamps,
        "node_id": ["FP-01"] * hours,
        "item": ["FUEL"] * hours,
        "requested_demand": base_demand,
        "rainfall": [0.0] * hours,
        "wind_speed": [10.0] * hours,
        "visibility": [10.0] * hours,
        "temperature": [-5.0] * hours,
    })

    X_a, _ = pipeline.fit_transform(df_a)

    # Mutate future demand at and after hour 200
    t_split = 200
    mutated_demand = list(base_demand)
    for h in range(t_split, hours):
        mutated_demand[h] = 9999.0

    df_b = pd.DataFrame({
        "timestamp_hour": timestamps,
        "node_id": ["FP-01"] * hours,
        "item": ["FUEL"] * hours,
        "requested_demand": mutated_demand,
        "rainfall": [0.0] * hours,
        "wind_speed": [10.0] * hours,
        "visibility": [10.0] * hours,
        "temperature": [-5.0] * hours,
    })

    X_b = pipeline.transform(df_b)

    # For all hours t < t_split (e.g. t = 199), features in X_a and X_b must be identical
    # Because valid_idx starts after warmup (hour 168), we check rows between 168 and 199
    idx_target = 199
    features_a = X_a.loc[idx_target]
    features_b = X_b.loc[idx_target]

    pd.testing.assert_series_equal(features_a, features_b, check_exact=True)


def test_lag_feature_mathematical_correctness():
    """Verify lag_1[t] == demand[t-1], lag_24[t] == demand[t-24], lag_168[t] == demand[t-168]."""
    pipeline = FeaturePipeline()
    hours = 250
    timestamps = list(range(hours))
    demand_values = [float(100 + h) for h in timestamps]

    df = pd.DataFrame({
        "timestamp_hour": timestamps,
        "node_id": ["FP-02"] * hours,
        "item": ["AMMUNITION"] * hours,
        "requested_demand": demand_values,
        "rainfall": [0.0] * hours,
        "wind_speed": [5.0] * hours,
        "visibility": [10.0] * hours,
        "temperature": [0.0] * hours,
    })

    engineered = pipeline._engineer_features(df)

    for t in [170, 200, 240]:
        assert engineered.loc[t, "lag_1"] == demand_values[t - 1]
        assert engineered.loc[t, "lag_24"] == demand_values[t - 24]
        assert engineered.loc[t, "lag_168"] == demand_values[t - 168]


# ==============================================================================
# 2. FORECAST TARGET INTEGRITY AUDIT
# ==============================================================================

def test_forecast_target_invariant_to_inventory_stockout():
    """If inventory becomes zero while requested demand is high, target remains requested demand."""
    pipeline = FeaturePipeline()
    hours = 200
    timestamps = list(range(hours))
    requested_demand = [50.0] * hours
    # Simulated stockout: inventory hits zero at hour 100, fulfilled drops to zero
    fulfilled_demand = [50.0 if h < 100 else 0.0 for h in timestamps]

    df = pd.DataFrame({
        "timestamp_hour": timestamps,
        "node_id": ["FP-03"] * hours,
        "item": ["RATIONS"] * hours,
        "requested_demand": requested_demand,
        "fulfilled_demand": fulfilled_demand,
        "current_inventory": [5000.0 if h < 100 else 0.0 for h in timestamps],
    })

    X, y = pipeline.fit_transform(df)

    # Verify that target y strictly equals requested_demand (50.0), never suppressed fulfilled_demand (0.0)
    for val in y.values:
        assert val == 50.0


# ==============================================================================
# 3. TEMPORAL CROSS-VALIDATION AUDIT
# ==============================================================================

def test_temporal_cross_validation_chronological_ordering():
    """Verify temporal CV never shuffles, expands strictly forward, and trains before tests."""
    cv = TemporalCrossValidator(month_hours=100, initial_train_months=3, n_splits=3)
    total_hours = 600
    df = pd.DataFrame({
        "timestamp_hour": list(range(total_hours)),
        "node_id": ["FP-01"] * total_hours,
        "item": ["FUEL"] * total_hours,
        "requested_demand": [10.0] * total_hours,
    })

    prev_test_end = 0
    for train_df, test_df, fold_idx in cv.split(df):
        train_max = train_df["timestamp_hour"].max()
        test_min = test_df["timestamp_hour"].min()
        test_max = test_df["timestamp_hour"].max()

        # Strict chronological order: test starts immediately after train ends
        assert test_min > train_max
        assert test_min == train_max + 1
        assert test_min >= prev_test_end

        # No test rows in training set
        assert set(train_df["timestamp_hour"]).isdisjoint(set(test_df["timestamp_hour"]))
        prev_test_end = test_max


# ==============================================================================
# 4. XGBOOST QUANTILE FORECAST AUDIT
# ==============================================================================

def test_xgboost_quantile_monotonicity_across_seeds():
    """Verify P50 <= P80 <= P95 and non-negativity across multiple random seeds."""
    pipeline = FeaturePipeline()
    hours = 250
    timestamps = list(range(hours))
    np.random.seed(123)
    base_demand = np.random.uniform(5.0, 50.0, size=hours).tolist()

    df = pd.DataFrame({
        "timestamp_hour": timestamps,
        "node_id": ["FP-01"] * hours,
        "item": ["FUEL"] * hours,
        "requested_demand": base_demand,
        "rainfall": [0.0] * hours,
        "wind_speed": [15.0] * hours,
        "visibility": [8.0] * hours,
        "temperature": [-10.0] * hours,
    })

    X, y = pipeline.fit_transform(df)

    for seed in [1, 42, 999]:
        config = XGBForecastConfig(n_estimators=30, max_depth=3, random_state=seed)
        model = DemandXGBForecaster(config=config)
        model.fit(X, y)
        forecast = model.predict(X)

        # Monotonicity check: p50 <= p80 <= p95
        assert np.all(forecast.p50 <= forecast.p80 + 1e-5)
        assert np.all(forecast.p80 <= forecast.p95 + 1e-5)

        # Non-negativity check
        assert np.all(forecast.p50 >= 0.0)
        assert np.all(forecast.p80 >= 0.0)
        assert np.all(forecast.p95 >= 0.0)


# ==============================================================================
# 5. METRIC EDGE CASES AUDIT
# ==============================================================================

def test_metrics_zero_actuals_and_empty_arrays():
    """Verify metrics handle zero actuals and empty arrays without division-by-zero or crash."""
    # Zero actuals
    y_true_zero = [0.0, 0.0, 0.0]
    y_pred = [5.0, 5.0, 5.0]
    metrics = evaluate_forecast(y_true_zero, y_pred)
    assert metrics["wape_percent"] > 0.0
    assert metrics["mape_percent"] == 0.0  # Zero actuals safely bypassed in MAPE
    assert not math.isnan(metrics["wape_percent"])

    # Empty arrays
    metrics_empty = evaluate_forecast([], [])
    assert metrics_empty["mae"] == 0.0
    assert metrics_empty["rmse"] == 0.0
    assert metrics_empty["wape_percent"] == 0.0

    q_empty = evaluate_quantile_forecast([], [], [], [])
    assert q_empty["sample_count"] == 0
    assert q_empty["p50_to_p95_interval_coverage_percent"] == 0.0


# ==============================================================================
# 6. MONTE CARLO STOCKOUT & UNCERTAINTY AUDIT
# ==============================================================================

def test_monte_carlo_uncertainty_and_inventory_sensitivity():
    """Verify Monte Carlo stockout sensitivity to inventory and inbound supply."""
    engine = InventoryProjectionEngine()
    horizon = 24
    p50 = [20.0] * horizon
    p80 = [25.0] * horizon
    p95 = [35.0] * horizon

    # Case 1: Low inventory (200 units for 480 demand -> high stockout risk)
    res_low = engine.run_monte_carlo_stockout(
        node_id="FP-01",
        item_id="FUEL",
        current_inventory=200.0,
        p50_series=p50,
        p80_series=p80,
        p95_series=p95,
        simulation_count=500,
        seed=42,
    )

    # Case 2: High inventory (1000 units for 480 demand -> low stockout risk)
    res_high = engine.run_monte_carlo_stockout(
        node_id="FP-01",
        item_id="FUEL",
        current_inventory=1000.0,
        p50_series=p50,
        p80_series=p80,
        p95_series=p95,
        simulation_count=500,
        seed=42,
    )

    assert res_high.stockout_probability <= res_low.stockout_probability
    assert res_low.stockout_probability > 0.90
    assert res_high.stockout_probability == 0.0


def test_monte_carlo_inbound_supply_alleviates_risk():
    """Adding inbound supply must not increase stockout probability."""
    engine = InventoryProjectionEngine()
    horizon = 24
    p50 = [20.0] * horizon
    p80 = [25.0] * horizon
    p95 = [35.0] * horizon

    # Baseline: 300 stock, no inbound
    res_no_inbound = engine.run_monte_carlo_stockout(
        node_id="FP-01",
        item_id="FUEL",
        current_inventory=300.0,
        p50_series=p50,
        p80_series=p80,
        p95_series=p95,
        scheduled_inbound={},
        simulation_count=500,
        seed=42,
    )

    # With scheduled delivery of 300 units at hour 6
    res_with_inbound = engine.run_monte_carlo_stockout(
        node_id="FP-01",
        item_id="FUEL",
        current_inventory=300.0,
        p50_series=p50,
        p80_series=p80,
        p95_series=p95,
        scheduled_inbound={6: 300.0},
        simulation_count=500,
        seed=42,
    )

    assert res_with_inbound.stockout_probability <= res_no_inbound.stockout_probability


# ==============================================================================
# 7. INVENTORY CONSERVATION AUDIT
# ==============================================================================

def test_inventory_conservation_hour_by_hour():
    """Verify I[t+1] = max(0, I[t] + inbound[t] - fulfilled_demand[t]) and I >= 0."""
    engine = InventoryProjectionEngine()
    current_inv = 100.0
    p50_demand = [30.0, 40.0, 50.0, 20.0]
    inbound = {1: 50.0}  # 50 arrives at t=1

    proj_inv, _, _, _, backlog, _ = engine.project_inventory(
        node_id="FP-01",
        item_id="FUEL",
        current_inventory=current_inv,
        predicted_demand_p50=p50_demand,
        scheduled_inbound=inbound,
    )

    # Step 0: stock = 100 -> demand 30 -> stock 70
    assert proj_inv[0] == 70.0
    # Step 1: stock = 70 + 50 = 120 -> demand 40 -> stock 80
    assert proj_inv[1] == 80.0
    # Step 2: stock = 80 -> demand 50 -> stock 30
    assert proj_inv[2] == 30.0
    # Step 3: stock = 30 -> demand 20 -> stock 10
    assert proj_inv[3] == 10.0
    assert backlog == 0.0
    assert all(s >= 0.0 for s in proj_inv)


# ==============================================================================
# 8. SAFETY STOCK EDGE CASES AUDIT
# ==============================================================================

def test_dynamic_safety_stock_edge_cases():
    """Verify safety stock handles lead_time=0, demand_std=0, large lead_time safely."""
    engine = InventoryProjectionEngine()

    # Zero lead time
    ss_zero_lt = engine.calculate_dynamic_safety_stock(demand_std=10.0, lead_time_hours=0.0)
    assert ss_zero_lt == 0.0

    # Zero demand std
    ss_zero_std = engine.calculate_dynamic_safety_stock(demand_std=0.0, lead_time_hours=24.0)
    assert ss_zero_std == 0.0

    # Large lead time (1 year = 8760h)
    ss_large = engine.calculate_dynamic_safety_stock(demand_std=10.0, lead_time_hours=8760.0)
    assert ss_large > 0.0
    assert not math.isnan(ss_large)
    assert not math.isinf(ss_large)


# ==============================================================================
# 9. RISK ENGINE & THRESHOLD AUDIT
# ==============================================================================

def test_risk_weights_validation_and_bounds():
    """Verify risk weights must sum to 1.0, and risk output is bounded in [0, 1]."""
    evaluator = RiskEvaluator()

    # Invalid weights sum raises ValueError
    with pytest.raises(ValueError):
        RiskWeightsConfig(inventory_weight=0.5, demand_weight=0.6)

    # All zero inputs produce overall risk = 0.0
    res_zero = evaluator.calculate_overall_risk(
        node_id="N-01",
        node_code="NODE_ZERO",
        inventory_risk=0.0,
        demand_risk=0.0,
        route_risk=0.0,
        transport_risk=0.0,
        environment_risk=0.0,
    )
    assert res_zero.overall_risk == 0.0
    assert res_zero.level == "LOW"

    # All one inputs produce overall risk = 1.0
    res_one = evaluator.calculate_overall_risk(
        node_id="N-02",
        node_code="NODE_ONE",
        inventory_risk=1.0,
        demand_risk=1.0,
        route_risk=1.0,
        transport_risk=1.0,
        environment_risk=1.0,
    )
    assert res_one.overall_risk == 1.0
    assert res_one.level == "CRITICAL"


def test_risk_threshold_boundary_continuity():
    """Test exact threshold boundaries: [0, 0.35) LOW, [0.35, 0.60) MODERATE, [0.60, 0.75) HIGH, [0.75, 1.0] CRITICAL."""
    evaluator = RiskEvaluator()
    # Direct threshold mapping test
    cases = [
        (0.00, "LOW"),
        (0.24, "LOW"),
        (0.349, "LOW"),
        (0.35, "MODERATE"),
        (0.599, "MODERATE"),
        (0.60, "HIGH"),
        (0.749, "HIGH"),
        (0.75, "CRITICAL"),
        (1.00, "CRITICAL"),
    ]
    for score, expected_lvl in cases:
        assessment = evaluator.calculate_overall_risk(
            node_id="N",
            node_code="CODE",
            inventory_risk=score,
            demand_risk=score,
            route_risk=score,
            transport_risk=score,
            environment_risk=score,
        )
        assert assessment.level == expected_lvl


# ==============================================================================
# 10. NETWORK RISK PROPAGATION AUDIT
# ==============================================================================

def test_network_risk_propagation_directionality_and_acyclic():
    """Verify risk propagates from upstream to downstream only, and cycles do not loop."""
    propagator = NetworkRiskPropagator(PropagationConfig(propagation_factor=0.5, propagation_decay=0.7, max_depth=3))

    # A -> B -> C (A feeds B, B feeds C)
    graph = nx.DiGraph()
    graph.add_edge("A", "B", dependency=1.0)
    graph.add_edge("B", "C", dependency=1.0)

    base_risks = {"A": 1.0, "B": 0.0, "C": 0.0}
    results = propagator.propagate_risk(graph, base_risks)

    # A has no upstream supplier, so its risk remains 1.0
    assert results["A"]["delta"] == 0.0

    # B has upstream supplier A with risk 1.0, so B receives propagated risk
    assert results["B"]["propagated_risk"] > 0.0

    # C receives risk from B (two hops)
    assert results["C"]["propagated_risk"] > 0.0
    # Due to decay, hop 2 transferred risk is less than hop 1
    assert results["B"]["propagated_risk"] > results["C"]["propagated_risk"]

    # Reverse direction test: upstream should not receive risk from downstream
    base_risks_rev = {"A": 0.0, "B": 0.0, "C": 1.0}
    results_rev = propagator.propagate_risk(graph, base_risks_rev)
    assert results_rev["A"]["propagated_risk"] == 0.0
    assert results_rev["B"]["propagated_risk"] == 0.0

    # Cycle test: A -> B -> A must terminate cleanly without infinite recursion
    graph_cycle = nx.DiGraph()
    graph_cycle.add_edge("A", "B", dependency=1.0)
    graph_cycle.add_edge("B", "A", dependency=1.0)
    cycle_res = propagator.propagate_risk(graph_cycle, {"A": 0.8, "B": 0.2})
    assert cycle_res["A"]["propagated_risk"] <= 1.0


# ==============================================================================
# 11. CRITICALITY VS OPERATIONAL RISK DECOUPLING
# ==============================================================================

def test_criticality_decoupled_from_operational_risk():
    """Verify strategic criticality is independent of transient operational stockout risk."""
    calc = NodeCriticalityCalculator()
    evaluator = RiskEvaluator()

    # Strategic frontline post (Priority 5) with high elevation and scarce routes
    crit = calc.calculate_node_criticality(
        node_priority=5,
        daily_demand_volume=500.0,
        inflow_routes_count=1,
        outflow_routes_count=0,
        elevation_meters=4500.0,
    )
    assert crit["criticality_tier"] in ["STRATEGIC_CRITICAL", "OPERATIONAL_HIGH"]

    # Even with high strategic criticality, if inventory is full, current operational risk is LOW
    risk_low = evaluator.calculate_overall_risk(
        node_id="FP-04",
        node_code="FP-04",
        inventory_risk=0.05,
        demand_risk=0.10,
        route_risk=0.10,
        transport_risk=0.05,
        environment_risk=0.10,
    )
    assert risk_low.level == "LOW"


# ==============================================================================
# 12. ALERT & EXPLANATION AUDIT
# ==============================================================================

def test_alerts_and_explanations_fact_grounded():
    """Verify explanations map strictly to physical quantities and do not invent facts."""
    alert_engine = EarlyWarningEngine()
    expl_engine = ExplanationEngine()

    alerts = alert_engine.evaluate_inventory_alerts(
        node_id="FP-04",
        node_code="FP-04",
        item="FUEL",
        current_inventory=420.0,
        safety_stock=825.0,
        time_to_ss_hours=1,
        time_to_zero_hours=51,
        stockout_prob=1.0,
        p95_cumulative_demand=2699.0,
        route_status="BLOCKED",
        weather_severity="SEVERE",
        demand_surge_percent=30.0,
    )

    assert len(alerts) > 0
    top_alert = alerts[0]
    assert top_alert.severity == "CRITICAL"
    assert top_alert.evidence["current_inventory"] == 420.0
    assert top_alert.evidence["dynamic_safety_stock"] == 825.0
    assert top_alert.evidence["stockout_probability"] == 1.0

    # Explanation contains factual mentions
    assert "FP-04" in top_alert.explanation
    assert "BLOCKED" in top_alert.explanation
    assert "SEVERE" in top_alert.explanation


# ==============================================================================
# 13. SCENARIO MONOTONICITY AUDIT
# ==============================================================================

def test_scenario_monotonicity_suite():
    """Verify monotonic sensitivity across inventory, demand, route, transport, and weather."""
    evaluator = RiskEvaluator()

    # Test A: Route status degradation
    r_normal = evaluator.evaluate_route_risk(["AVAILABLE", "AVAILABLE"], 2, 0.95)
    r_degraded = evaluator.evaluate_route_risk(["DEGRADED", "AVAILABLE"], 1, 0.70)
    r_blocked = evaluator.evaluate_route_risk(["BLOCKED", "BLOCKED"], 0, 0.0)
    assert r_normal <= r_degraded <= r_blocked

    # Test B: Demand volatility & growth
    d_base = evaluator.evaluate_demand_risk(1.0, 0.1, 0.2)
    d_surge = evaluator.evaluate_demand_risk(1.3, 0.3, 0.5)
    d_extreme = evaluator.evaluate_demand_risk(2.0, 0.8, 1.2)
    assert d_base <= d_surge <= d_extreme

    # Test C: Transport fleet shortage
    t_full = evaluator.evaluate_transport_risk(1.0, 0)
    t_half = evaluator.evaluate_transport_risk(0.5, 1)
    t_empty = evaluator.evaluate_transport_risk(0.1, 3)
    assert t_full <= t_half <= t_empty

    # Test D: Weather degradation
    w_norm = evaluator.evaluate_environment_risk("NORMAL", 10.0, 10.0, 10.0)
    w_mod = evaluator.evaluate_environment_risk("MODERATE", 40.0, 3.0, -15.0)
    w_sev = evaluator.evaluate_environment_risk("SEVERE", 75.0, 0.5, -25.0)
    assert w_norm <= w_mod <= w_sev


# ==============================================================================
# 14. END-TO-END REPRODUCIBILITY AUDIT
# ==============================================================================

def test_end_to_end_reproducibility():
    """Verify Run 1 == Run 2 under identical random seed."""
    world_gen1 = WorldGenerator(seed=42)
    w1 = world_gen1.generate_world()

    world_gen2 = WorldGenerator(seed=42)
    w2 = world_gen2.generate_world()

    assert set(w1.nodes.keys()) == set(w2.nodes.keys())
    for nid in w1.nodes:
        assert w1.nodes[nid].initial_inventory == w2.nodes[nid].initial_inventory


# ==============================================================================
# 15. DATA QUALITY GATE AUDIT
# ==============================================================================

def test_data_quality_gate_evaluations():
    """Verify data quality gate correctly reports READY, DEGRADED, and INSUFFICIENT."""
    gate = DataQualityGate()

    # Valid demand history
    df_good = pd.DataFrame({
        "timestamp_hour": list(range(800)),
        "node_id": ["FP-01"] * 800,
        "item": ["FUEL"] * 800,
        "requested_demand": [10.0] * 800,
    })

    # Case 1: READY
    res_ready = gate.evaluate(
        demand_history_df=df_good,
        inventory_freshness_hours=2.0,
        route_freshness_hours=1.0,
        weather_freshness_hours=0.5,
        vehicle_freshness_hours=2.0,
    )
    assert res_ready.overall_status == QualityStatus.READY

    # Case 2: DEGRADED (slightly stale inventory)
    res_degraded = gate.evaluate(
        demand_history_df=df_good,
        inventory_freshness_hours=30.0,  # > 24h threshold
        route_freshness_hours=1.0,
    )
    assert res_degraded.overall_status == QualityStatus.DEGRADED

    # Case 3: INSUFFICIENT (empty demand history)
    res_insufficient = gate.evaluate(
        demand_history_df=pd.DataFrame(),
        inventory_freshness_hours=2.0,
    )
    assert res_insufficient.overall_status == QualityStatus.INSUFFICIENT
