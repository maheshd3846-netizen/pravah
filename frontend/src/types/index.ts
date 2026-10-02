/**
 * TypeScript Data Models and API Contracts for PRAVAH Command Center.
 * Generated strictly from backend schemas across simulation, intelligence,
 * optimization, counterfactual evaluation, and decision engine.
 */

export type EchelonType = 'CENTRAL_DEPOT' | 'REGIONAL_HUB' | 'TRANSIT_POINT' | 'FORWARD_POST';
export type RouteStatusType = 'AVAILABLE' | 'DEGRADED' | 'BLOCKED';
export type VehicleStatusType = 'AVAILABLE' | 'IN_TRANSIT' | 'MAINTENANCE' | 'DISRUPTED';
export type ActionType = 'MOVE' | 'REROUTE' | 'REALLOCATE' | 'PRIORITIZE' | 'HOLD' | 'DEFER';
export type RecommendationStatus = 'PROPOSED' | 'VERIFIED' | 'MIXED' | 'REJECTED' | 'INCONCLUSIVE';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';
export type DataQualityState = 'READY' | 'DEGRADED' | 'INSUFFICIENT';

export interface NodeItem {
  id: string;
  code: string;
  name: string;
  type: string;
  priority: number;
  latitude: number;
  longitude: number;
  elevation: number;
  storage_capacity: number;
  safety_stock_days: number;
  active: boolean;
  initial_inventory: Record<string, number>;
  reorder_point: Record<string, number>;
  reorder_quantity: Record<string, number>;
}

export interface RouteItem {
  id: string;
  route_code: string;
  source_node_id: string;
  destination_node_id: string;
  distance_km: number;
  base_travel_hours: number;
  max_capacity: number;
  terrain_type: string;
  reliability_score: number;
  weather_sensitivity: number;
  status: string;
  geometry: [number, number][];
}

export interface VehicleItem {
  id: string;
  vehicle_code: string;
  vehicle_type: string;
  capacity: number;
  current_node_id: string;
  availability: boolean;
  fuel_level: number;
  status: string;
}

export interface NetworkResponse {
  total_nodes: number;
  total_routes: number;
  total_vehicles: number;
  nodes: NodeItem[];
  routes: RouteItem[];
  vehicles: VehicleItem[];
}

export interface RiskComponents {
  inventory: number;
  demand: number;
  route: number;
  transport: number;
  environment: number;
}

export interface NodeRiskDetail {
  node_id: string;
  node_code: string;
  overall_risk: number;
  level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  components: RiskComponents;
  raw_indicators: Record<string, any>;
  criticality?: number | null;
  propagated_risk?: number | null;
}

export interface RiskOverviewResponse {
  total_nodes_assessed: number;
  high_risk_nodes_count: number;
  high_risk_nodes: string[];
  blocked_routes_count: number;
  blocked_routes: string[];
  total_active_alerts: number;
  critical_alerts_count: number;
  nodes: NodeRiskDetail[];
}

export interface AlertItem {
  alert_id: string;
  severity: 'CRITICAL' | 'HIGH' | 'WARNING';
  node_id: string;
  node_code: string;
  item: string;
  alert_type: string;
  time_horizon_hours: number;
  probability: number;
  causes: string[];
  evidence: Record<string, any>;
  explanation: string;
}

export interface AlertsListResponse {
  total_alerts: number;
  critical_count: number;
  high_count: number;
  warning_count: number;
  alerts: AlertItem[];
}

export interface ForecastItemResponse {
  node_id: string;
  item_id: string;
  horizon_hours: number;
  model_version: string;
  feature_version: string;
  generated_at: string;
  p50: number[];
  p80: number[];
  p95: number[];
  stockout_probability?: number | null;
  time_to_safety_stock_hours?: number | null;
  time_to_zero_hours?: number | null;
  dynamic_safety_stock?: number | null;
}

