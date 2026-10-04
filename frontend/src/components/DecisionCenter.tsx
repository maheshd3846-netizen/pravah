import React, { useState } from 'react';
import type { RecommendationItem, DecisionEvidenceItem } from '../types';
import { tokens } from '../tokens';

interface DecisionCenterProps {
  recommendation?: RecommendationItem | null;
  onEvidenceClick?: (item: DecisionEvidenceItem) => void;
  onOpenEvidenceDrawer?: () => void;
  isLoading?: boolean;
}

export const DecisionCenter: React.FC<DecisionCenterProps> = ({
  recommendation,
  onEvidenceClick,
  onOpenEvidenceDrawer,
  isLoading = false,
}) => {
  const [selectedEvidenceType, setSelectedEvidenceType] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="card-panel" style={{ height: '100%', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ color: tokens.colors.text.muted, fontSize: '11px', fontFamily: tokens.typography.fontMono }}>
          Synthesizing decision support recommendations...
        </div>
      </div>
    );
  }

  if (!recommendation) {
    return (
      <div className="card-panel" style={{ height: '100%', padding: '24px', justifyContent: 'center', alignItems: 'center' }}>
        <div
          style={{
            backgroundColor: tokens.colors.background.secondary,
            border: `1px solid ${tokens.colors.status.warningBorder}`,
            borderRadius: tokens.radii.card,
            padding: '16px 20px',
            maxWidth: '480px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '12px', fontWeight: 800, color: tokens.colors.status.warning, textTransform: 'uppercase', marginBottom: '4px' }}>
            NO VERIFIED ACTIONS
          </div>
          <div style={{ fontSize: '11px', color: tokens.colors.text.secondary, lineHeight: 1.5, marginBottom: '8px' }}>
            Counterfactual evaluation completed. Expected benefit was not verified. Recommendation suppressed. This is a safety state.
          </div>
          <div style={{ fontSize: '10px', color: tokens.colors.text.muted }}>
            Reason: Continuous Multi-Commodity Linear Flow LP via SciPy HiGHS generated candidates, but closed-loop verification did not verify net gain under disrupted operating conditions.
          </div>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
        return 'badge-healthy';
      case 'MIXED':
        return 'badge-warning';
      case 'DEGRADED':
        return 'badge-warning';
      case 'REJECTED':
        return 'badge-critical';
      default:
        return 'badge-neutral';
    }
  };

  const recStatus = (recommendation.status as string);

  return (
    <div className="card-panel" style={{ height: '100%' }}>
      {/* Panel Header */}
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: tokens.colors.brand.primary, fontSize: '13px' }}>⚡</span>
          <span>DECISION CENTER — AUDITABLE RECOMMENDATION</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {onOpenEvidenceDrawer && (
            <button
              onClick={onOpenEvidenceDrawer}
              className="btn btn-secondary"
              style={{
                fontSize: '11px',
                padding: '3px 8px',
                color: tokens.colors.brand.primary,
                borderColor: tokens.colors.brand.primaryBorder,
              }}
            >
              LEVEL 3 EVIDENCE →
            </button>
          )}
          <span className={`badge ${getStatusBadge(recommendation.status)}`}>
            {recommendation.status}
          </span>
          <span className="badge badge-brand">
            CONFIDENCE: {recommendation.confidence.level} ({(recommendation.confidence.score * 100).toFixed(0)}%)
          </span>
        </div>
      </div>

      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Optimization & Verification Pipeline Strip */}
        <div
          style={{
            backgroundColor: tokens.colors.background.secondary,
            border: `1px solid ${tokens.colors.border.subtle}`,
            borderRadius: tokens.radii.badge,
            padding: '7px 10px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '9.5px',
            fontFamily: tokens.typography.fontMono,
            flexWrap: 'wrap',
            gap: '6px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: tokens.colors.text.muted }}>
            <span style={{ color: tokens.colors.text.primary, fontWeight: 700 }}>PIPELINE:</span>
            <span>Candidates</span>
            <span>→</span>
            <span style={{ color: tokens.colors.brand.primary }}>Physical Validation</span>
            <span>→</span>
            <span style={{ color: tokens.colors.status.warning }}>Counterfactual Evaluation</span>
            <span>→</span>
            <span style={{ color: tokens.colors.status.healthy }}>Verified / Rejected</span>
          </div>
          <div style={{ color: tokens.colors.text.secondary }}>
            Solver: <span style={{ color: tokens.colors.text.primary }}>Continuous Multi-Commodity Linear Flow LP via SciPy HiGHS</span>, followed by <span style={{ color: tokens.colors.brand.primary }}>Deterministic Heuristic Fleet Dispatch</span>
          </div>
        </div>

        {/* Degraded Safety Alert Banner if DEGRADED */}
        {recStatus === 'DEGRADED' && (
          <div
            style={{
              backgroundColor: tokens.colors.status.warningSoft,
              border: `1px solid ${tokens.colors.status.warningBorder}`,
              borderRadius: tokens.radii.card,
              padding: '10px 14px',
              fontSize: '11px',
              color: tokens.colors.text.secondary,
              lineHeight: 1.5,
            }}
          >
            <div style={{ fontWeight: 800, color: tokens.colors.status.warning, textTransform: 'uppercase', marginBottom: '2px' }}>
              ⚠ COUNTERFACTUAL RESULT: DEGRADED
            </div>
            <div>
              Counterfactual evaluation completed. Expected benefit was not verified. Recommendation suppressed. This is a safety state.
            </div>
          </div>
        )}

        {/* Rejection Safety Alert Banner if REJECTED */}
        {recStatus === 'REJECTED' && (
          <div
            style={{
              backgroundColor: tokens.colors.status.criticalSoft,
              border: `1px solid ${tokens.colors.status.criticalBorder}`,
              borderRadius: tokens.radii.card,
              padding: '10px 14px',
              fontSize: '11px',
              color: tokens.colors.text.secondary,
              lineHeight: 1.5,
            }}
          >
            <div style={{ fontWeight: 800, color: tokens.colors.status.critical, textTransform: 'uppercase', marginBottom: '2px' }}>
              ⚠ ACTION CONFLICT: REJECTED
            </div>
            <div>
              {recommendation.conflict_details && recommendation.conflict_details.length > 0
                ? recommendation.conflict_details.join('; ')
                : 'This action was suppressed from final operational dispatch due to physical constraint violations or simulated degradation.'}
            </div>
          </div>
        )}

        {/* Recommended Tactical Action Card */}
        <div
          style={{
            backgroundColor: tokens.colors.background.secondary,
            border: `1px solid ${recommendation.status === 'VERIFIED' ? tokens.colors.brand.primaryBorder : tokens.colors.border.default}`,
            borderRadius: tokens.radii.card,
            padding: '12px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <div>
              <div
                style={{
                  fontSize: '9.5px',
                  textTransform: 'uppercase',
                  color: tokens.colors.brand.primary,
                  fontWeight: 700,
                  letterSpacing: '0.06em',
                }}
              >
                RECOMMENDED ACTION
              </div>
              <div
                style={{
                  fontSize: '17px',
                  fontWeight: 800,
                  color: tokens.colors.text.primary,
                  fontFamily: tokens.typography.fontMono,
                  marginTop: '1px',
                }}
              >
                {recommendation.action_type} {recommendation.quantity.toFixed(0)} {recommendation.item}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '9.5px', color: tokens.colors.text.muted, letterSpacing: '0.04em' }}>
                DISPATCH WINDOW
              </div>
              <div className="font-mono" style={{ fontSize: '11.5px', color: tokens.colors.brand.primary, fontWeight: 600, marginTop: '1px' }}>
                T+{recommendation.planned_departure}h → ETA T+{recommendation.expected_arrival}h
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px', fontSize: '10.5px' }}>
            <div style={{ backgroundColor: tokens.colors.background.surface, padding: '5px 8px', borderRadius: tokens.radii.badge, border: `1px solid ${tokens.colors.border.subtle}` }}>
              <div style={{ color: tokens.colors.text.muted, fontSize: '8.5px' }}>SOURCE DEPOT</div>
              <div className="font-mono" style={{ fontWeight: 700, color: tokens.colors.text.primary }}>
                {recommendation.source_node}
              </div>
            </div>
            <div style={{ backgroundColor: tokens.colors.background.surface, padding: '5px 8px', borderRadius: tokens.radii.badge, border: `1px solid ${tokens.colors.border.subtle}` }}>
              <div style={{ color: tokens.colors.text.muted, fontSize: '8.5px' }}>DESTINATION</div>
              <div className="font-mono" style={{ fontWeight: 700, color: tokens.colors.text.primary }}>
                {recommendation.destination_node}
              </div>
            </div>
            <div style={{ backgroundColor: tokens.colors.background.surface, padding: '5px 8px', borderRadius: tokens.radii.badge, border: `1px solid ${tokens.colors.brand.primaryBorder}` }}>
              <div style={{ color: tokens.colors.brand.primary, fontSize: '8.5px' }}>ASSIGNED ROUTE</div>
              <div className="font-mono" style={{ fontWeight: 700, color: tokens.colors.brand.primary }}>
                {recommendation.route}
              </div>
            </div>
            <div style={{ backgroundColor: tokens.colors.background.surface, padding: '5px 8px', borderRadius: tokens.radii.badge, border: `1px solid ${tokens.colors.border.subtle}` }}>
              <div style={{ color: tokens.colors.text.muted, fontSize: '8.5px' }}>ASSIGNED VEHICLE</div>
              <div className="font-mono" style={{ fontWeight: 700, color: tokens.colors.text.primary }}>
                {recommendation.vehicle}
              </div>
            </div>
          </div>
        </div>

        {/* Why This Decision? (Fact-Grounded Evidence Chain) */}
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
            WHY THIS DECISION? (DETERMINISTIC FACT-GROUNDED EVIDENCE)
          </div>
          <div
            style={{
              backgroundColor: tokens.colors.background.secondary,
              border: `1px solid ${tokens.colors.border.subtle}`,
              borderRadius: tokens.radii.card,
              padding: '8px 10px',
            }}
          >
            <div style={{ fontSize: '11px', color: tokens.colors.text.secondary, lineHeight: 1.5, whiteSpace: 'pre-line', marginBottom: '8px' }}>
              {recommendation.reason}
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {recommendation.evidence.map((ev, idx) => {
                const isSelected = selectedEvidenceType === ev.type;
                return (
                  <button
                    key={idx}
                    onClick={() => {
                      setSelectedEvidenceType(ev.type);
                      onEvidenceClick?.(ev);
                    }}
                    className="btn btn-secondary"
                    style={{
                      padding: '3px 8px',
                      fontSize: '9.5px',
                      fontFamily: tokens.typography.fontMono,
                      borderColor: isSelected ? tokens.colors.brand.primary : undefined,
                      color: isSelected ? tokens.colors.brand.primary : tokens.colors.text.secondary,
                    }}
                  >
                    <span>{ev.type}: {String(ev.value)}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Why This Corridor? (Corridor Alternatives & Feasibility) */}
        {recommendation.alternatives && recommendation.alternatives.length > 0 && (
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
              WHY THIS CORRIDOR? (PHYSICAL CAPACITY & BYPASS FEASIBILITY)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '6px' }}>
              {recommendation.alternatives.map((alt) => (
                <div
                  key={alt.route_id}
                  style={{
                    backgroundColor: alt.is_selected ? tokens.colors.brand.primarySoft : tokens.colors.background.secondary,
                    border: `1px solid ${alt.is_selected ? tokens.colors.brand.primaryBorder : tokens.colors.border.subtle}`,
                    borderRadius: tokens.radii.badge,
                    padding: '6px 8px',
                    fontSize: '10px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                    <span className="font-mono" style={{ fontWeight: 700, color: alt.is_selected ? tokens.colors.brand.primary : tokens.colors.text.primary }}>
                      {alt.route_id} {alt.is_selected && '✓ (SELECTED)'}
                    </span>
                    <span
                      className={`badge ${
                        alt.status === 'AVAILABLE' ? 'badge-healthy' : alt.status === 'BLOCKED' ? 'badge-critical' : 'badge-warning'
                      }`}
                      style={{ fontSize: '8.5px' }}
                    >
                      {alt.status}
                    </span>
                  </div>
                  <div style={{ color: tokens.colors.text.muted, fontSize: '9px' }}>
                    {alt.reason} • {alt.distance_km} km
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DecisionCenter;
