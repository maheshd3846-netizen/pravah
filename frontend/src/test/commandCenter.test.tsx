import React from 'react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '../components/Header';
import { StatusBar } from '../components/StatusBar';
import { KpiStrip } from '../components/KpiStrip';
import { DigitalTwinMap } from '../components/DigitalTwinMap';
import { RiskPanel } from '../components/RiskPanel';
import { ForecastPanel } from '../components/ForecastPanel';
import { DecisionCenter } from '../components/DecisionCenter';
import { VerificationPanel } from '../components/VerificationPanel';
import { ScenarioSimulator } from '../components/ScenarioSimulator';
import { RecommendationsView } from '../components/RecommendationsView';
import { AuditTrailView } from '../components/AuditTrailView';
import { AnalyzeModal } from '../components/AnalyzeModal';
import { DemoTour } from '../components/DemoTour';
import { SituationBar } from '../components/SituationBar';
import { CurrentDecisionBar } from '../components/CurrentDecisionBar';
import { NetworkRiskOverlay } from '../components/NetworkRiskOverlay';
import { SimulationDetailsModal } from '../components/SimulationDetailsModal';
import type {
  NodeItem,
  RouteItem,
  VehicleItem,
  NodeRiskDetail,
  AlertItem,
  ForecastItemResponse,
  RecommendationItem,
  CounterfactualEvaluationResponse,
} from '../types';

const mockNodes: NodeItem[] = [
  {
    id: 'NODE_CD_01',
    code: 'CD-01',
    name: 'Central Base Depot Alpha',
    type: 'CENTRAL_DEPOT',
    priority: 1,
    latitude: 34.12,
    longitude: 76.21,
    elevation: 1850,
    storage_capacity: 500000,
    safety_stock_days: 21,
    active: true,
    initial_inventory: { FUEL: 50000, RATIONS: 25000 },
    reorder_point: {},
    reorder_quantity: {},
  },
  {
    id: 'NODE_FP_01',
    code: 'FP-01',
    name: 'Forward Defense Post Siachen-North',
    type: 'FORWARD_POST',
    priority: 5,
    latitude: 35.32,
    longitude: 77.15,
    elevation: 5400,
    storage_capacity: 25000,
    safety_stock_days: 30,
    active: true,
    initial_inventory: { FUEL: 1200, RATIONS: 800 },
    reorder_point: {},
    reorder_quantity: {},
  },
];

const mockRoutes: RouteItem[] = [
  {
    id: 'ROUTE_R_01',
    route_code: 'R-01',
    source_node_id: 'NODE_CD_01',
    destination_node_id: 'NODE_FP_01',
    distance_km: 84.5,
    base_travel_hours: 4,
    max_capacity: 5000,
    terrain_type: 'HIGH_ALTITUDE_PASS',
    reliability_score: 0.65,
    weather_sensitivity: 0.8,
    status: 'BLOCKED',
    geometry: [[34.12, 76.21], [35.32, 77.15]],
  },
];

const mockVehicles: VehicleItem[] = [
  {
    id: 'VEH_01',
    vehicle_code: 'ALS-101',
    vehicle_type: 'HEAVY_TRUCK',
    capacity: 10000,
    current_node_id: 'NODE_CD_01',
    availability: true,
    fuel_level: 1.0,
    status: 'AVAILABLE',
  },
];

const mockNodeRisks: Record<string, NodeRiskDetail> = {
  NODE_FP_01: {
    node_id: 'NODE_FP_01',
    node_code: 'FP-01',
    overall_risk: 0.78,
    level: 'HIGH',
    components: {
      inventory: 0.85,
      demand: 0.65,
      route: 0.9,
      transport: 0.4,
      environment: 0.5,
    },
    raw_indicators: {},
  },
};

const mockAlerts: AlertItem[] = [
  {
    alert_id: 'ALERT_01',
    severity: 'CRITICAL',
    node_id: 'NODE_FP_01',
    node_code: 'FP-01',
    item: 'FUEL',
    alert_type: 'STOCKOUT_IMMINENT',
    time_horizon_hours: 18,
    probability: 0.95,
    causes: ['Corridor blocked', 'Forward demand surge'],
    evidence: {},
    explanation: 'Fuel depleted rapidly under sub-zero conditions.',
  },
];

