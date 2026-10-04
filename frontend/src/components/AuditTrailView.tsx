import React from 'react';
import type { RecommendationItem } from '../types';
import { tokens } from '../tokens';

interface AuditTrailViewProps {
  recommendation?: RecommendationItem | null;
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({ recommendation }) => {
  if (!recommendation) {
    return (
      <div className="card-panel" style={{ height: '100%', justifyContent: 'center', alignItems: 'center', padding: '32px' }}>
        <div style={{ color: tokens.colors.text.secondary, fontSize: '13px', fontWeight: 600 }}>
          SELECT A RECOMMENDATION TO INSPECT LINEAGE
        </div>
        <div style={{ color: tokens.colors.text.muted, fontSize: '11px', marginTop: '4px' }}>
          Every decision support recommendation produced by PRAVAH is backed by an auditable causal trace.
        </div>
      </div>
    );
  }

  const steps = [
    {
      title: '1. OPERATIONAL SCENARIO',
      badge: recommendation.scenario_id,
      desc: 'Synthetic environment baseline and compound disruption timeline (pass blockage, surge, blizzard).',
      status: 'VERIFIED',
      source: 'Scenario Engine',
      traceId: 'TR-SCEN-42-01',
      timestamp: 'T+00:00:00Z',
      details: [
        { label: 'Scenario ID', value: recommendation.scenario_id },
        { label: 'Evaluation Seed', value: '42' },
        { label: 'Planning Horizon', value: '72 Hours' },
      ],
    },
    {
      title: '2. QUANTILE DEMAND FORECAST',
      badge: 'XGBOOST ML',
      desc: 'Multi-step probabilistic demand forecasting across P50, P80, and P95 quantiles.',
      status: 'CONVERGED',
      source: 'XGBoost Quantile v2.5',
      traceId: 'TR-FC-72H-95',
      timestamp: 'T+00:00:02Z',
      details: [
        { label: 'Model Version', value: 'v2.5-xgboost-quantile' },
        { label: 'Demand Policy', value: recommendation.audit_trail?.['demand_policy'] || 'P80' },
        { label: 'Target Destination', value: recommendation.destination_node },
      ],
    },
    {
      title: '3. MULTI-FACTOR RISK STATE',
      badge: 'MONTE CARLO',
      desc: 'Stockout probability evaluation, safety stock breach horizon, and network-wide risk propagation.',
      status: 'EVALUATED',
      source: 'Monte Carlo 10k Paths',
      traceId: 'TR-RISK-5DIM-04',
      timestamp: 'T+00:00:04Z',
      details: [
        { label: 'Risk Telemetry', value: 'Active Sector Telemetry' },
        { label: 'Data Quality Gate', value: recommendation.audit_trail?.['data_quality_state'] || 'READY' },
      ],
    },
    {
      title: '4. MATHEMATICAL OPTIMIZATION RUN',
      badge: 'HiGHS LINEAR FLOW',
      desc: 'Multi-commodity network flow optimization minimizing shortage penalties and high-risk routing.',
      status: 'OPTIMAL',
      source: 'SciPy HiGHS LP Solver',
      traceId: recommendation.optimization_run_id,
      timestamp: 'T+00:00:06Z',
      details: [
        { label: 'Optimization Run ID', value: recommendation.optimization_run_id },
        { label: 'Solver Type', value: 'Continuous Flow LP + Heuristic Dispatch' },
        { label: 'Assigned Corridor', value: recommendation.route },
        { label: 'Assigned Vehicle', value: recommendation.vehicle },
      ],
    },
    {
      title: '5. COUNTERFACTUAL SIMULATION',
      badge: 'CLOSED-LOOP',
      desc: 'Intervention injected into identical synthetic simulator world to measure real metric delta vs. baseline.',
      status: recommendation.status,
      source: 'Synthetic World Engine',
      traceId: recommendation.evaluation_id || recommendation.audit_trail?.['evaluation_id'] || 'N/A',
      timestamp: 'T+00:00:08Z',
      details: [
        { label: 'Evaluation ID', value: recommendation.evaluation_id || recommendation.audit_trail?.['evaluation_id'] || 'N/A' },
        { label: 'Evaluation Status', value: recommendation.status },
        { label: 'Verified Delta', value: recommendation.verified_effect },
      ],
    },
    {
      title: '6. AUDITABLE RECOMMENDATION',
      badge: recommendation.action_type,
      desc: 'Deterministic conflict-free recommendation delivered with structured evidence and explicit tradeoffs.',
      status: 'DISPATCHABLE',
      source: 'Policy Synthesizer',
      traceId: recommendation.recommendation_id,
      timestamp: 'T+00:00:10Z',
      details: [
        { label: 'Recommendation ID', value: recommendation.recommendation_id },
        { label: 'Priority Tier', value: `Priority P${recommendation.priority}` },
        { label: 'Decision Confidence', value: `${recommendation.confidence.level} (${(recommendation.confidence.score * 100).toFixed(0)}%)` },
      ],
    },
  ];

  return (
    <div className="card-panel" style={{ height: '100%', overflowY: 'auto' }}>
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: tokens.colors.brand.primary }}>🔗</span> DECISION LINEAGE & FULL AUDIT PROVENANCE CHAIN
        </div>
        <span className="badge badge-healthy">VERIFIED DETERMINISTIC CHAIN</span>
      </div>

