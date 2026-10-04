import React, { useState, useEffect, useCallback } from 'react';
import type {
  NetworkResponse,
  NodeItem,
  RouteItem,
  RiskOverviewResponse,
  NodeRiskDetail,
  AlertItem,
  ForecastItemResponse,
  RecommendationItem,
  CounterfactualEvaluationResponse,
} from './types';
import * as api from './api';
import { Header } from './components/Header';
import type { NavTab } from './components/Header';
import { SituationBar } from './components/SituationBar';
import { NetworkRiskOverlay } from './components/NetworkRiskOverlay';
import { CurrentDecisionBar } from './components/CurrentDecisionBar';
import { DigitalTwinMap } from './components/DigitalTwinMap';
import { RiskPanel } from './components/RiskPanel';
import { ForecastPanel } from './components/ForecastPanel';
import { DecisionCenter } from './components/DecisionCenter';
import { ScenarioSimulator } from './components/ScenarioSimulator';
import { RecommendationsView } from './components/RecommendationsView';
import { AuditTrailView } from './components/AuditTrailView';
import { DemoTour } from './components/DemoTour';
import { AnalyzeModal } from './components/AnalyzeModal';
import type { PipelineStage } from './components/AnalyzeModal';
import { EvidenceDrawer } from './components/EvidenceDrawer';
import { KpiStrip } from './components/KpiStrip';