const mockForecast: ForecastItemResponse = {
  node_id: 'NODE_FP_01',
  item_id: 'FUEL',
  horizon_hours: 24,
  model_version: 'v2.5-xgboost-quantile',
  feature_version: 'f-v2.1',
  generated_at: new Date().toISOString(),
  p50: [10, 12, 14, 15, 12, 10],
  p80: [15, 18, 20, 22, 18, 16],
  p95: [22, 25, 28, 30, 26, 24],
  stockout_probability: 0.92,
  time_to_safety_stock_hours: 8,
  time_to_zero_hours: 18,
  dynamic_safety_stock: 450,
};

const mockRecommendation: RecommendationItem = {
  recommendation_id: 'REC_001',
  scenario_id: 'COMPOUND_DISRUPTION',
  optimization_run_id: 'RUN_123',
  evaluation_id: 'EVAL_456',
  priority: 1,
  action_type: 'REALLOCATE',
  source_node: 'RH-03',
  destination_node: 'FP-01',
  item: 'FUEL',
  quantity: 35.0,
  route: 'R-11',
  vehicle: 'ALS-104',
  planned_departure: 0,
  expected_arrival: 4,
  title: 'REALLOCATE FUEL to FP-01',
  reason: '- FP-01 requires emergency replenishment.\n- Alternate corridor R-11 is available.',
  evidence: [
    {
      type: 'STOCKOUT_PROBABILITY',
      value: 0.92,
      source: 'Monte Carlo',
      details: 'Risk of stockout',
    },
    {
      type: 'TIME_TO_ZERO',
      value: 18,
      source: 'Inventory Model',
      details: 'Hours to empty',
    },
  ],
  tradeoffs: {
    SERVICE: 'IMPROVED',
    RISK: 'MITIGATED',
    TRANSPORT_COST: 'INCREASED',
    DELAY: 'INCREASED',
  },
  expected_effect: 'Projected to reduce unmet demand by 35 units.',
  verified_effect: 'Simulation verified unmet demand reduction of 4486.9 units (-79.0%).',
  status: 'MIXED',
  confidence: {
    level: 'HIGH',
    score: 0.95,
    factors: ['Telemetry verified', 'Corridor open'],
  },
  validation_state: {
    source_inventory: 'PASS',
    route: 'PASS',
    vehicle: 'PASS',
    quantity: 'PASS',
  },
  conflict_detected: false,
  conflict_details: [],
  alternatives: [
    {
      route_id: 'R-01',
      distance_km: 84.5,
      status: 'BLOCKED',
      risk_score: 0.95,
      is_selected: false,
      reason: 'Blocked by landslide',
    },
    {
      route_id: 'R-11',
      distance_km: 99.0,
      status: 'AVAILABLE',
      risk_score: 0.15,
      is_selected: true,
      reason: 'Open bypass corridor',
    },
  ],
  audit_trail: {
    scenario_id: 'COMPOUND_DISRUPTION',
    optimization_run_id: 'RUN_123',
    evaluation_id: 'EVAL_456',
  },
  created_at: new Date().toISOString(),
};