export interface MovementDecision {
  decision_id: string;
  source_node_id: string;
  destination_node_id: string;
  item: string;
  quantity: number;
  route_id: string;
  vehicle_id: string;
  dispatch_hour: number;
  estimated_arrival_hour: number;
  priority: number;
  reason_codes: string[];
  rationale: string;
}

export interface OptimizationSolveResponse {
  run_id: string;
  status: string;
  solver_type: string;
  objective_value: number;
  execution_time_ms: number;
  demand_policy: string;
  total_transport_cost: number;
  total_shortage: number;
  total_delay: number;
  total_risk_cost: number;
  vehicle_utilization: number;
  route_utilization: number;
  decisions: MovementDecision[];
  infeasibility_reasons: string[];
  metadata: Record<string, any>;
}

export interface MetricDelta {
  metric_name: string;
  baseline: number;
  optimized: number;
  absolute_delta: number;
  relative_delta_percent: number;
  direction: 'IMPROVED' | 'DEGRADED' | 'NEUTRAL';
  is_better: boolean;
}

export interface SimulationRunMetrics {
  total_requested_demand: number;
  total_fulfilled_demand: number;
  total_unmet_demand: number;
  fulfillment_rate_percent: number;
  total_stockout_events: number;
  stockout_duration_hours: number;
  total_transport_cost: number;
  total_transport_distance_km: number;
  average_delay_hours: number;
}

export interface CounterfactualEvaluationResponse {
  evaluation_id: string;
  optimization_run_id: string;
  scenario_id: string;
  status: string;
  horizon_hours: number;
  seed: number;
  initial_state_hash: string;
  baseline: SimulationRunMetrics;
  optimized: SimulationRunMetrics;
  deltas: Record<string, MetricDelta>;
  tradeoffs: Record<string, string>;
  critical_nodes: string[];
  shipment_trace: Record<string, any>[];
  plan_validation: {
    status: string;
    violations: string[];
  };
  created_at: string;
}

export interface DecisionEvidenceItem {
  type: string;
  value: any;
  source: string;
  details: string;
}

export interface RouteAlternative {
  route_id: string;
  distance_km: number;
  status: string;
  risk_score: number;
  is_selected: boolean;
  reason: string;
}

export interface DecisionConfidence {
  level: ConfidenceLevel;
  score: number;
  factors: string[];
}

export interface RecommendationItem {
  recommendation_id: string;
  scenario_id: string;
  optimization_run_id: string;
  evaluation_id?: string | null;

  priority: number;
  action_type: ActionType;

  source_node: string;
  destination_node: string;
  item: string;
  quantity: number;
  route: string;
  vehicle: string;

  planned_departure: number;
  expected_arrival: number;

  title: string;
  reason: string;

  evidence: DecisionEvidenceItem[];
  tradeoffs: Record<string, any>;

  expected_effect: string;
  verified_effect: string;

  status: RecommendationStatus;
  confidence: DecisionConfidence;

  validation_state: Record<string, string>;
  conflict_detected: boolean;
  conflict_details: string[];
  alternatives: RouteAlternative[];
  audit_trail: Record<string, string>;
  created_at: string;
}

export interface RecommendationListResponse {
  total_recommendations: number;
  status_counts: Record<string, number>;
  action_counts: Record<string, number>;
  recommendations: RecommendationItem[];
}

export interface DecisionSummaryResponse {
  readiness: string;
  data_quality: string;
  critical_nodes: Record<string, any>[];
  active_risks: Record<string, any>[];
  recommendations_count: number;
  verified_actions_count: number;
  top_recommendations: RecommendationItem[];
  overall_tradeoffs: Record<string, any>;
  last_updated: string;
}

export interface DisruptionItem {
  id: string;
  type: string;
  target: string;
  severity: number;
  start_time: number;
  duration: number;
  impact_factor: number;
  description: string;
}

export interface ScenarioItem {
  name: string;
  description: string;
  horizon_hours: number;
  disruptions: DisruptionItem[];
}
