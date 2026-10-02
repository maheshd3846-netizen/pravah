"""Tests for Forward Inventory Projection and Monte Carlo Stockout Simulation."""

import math
from backend.app.forecasting.inventory_projection import (
    InventoryProjectionEngine,
    DynamicSafetyStockConfig,
)


def test_dynamic_safety_stock_calculation():
    engine = InventoryProjectionEngine(DynamicSafetyStockConfig(service_factor_z=1.96))

    demand_std = 15.0
    lead_time_hours = 48.0  # 2 days

    expected_days = 48.0 / 24.0
    expected_ss = 1.96 * 15.0 * math.sqrt(expected_days)

    calculated_ss = engine.calculate_dynamic_safety_stock(
        demand_std=demand_std,
        lead_time_hours=lead_time_hours,
    )

    assert abs(calculated_ss - expected_ss) < 0.05


def test_deterministic_inventory_projection():
    engine = InventoryProjectionEngine()

    current_inv = 100.0
    p50_demand = [20.0, 30.0, 40.0, 50.0]  # Cumulative: 20, 50, 90, 140
    # Inbound delivery of 20 units at step 2 (index 2)
    inbound = {2: 20.0}

    (
        proj_inv,
        proj_ss,
        time_to_ss,
        time_to_zero,
        backlog,
        ss,
    ) = engine.project_inventory(
        node_id="NODE_TEST",
        item_id="FUEL",
        current_inventory=current_inv,
        predicted_demand_p50=p50_demand,
        scheduled_inbound=inbound,
        demand_std=5.0,
        lead_time_hours=24.0,
    )

    # Step 0: start 100 -> demand 20 -> end 80
    assert proj_inv[0] == 80.0
    # Step 1: start 80 -> demand 30 -> end 50
    assert proj_inv[1] == 50.0
    # Step 2: start 50 + inbound 20 = 70 -> demand 40 -> end 30
    assert proj_inv[2] == 30.0
    # Step 3: start 30 -> demand 50 -> end 0, backlog 20
    assert proj_inv[3] == 0.0
    assert backlog == 20.0
    assert time_to_zero == 4  # step 4 (1-indexed hour)


def test_monte_carlo_stockout_determinism_and_bounds():
    engine = InventoryProjectionEngine()

    current_inv = 50.0
    p50 = [25.0] * 5  # Total 125 > 50 -> should have high stockout prob
    p80 = [30.0] * 5
    p95 = [40.0] * 5

    res1 = engine.run_monte_carlo_stockout(
        node_id="FP-01",
        item_id="FUEL",
        current_inventory=current_inv,
        p50_series=p50,
        p80_series=p80,
        p95_series=p95,
        simulation_count=500,
        seed=42,
    )

    res2 = engine.run_monte_carlo_stockout(
        node_id="FP-01",
        item_id="FUEL",
        current_inventory=current_inv,
        p50_series=p50,
        p80_series=p80,
        p95_series=p95,
        simulation_count=500,
        seed=42,
    )

    # Probability bounds
    assert 0.0 <= res1.stockout_probability <= 1.0
    assert res1.stockout_probability > 0.8  # Definite stockout trajectory

    # Determinism test: same seed must produce exact identical probability
    assert res1.stockout_probability == res2.stockout_probability
    assert res1.time_to_zero_hours == res2.time_to_zero_hours
