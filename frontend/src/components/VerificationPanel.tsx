import React from 'react';
import type { RecommendationItem, CounterfactualEvaluationResponse } from '../types';
import { tokens } from '../tokens';

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
  const baseline = evaluation?.baseline;
  const optimized = evaluation?.optimized;

  const getTradeoffBadge = (_key: string, value: string) => {
    const valUpper = (value || '').toUpperCase();
    if (valUpper.includes('IMPROVED') || valUpper.includes('MITIGATED') || valUpper.includes('REDUCED')) {
      return { cls: 'badge-healthy', icon: '↑' };
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
        return 'The proposed intervention was evaluated against the disrupted operating state. Expected benefit could not be verified. Recommendation suppressed as a safety decision.';
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
          <span style={{ color: tokens.colors.brand.primary, fontSize: '13px' }}>⚖</span>
          <span>COUNTERFACTUAL VERIFICATION & TRADEOFF ANALYSIS</span>
        </div>
        <span
          className={`badge ${
            status === 'VERIFIED'
              ? 'badge-healthy'
              : status === 'MIXED'
              ? 'badge-warning'
              : status === 'DEGRADED'
              ? 'badge-warning'
              : status === 'REJECTED'
              ? 'badge-critical'
              : 'badge-neutral'
          }`}
        >
          {status}
        </span>
      </div>

      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Side-by-Side Baseline vs Intervention (Section 17) */}
        {baseline && optimized && (
          <div
            style={{
              backgroundColor: tokens.colors.background.secondary,
              border: `1px solid ${tokens.colors.border.subtle}`,
              borderRadius: tokens.radii.card,
              padding: '10px',
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '10.5px' }}>
              {/* Baseline */}
              <div style={{ backgroundColor: tokens.colors.background.surface, padding: '8px 10px', borderRadius: tokens.radii.badge, border: `1px solid ${tokens.colors.border.subtle}` }}>
                <div style={{ fontSize: '9.5px', color: tokens.colors.text.muted, fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                  BASELINE (NO INTERVENTION)
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span style={{ color: tokens.colors.text.secondary }}>Fulfillment:</span>
                  <span className="font-mono" style={{ color: tokens.colors.text.primary, fontWeight: 700 }}>
                    {baseline.fulfillment_rate_percent.toFixed(1)}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span style={{ color: tokens.colors.text.secondary }}>Unmet Demand:</span>
                  <span className="font-mono" style={{ color: tokens.colors.status.critical }}>
                    {baseline.total_unmet_demand.toFixed(1)} u
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span style={{ color: tokens.colors.text.secondary }}>Distance:</span>
                  <span className="font-mono">{baseline.total_transport_distance_km.toFixed(0)} km</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: tokens.colors.text.secondary }}>Avg Delay:</span>
                  <span className="font-mono">{baseline.average_delay_hours.toFixed(1)}h</span>
                </div>
              </div>

              {/* Intervention */}
              <div style={{ backgroundColor: tokens.colors.background.surface, padding: '8px 10px', borderRadius: tokens.radii.badge, border: `1px solid ${tokens.colors.brand.primaryBorder}` }}>
                <div style={{ fontSize: '9.5px', color: tokens.colors.brand.primary, fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                  INTERVENTION (OPTIMIZED DISPATCH)
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span style={{ color: tokens.colors.text.secondary }}>Fulfillment:</span>
                  <span className="font-mono" style={{ color: tokens.colors.status.healthy, fontWeight: 700 }}>
                    {optimized.fulfillment_rate_percent.toFixed(1)}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span style={{ color: tokens.colors.text.secondary }}>Unmet Demand:</span>
                  <span className="font-mono" style={{ color: tokens.colors.status.healthy }}>
                    {optimized.total_unmet_demand.toFixed(1)} u
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span style={{ color: tokens.colors.text.secondary }}>Distance:</span>
                  <span className="font-mono" style={{ color: tokens.colors.status.warning }}>{optimized.total_transport_distance_km.toFixed(0)} km</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: tokens.colors.text.secondary }}>Avg Delay:</span>
                  <span className="font-mono" style={{ color: tokens.colors.status.warning }}>{optimized.average_delay_hours.toFixed(1)}h</span>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '8px', padding: '6px 8px', backgroundColor: tokens.colors.background.elevated, borderRadius: tokens.radii.badge, fontSize: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: tokens.colors.text.muted, fontWeight: 600 }}>VERDICT:</span>
              <span style={{ color: status === 'VERIFIED' ? tokens.colors.status.healthy : tokens.colors.status.warning, fontWeight: 700, fontFamily: tokens.typography.fontMono }}>
                {status === 'MIXED' ? 'MIXED — Service improved, but transport distance increased.' : status}
              </span>
            </div>
          </div>
        )}

        {/* Expected vs. Verified Comparison Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          {/* Expected Effect */}
          <div
            style={{
              backgroundColor: tokens.colors.background.secondary,
              border: `1px solid ${tokens.colors.border.subtle}`,
              borderRadius: tokens.radii.badge,
              padding: '10px 12px',
            }}
          >
            <div
              style={{
                fontSize: '9.5px',
                fontWeight: 700,
                color: tokens.colors.brand.primary,
                textTransform: 'uppercase',
                marginBottom: '4px',
                letterSpacing: '0.04em',
              }}
            >
              EXPECTED EFFECT (OPTIMIZER)
            </div>
            <div style={{ fontSize: '10.5px', color: tokens.colors.text.secondary, lineHeight: 1.5 }}>
              {recommendation?.expected_effect || 'Expected to reduce forward stockout risk.'}
            </div>
            <div style={{ fontSize: '9px', color: tokens.colors.text.muted, marginTop: '6px', fontFamily: tokens.typography.fontMono }}>
              Source: Multi-Commodity Linear Flow LP
            </div>
          </div>

          {/* Verified Effect */}
          <div
            style={{
              backgroundColor: tokens.colors.background.secondary,
              border: `1px solid ${tokens.colors.border.subtle}`,
              borderRadius: tokens.radii.badge,
              padding: '10px 12px',
            }}
          >
            <div
              style={{
                fontSize: '9.5px',
                fontWeight: 700,
                color: status === 'VERIFIED' || status === 'MIXED' ? tokens.colors.status.healthy : tokens.colors.status.warning,
                textTransform: 'uppercase',
                marginBottom: '4px',
                letterSpacing: '0.04em',
              }}
            >
              VERIFIED EFFECT (SIMULATOR)
            </div>
            <div style={{ fontSize: '10.5px', color: tokens.colors.text.secondary, lineHeight: 1.5 }}>
              {recommendation?.verified_effect || 'Counterfactual evaluation not run yet.'}
            </div>
            <div style={{ fontSize: '9px', color: tokens.colors.text.muted, marginTop: '6px', fontFamily: tokens.typography.fontMono }}>
              Source: Closed-Loop Synthetic Simulation
            </div>
          </div>
        </div>

        {/* Operational Tradeoff Matrix */}
        <div>
          <div
            style={{
              fontSize: '10px',
              fontWeight: 700,
              color: tokens.colors.text.secondary,
              textTransform: 'uppercase',
              marginBottom: '4px',
              letterSpacing: '0.04em',
            }}
          >
            OPERATIONAL TRADEOFF MATRIX
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
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
                    backgroundColor: tokens.colors.background.secondary,
                    border: `1px solid ${tokens.colors.border.subtle}`,
                    borderRadius: tokens.radii.badge,
                    padding: '7px 10px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontSize: '9.5px', color: tokens.colors.text.secondary }}>
                    {t.label}
                  </span>
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
            backgroundColor: tokens.colors.background.secondary,
            borderLeft: `3px solid ${
              status === 'VERIFIED'
                ? tokens.colors.status.healthy
                : status === 'MIXED' || status === 'DEGRADED'
                ? tokens.colors.status.warning
                : tokens.colors.status.critical
            }`,
            borderRadius: '0 4px 4px 0',
            padding: '8px 12px',
            fontSize: '10.5px',
            color: tokens.colors.text.secondary,
            lineHeight: 1.5,
          }}
        >
          <strong style={{ color: tokens.colors.text.primary }}>{status}: </strong>
          {getStatusExplanation(status)}
        </div>
      </div>
    </div>
  );
};

export default VerificationPanel;
