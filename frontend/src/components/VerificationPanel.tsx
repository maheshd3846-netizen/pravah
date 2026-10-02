import React from 'react';
import type { RecommendationItem, CounterfactualEvaluationResponse } from '../types';

interface VerificationPanelProps {
  recommendation?: RecommendationItem | null;
  evaluation?: CounterfactualEvaluationResponse | null;
  isLoading?: boolean;
}

export const VerificationPanel: React.FC<VerificationPanelProps> = ({
  recommendation,
  evaluation,
  isLoading: _isLoading = false,
}) => {
  const tradeoffs = recommendation?.tradeoffs || evaluation?.tradeoffs || {};
  const status = recommendation?.status || evaluation?.status || 'PROPOSED';

  const getTradeoffBadge = (_key: string, value: string) => {
    const valUpper = (value || '').toUpperCase();
    if (valUpper.includes('IMPROVED') || valUpper.includes('MITIGATED') || valUpper.includes('REDUCED')) {
      return { cls: 'badge-ready', icon: '↑' };
    }
    if (valUpper.includes('INCREASED') || valUpper.includes('ELEVATED') || valUpper.includes('DEGRADED')) {
      return { cls: 'badge-warning', icon: '↑' };
    }
    return { cls: 'badge-neutral', icon: '•' };
  };

  const getStatusExplanation = (st: string) => {
    switch (st) {
      case 'VERIFIED':
        return 'Counterfactual closed-loop simulation confirms the intervention strictly improves service metrics with acceptable operational costs under identical disruption.';
      case 'MIXED':
        return 'Forward stockout is mitigated and service significantly improves, but transport distance and transit delays increased due to mountain pass detour.';
      case 'DEGRADED':
        return 'Counterfactual simulation determined that the candidate intervention worsens logistics outcomes vs baseline under active disruption. PRAVAH safely suppresses recommendations to prevent counter-productive dispatch.';
      case 'REJECTED':
        return 'Recommendation is rejected due to conflict with physical vehicle availability, corridor capacity, or simulated outcome degradation.';
      case 'PROPOSED':
        return 'Mathematical optimization plan is feasible; counterfactual closed-loop evaluation pending verification.';
      default:
        return 'Simulation results are inconclusive under current confidence parameters.';
    }
  };

  return (
    <div className="card-panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: '#06b6d4' }}>⚖</span> COUNTERFACTUAL VERIFICATION & TRADEOFF ANALYSIS
        </div>
        <span
          className={`badge ${
            status === 'VERIFIED'
              ? 'badge-verified'
              : status === 'MIXED'
              ? 'badge-mixed'
              : status === 'REJECTED' || status === 'DEGRADED'
              ? 'badge-rejected'
              : 'badge-proposed'
          }`}
        >
          {status}
        </span>
      </div>

      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Expected vs. Verified Comparison Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          {/* Expected Effect */}
          <div
            style={{
              backgroundColor: 'rgba(59, 130, 246, 0.05)',
              border: '1px solid rgba(59, 130, 246, 0.2)',
              borderRadius: '4px',
              padding: '10px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', marginBottom: '4px' }}>
              EXPECTED EFFECT (OPTIMIZER)
            </div>
            <div style={{ fontSize: '11px', color: '#cbd5e1', lineHeight: 1.5 }}>
              {recommendation?.expected_effect || 'Expected to reduce forward stockout risk.'}
            </div>
            <div style={{ fontSize: '9px', color: '#64748b', marginTop: '6px' }}>
              Source: Multi-Commodity Linear Flow LP
            </div>
          </div>

          {/* Verified Effect */}
          <div
            style={{
              backgroundColor:
                status === 'VERIFIED' || status === 'MIXED'
                  ? 'rgba(16, 185, 129, 0.05)'
                  : 'rgba(239, 68, 68, 0.05)',
              border:
                status === 'VERIFIED' || status === 'MIXED'
                  ? '1px solid rgba(16, 185, 129, 0.25)'
                  : '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: '4px',
              padding: '10px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 700, color: status === 'VERIFIED' || status === 'MIXED' ? '#10b981' : '#ef4444', textTransform: 'uppercase', marginBottom: '4px' }}>
              VERIFIED EFFECT (SIMULATOR)
            </div>
            <div style={{ fontSize: '11px', color: '#cbd5e1', lineHeight: 1.5 }}>
              {recommendation?.verified_effect || 'Counterfactual evaluation not run yet.'}
            </div>
            <div style={{ fontSize: '9px', color: '#64748b', marginTop: '6px' }}>
              Source: Closed-Loop Synthetic Simulation
            </div>
          </div>
        </div>

        {/* Tradeoffs Grid */}
        <div>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '6px' }}>
            OPERATIONAL TRADEOFF MATRIX
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
            {[
              { label: 'SERVICE OUTCOME', key: 'SERVICE', val: tradeoffs['SERVICE'] || 'IMPROVED' },
              { label: 'LOGISTICS RISK', key: 'RISK', val: tradeoffs['RISK'] || 'MITIGATED' },
              { label: 'TRANSPORT DISTANCE', key: 'TRANSPORT', val: tradeoffs['TRANSPORT_COST'] || tradeoffs['TRANSPORT_DISTANCE'] || 'INCREASED' },
              { label: 'CONVOY DELAY', key: 'DELAY', val: tradeoffs['DELAY'] || 'INCREASED' },
            ].map((t) => {
              const b = getTradeoffBadge(t.key, t.val);
              return (
                <div
                  key={t.label}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    padding: '8px 10px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontSize: '10px', color: '#94a3b8' }}>{t.label}</span>
                  <span className={`badge ${b.cls}`} style={{ fontSize: '9px' }}>
                    {b.icon} {t.val}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Verification Status Explanation Banner */}
        <div
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            borderLeft: `3px solid ${
              status === 'VERIFIED' ? '#10b981' : status === 'MIXED' ? '#f59e0b' : '#ef4444'
            }`,
            padding: '8px 12px',
            fontSize: '11px',
            color: '#94a3b8',
            lineHeight: 1.5,
          }}
        >
          <strong style={{ color: '#f8fafc' }}>{status}: </strong>
          {getStatusExplanation(status)}
        </div>
      </div>
    </div>
  );
};
