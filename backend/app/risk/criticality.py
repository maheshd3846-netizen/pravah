"""Node Criticality Scoring Engine for Strategic Asset Valuation.

Decouples intrinsic node importance from transient operational risk:
CRITICALITY = How important the node is to defense operations and network stability.
RISK = How likely the node is to experience stockouts or operational failure right now.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np


@dataclass
class CriticalityWeightsConfig:
    """Configurable weights for strategic asset valuation."""
    priority_weight: float = 0.35      # Tactical defense echelon priority (1 to 5)
    demand_volume_weight: float = 0.25 # Relative throughput / consumption rate
    connectivity_weight: float = 0.20  # Degree centrality and transit routing role
    scarcity_weight: float = 0.20      # Isolation vulnerability (lack of alternate routes)

    def to_dict(self) -> Dict[str, float]:
        return {
            "priority": self.priority_weight,
            "demand_volume": self.demand_volume_weight,
            "connectivity": self.connectivity_weight,
            "scarcity": self.scarcity_weight,
        }


class NodeCriticalityCalculator:
    """Evaluates intrinsic strategic criticality for military logistics nodes."""

    def __init__(self, weights: Optional[CriticalityWeightsConfig] = None):
        self.weights = weights or CriticalityWeightsConfig()

    def calculate_node_criticality(
        self,
        node_priority: int,             # 1 (depot) to 5 (forward combat post)
        daily_demand_volume: float,     # average daily demand
        inflow_routes_count: int,       # total incoming route links
        outflow_routes_count: int,      # total outgoing route links
        elevation_meters: float,        # terrain elevation
        max_demand_in_network: float = 10000.0,
    ) -> Dict[str, Any]:
        """Calculates normalized strategic criticality score in [0, 1]."""
        # 1. Priority Score: Forward combat posts (Priority 5) have maximum frontline criticality
        priority_score = float(np.clip((node_priority - 1.0) / 4.0, 0.0, 1.0))

        # 2. Demand volume score
        volume_score = float(np.clip(daily_demand_volume / max(1.0, max_demand_in_network), 0.0, 1.0))

        # 3. Connectivity / Hub score (nodes that distribute to many forward posts)
        total_connections = inflow_routes_count + outflow_routes_count
        connectivity_score = float(np.clip(total_connections / 8.0, 0.0, 1.0))

        # 4. Route scarcity (isolated forward post with few routes has high scarcity criticality)
        scarcity_score = 1.0 if inflow_routes_count <= 1 else (0.5 if inflow_routes_count == 2 else 0.2)

        # High altitude elevation bonus
        altitude_factor = float(np.clip((elevation_meters - 2000.0) / 3000.0, 0.0, 0.2))

        composite = (
            self.weights.priority_weight * priority_score
            + self.weights.demand_volume_weight * volume_score
            + self.weights.connectivity_weight * connectivity_score
            + self.weights.scarcity_weight * scarcity_score
            + altitude_factor
        )
        composite = float(np.clip(composite, 0.0, 1.0))

        # Tier classification
        if composite >= 0.75:
            tier = "STRATEGIC_CRITICAL"
        elif composite >= 0.50:
            tier = "OPERATIONAL_HIGH"
        elif composite >= 0.30:
            tier = "TACTICAL_MEDIUM"
        else:
            tier = "STANDARD"

        return {
            "criticality_score": round(composite, 3),
            "criticality_tier": tier,
            "components": {
                "priority_score": round(priority_score, 3),
                "volume_score": round(volume_score, 3),
                "connectivity_score": round(connectivity_score, 3),
                "scarcity_score": round(scarcity_score, 3),
            },
        }
