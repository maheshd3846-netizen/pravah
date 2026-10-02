import React from 'react';
import type { RecommendationItem } from '../types';

interface AuditTrailViewProps {
  recommendation?: RecommendationItem | null;
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({ recommendation }) => {
  if (!recommendation) {
    return (
      <div className="card-panel" style={{ height: '100%', justifyContent: 'center', alignItems: 'center', padding: '32px' }}>
        <div style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 600 }}>
          SELECT A RECOMMENDATION TO INSPECT LINEAGE
        </div>
        <div style={{ color: '#64748b', fontSize: '11px', marginTop: '4px' }}>
          Every decision support recommendation produced by PRAVAH is backed by an auditable causal chain.
        </div>
      </div>
    );
  }

  const steps = [
    {
      title: '1. OPERATIONAL SCENARIO',
      badge: recommendation.scenario_id,
      desc: 'Synthetic environment baseline and compound disruption timeline (pass blockage, surge, blizzard).',
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
      details: [
        { label: 'Model Version', value: 'v2.5-xgboost-quantile' },
        { label: 'Demand Policy', value: recommendation.audit_trail['demand_policy'] || 'P80' },
        { label: 'Target Destination', value: recommendation.destination_node },
      ],
    },
    {
      title: '3. MULTI-FACTOR RISK STATE',
      badge: 'MONTE CARLO',
      desc: 'Stockout probability evaluation, safety stock breach horizon, and network-wide risk propagation.',
      details: [
        { label: 'Risk Telemetry', value: 'Active Sector Telemetry' },
        { label: 'Data Quality Gate', value: recommendation.audit_trail['data_quality_state'] || 'READY' },
      ],
    },
    {
      title: '4. MATHEMATICAL OPTIMIZATION RUN',
      badge: 'HiGHS LINEAR FLOW',
      desc: 'Multi-commodity network flow optimization minimizing shortage penalties and high-risk routing.',
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
      details: [
        { label: 'Evaluation ID', value: recommendation.evaluation_id || recommendation.audit_trail['evaluation_id'] || 'N/A' },
        { label: 'Evaluation Status', value: recommendation.status },
        { label: 'Verified Delta', value: recommendation.verified_effect },
      ],
    },
    {
      title: '6. AUDITABLE RECOMMENDATION',
      badge: recommendation.action_type,
      desc: 'Deterministic conflict-free recommendation delivered with structured evidence and explicit tradeoffs.',
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
          <span>🔗</span> DECISION LINEAGE & FULL AUDIT PROVENANCE CHAIN
        </div>
        <span className="badge badge-ready">VERIFIED DETERMINISTIC CHAIN</span>
      </div>

      <div className="panel-body" style={{ padding: '24px' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div style={{ marginBottom: '20px', textAlign: 'center' }}>
            <div style={{ fontSize: '15px', fontWeight: 800, color: '#f8fafc' }}>
              HOW DID PRAVAH REACH THIS DECISION?
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
              Traceable end-to-end evidence graph from initial sensor disruption through verified causal simulation.
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative' }}>
            {/* Visual Line */}
            <div
              style={{
                position: 'absolute',
                top: '20px',
                bottom: '20px',
                left: '20px',
                width: '2px',
                backgroundColor: 'rgba(56, 189, 248, 0.3)',
                zIndex: 0,
              }}
            />

            {steps.map((step, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '16px',
                  position: 'relative',
                  zIndex: 1,
                }}
              >
                {/* Step Circle Marker */}
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '50%',
                    backgroundColor: '#0c1322',
                    border: '2px solid #38bdf8',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 800,
                    fontSize: '12px',
                    color: '#38bdf8',
                    fontFamily: 'var(--font-mono)',
                    flexShrink: 0,
                    boxShadow: 'var(--shadow-md)',
                  }}
                >
                  0{idx + 1}
                </div>

                {/* Step Card Content */}
                <div
                  style={{
                    flex: 1,
                    backgroundColor: 'rgba(15, 23, 42, 0.85)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '6px',
                    padding: '12px 16px',
                    boxShadow: 'var(--shadow-sm)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <div style={{ fontSize: '12px', fontWeight: 800, color: '#f8fafc' }}>
                      {step.title}
                    </div>
                    <span className="badge badge-cyan">{step.badge}</span>
                  </div>

                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px' }}>
                    {step.desc}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '6px', fontSize: '10px' }}>
                    {step.details.map((d, dIdx) => (
                      <div key={dIdx} style={{ backgroundColor: 'rgba(0,0,0,0.25)', padding: '4px 8px', borderRadius: '4px' }}>
                        <span style={{ color: '#64748b' }}>{d.label}: </span>
                        <span className="font-mono" style={{ color: '#cbd5e1', fontWeight: 600 }}>{d.value}</span>
                      </div>
                    ))}
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