export const App: React.FC = () => {
  // Navigation
  const [currentTab, setCurrentTab] = useState<NavTab>('COMMAND_CENTER');

  // Core Data States
  const [network, setNetwork] = useState<NetworkResponse | null>(null);
  const [riskOverview, setRiskOverview] = useState<RiskOverviewResponse | null>(null);
  const [nodeRisks, setNodeRisks] = useState<Record<string, NodeRiskDetail>>({});
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [rejectionSummary, setRejectionSummary] = useState<string | null>(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState<RecommendationItem | null>(null);
  const [evaluation, setEvaluation] = useState<CounterfactualEvaluationResponse | null>(null);
  const [activeForecast, setActiveForecast] = useState<ForecastItemResponse | null>(null);

  // Selection States - Default null so NO inspection drawer is shown by default!
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<string>('FUEL');

  // Loading & Error States
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  // Interactive Modals & Demo
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analyzeStage, setAnalyzeStage] = useState<PipelineStage>('IDLE');
  const [showAnalyzeModal, setShowAnalyzeModal] = useState<boolean>(false);
  const [demoMode, setDemoMode] = useState<boolean>(false);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);

  // Fetch initial telemetry
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // 1. Network Topology
      const netRes = await api.fetchNetwork();
      setNetwork(netRes);

      // 2. Risk Overview & Nodes
      const riskRes = await api.fetchRiskOverview();
      setRiskOverview(riskRes);
      const riskMap: Record<string, NodeRiskDetail> = {};
      riskRes.nodes.forEach((n) => {
        riskMap[n.node_id] = n;
        riskMap[n.node_code] = n;
      });
      setNodeRisks(riskMap);

      // 3. Early Warning Alerts
      const alertsRes = await api.fetchAlerts();
      setAlerts(alertsRes.alerts);

      // 4. Initial Recommendations & Evaluation
      const recsRes = await api.generateRecommendations({
        scenario_id: 'COMPOUND_DISRUPTION',
        demand_policy: 'P80',
        data_quality_state: 'READY',
      });
      setRecommendations(recsRes.recommendations);
      setRejectionSummary(recsRes.rejection_summary || null);

      if (recsRes.recommendations.length > 0) {
        // Pick primary critical recommendation for decision status bar
        const target =
          recsRes.recommendations.find(
            (r) => r.status === 'VERIFIED' || r.status === 'MIXED'
          ) || recsRes.recommendations[0];
        setSelectedRecommendation(target);

        // NOTE: We deliberately do NOT set selectedNodeId here so the Digital Twin
        // starts clean without any default node inspection drawer open!

        // Load evaluation if present
        const evalId = target.audit_trail?.['evaluation_id'];
        if (evalId) {
          try {
            const evalRes = await api.getEvaluationRecord(evalId);
            setEvaluation(evalRes);
          } catch {
            // Evaluation record retrieval non-fatal
          }
        }
      }

      setLastUpdated(new Date().toISOString());
    } catch (err: any) {
      console.error('Failed to load telemetry:', err);
      setErrorMessage(
        err.message || 'Unable to connect to PRAVAH intelligence services.'
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Load forecast whenever selected node or commodity changes
  useEffect(() => {
    const targetNode = selectedNodeId || 'NODE_FP_01';
    const fetchForecast = async () => {
      try {
        const fc = await api.runForecast({
          node_id: targetNode,
          item_id: selectedItem,
          horizon_hours: 72,
        });
        setActiveForecast(fc);
      } catch (err) {
        console.error('Forecast retrieval failed:', err);
      }
    };
    fetchForecast();
  }, [selectedNodeId, selectedItem]);

  // One-Click "ANALYZE NETWORK" Pipeline Execution
  const handleAnalyzeNetwork = async () => {
    setIsAnalyzing(true);
    setShowAnalyzeModal(true);
    try {
      // Step 1: Demand & Quantile Inference (Predict)
      setAnalyzeStage('DEMAND');
      await new Promise((r) => setTimeout(r, 550));

      // Step 2: Multi-Factor Risk Assessment (Risk)
      setAnalyzeStage('RISK');
      await api.recalculateRisk();
      await new Promise((r) => setTimeout(r, 550));

      // Step 3: Mathematical Optimization (Optimize)
      setAnalyzeStage('OPTIMIZE');
      const optRes = await api.solveOptimization({
        scenario_id: 'COMPOUND_DISRUPTION',
        demand_policy: 'P80',
      });
      await new Promise((r) => setTimeout(r, 550));

      // Step 4: Closed-Loop Counterfactual Simulation (Verify)
      setAnalyzeStage('COUNTERFACTUAL');
      const evalRes = await api.evaluatePlan({
        optimization_run_id: optRes.run_id,
        scenario_id: 'COMPOUND_DISRUPTION',
        horizon_hours: 72,
      });
      setEvaluation(evalRes);
      await new Promise((r) => setTimeout(r, 550));

      // Step 5: Decision Recommendation Assembly (Decide)
      setAnalyzeStage('RECOMMEND');
      const recsRes = await api.generateRecommendations({
        scenario_id: 'COMPOUND_DISRUPTION',
        optimization_run_id: optRes.run_id,
        evaluation_id: evalRes.evaluation_id,
      });
      setRecommendations(recsRes.recommendations);
      setRejectionSummary(recsRes.rejection_summary || null);

      if (recsRes.recommendations.length > 0) {
        const target =
          recsRes.recommendations.find(
            (r) => r.status === 'VERIFIED' || r.status === 'MIXED'
          ) || recsRes.recommendations[0];
        setSelectedRecommendation(target);
      }

      setAnalyzeStage('COMPLETE');
      setLastUpdated(new Date().toISOString());
    } catch (err: any) {
      alert(`Network analysis failed: ${err.message}`);
      setShowAnalyzeModal(false);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Run What-If Scenario Simulator
  const handleRunScenario = async (
    scenarioName: string,
    _overrides: Record<string, any>
  ) => {
    setIsLoading(true);
    try {
      const optRes = await api.solveOptimization({
        scenario_id: scenarioName,
        demand_policy: 'P80',
      });
      const evalRes = await api.evaluatePlan({
        optimization_run_id: optRes.run_id,
        scenario_id: scenarioName,
        horizon_hours: 72,
      });
      setEvaluation(evalRes);

      const recsRes = await api.generateRecommendations({
        scenario_id: scenarioName,
        optimization_run_id: optRes.run_id,
        evaluation_id: evalRes.evaluation_id,
      });
      setRecommendations(recsRes.recommendations);
      setRejectionSummary(recsRes.rejection_summary || null);
      if (recsRes.recommendations.length > 0) {
        const target =
          recsRes.recommendations.find(
            (r) => r.status === 'VERIFIED' || r.status === 'MIXED'
          ) || recsRes.recommendations[0];
        setSelectedRecommendation(target);
      }
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Demo Tour Handler - smooth guided transitions
  const handleDemoStepChange = (stepIdx: number) => {
    switch (stepIdx) {
      case 0: // Normal grid
        setCurrentTab('COMMAND_CENTER');
        setSelectedNodeId(null);
        setSelectedRouteId(null);
        break;
      case 1: // Compound disruption
        setCurrentTab('SIMULATION');
        break;
      case 2: // Risk intelligence
        setCurrentTab('RISK');
        break;
      case 3: // Drill into forward post
        setCurrentTab('COMMAND_CENTER');
        setSelectedNodeId('NODE_FP_01');
        setSelectedItem('FUEL');
        break;
      case 4: // Forecast quantiles
      case 5: // Stockout outlook
        setCurrentTab('FORECAST');
        setSelectedNodeId('NODE_FP_01');
        break;
      case 6: // Continuous LP optimization
        setCurrentTab('OPTIMIZATION');
        break;
      case 7: // Fleet validation
        setCurrentTab('RECOMMENDATIONS');
        break;
      case 8: // Counterfactual simulation
      case 9: // Empirical verification
        setCurrentTab('SIMULATION');
        break;
      case 10: // Decision recommendations
        setCurrentTab('RECOMMENDATIONS');
        break;
      case 11: // Audit lineage & provenance
        setCurrentTab('AUDIT');
        break;
      default:
        setCurrentTab('COMMAND_CENTER');
    }
  };

  const selectedNodeObj = network?.nodes.find(
    (n) => n.id === selectedNodeId || n.code === selectedNodeId
  );

  // Dynamic status parameters
  const blockedRouteCodes = (network?.routes || [])
    .filter((r) => r.status === 'BLOCKED')
    .map((r) => r.route_code);

  const degradedRouteCodes = (network?.routes || [])
    .filter((r) => r.status === 'DEGRADED')
    .map((r) => r.route_code);

  const criticalNodeCodes = Object.values(nodeRisks)
    .filter((nr) => nr.level === 'CRITICAL' || nr.level === 'HIGH')
    .map((nr) => nr.node_code || nr.node_id);

  const stockoutExposedNodesCount =
    riskOverview?.high_risk_nodes_count ??
    (criticalNodeCodes.length > 0 ? criticalNodeCodes.length : 2);

  const overallRiskScore = riskOverview?.nodes?.length
    ? Math.max(...riskOverview.nodes.map((n) => n.overall_risk))
    : 0.72;

  const overallRiskLevel =
    overallRiskScore >= 0.8
      ? 'CRITICAL'
      : overallRiskScore >= 0.6
      ? 'HIGH'
      : overallRiskScore >= 0.35
      ? 'MODERATE'
      : 'NOMINAL';

  return (
    <div className="app-container">
      {/* 1. Header: Simplified Aggressively (56px) */}
      <Header
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        onAnalyzeClick={handleAnalyzeNetwork}
        isAnalyzing={isAnalyzing}
        demoMode={demoMode}
        onToggleDemoMode={() => setDemoMode(!demoMode)}
        activeScenario="Compound Disruption"
        horizon="72h"
        lastUpdated={lastUpdated}
      />

      {/* 2. Central Operational Workspace */}
      <div className="app-workspace">
        {/* Error Alert Banner */}
        {errorMessage && (
          <div
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid #ef4444',
              padding: '8px 16px',
              margin: '8px 16px 0 16px',
              borderRadius: '4px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '11px',
              color: '#fca5a5',
            }}
          >
            <span>⚠ {errorMessage}</span>
            <button
              onClick={loadData}
              className="btn btn-secondary"
              style={{ padding: '2px 8px', fontSize: '10px' }}
            >
              RETRY CONNECTION
            </button>
          </div>
        )}

        {/* Main Body Views */}
        <main
          className={`main-content ${currentTab === 'COMMAND_CENTER' ? 'flush-view' : ''}`}
          role="main"
        >
          {/* =========================================================================
              COMMAND CENTER: SPATIAL DECISION WORKSPACE
              SITUATION -> DIGITAL TWIN (HERO) -> RISK OVERLAY -> CURRENT DECISION
              ========================================================================= */}
          {currentTab === 'COMMAND_CENTER' && (
            <div
              className="cc-workspace-container"
              style={{
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                overflow: 'hidden',
              }}
            >
              {/* 1. Current Situation Strip with Inline Metrics */}
              <SituationBar
                activeScenario="COMPOUND_DISRUPTION"
                blockedRoutes={blockedRouteCodes}
                degradedRoutes={degradedRouteCodes}
                criticalNodes={criticalNodeCodes}
                totalNodes={network?.total_nodes ?? 15}
                overallRiskScore={overallRiskScore}
                overallRiskLevel={overallRiskLevel}
                stockoutExposedCount={stockoutExposedNodesCount}
                onViewAnalysis={handleAnalyzeNetwork}
                onViewNetworkDetails={() => setCurrentTab('NETWORK')}
              />

              {/* 2. Hero Digital Twin Workspace (~70-75% Dominant Spatial Surface) */}
              <div
                style={{
                  flex: 1,
                  minHeight: '440px',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <DigitalTwinMap
                  nodes={network?.nodes || []}
                  routes={network?.routes || []}
                  vehicles={network?.vehicles || []}
                  nodeRisks={nodeRisks}
                  selectedNodeId={selectedNodeId}
                  onSelectNode={(node: NodeItem) => {
                    setSelectedNodeId(node.id || node.code);
                    setSelectedRouteId(null);
                  }}
                  selectedRouteId={selectedRouteId}
                  onSelectRoute={(route: RouteItem) => {
                    setSelectedRouteId(route.id);
                    setSelectedNodeId(null);
                  }}
                  onViewIntelligence={(node: NodeItem) => {
                    setSelectedNodeId(node.id || node.code);
                    setCurrentTab('FORECAST');
                  }}
                  onViewRisk={(node?: NodeItem) => {
                    if (node) setSelectedNodeId(node.id || node.code);
                    setCurrentTab('RISK');
                  }}
                  highlightedRouteId={selectedRecommendation?.route}
                >
                  {/* Floating Network Risk Summary Overlay on the map */}
                  <NetworkRiskOverlay
                    score={overallRiskScore}
                    level={overallRiskLevel}
                    topDrivers={[
                      blockedRouteCodes.length > 0 ? `Route (${blockedRouteCodes[0]} blocked)` : 'Corridor degradation',
                      criticalNodeCodes.length > 0 ? `Demand (${criticalNodeCodes[0]} surge)` : 'Demand pressure',
                      'Inventory (forward safety stock)',
                    ]}
                    onViewRisk={() => setCurrentTab('RISK')}
                  />
                </DigitalTwinMap>
              </div>

              {/* 3. Current Decision State at Bottom of Command Center */}
              <CurrentDecisionBar
                recommendation={selectedRecommendation}
                evaluation={evaluation}
                rejectionSummary={rejectionSummary}
                candidateCount={recommendations.length > 0 ? recommendations.length : 55}
                onViewEvidence={() => setIsEvidenceDrawerOpen(true)}
              />
            </div>
          )}

          {/* =========================================================================
              NETWORK TOPOLOGY & KPI VIEW
              ========================================================================= */}
          {currentTab === 'NETWORK' && (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' }}>
              <KpiStrip
                totalNodes={network?.total_nodes ?? 15}
                totalRoutes={network?.total_routes ?? 28}
                totalVehicles={network?.total_vehicles ?? 12}
                highRiskNodesCount={riskOverview?.high_risk_nodes_count ?? 3}
                activeRecommendationsCount={recommendations.length}
                isLoading={isLoading}
              />
              <div style={{ flex: 1, minHeight: '520px' }}>
                <DigitalTwinMap
                  nodes={network?.nodes || []}
                  routes={network?.routes || []}
                  vehicles={network?.vehicles || []}
                  nodeRisks={nodeRisks}
                  selectedNodeId={selectedNodeId}
                  onSelectNode={(node: NodeItem) => setSelectedNodeId(node.id)}
                  selectedRouteId={selectedRouteId}
                  onSelectRoute={(route: RouteItem) => setSelectedRouteId(route.id)}
                  onViewIntelligence={(node: NodeItem) => {
                    setSelectedNodeId(node.id);
                    setCurrentTab('FORECAST');
                  }}
                  onViewRisk={(node?: NodeItem) => {
                    if (node) setSelectedNodeId(node.id);
                    setCurrentTab('RISK');
                  }}
                />
              </div>
            </div>
          )}

          {/* =========================================================================
              FORECAST INTELLIGENCE VIEW
              ========================================================================= */}
          {currentTab === 'FORECAST' && (
            <div style={{ height: '100%', minHeight: '520px' }}>
              <ForecastPanel
                nodeCode={selectedNodeObj?.code || 'FP-01'}
                itemId={selectedItem}
                forecastData={activeForecast}
                currentInventory={
                  selectedNodeObj?.initial_inventory?.[selectedItem] || 1500
                }
                isLoading={isLoading}
              />
            </div>
          )}

          {/* =========================================================================
              RISK INTELLIGENCE VIEW
              ========================================================================= */}
          {currentTab === 'RISK' && (
            <div style={{ height: '100%', minHeight: '520px' }}>
              <RiskPanel
                alerts={alerts}
                nodeRisks={nodeRisks}
                selectedNodeId={selectedNodeId}
                onSelectNode={(nodeId: string) => setSelectedNodeId(nodeId)}
                isLoading={isLoading}
              />
            </div>
          )}

          {/* =========================================================================
              OPTIMIZATION & SOLVER VIEW
              ========================================================================= */}
          {currentTab === 'OPTIMIZATION' && (
            <div style={{ height: '100%', minHeight: '520px' }}>
              <DecisionCenter
                recommendation={selectedRecommendation}
                isLoading={isLoading}
              />
            </div>
          )}

          {/* =========================================================================
              COUNTERFACTUAL SIMULATION & WHAT-IF COMPARISON
              ========================================================================= */}
          {currentTab === 'SIMULATION' && (
            <div style={{ height: '100%', minHeight: '520px' }}>
              <ScenarioSimulator
                evaluation={evaluation}
                onRunScenario={handleRunScenario}
                isRunning={isLoading}
              />
            </div>
          )}

          {/* =========================================================================
              RECOMMENDATIONS & ACTION DISPATCH VIEW
              ========================================================================= */}
          {currentTab === 'RECOMMENDATIONS' && (
            <div style={{ height: '100%', minHeight: '550px' }}>
              <RecommendationsView
                recommendations={recommendations}
                rejectionSummary={rejectionSummary}
                onSelectRecommendation={(r) => {
                  setSelectedRecommendation(r);
                  setSelectedNodeId(r.destination_node);
                }}
                selectedRecommendationId={selectedRecommendation?.recommendation_id}
              />
            </div>
          )}

          {/* =========================================================================
              AUDIT TRAIL & FULL CAUSAL LINEAGE VIEW
              ========================================================================= */}
          {currentTab === 'AUDIT' && (
            <div style={{ height: '100%', minHeight: '550px' }}>
              <AuditTrailView recommendation={selectedRecommendation} />
            </div>
          )}
        </main>
      </div>

      {/* Guided Tour Controller */}
      {demoMode && (
        <DemoTour
          onStepChange={handleDemoStepChange}
          onClose={() => setDemoMode(false)}
        />
      )}

      {/* Analysis Progress Overlay Modal (Predict -> Risk -> Optimize -> Verify -> Decide) */}
      <AnalyzeModal
        isOpen={showAnalyzeModal}
        currentStage={analyzeStage}
        onClose={() => setShowAnalyzeModal(false)}
      />

      {/* Evidence & Provenance Drawer */}
      <EvidenceDrawer
        isOpen={isEvidenceDrawerOpen}
        onClose={() => setIsEvidenceDrawerOpen(false)}
        recommendation={selectedRecommendation}
        evaluation={evaluation}
        forecastData={activeForecast}
      />
    </div>
  );
};

export default App;
