"""Inventory Projection & Monte Carlo Stockout Simulation Engine.

Projects multi-echelon stock levels forward over arbitrary forecast horizons (24h, 72h, 168h),
calculates dynamic safety stock levels, and computes uncertainty-aware stockout probabilities.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np


@dataclass
class DynamicSafetyStockConfig:
    """Configurable dynamic safety stock policy."""
    service_factor_z: float = 1.65  # 95% service level default
    minimum_safety_days: float = 3.0
    lead_time_factor: float = 1.0


@dataclass
class InventoryProjectionResult:
    node_id: str
    item_id: str
    horizon_hours: int
    current_inventory: float
    current_backlog: float
    dynamic_safety_stock: float
    projected_inventory: List[float]
    projected_safety_stock: List[float]
    time_to_safety_stock_hours: Optional[int]
    time_to_zero_hours: Optional[int]
    projected_backlog: float
    stockout_probability: float
    monte_carlo_runs: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "item_id": self.item_id,
            "horizon_hours": self.horizon_hours,
            "current_inventory": round(self.current_inventory, 2),
            "current_backlog": round(self.current_backlog, 2),
            "dynamic_safety_stock": round(self.dynamic_safety_stock, 2),
            "projected_inventory": [round(x, 2) for x in self.projected_inventory],
            "projected_safety_stock": [round(x, 2) for x in self.projected_safety_stock],
            "time_to_safety_stock_hours": self.time_to_safety_stock_hours,
            "time_to_zero_hours": self.time_to_zero_hours,
            "projected_backlog": round(self.projected_backlog, 2),
            "stockout_probability": round(self.stockout_probability, 4),
            "monte_carlo_runs": self.monte_carlo_runs,
        }


class InventoryProjectionEngine:
    """Simulates forward stock evolution and runs Monte Carlo stockout probability estimation."""

    def __init__(self, safety_stock_config: Optional[DynamicSafetyStockConfig] = None):
        self.safety_config = safety_stock_config or DynamicSafetyStockConfig()

    def calculate_dynamic_safety_stock(
        self,
        demand_std: float,
        lead_time_hours: float,
        service_factor_z: Optional[float] = None,
        daily_baseline: Optional[float] = None,
    ) -> float:
        """Computes dynamic safety stock: SafetyStock = z * demand_std * sqrt(lead_time_days)."""
        z = service_factor_z if service_factor_z is not None else self.safety_config.service_factor_z
        lead_time_days = max(0.0, lead_time_hours / 24.0)
        demand_std_safe = max(0.0, demand_std)
        statistical_buffer = z * demand_std_safe * math.sqrt(lead_time_days)

        if daily_baseline is not None and daily_baseline > 0:
            min_floor = daily_baseline * self.safety_config.minimum_safety_days
            return max(round(statistical_buffer, 2), round(min_floor, 2))

        return round(statistical_buffer, 2)

    def project_inventory(
        self,
        node_id: str,
        item_id: str,
        current_inventory: float,
        predicted_demand_p50: List[float],
        scheduled_inbound: Optional[Dict[int, float]] = None,
        current_backlog: float = 0.0,
        demand_std: float = 10.0,
        lead_time_hours: float = 24.0,
    ) -> Tuple[List[float], List[float], Optional[int], Optional[int], float, float]:
        """Calculates deterministic inventory trajectory hour-by-hour."""
        inbound = scheduled_inbound or {}
        horizon = len(predicted_demand_p50)
        daily_burn = float(np.mean(predicted_demand_p50)) * 24.0 if horizon > 0 else 100.0

        safety_stock = self.calculate_dynamic_safety_stock(
            demand_std=demand_std,
            lead_time_hours=lead_time_hours,
            daily_baseline=daily_burn,
        )

        projected_inv = []
        projected_ss = []
        time_to_ss: Optional[int] = None
        time_to_zero: Optional[int] = None
        cum_backlog = current_backlog

        stock = current_inventory

        for t in range(horizon):
            arrivals = inbound.get(t, 0.0)
            demand_t = predicted_demand_p50[t]

            # Inbound receipts arrive before consumption
            stock += arrivals

            # Fulfill existing backlog if stock allows
            if cum_backlog > 0:
                backlog_served = min(stock, cum_backlog)
                stock -= backlog_served
                cum_backlog -= backlog_served

            # Demand consumption with non-negativity constraint
            if stock >= demand_t:
                stock -= demand_t
            else:
                unmet = demand_t - stock
                cum_backlog += unmet
                stock = 0.0

            projected_inv.append(stock)
            projected_ss.append(safety_stock)

            if stock < safety_stock and time_to_ss is None:
                time_to_ss = t + 1

            if stock == 0.0 and time_to_zero is None:
                time_to_zero = t + 1

        return (
            projected_inv,
            projected_ss,
            time_to_ss,
            time_to_zero,
            cum_backlog,
            safety_stock,
        )

    def run_monte_carlo_stockout(
        self,
        node_id: str,
        item_id: str,
        current_inventory: float,
        p50_series: List[float],
        p80_series: List[float],
        p95_series: List[float],
        scheduled_inbound: Optional[Dict[int, float]] = None,
        demand_std: float = 10.0,
        lead_time_hours: float = 24.0,
        simulation_count: int = 1000,
        seed: int = 42,
    ) -> InventoryProjectionResult:
        """Executes Monte Carlo simulation generating plausible stochastic demand trajectories."""
        rng = np.random.RandomState(seed)
        horizon = len(p50_series)
        inbound = scheduled_inbound or {}

        # 1. Deterministic baseline projection
        (
            proj_inv,
            proj_ss,
            time_to_ss,
            time_to_zero,
            proj_backlog,
            safety_stock,
        ) = self.project_inventory(
            node_id=node_id,
            item_id=item_id,
            current_inventory=current_inventory,
            predicted_demand_p50=p50_series,
            scheduled_inbound=inbound,
            demand_std=demand_std,
            lead_time_hours=lead_time_hours,
        )

        # 2. Monte Carlo paths
        p50_arr = np.asarray(p50_series, dtype=np.float32)
        p95_arr = np.asarray(p95_series, dtype=np.float32)
        # Derive standard deviation from (P95 - P50) / 1.645
        spread_sigma = np.maximum(0.5, (p95_arr - p50_arr) / 1.645)

        stockout_paths = 0

        for _ in range(simulation_count):
            # Sample trajectory around P50 with normal or lognormal perturbation
            noise = rng.normal(loc=0.0, scale=spread_sigma)
            sampled_demand = np.maximum(0.1, p50_arr + noise)

            path_stock = current_inventory
            has_stockout = False

            for t in range(horizon):
                path_stock += inbound.get(t, 0.0)
                dem = sampled_demand[t]
                if path_stock < dem:
                    has_stockout = True
                    break
                path_stock -= dem

            if has_stockout:
                stockout_paths += 1

        prob = float(stockout_paths / max(1, simulation_count))

        return InventoryProjectionResult(
            node_id=node_id,
            item_id=item_id,
            horizon_hours=horizon,
            current_inventory=current_inventory,
            current_backlog=0.0,
            dynamic_safety_stock=safety_stock,
            projected_inventory=proj_inv,
            projected_safety_stock=proj_ss,
            time_to_safety_stock_hours=time_to_ss,
            time_to_zero_hours=time_to_zero,
            projected_backlog=proj_backlog,
            stockout_probability=prob,
            monte_carlo_runs=simulation_count,
        )
