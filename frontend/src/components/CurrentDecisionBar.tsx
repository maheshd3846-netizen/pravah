import React from 'react';
import type { RecommendationItem, CounterfactualEvaluationResponse } from '../types';
import { tokens } from '../tokens';

interface CurrentDecisionBarProps {
  recommendation: RecommendationItem | null;
  evaluation: CounterfactualEvaluationResponse | null;
  rejectionSummary?: string | null;
  candidateCount?: number;
  onViewEvidence: () => void;
}

export const CurrentDecisionBar: React.FC<CurrentDecisionBarProps> = ({
  recommendation,
  evaluation,
  rejectionSummary,
  candidateCount = 55,
  onViewEvidence,
}) => {
  const isSuppressed =
    recommendation?.status === 'REJECTED' ||
    evaluation?.status === 'DEGRADED' ||
    evaluation?.deltas?.unmet_demand?.direction === 'DEGRADED' ||
    (Boolean(rejectionSummary) && !recommendation);

  const isVerified =
    recommendation?.status === 'VERIFIED' ||
    (evaluation?.deltas?.unmet_demand?.direction === 'IMPROVED' &&
      recommendation &&
      recommendation.status !== 'REJECTED');

  // Format action text dynamically from actual recommendation data
  const actionTitle = recommendation?.title
    ? recommendation.title
    : recommendation
    ? `Reroute → ${recommendation.destination_node}`
    : 'No active intervention proposed';

  return (
    <section
      className="current-decision-bar"
      aria-label="Current Decision and System State"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 20px',
        backgroundColor: tokens.colors.background.surface,
        borderTop: `1px solid ${tokens.colors.border.default}`,
        flexShrink: 0,
        gap: '20px',
        flexWrap: 'wrap',
      }}
    >
      {/* State 1: Deliberate Safety Rejection / Suppression */}
      {isSuppressed && (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', flex: '1 1 auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '10.5px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: tokens.colors.status.warning,
                  fontFamily: tokens.typography.fontSans,
                }}
              >
                Recommendation Suppressed
              </span>
              <span
                style={{
                  fontSize: '10px',
                  padding: '1px 6px',
                  borderRadius: tokens.radii.badge,
                  backgroundColor: tokens.colors.status.warningSoft,
                  color: tokens.colors.status.warning,
                  border: `1px solid ${tokens.colors.status.warningBorder}`,
                  fontWeight: 600,
                }}
              >
                Safety Protocol Active
              </span>
            </div>
            <div style={{ fontSize: '13px', color: tokens.colors.text.primary, fontWeight: 500 }}>
              The proposed intervention did not demonstrate a verified improvement under the current operating conditions.
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                fontSize: '11.5px',
                color: tokens.colors.text.secondary,
                marginTop: '2px',
              }}
            >
              <span style={{ color: tokens.colors.status.healthy }}>✓ Physical evaluation completed</span>
              <span style={{ color: tokens.colors.status.healthy }}>✓ Counterfactual evaluated</span>
              <span style={{ color: tokens.colors.status.warning }}>⚠ Benefit not verified</span>
            </div>
          </div>

          <button
            onClick={onViewEvidence}
            className="btn btn-secondary"
            style={{
              fontSize: '12px',
              padding: '6px 14px',
              color: tokens.colors.brand.primary,
              borderColor: tokens.colors.brand.primaryBorder,
              backgroundColor: tokens.colors.brand.primarySoft,
              flexShrink: 0,
            }}
          >
            View Evidence →
          </button>
        </>
      )}

      {/* State 2: Verified Action Available */}
      {!isSuppressed && isVerified && (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', flex: '1 1 auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '10.5px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: tokens.colors.brand.primary,
                  fontFamily: tokens.typography.fontSans,
                }}
              >
                Decision Status
              </span>
              <span
                style={{
                  fontSize: '10px',
                  padding: '1px 6px',
                  borderRadius: tokens.radii.badge,
                  backgroundColor: tokens.colors.status.healthySoft,
                  color: tokens.colors.status.healthy,
                  border: `1px solid ${tokens.colors.status.healthyBorder}`,
                  fontWeight: 600,
                }}
              >
                Verified Action Available
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
              <span style={{ fontSize: '13.5px', fontWeight: 600, color: tokens.colors.text.primary }}>
                {actionTitle}
              </span>
              {recommendation?.vehicle && (
                <span className="font-mono" style={{ fontSize: '11.5px', color: tokens.colors.text.muted }}>
                  via {recommendation.route || 'Bypass'} • Convoy {recommendation.vehicle}
                </span>
              )}
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                fontSize: '11.5px',
                color: tokens.colors.text.secondary,
                marginTop: '2px',
              }}
            >
              <span>
                Physical feasibility:{' '}
                <strong style={{ color: tokens.colors.status.healthy }}>PASSED</strong>
              </span>
              <span>
                Counterfactual:{' '}
                <strong style={{ color: tokens.colors.status.healthy }}>IMPROVED</strong>
              </span>
              {evaluation?.deltas?.unmet_demand && (
                <span className="font-mono" style={{ color: tokens.colors.status.healthy }}>
                  {evaluation.deltas.unmet_demand.relative_delta_percent}% unmet demand delta
                </span>
              )}
            </div>
          </div>

          <button
            onClick={onViewEvidence}
            className="btn btn-primary"
            style={{
              fontSize: '12px',
              padding: '6px 16px',
              flexShrink: 0,
            }}
          >
            View Evidence →
          </button>
        </>
      )}

      {/* State 3: Mixed / Candidates Generated */}
      {!isSuppressed && !isVerified && (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', flex: '1 1 auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '10.5px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: tokens.colors.text.muted,
                  fontFamily: tokens.typography.fontSans,
                }}
              >
                Decision Status
              </span>
              <span
                style={{
                  fontSize: '10px',
                  padding: '1px 6px',
                  borderRadius: tokens.radii.badge,
                  backgroundColor: tokens.colors.brand.primarySoft,
                  color: tokens.colors.brand.primary,
                  fontWeight: 600,
                }}
              >
                Candidate Dispatch Generated
              </span>
            </div>
            <div style={{ fontSize: '13.5px', fontWeight: 600, color: tokens.colors.text.primary }}>
              {candidateCount} candidate actions generated • Physical validation completed
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                fontSize: '11.5px',
                color: tokens.colors.text.secondary,
                marginTop: '2px',
              }}
            >
              <span>
                Counterfactual status:{' '}
                <strong style={{ color: tokens.colors.status.warning }}>
                  {evaluation?.status || 'MIXED'}
                </strong>
              </span>
              <span>
                Recommendation:{' '}
                <strong style={{ color: tokens.colors.text.primary }}>
                  {recommendation ? 'AVAILABLE' : 'PENDING'}
                </strong>
              </span>
            </div>
          </div>

          <button
            onClick={onViewEvidence}
            className="btn btn-secondary"
            style={{
              fontSize: '12px',
              padding: '6px 14px',
              color: tokens.colors.brand.primary,
              borderColor: tokens.colors.brand.primaryBorder,
              flexShrink: 0,
            }}
          >
            View Evidence →
          </button>
        </>
      )}
    </section>
  );
};

export default CurrentDecisionBar;