const mockEvaluation: CounterfactualEvaluationResponse = {
  evaluation_id: 'EVAL_456',
  optimization_run_id: 'RUN_123',
  scenario_id: 'COMPOUND_DISRUPTION',
  status: 'MIXED',
  horizon_hours: 72,
  seed: 42,
  initial_state_hash: 'hash_abc123',
  baseline: {
    total_requested_demand: 120000,
    total_fulfilled_demand: 114321.3,
    total_unmet_demand: 5678.7,
    fulfillment_rate_percent: 95.27,
    total_stockout_events: 52,
    stockout_duration_hours: 52,
    total_transport_cost: 1200,
    total_transport_distance_km: 980.5,
    average_delay_hours: 1.2,
  },
  optimized: {
    total_requested_demand: 120000,
    total_fulfilled_demand: 118808.2,
    total_unmet_demand: 1191.8,
    fulfillment_rate_percent: 99.01,
    total_stockout_events: 18,
    stockout_duration_hours: 18,
    total_transport_cost: 2800,
    total_transport_distance_km: 2634.2,
    average_delay_hours: 3.1,
  },
  deltas: {
    unmet_demand: {
      metric_name: 'unmet_demand',
      baseline: 5678.7,
      optimized: 1191.8,
      absolute_delta: -4486.9,
      relative_delta_percent: -79.0,
      direction: 'IMPROVED',
      is_better: true,
    },
    stockout_events: {
      metric_name: 'stockout_events',
      baseline: 52,
      optimized: 18,
      absolute_delta: -34,
      relative_delta_percent: -65.4,
      direction: 'IMPROVED',
      is_better: true,
    },
    fulfillment_rate_percent: {
      metric_name: 'fulfillment_rate_percent',
      baseline: 95.27,
      optimized: 99.01,
      absolute_delta: 3.74,
      relative_delta_percent: 3.93,
      direction: 'IMPROVED',
      is_better: true,
    },
    total_transport_distance_km: {
      metric_name: 'total_transport_distance_km',
      baseline: 980.5,
      optimized: 2634.2,
      absolute_delta: 1653.7,
      relative_delta_percent: 168.7,
      direction: 'DEGRADED',
      is_better: false,
    },
    average_delay_hours: {
      metric_name: 'average_delay_hours',
      baseline: 1.2,
      optimized: 3.1,
      absolute_delta: 1.9,
      relative_delta_percent: 158.3,
      direction: 'DEGRADED',
      is_better: false,
    },
  },
  tradeoffs: {
    SERVICE: 'IMPROVED',
    RISK: 'MITIGATED',
    TRANSPORT_COST: 'INCREASED',
    DELAY: 'INCREASED',
  },
  critical_nodes: ['FP-01'],
  shipment_trace: [],
  plan_validation: {
    status: 'VALID',
    violations: [],
  },
  created_at: new Date().toISOString(),
};

