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
import { StatusBar } from './components/StatusBar';
import { KpiStrip } from './components/KpiStrip';
import { DigitalTwinMap } from './components/DigitalTwinMap';
import { RiskPanel } from './components/RiskPanel';
import { ForecastPanel } from './components/ForecastPanel';
import { DecisionCenter } from './components/DecisionCenter';
import { VerificationPanel } from './components/VerificationPanel';
import { ScenarioSimulator } from './components/ScenarioSimulator';
import { RecommendationsView } from './components/RecommendationsView';
import { AuditTrailView } from './components/AuditTrailView';
import { DemoTour } from './components/DemoTour';
import { AnalyzeModal } from './components/AnalyzeModal';
import type { PipelineStage } from './components/AnalyzeModal';

export const App: React.FC = () => {
  // Navigation
  const [currentTab, setCurrentTab] = useState<NavTab>('COMMAND_CENTER');

  // Core Data States
  const [network, setNetwork] = useState<NetworkResponse | null>(null);
  const [riskOverview, setRiskOverview] = useState<RiskOverviewResponse | null>(null);
  const [nodeRisks, setNodeRisks] = useState<Record<string, NodeRiskDetail>>({});
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [selectedRecommendation, setSelectedRecommendation] = useState<RecommendationItem | null>(null);
  const [evaluation, setEvaluation] = useState<CounterfactualEvaluationResponse | null>(null);
  const [activeForecast, setActiveForecast] = useState<ForecastItemResponse | null>(null);

  // Selection States
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

      if (recsRes.recommendations.length > 0) {
        // Pick primary critical recommendation
        const target =
          recsRes.recommendations.find(
            (r) => r.status === 'VERIFIED' || r.status === 'MIXED'
          ) || recsRes.recommendations[0];
        setSelectedRecommendation(target);
        setSelectedNodeId(target.destination_node);

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
    if (!selectedNodeId) return;
    const fetchForecast = async () => {
      try {
        const fc = await api.runForecast({
          node_id: selectedNodeId,
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
      // Step 1: Demand & Quantile Inference
      setAnalyzeStage('DEMAND');
      await new Promise((r) => setTimeout(r, 600));

      // Step 2: Multi-Factor Risk Assessment
      setAnalyzeStage('RISK');
      await api.recalculateRisk();
      await new Promise((r) => setTimeout(r, 600));

      // Step 3: Mathematical Optimization
      setAnalyzeStage('OPTIMIZE');
      const optRes = await api.solveOptimization({
        scenario_id: 'COMPOUND_DISRUPTION',
        demand_policy: 'P80',
      });
      await new Promise((r) => setTimeout(r, 600));

      // Step 4: Closed-Loop Counterfactual Simulation
      setAnalyzeStage('COUNTERFACTUAL');
      const evalRes = await api.evaluatePlan({
        optimization_run_id: optRes.run_id,
        scenario_id: 'COMPOUND_DISRUPTION',
        horizon_hours: 72,
      });
      setEvaluation(evalRes);
      await new Promise((r) => setTimeout(r, 600));

      // Step 5: Decision Recommendation Assembly
      setAnalyzeStage('RECOMMEND');
      const recsRes = await api.generateRecommendations({
        scenario_id: 'COMPOUND_DISRUPTION',
        optimization_run_id: optRes.run_id,
        evaluation_id: evalRes.evaluation_id,
      });
      setRecommendations(recsRes.recommendations);

      if (recsRes.recommendations.length > 0) {
        setSelectedRecommendation(recsRes.recommendations[0]);
        setSelectedNodeId(recsRes.recommendations[0].destination_node);
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
      if (recsRes.recommendations.length > 0) {
        setSelectedRecommendation(recsRes.recommendations[0]);
      }
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Demo Tour Handler
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
      case 2: // Risk escalation
        setCurrentTab('COMMAND_CENTER');
        break;
      case 3: // Select forward outpost FP-01
        setCurrentTab('COMMAND_CENTER');
        setSelectedNodeId('NODE_FP_01');
        setSelectedItem('FUEL');
        break;
      case 4: // Forecast
      case 5: // Stockout Outlook
        setCurrentTab('FORECAST');
        setSelectedNodeId('NODE_FP_01');
        break;
      case 6: // Optimize
        setCurrentTab('OPTIMIZATION');
        break;
      case 7: // Inspect Alternate Route
        setCurrentTab('NETWORK');
        setSelectedRouteId('ROUTE_R_11');
        break;
      case 8: // Counterfactual
      case 9: // Deltas
        setCurrentTab('SIMULATION');
        break;
      case 10: // Recommendation
        setCurrentTab('RECOMMENDATIONS');
        break;
      case 11: // Explanation & Lineage
        setCurrentTab('AUDIT');
        break;
      default:
        setCurrentTab('COMMAND_CENTER');
    }
  };

  const selectedNodeObj = network?.nodes.find(
    (n) => n.id === selectedNodeId || n.code === selectedNodeId
  );

  return (
    <div className="app-container">
      {/* 1. Header with Navigation & Live Indicators */}
      <Header
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        onAnalyzeClick={handleAnalyzeNetwork}
        isAnalyzing={isAnalyzing}
        demoMode={demoMode}
        onToggleDemoMode={() => setDemoMode(!demoMode)}
      />

      {/* 2. Global Status Bar */}
      <StatusBar
        systemStatus="READY"
        dataQuality="READY"
        forecastHorizonDays={14}
        activeScenario="COMPOUND_DISRUPTION"
        lastUpdated={lastUpdated}
      />

      {/* 3. High-Value KPI Strip */}
      <KpiStrip
        totalNodes={network?.total_nodes ?? 15}
        totalRoutes={network?.total_routes ?? 28}
        totalVehicles={network?.total_vehicles ?? 12}
        highRiskNodesCount={riskOverview?.high_risk_nodes_count ?? 3}
        activeRecommendationsCount={recommendations.length}
        isLoading={isLoading}
      />

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

      {/* 4. Main Body Views */}
      <main className="main-content" role="main">
        {currentTab === 'COMMAND_CENTER' && (
          <>
            {/* Top Zone: Digital Twin (dominant) & Critical Risks */}
            <div className="cc-grid-middle">
              <DigitalTwinMap
                nodes={network?.nodes || []}
                routes={network?.routes || []}
                vehicles={network?.vehicles || []}
                nodeRisks={nodeRisks}
                selectedNodeId={selectedNodeId}
                onSelectNode={(node: NodeItem) => {
                  setSelectedNodeId(node.id);
                  setSelectedRouteId(null);
                }}
                selectedRouteId={selectedRouteId}
                onSelectRoute={(route: RouteItem) => {
                  setSelectedRouteId(route.id);
                  setSelectedNodeId(null);
                }}
                onViewIntelligence={(node: NodeItem) => {
                  setSelectedNodeId(node.id);
                  setCurrentTab('FORECAST');
                }}
                highlightedRouteId={selectedRecommendation?.route}
              />

              <RiskPanel
                alerts={alerts}
                nodeRisks={nodeRisks}
                selectedNodeId={selectedNodeId}
                onSelectNode={(nodeId: string) => setSelectedNodeId(nodeId)}
                isLoading={isLoading}
              />
            </div>

            {/* Middle Zone: Prediction & Inventory Outlook */}
            <div style={{ minHeight: '260px' }}>
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

            {/* Bottom Zone: Decision Center & Counterfactual Verification */}
            <div className="cc-grid-bottom">
              <DecisionCenter
                recommendation={selectedRecommendation}
                onEvidenceClick={(ev) => {
                  if (ev.type.includes('ROUTE')) setCurrentTab('NETWORK');
                  if (ev.type.includes('STOCKOUT') || ev.type.includes('TIME_TO_ZERO'))
                    setCurrentTab('FORECAST');
                }}
                isLoading={isLoading}
              />

              <VerificationPanel
                recommendation={selectedRecommendation}
                evaluation={evaluation}
                isLoading={isLoading}
              />
            </div>
          </>
        )}

        {currentTab === 'NETWORK' && (
          <div style={{ height: '100%', minHeight: '600px' }}>
            <DigitalTwinMap
              nodes={network?.nodes || []}
              routes={network?.routes || []}
              vehicles={network?.vehicles || []}
              nodeRisks={nodeRisks}
              selectedNodeId={selectedNodeId}
              onSelectNode={(node: NodeItem) => setSelectedNodeId(node.id)}
              selectedRouteId={selectedRouteId}
              onSelectRoute={(route: RouteItem) => setSelectedRouteId(route.id)}
            />
          </div>
        )}

        {currentTab === 'FORECAST' && (
          <div style={{ height: '100%', minHeight: '500px' }}>
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

        {currentTab === 'RISK' && (
          <div style={{ height: '100%', minHeight: '500px' }}>
            <RiskPanel
              alerts={alerts}
              nodeRisks={nodeRisks}
              selectedNodeId={selectedNodeId}
              onSelectNode={(nodeId: string) => setSelectedNodeId(nodeId)}
              isLoading={isLoading}
            />
          </div>
        )}

        {currentTab === 'OPTIMIZATION' && (
          <div style={{ height: '100%', minHeight: '500px' }}>
            <DecisionCenter
              recommendation={selectedRecommendation}
              isLoading={isLoading}
            />
          </div>
        )}

        {currentTab === 'SIMULATION' && (
          <div style={{ height: '100%', minHeight: '500px' }}>
            <ScenarioSimulator
              evaluation={evaluation}
              onRunScenario={handleRunScenario}
              isRunning={isLoading}
            />
          </div>
        )}

        {currentTab === 'RECOMMENDATIONS' && (
          <div style={{ height: '100%', minHeight: '550px' }}>
            <RecommendationsView
              recommendations={recommendations}
              onSelectRecommendation={(r) => {
                setSelectedRecommendation(r);
                setSelectedNodeId(r.destination_node);
              }}
              selectedRecommendationId={selectedRecommendation?.recommendation_id}
            />
          </div>
        )}

        {currentTab === 'AUDIT' && (
          <div style={{ height: '100%', minHeight: '550px' }}>
            <AuditTrailView recommendation={selectedRecommendation} />
          </div>
        )}
      </main>

      {/* Demo Tour Controller */}
      {demoMode && (
        <DemoTour
          onStepChange={handleDemoStepChange}
          onClose={() => setDemoMode(false)}
        />
      )}

      {/* One-Click Analysis Modal */}
      <AnalyzeModal
        isOpen={showAnalyzeModal}
        currentStage={analyzeStage}
        onClose={() => setShowAnalyzeModal(false)}
      />
    </div>
  );
};

export default App;