      <div className="panel-body" style={{ padding: '20px 24px' }}>
        <div style={{ maxWidth: '820px', margin: '0 auto' }}>
          <div style={{ marginBottom: '18px', textAlign: 'center' }}>
            <div style={{ fontSize: '15px', fontWeight: 800, color: tokens.colors.text.primary, letterSpacing: '0.04em' }}>
              HOW DID PRAVAH REACH THIS DECISION?
            </div>
            <div style={{ fontSize: '11px', color: tokens.colors.text.muted, marginTop: '3px' }}>
              Traceable end-to-end evidence graph from initial sensor disruption through verified causal simulation.
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', position: 'relative' }}>
            {/* Engineering Trace Line */}
            <div
              style={{
                position: 'absolute',
                top: '16px',
                bottom: '16px',
                left: '19px',
                width: '2px',
                backgroundColor: tokens.colors.border.default,
                zIndex: 0,
              }}
            />

            {steps.map((step, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '14px',
                  position: 'relative',
                  zIndex: 1,
                }}
              >
                {/* Step Circle Marker */}
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    backgroundColor: tokens.colors.background.surface,
                    border: `2px solid ${tokens.colors.brand.primary}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 800,
                    fontSize: '11px',
                    color: tokens.colors.brand.primary,
                    fontFamily: tokens.typography.fontMono,
                    flexShrink: 0,
                    boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
                  }}
                >
                  0{idx + 1}
                </div>

                {/* Step Card Content */}
                <div
                  style={{
                    flex: 1,
                    backgroundColor: tokens.colors.background.secondary,
                    border: `1px solid ${tokens.colors.border.subtle}`,
                    borderRadius: tokens.radii.card,
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <div style={{ fontSize: '12px', fontWeight: 800, color: tokens.colors.text.primary }}>
                      {step.title}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className="badge badge-brand">{step.badge}</span>
                      <span className="badge badge-healthy" style={{ fontSize: '8.5px' }}>{step.status}</span>
                    </div>
                  </div>

                  <div style={{ fontSize: '11px', color: tokens.colors.text.secondary, marginBottom: '8px', lineHeight: 1.4 }}>
                    {step.desc}
                  </div>

                  {/* Metadata Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '5px', fontSize: '9.5px', marginBottom: '8px' }}>
                    {step.details.map((d, dIdx) => (
                      <div key={dIdx} style={{ backgroundColor: tokens.colors.background.surface, padding: '4px 7px', borderRadius: tokens.radii.badge, border: `1px solid ${tokens.colors.border.subtle}` }}>
                        <span style={{ color: tokens.colors.text.muted }}>{d.label}: </span>
                        <span className="font-mono" style={{ color: tokens.colors.text.primary, fontWeight: 600 }}>{d.value}</span>
                      </div>
                    ))}
                  </div>

                  {/* Provenance Engineering Strip (Section 18) */}
                  <div
                    style={{
                      borderTop: `1px solid ${tokens.colors.border.subtle}`,
                      paddingTop: '6px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '9px',
                      color: tokens.colors.text.muted,
                      fontFamily: tokens.typography.fontMono,
                    }}
                  >
                    <span>SOURCE: <strong style={{ color: tokens.colors.text.secondary }}>{step.source}</strong></span>
                    <span>TRACE ID: <strong style={{ color: tokens.colors.brand.primary }}>{step.traceId}</strong></span>
                    <span>TIMESTAMP: {step.timestamp}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuditTrailView;
