"""PRAVAH Intelligence Engine -- Demonstration Script.

Runs end-to-end predictive pipeline:
Historical Demand -> Feature Engineering -> Baseline & XGBoost Quantile Models ->
Multi-Horizon Forecasts (24h, 72h, 168h) -> Inventory Projection & Monte Carlo ->
Risk Assessment & Network Propagation -> Early Warning Alerts.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Add project root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd

from simulation.world_generator import WorldGenerator
from simulation.demand_generator import DemandGenerator
from ml.features.feature_pipeline import FeaturePipeline
from ml.baselines.moving_average import MovingAverageForecaster
from ml.xgboost.forecaster import DemandXGBForecaster, XGBForecastConfig
from ml.evaluation.metrics import evaluate_quantile_forecast
from backend.app.forecasting.inventory_projection import InventoryProjectionEngine
from backend.app.risk.service import RiskIntelligenceService


def run_intelligence_demo():
    seed = 42
    print("Initializing PRAVAH Logistics World and Intelligence Pipeline...")

    # 1. World Generation
    world_gen = WorldGenerator(seed=seed)
    world = world_gen.generate_world()

    # 2. Demand History (4 months synthetic data)
    demand_gen = DemandGenerator(seed=seed)
    history_df = demand_gen.generate_annual_history(world.nodes, months=4)

    # 3. Feature Pipeline
    pipeline = FeaturePipeline()
    X, y = pipeline.fit_transform(history_df)

    # 4. Train Models
    # A. Moving Average Baseline
    ma_model = MovingAverageForecaster()
    ma_model.fit(X, y)
    ma_preds = ma_model.predict(X)
    ma_metrics = evaluate_quantile_forecast(y, ma_preds.p50, ma_preds.p80, ma_preds.p95, model_name="MovingAverage")

    # B. XGBoost Quantile Forecaster
    xgb_config = XGBForecastConfig(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.08,
        random_state=seed,
    )
    xgb_model = DemandXGBForecaster(config=xgb_config)
    xgb_model.fit(X, y)
    xgb_preds = xgb_model.predict(X)
    xgb_metrics = evaluate_quantile_forecast(y, xgb_preds.p50, xgb_preds.p80, xgb_preds.p95, model_name="XGBoost")

    # 5. Forecast Target: Forward Defense Post FP-04 (Changla-Frontier) / FUEL
    target_node_id = "NODE_FP_04"
    target_code = "FP-04"
    target_item = "FUEL"
    target_node = world.nodes[target_node_id]

    # Build future feature rows for 24h, 72h, and 168h horizons
    def build_future_features(horizon_h: int) -> pd.DataFrame:
        rows = []
        base_h = int(history_df["timestamp_hour"].max()) + 1
        for step in range(horizon_h):
            h = base_h + step
            rows.append({
                "node_id": target_node_id,
                "item": target_item,
                "timestamp_hour": h,
                "hour_of_day": h % 24,
                "day_of_week": (h // 24) % 7,
                "elevation": target_node.elevation,
                "temperature": -18.5,  # extreme cold winter pass
                "rainfall": 12.0,       # blizzard snow equivalent
                "wind_speed": 55.0,
                "visibility": 1.2,
                "weather_severity": "SEVERE",
                "current_inventory": 420.0,
                "inbound_quantity": 0.0,
                "vehicle_availability": 0.8,
                "node_priority": target_node.priority,
                "requested_demand": 60.0,
            })
        return pipeline.transform(pd.DataFrame(rows))

    X_24 = build_future_features(24)
    fc_24 = xgb_model.predict(X_24)

    X_72 = build_future_features(72)
    fc_72 = xgb_model.predict(X_72)

    X_168 = build_future_features(168)
    fc_168 = xgb_model.predict(X_168)

    # 6. Inventory Projection & Monte Carlo Simulation
    inv_engine = InventoryProjectionEngine()
    current_fuel = 420.0  # Current constrained on-hand stock for demo scenario
    mc_result = inv_engine.run_monte_carlo_stockout(
        node_id=target_node_id,
        item_id=target_item,
        current_inventory=current_fuel,
        p50_series=[float(v) for v in fc_72.p50],
        p80_series=[float(v) for v in fc_72.p80],
        p95_series=[float(v) for v in fc_72.p95],
        simulation_count=1000,
        seed=seed,
    )

    # 7. Risk Intelligence & Network Risk Propagation
    risk_service = RiskIntelligenceService()
    # Inject forward post projection
    projections = {
        target_node_id: {
            "stockout_probability": mc_result.stockout_probability,
            "time_to_zero_hours": mc_result.time_to_zero_hours,
            "time_to_safety_stock_hours": mc_result.time_to_safety_stock_hours,
            "demand_growth_ratio": 1.35,
            "demand_volatility_cv": 0.28,
            "forecast_spread_ratio": 0.45,
            "p95_cumulative_demand": float(np.sum(fc_72.p95)),
        }
    }
    # Set one route degraded for demo
    if "ROUTE_R_22" in world.routes:
        from simulation.world_generator import RouteStatus
        world.routes["ROUTE_R_22"].status = RouteStatus.BLOCKED

    risk_results = risk_service.evaluate_world_risk(world, inventory_projections=projections)
    fp04_risk = risk_results["node_assessments"].get(target_node_id, {})
    components = fp04_risk.get("components", {})

    # Critical nodes and high-risk routes
    critical_nodes = [
        f"{world.nodes[nid].code} ({data['criticality_tier']})"
        for nid, data in risk_results["criticalities"].items()
        if data["criticality_tier"] in ["STRATEGIC_CRITICAL", "OPERATIONAL_HIGH"]
    ]

    high_risk_routes = [
        r.route_code for r in world.routes.values() if r.status.value in ["BLOCKED", "DEGRADED"]
    ]

    # Alerts for target
    target_alerts = [
        a for a in risk_results["alerts"]
        if a["node_code"] == target_code or a["node_id"] == target_node_id
    ]

    # Print Clean Formatted Output
    print("==================================================")
    print("PRAVAH -- INTELLIGENCE ENGINE")
    print(f"Forecast target:\n{target_code} / {target_item} ({target_node.name})")
    print("--------------------------------------------------")
    print("MODEL BENCHMARK (In-sample holdout):")
    print(f"Moving Average Baseline: MAE={ma_metrics['mae']:.2f}, WAPE={ma_metrics['wape_percent']:.2f}%, P95 Coverage={ma_metrics['p95_coverage_percent']:.1f}%")
    print(f"XGBoost Quantile Model:  MAE={xgb_metrics['mae']:.2f}, WAPE={xgb_metrics['wape_percent']:.2f}%, P95 Coverage={xgb_metrics['p95_coverage_percent']:.1f}%")
    print("--------------------------------------------------")
    print("24h Forecast:")
    print(f"P50: {float(np.mean(fc_24.p50)):.1f} units/h (Sum: {float(np.sum(fc_24.p50)):,.1f})")
    print(f"P80: {float(np.mean(fc_24.p80)):.1f} units/h (Sum: {float(np.sum(fc_24.p80)):,.1f})")
    print(f"P95: {float(np.mean(fc_24.p95)):.1f} units/h (Sum: {float(np.sum(fc_24.p95)):,.1f})")
    print("72h Forecast:")
    print(f"P50: {float(np.mean(fc_72.p50)):.1f} units/h (Sum: {float(np.sum(fc_72.p50)):,.1f})")
    print(f"P80: {float(np.mean(fc_72.p80)):.1f} units/h (Sum: {float(np.sum(fc_72.p80)):,.1f})")
    print(f"P95: {float(np.mean(fc_72.p95)):.1f} units/h (Sum: {float(np.sum(fc_72.p95)):,.1f})")
    print("168h Forecast:")
    print(f"P50: {float(np.mean(fc_168.p50)):.1f} units/h (Sum: {float(np.sum(fc_168.p50)):,.1f})")
    print(f"P80: {float(np.mean(fc_168.p80)):.1f} units/h (Sum: {float(np.sum(fc_168.p80)):,.1f})")
    print(f"P95: {float(np.mean(fc_168.p95)):.1f} units/h (Sum: {float(np.sum(fc_168.p95)):,.1f})")
    print("--------------------------------------------------")
    print("Inventory:")
    print(f"Current: {current_fuel:.1f} units")
    print(f"Dynamic safety stock: {mc_result.dynamic_safety_stock:.1f} units")
    print(f"Time to safety stock: {mc_result.time_to_safety_stock_hours if mc_result.time_to_safety_stock_hours is not None else '>72'} h")
    print(f"Time to zero: {mc_result.time_to_zero_hours if mc_result.time_to_zero_hours is not None else '>72'} h")
    print("Stockout probability:")
    print(f"{mc_result.stockout_probability * 100:.1f} % (Monte Carlo 1,000 paths)")
    print("--------------------------------------------------")
    print("Risk:")
    print(f"Overall: {fp04_risk.get('overall_risk', 0.0):.2f}")
    print(f"Level: {fp04_risk.get('level', 'UNKNOWN')}")
    print("Risk Drivers:")
    print(f"Inventory: {components.get('inventory', 0.0):.2f}")
    print(f"Demand: {components.get('demand', 0.0):.2f}")
    print(f"Route: {components.get('route', 0.0):.2f}")
    print(f"Transport: {components.get('transport', 0.0):.2f}")
    print(f"Environment: {components.get('environment', 0.0):.2f}")
    print("--------------------------------------------------")
    print("Network:")
    print(f"Critical nodes: {', '.join(critical_nodes[:4])}")
    print(f"High-risk routes: {', '.join(high_risk_routes) if high_risk_routes else 'None'}")
    print("--------------------------------------------------")
    print("Alerts:")
    for a in target_alerts[:2]:
        print(f"[{a['severity']}] {a['alert_type']}: {a['explanation']}")
    print("==================================================")


if __name__ == "__main__":
    run_intelligence_demo()