describe('PRAVAH Phase 4 Command Center UI Test Suite', () => {
  it('renders Header with navigation tabs, system status, and synthetic simulation label', () => {
    const onTabChange = vi.fn();
    const onAnalyze = vi.fn();
    const onToggleDemo = vi.fn();

    render(
      <Header
        currentTab="COMMAND_CENTER"
        onTabChange={onTabChange}
        onAnalyzeClick={onAnalyze}
        isAnalyzing={false}
        demoMode={false}
        onToggleDemoMode={onToggleDemo}
      />
    );

    expect(screen.getByText('PRAVAH')).toBeInTheDocument();
    expect(screen.getByText('SYSTEM READY')).toBeInTheDocument();
    expect(screen.getByText(/Synthetic Simulation/i)).toBeInTheDocument();
    expect(screen.getByText('COMMAND CENTER')).toBeInTheDocument();
    expect(screen.getByText('RECOMMENDATIONS')).toBeInTheDocument();

    fireEvent.click(screen.getByText('NETWORK'));
    expect(onTabChange).toHaveBeenCalledWith('NETWORK');

    fireEvent.click(screen.getByText('⚡ ANALYZE NETWORK'));
    expect(onAnalyze).toHaveBeenCalled();

    fireEvent.click(screen.getByText('DEMO MODE'));
    expect(onToggleDemo).toHaveBeenCalled();
  });

  it('renders StatusBar with data quality gate and active scenario', () => {
    render(
      <StatusBar
        systemStatus="READY"
        dataQuality="READY"
        forecastHorizonDays={14}
        activeScenario="COMPOUND_DISRUPTION"
        lastUpdated="2026-10-02T12:00:00Z"
      />
    );

    expect(screen.getByText(/SYSTEM STATUS:/i)).toBeInTheDocument();
    expect(screen.getAllByText('READY').length).toBe(2);
    expect(screen.getByText('14 DAYS')).toBeInTheDocument();
    expect(screen.getByText('COMPOUND_DISRUPTION')).toBeInTheDocument();
  });

  it('renders KpiStrip with real values and unavailable fallback handling', () => {
    const { rerender } = render(
      <KpiStrip
        totalNodes={15}
        totalRoutes={28}
        totalVehicles={12}
        highRiskNodesCount={3}
        activeRecommendationsCount={55}
      />
    );

    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('28')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('55')).toBeInTheDocument();

    // Unavailable fallback test (No fabricated numbers)
    rerender(
      <KpiStrip
        totalNodes={null}
        totalRoutes={null}
        totalVehicles={null}
        highRiskNodesCount={null}
        activeRecommendationsCount={null}
      />
    );

    const unavailables = screen.getAllByText('Unavailable');
    expect(unavailables.length).toBe(5);
  });

  it('renders DigitalTwinMap with nodes and routes and handles selection', () => {
    const onSelectNode = vi.fn();
    const onSelectRoute = vi.fn();

    render(
      <DigitalTwinMap
        nodes={mockNodes}
        routes={mockRoutes}
        vehicles={mockVehicles}
        nodeRisks={mockNodeRisks}
        onSelectNode={onSelectNode}
        onSelectRoute={onSelectRoute}
      />
    );

    expect(screen.getByText(/LOGISTICS DIGITAL TWIN/i)).toBeInTheDocument();
    expect(screen.getAllByText('CD-01')[0]).toBeInTheDocument();
    expect(screen.getAllByText('FP-01')[0]).toBeInTheDocument();

    // Node click
    fireEvent.click(screen.getAllByText('FP-01')[0]);
    expect(onSelectNode).toHaveBeenCalled();
  });

  it('renders RiskPanel with critical stockout warnings and 5-factor breakdown', () => {
    const onSelectNode = vi.fn();

    render(
      <RiskPanel
        alerts={mockAlerts}
        nodeRisks={mockNodeRisks}
        selectedNodeId="NODE_FP_01"
        onSelectNode={onSelectNode}
      />
    );

    expect(screen.getByText(/CRITICAL RISKS & EARLY WARNINGS/i)).toBeInTheDocument();
    expect(screen.getAllByText('FP-01')[0]).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('Inventory')).toBeInTheDocument();
    expect(screen.getByText('Demand')).toBeInTheDocument();
    expect(screen.getByText('Route')).toBeInTheDocument();
  });

  it('renders ForecastPanel with quantiles P50/P80/P95 and stockout horizon', () => {
    render(
      <ForecastPanel
        nodeCode="FP-01"
        itemId="FUEL"
        forecastData={mockForecast}
      />
    );

    expect(screen.getByText(/DEMAND FORECAST & UNCERTAINTY BANDS/i)).toBeInTheDocument();
    expect(screen.getByText(/STOCKOUT & SAFETY STOCK OUTLOOK/i)).toBeInTheDocument();
    expect(screen.getByText('92%')).toBeInTheDocument(); // Stockout prob
    expect(screen.getByText('+18h')).toBeInTheDocument(); // Time to zero
    expect(screen.getByText('+8h')).toBeInTheDocument(); // Time to safety stock
  });

  it('renders DecisionCenter with recommended action, evidence, and corridor comparison', () => {
    const onEvidenceClick = vi.fn();

    render(
      <DecisionCenter
        recommendation={mockRecommendation}
        onEvidenceClick={onEvidenceClick}
      />
    );

    expect(screen.getByText(/DECISION CENTER/i)).toBeInTheDocument();
    expect(screen.getByText(/REALLOCATE 35 FUEL/i)).toBeInTheDocument();
    expect(screen.getByText('MIXED')).toBeInTheDocument();
    expect(screen.getByText('CONFIDENCE: HIGH (95%)')).toBeInTheDocument();
    expect(screen.getByText(/WHY THIS DECISION/i)).toBeInTheDocument();
    expect(screen.getByText(/WHY THIS CORRIDOR/i)).toBeInTheDocument();

    // Click evidence item
    const evButton = screen.getByText(/STOCKOUT_PROBABILITY: 0.92/i);
    fireEvent.click(evButton);
    expect(onEvidenceClick).toHaveBeenCalled();
  });

  it('renders VerificationPanel with expected vs verified effects and tradeoffs', () => {
    render(
      <VerificationPanel
        recommendation={mockRecommendation}
        evaluation={mockEvaluation}
      />
    );

    expect(screen.getByText(/EXPECTED EFFECT/i)).toBeInTheDocument();
    expect(screen.getByText(/VERIFIED EFFECT/i)).toBeInTheDocument();
    expect(screen.getByText(/OPERATIONAL TRADEOFF MATRIX/i)).toBeInTheDocument();
    expect(screen.getByText(/SERVICE OUTCOME/i)).toBeInTheDocument();
    expect(screen.getByText(/LOGISTICS RISK/i)).toBeInTheDocument();
  });

  it('renders ScenarioSimulator with disruption presets and causal delta table', () => {
    const onRun = vi.fn();

    render(
      <ScenarioSimulator
        evaluation={mockEvaluation}
        onRunScenario={onRun}
      />
    );

    expect(screen.getByText(/WHAT-IF DISRUPTION SIMULATOR/i)).toBeInTheDocument();
    expect(screen.getByText(/CLOSED-LOOP CAUSAL COMPARISON/i)).toBeInTheDocument();
    expect(screen.getByText('Unmet Supply Demand')).toBeInTheDocument();
    expect(screen.getByText('5678.7 u')).toBeInTheDocument();
    expect(screen.getByText('1191.8 u')).toBeInTheDocument();

    fireEvent.click(screen.getByText('▶ RUN SCENARIO'));
    expect(onRun).toHaveBeenCalled();
  });

  it('renders RecommendationsView with filterable list and audit drawer', () => {
    const onSelect = vi.fn();

    render(
      <RecommendationsView
        recommendations={[mockRecommendation]}
        onSelectRecommendation={onSelect}
        selectedRecommendationId="REC_001"
      />
    );

    expect(screen.getByText(/ALL TACTICAL LOGISTICS RECOMMENDATIONS/i)).toBeInTheDocument();
    expect(screen.getByText('REC_001')).toBeInTheDocument();
    expect(screen.getByText('PROVENANCE AUDIT TRAIL')).toBeInTheDocument();
  });

  it('renders AuditTrailView showing full causal lineage chain', () => {
    render(<AuditTrailView recommendation={mockRecommendation} />);

    expect(screen.getByText(/DECISION LINEAGE & FULL AUDIT PROVENANCE CHAIN/i)).toBeInTheDocument();
    expect(screen.getByText(/HOW DID PRAVAH REACH THIS DECISION/i)).toBeInTheDocument();
    expect(screen.getByText('1. OPERATIONAL SCENARIO')).toBeInTheDocument();
    expect(screen.getByText('2. QUANTILE DEMAND FORECAST')).toBeInTheDocument();
    expect(screen.getByText('3. MULTI-FACTOR RISK STATE')).toBeInTheDocument();
    expect(screen.getByText('4. MATHEMATICAL OPTIMIZATION RUN')).toBeInTheDocument();
    expect(screen.getByText('5. COUNTERFACTUAL SIMULATION')).toBeInTheDocument();
    expect(screen.getByText('6. AUDITABLE RECOMMENDATION')).toBeInTheDocument();
  });

  it('renders AnalyzeModal with 5-stage progress indicator', () => {
    const onClose = vi.fn();

    render(
      <AnalyzeModal
        isOpen={true}
        currentStage="OPTIMIZE"
        onClose={onClose}
      />
    );

    expect(screen.getByText(/PRAVAH INTELLIGENCE PIPELINE/i)).toBeInTheDocument();
    expect(screen.getByText(/Optimizing Supply Allocation & Routing/i)).toBeInTheDocument();
  });

  it('renders DemoTour and advances through guided presentation steps', () => {
    const onStep = vi.fn();
    const onClose = vi.fn();

    render(<DemoTour onStepChange={onStep} onClose={onClose} />);

    expect(screen.getByText(/DEMO MODE \(STEP 1 OF 12\)/i)).toBeInTheDocument();
    expect(screen.getByText(/1. NORMAL LOGISTICS TOPOLOGY/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText('NEXT STEP ▶'));
    expect(onStep).toHaveBeenCalledWith(1);
    expect(screen.getByText(/DEMO MODE \(STEP 2 OF 12\)/i)).toBeInTheDocument();
  });

  it('renders SituationBar with dynamic operational statement and compact inline metrics', () => {
    const onAnalysis = vi.fn();
    const onNetwork = vi.fn();

    render(
      <SituationBar
        activeScenario="COMPOUND_DISRUPTION"
        blockedRoutes={['R-22']}
        criticalNodes={['FP-04']}
        totalNodes={15}
        overallRiskScore={0.72}
        overallRiskLevel="HIGH"
        stockoutExposedCount={2}
        onViewAnalysis={onAnalysis}
        onViewNetworkDetails={onNetwork}
      />
    );

    expect(screen.getByText(/CURRENT SITUATION/i)).toBeInTheDocument();
    expect(screen.getByText(/Compound Disruption/i)).toBeInTheDocument();
    expect(screen.getByText(/R-22 blocked/i)).toBeInTheDocument();
    expect(screen.getByText(/FP-04 demand pressure rising/i)).toBeInTheDocument();
    expect(screen.getByText(/15 Nodes/i)).toBeInTheDocument();
    expect(screen.getByText(/0.72/i)).toBeInTheDocument();
    expect(screen.getByText(/2 Nodes/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText('View Analysis →'));
    expect(onAnalysis).toHaveBeenCalled();

    fireEvent.click(screen.getByText('View Network Details →'));
    expect(onNetwork).toHaveBeenCalled();
  });

  it('renders CurrentDecisionBar with verified action and degraded/suppressed safety state', () => {
    const onEvidence = vi.fn();

    // 1. Verified action available state
    const { rerender } = render(
      <CurrentDecisionBar
        recommendation={mockRecommendation}
        evaluation={mockEvaluation}
        onViewEvidence={onEvidence}
      />
    );

    expect(screen.getByText(/DECISION STATUS/i)).toBeInTheDocument();
    expect(screen.getByText(/Verified Action Available/i)).toBeInTheDocument();
    expect(screen.getByText(/Physical feasibility:/i)).toBeInTheDocument();
    expect(screen.getByText(/PASSED/i)).toBeInTheDocument();
    expect(screen.getByText(/IMPROVED/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText('View Evidence →'));
    expect(onEvidence).toHaveBeenCalled();

    // 2. Deliberate Safety Rejection / Suppressed state
    const suppressedEval: CounterfactualEvaluationResponse = {
      ...mockEvaluation,
      status: 'DEGRADED',
      deltas: {
        ...mockEvaluation.deltas,
        unmet_demand: {
          ...mockEvaluation.deltas.unmet_demand,
          direction: 'DEGRADED',
          is_better: false,
        },
      },
    };

    rerender(
      <CurrentDecisionBar
        recommendation={{ ...mockRecommendation, status: 'REJECTED' }}
        evaluation={suppressedEval}
        rejectionSummary="Suppressed by safety protocol"
        onViewEvidence={onEvidence}
      />
    );

    expect(screen.getByText(/RECOMMENDATION SUPPRESSED/i)).toBeInTheDocument();
    expect(screen.getByText(/Safety Protocol Active/i)).toBeInTheDocument();
    expect(screen.getByText(/The proposed intervention did not demonstrate a verified improvement/i)).toBeInTheDocument();
    expect(screen.getByText(/Benefit not verified/i)).toBeInTheDocument();
  });

  it('renders NetworkRiskOverlay with score, level badge, and top drivers', () => {
    const onRisk = vi.fn();

    render(
      <NetworkRiskOverlay
        score={0.72}
        level="HIGH"
        topDrivers={['Route (R-22 blocked)', 'Demand (FP-04 surge)', 'Inventory']}
        onViewRisk={onRisk}
      />
    );

    expect(screen.getByText(/NETWORK RISK/i)).toBeInTheDocument();
    expect(screen.getByText('0.72')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('Route (R-22 blocked)')).toBeInTheDocument();

    fireEvent.click(screen.getByText('View Risk →'));
    expect(onRisk).toHaveBeenCalled();
  });

  it('renders SimulationDetailsModal with technical metadata and dismiss handler', () => {
    const onClose = vi.fn();

    render(
      <SimulationDetailsModal
        isOpen={true}
        onClose={onClose}
        activeScenario="COMPOUND_DISRUPTION"
        seed={42}
      />
    );

    expect(screen.getByText(/Simulation & System Details/i)).toBeInTheDocument();
    expect(screen.getByText(/Sector Shivalik-Vanguard/i)).toBeInTheDocument();
    expect(screen.getByText(/Seed 42/i)).toBeInTheDocument();
    expect(screen.getByText(/SATCOM Primary/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText('Close Details'));
    expect(onClose).toHaveBeenCalled();
  });
});
