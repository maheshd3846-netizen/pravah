"""Simulation Service executing runs and managing run states."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from simulation.simulator import Simulator, SimulationConfig, SimulationResult
from simulation.disruption_engine import Disruption
from simulation.world_generator import DisruptionType
from backend.app.services.scenario_service import ScenarioService


class SimulationService:
    """Orchestrates simulation execution and maintains runtime memory cache."""

    def __init__(self, scenario_service: Optional[ScenarioService] = None):
        self.scenario_service = scenario_service or ScenarioService()
        self.active_runs: Dict[str, Simulator] = {}
        self.completed_results: Dict[str, SimulationResult] = {}

    def execute_simulation(
        self,
        scenario_name: str = "COMPOUND_DISRUPTION",
        seed: int = 42,
        start_hour: int = 0,
        horizon_hours: int = 336,
        auto_replenish: bool = True,
        custom_disruptions: Optional[List[Dict[str, Any]]] = None,
    ) -> SimulationResult:
        """Configures and runs full discrete-time simulation."""
        # 1. Load scenario disruptions
        disruptions = self.scenario_service.load_disruptions(scenario_name)

        # 2. Append any custom override disruptions
        if custom_disruptions:
            for cd in custom_disruptions:
                d = Disruption(
                    id=cd.get("id", f"DISR_CUSTOM_{len(disruptions)+1}"),
                    type=DisruptionType(cd["type"]),
                    target=cd["target"],
                    severity=float(cd["severity"]),
                    start_time=int(cd["start_time"]),
                    duration=int(cd["duration"]),
                    impact_factor=float(cd["impact_factor"]),
                    description=cd.get("description", "Custom runtime disruption"),
                )
                disruptions.append(d)

        # 3. Create simulation configuration
        config = SimulationConfig(
            seed=seed,
            start_hour=start_hour,
            horizon_hours=horizon_hours,
            scenario_name=scenario_name,
            auto_replenish=auto_replenish,
            disruptions=disruptions,
        )

        sim = Simulator(config=config)
        self.active_runs[sim.run_id] = sim

        result = sim.run()
        self.completed_results[result.run_id] = result
        return result

    def get_run_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Queries running or completed simulation status and active operational metrics."""
        if run_id in self.completed_results:
            res = self.completed_results[run_id]
            sim = self.active_runs.get(run_id)
            return {
                "run_id": res.run_id,
                "current_hour": res.horizon_hours,
                "horizon_hours": res.horizon_hours,
                "is_completed": True,
                "summary": res.summary_metrics,
                "active_disruptions": [d.to_dict() for d in sim.config.disruptions] if sim else [],
                "active_shipments": [s.to_dict() for s in sim.world.active_shipments] if sim else [],
                "completed_shipments_count": len(res.shipments),
                "critical_nodes": res.critical_nodes,
            }
        return None
