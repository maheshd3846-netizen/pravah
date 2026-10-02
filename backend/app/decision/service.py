"""Decision & Recommendation Application Service."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from simulation.world_generator import WorldGenerator
from simulation.simulator import SimulationConfig
from simulation.disruption_engine import Disruption, DisruptionEngine
from backend.app.services.scenario_service import ScenarioService
from backend.app.risk.service import RiskIntelligenceService
from backend.app.optimization.service import OptimizationService
from optimization.types import DemandPolicy, SolverType
from optimization.adapters import OptimizationInputAdapter
from optimization.solver import LogisticsSolver
from optimization.evaluator import PlanEvaluator

from backend.app.decision.schemas import (
    RecommendationSchema,
    RecommendationGenerateRequest,
    RecommendationListResponse,
    DecisionSummaryResponse,
    DataQualityState,
    RecommendationStatus,
)
from backend.app.decision.engine import DecisionEngine


class DecisionService:
    """Orchestrates end-to-end recommendation generation, storage, and retrieval."""

    def __init__(self):
        self.engine = DecisionEngine()
        self.scenario_service = ScenarioService()
        self.risk_service = RiskIntelligenceService()
        self.opt_service = OptimizationService()
        self.evaluator = PlanEvaluator()

        # In-memory storage for recommendations: recommendation_id -> RecommendationSchema
        self._recommendations_db: Dict[str, RecommendationSchema] = {}

    def generate_recommendations(
        self,
        request: RecommendationGenerateRequest,
    ) -> RecommendationListResponse:
        """Executes full intelligence, optimization, simulation, and decision pipeline."""
        scenario_id = request.scenario_id
        seed = request.seed
        horizon_hours = request.horizon_hours
        data_quality = request.data_quality_state

        # 1. Initialize world and scenario disruptions
        world = WorldGenerator(seed=seed).generate_world()
        sc_dict = self.scenario_service.get_scenario(scenario_id)
        dis_list = []
        if sc_dict and "disruptions" in sc_dict:
            for d_data in sc_dict["disruptions"]:
                dis_list.append(Disruption.from_dict(d_data))

        dis_engine = DisruptionEngine(dis_list)
        dis_engine.apply_route_disruptions(world.routes, current_hour=0)
        dis_engine.apply_vehicle_disruptions(world.vehicles, current_hour=0)

        # 2. Risk Intelligence
        risk_data = self.risk_service.evaluate_world_risk(world)
        risk_assessments = self.risk_service._cached_assessments

        # 3. Retrieve or Solve Optimization Plan
        # 3. Retrieve or Solve Optimization Plan
        opt_run_id = request.optimization_run_id
        opt_result = None
        if opt_run_id:
            opt_result = self.opt_service.get_result(opt_run_id)
        if not opt_result:
            pol = DemandPolicy(request.demand_policy) if hasattr(DemandPolicy, request.demand_policy) else DemandPolicy.P80
            problem = OptimizationInputAdapter.create_problem(
                world=world,
                risk_assessments=risk_assessments,
                demand_policy=pol,
                horizon_hours=horizon_hours,
                scenario_id=scenario_id,
            )
            solver = LogisticsSolver(solver_type=SolverType.MILP)
            opt_result = solver.solve(problem)
            self.opt_service._cached_results[opt_result.run_id] = opt_result
            opt_run_id = opt_result.run_id

        # 4. Retrieve or Execute Counterfactual Simulation
        eval_id = request.evaluation_id
        eval_result = None
        if eval_id:
            eval_result = self.opt_service.get_evaluation(eval_id)
        elif opt_result and opt_result.decisions:
            sim_cfg = SimulationConfig(
                seed=seed,
                horizon_hours=horizon_hours,
                scenario_name=scenario_id,
                auto_replenish=True,
            )
            eval_result = self.evaluator.evaluate_plan(
                plan_or_result=opt_result,
                base_config=sim_cfg,
                scenario_id=scenario_id,
                horizon_hours=horizon_hours,
                seed=seed,
            )
            if not hasattr(self.opt_service, "_cached_evaluations"):
                self.opt_service._cached_evaluations = {}
            self.opt_service._cached_evaluations[eval_result.evaluation_id] = eval_result

        # 5. Generate Auditable Recommendations
        recs = self.engine.generate_recommendations(
            world=world,
            optimization_result=opt_result,
            evaluation_result=eval_result,
            risk_assessments=risk_assessments,
            scenario_id=scenario_id,
            data_quality_state=data_quality,
        )

        # Store in db
        for r in recs:
            self._recommendations_db[r.recommendation_id] = r

        # Aggregate counts
        status_counts: Dict[str, int] = {}
        action_counts: Dict[str, int] = {}
        for r in recs:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1
            action_counts[r.action_type] = action_counts.get(r.action_type, 0) + 1

        return RecommendationListResponse(
            total_recommendations=len(recs),
            status_counts=status_counts,
            action_counts=action_counts,
            recommendations=recs,
        )

    def list_recommendations(
        self,
        scenario_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        node: Optional[str] = None,
        item: Optional[str] = None,
    ) -> RecommendationListResponse:
        """Retrieves filtered recommendations from active store."""
        results = list(self._recommendations_db.values())

        if scenario_id:
            results = [r for r in results if r.scenario_id.lower() == scenario_id.lower()]
        if status:
            results = [r for r in results if r.status.upper() == status.upper()]
        if priority is not None:
            results = [r for r in results if r.priority == priority]
        if node:
            node_clean = node.lower()
            results = [r for r in results if node_clean in r.destination_node.lower() or node_clean in r.source_node.lower()]
        if item:
            results = [r for r in results if r.item.upper() == item.upper()]

        status_counts: Dict[str, int] = {}
        action_counts: Dict[str, int] = {}
        for r in results:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1
            action_counts[r.action_type] = action_counts.get(r.action_type, 0) + 1

        return RecommendationListResponse(
            total_recommendations=len(results),
            status_counts=status_counts,
            action_counts=action_counts,
            recommendations=results,
        )

    def get_recommendation(self, recommendation_id: str) -> Optional[RecommendationSchema]:
        """Fetches an individual recommendation by identifier."""
        return self._recommendations_db.get(recommendation_id)

    def get_decision_summary(self) -> DecisionSummaryResponse:
        """Constructs an operational summary for tactical commanders."""
        all_recs = list(self._recommendations_db.values())
        verified_count = sum(1 for r in all_recs if r.status in [RecommendationStatus.VERIFIED.value, RecommendationStatus.MIXED.value])

        # If empty, generate a quick default baseline
        if not all_recs:
            gen_resp = self.generate_recommendations(
                RecommendationGenerateRequest(scenario_id="COMPOUND_DISRUPTION")
            )
            all_recs = gen_resp.recommendations
            verified_count = sum(1 for r in all_recs if r.status in [RecommendationStatus.VERIFIED.value, RecommendationStatus.MIXED.value])

        # Critical nodes facing high stockout probability
        world = WorldGenerator(seed=42).generate_world()
        risk_data = self.risk_service.evaluate_world_risk(world)
        cached_assessments = self.risk_service._cached_assessments

        critical_nodes: List[Dict[str, Any]] = []
        for nid, node in world.nodes.items():
            ass = cached_assessments.get(nid)
            score = getattr(ass, "overall_risk", 0.0) if ass else 0.0
            tier = getattr(ass, "level", "MODERATE") if ass else "MODERATE"
            if score >= 0.35 or tier in ["HIGH", "CRITICAL"]:
                critical_nodes.append({
                    "node_id": nid,
                    "node_code": node.code,
                    "priority": node.priority,
                    "risk_score": round(score, 3),
                    "risk_tier": tier,
                })

        overall_tradeoffs = {
            "SERVICE": "IMPROVED",
            "RISK": "MITIGATED",
            "TRANSPORT_COST": "EXPEDITION_ACTIVE",
            "VERIFIED_DECISIONS": verified_count,
        }

        return DecisionSummaryResponse(
            readiness="OPERATIONAL",
            data_quality=DataQualityState.READY.value,
            critical_nodes=critical_nodes,
            active_risks=[a.to_dict() for a in cached_assessments.values() if a.overall_risk >= 0.35][:5],
            recommendations_count=len(all_recs),
            verified_actions_count=verified_count,
            top_recommendations=all_recs[:5],
            overall_tradeoffs=overall_tradeoffs,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )


# Global singleton instance
_decision_service_instance: Optional[DecisionService] = None


def get_decision_service() -> DecisionService:
    global _decision_service_instance
    if _decision_service_instance is None:
        _decision_service_instance = DecisionService()
    return _decision_service_instance
