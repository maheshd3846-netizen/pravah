import React, { useState } from 'react';
import type { RecommendationItem, DecisionEvidenceItem, RouteAlternative } from '../types';

interface DecisionCenterProps {
  recommendation?: RecommendationItem | null;
  onEvidenceClick?: (item: DecisionEvidenceItem) => void;
  isLoading?: boolean;
}

export const DecisionCenter: React.FC<DecisionCenterProps> = ({
  recommendation,
  onEvidenceClick,
  isLoading = false,
}) => {
  const [selectedEvidenceType, setSelectedEvidenceType] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="card-panel" style={{ height: '100%', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ color: '#64748b', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
          Synthesizing decision support recommendations...
        </div>
      </div>
    );
  }

  if (!recommendation) {
    return (
      <div className="card-panel" style={{ height: '100%', justifyContent: 'center', alignItems: 'center', padding: '24px' }}>
        <div style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 600, marginBottom: '4px', fontFamily: 'var(--font-heading)' }}>
          NO ACTIVE RECOMMENDATION SELECTED
        </div>
        <div style={{ color: '#64748b', fontSize: '11px', textAlign: 'center' }}>
          Select a forward node from the Digital Twin or click "ANALYZE NETWORK" to generate tactical movement recommendations.
        </div>
      </div>
    );
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'VERIFIED':
        return 'badge-verified';
      case 'MIXED':
        return 'badge-mixed';
      case 'REJECTED':
        return 'badge-rejected';
      case 'PROPOSED':
        return 'badge-proposed';
      default:
        return 'badge-inconclusive';
    }
  };

  const getConfidenceBadgeClass = (level: string) => {
    switch (level) {
      case 'HIGH':
        return 'badge-ready';
      case 'MEDIUM':
        return 'badge-warning';
      default:
        return 'badge-critical';
    }
  };

  return (
    <div className="card-panel" style={{ height: '100%' }}>
      {/* Header */}
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: '#10b981', fontSize: '13px' }}>⚡</span>
          <span>DECISION CENTER — AUDITABLE RECOMMENDATION</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className={`badge ${getStatusBadgeClass(recommendation.status)}`}>
            {recommendation.status}
          </span>
          <span className={`badge ${getConfidenceBadgeClass(recommendation.confidence.level)}`}>
            CONFIDENCE: {recommendation.confidence.level} ({(recommendation.confidence.score * 100).toFixed(0)}%)
          </span>
        </div>
      </div>

      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Top: Recommended Tactical Action Strip */}
        <div
          style={{
            backgroundColor: 'rgba(16, 185, 129, 0.06)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: '6px',
            padding: '14px',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <div>
              <div
                style={{
                  fontSize: '10px',
                  textTransform: 'uppercase',
                  color: '#10b981',
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                  fontFamily: 'var(--font-heading)',
                }}
              >
                RECOMMENDED ACTION
              </div>
              <div
                style={{
                  fontSize: '19px',
                  fontWeight: 800,
                  color: '#f8fafc',
                  fontFamily: 'var(--font-mono)',
                  letterSpacing: '0.02em',
                  marginTop: '2px',
                }}
              >
                {recommendation.action_type} {recommendation.quantity.toFixed(0)} {recommendation.item}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'var(--font-heading)', letterSpacing: '0.04em' }}>
                DISPATCH WINDOW
              </div>
              <div className="font-mono" style={{ fontSize: '12px', color: '#38bdf8', fontWeight: 600, marginTop: '2px' }}>
                Hour +{recommendation.planned_departure}h → ETA +{recommendation.expected_arrival}h
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', fontSize: '11px' }}>
            <div style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '7px 9px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: '#64748b', fontSize: '9px', fontFamily: 'var(--font-heading)', letterSpacing: '0.04em' }}>SOURCE DEPOT</div>
              <div className="font-mono" style={{ fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
                {recommendation.source_node}
              </div>
            </div>
            <div style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '7px 9px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: '#64748b', fontSize: '9px', fontFamily: 'var(--font-heading)', letterSpacing: '0.04em' }}>DESTINATION</div>
              <div className="font-mono" style={{ fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
                {recommendation.destination_node}
              </div>
            </div>
            <div style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '7px 9px', borderRadius: '4px', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
              <div style={{ color: '#38bdf8', fontSize: '9px', fontFamily: 'var(--font-heading)', letterSpacing: '0.04em' }}>ASSIGNED ROUTE</div>
              <div className="font-mono" style={{ fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
                {recommendation.route}
              </div>
            </div>
            <div style={{ backgroundColor: 'rgba(0,0,0,0.3)', padding: '7px 9px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: '#64748b', fontSize: '9px', fontFamily: 'var(--font-heading)', letterSpacing: '0.04em' }}>ASSIGNED VEHICLE</div>
              <div className="font-mono" style={{ fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
                {recommendation.vehicle}
              </div>
            </div>
          </div>
        </div>

        {/* Middle: Why This Decision? (Fact-Grounded Explanation) */}
        <div>
          <div
            style={{
              fontSize: '11px',
              fontWeight: 700,
              color: '#94a3b8',
              textTransform: 'uppercase',
              marginBottom: '6px',
              fontFamily: 'var(--font-heading)',
              letterSpacing: '0.06em',
            }}
          >
            WHY THIS DECISION? (DETERMINISTIC FACT-GROUNDED EVIDENCE)
          </div>
          <div
            style={{
              backgroundColor: 'rgba(16, 24, 40, 0.7)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '5px',
              padding: '10px 12px',
              fontSize: '11px',
              lineHeight: 1.6,
              color: '#cbd5e1',
            }}
          >
            {recommendation.reason.split('\n').map((line, idx) => {
              if (!line.trim()) return null;
              return (
                <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
                  <span style={{ color: '#10b981', fontWeight: 'bold' }}>✓</span>
                  <span>{line.replace(/^-\s*/, '')}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Evidence Clickable Tags */}
        {recommendation.evidence && recommendation.evidence.length > 0 && (
          <div>
            <div
              style={{
                fontSize: '10px',
                color: '#64748b',
                textTransform: 'uppercase',
                marginBottom: '5px',
                fontFamily: 'var(--font-heading)',
                letterSpacing: '0.05em',
              }}
            >
              CLICKABLE EVIDENCE ITEMS
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {recommendation.evidence.map((ev, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setSelectedEvidenceType(ev.type);
                    if (onEvidenceClick) onEvidenceClick(ev);
                  }}
                  className="btn btn-secondary"
                  style={{
                    padding: '3px 9px',
                    fontSize: '10px',
                    borderColor: selectedEvidenceType === ev.type ? '#00e5ff' : undefined,
                    color: selectedEvidenceType === ev.type ? '#00e5ff' : undefined,
                    background: selectedEvidenceType === ev.type ? 'rgba(0, 229, 255, 0.1)' : undefined,
                  }}
                >
                  <span style={{ color: '#00e5ff' }}>●</span> {ev.type}: {String(ev.value)}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Route Alternative Comparative Analysis */}
        {recommendation.alternatives && recommendation.alternatives.length > 0 && (
          <div>
            <div
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: '#94a3b8',
                textTransform: 'uppercase',
                marginBottom: '6px',
                fontFamily: 'var(--font-heading)',
                letterSpacing: '0.06em',
              }}
            >
              WHY THIS CORRIDOR? (OPTIMIZER ROUTE COMPARISON)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px' }}>
              {recommendation.alternatives.map((alt: RouteAlternative) => (
                <div
                  key={alt.route_id}
                  style={{
                    backgroundColor: alt.is_selected ? 'rgba(0, 229, 255, 0.08)' : 'rgba(16, 24, 40, 0.65)',
                    border: alt.is_selected ? '1px solid rgba(0, 229, 255, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '5px',
                    padding: '9px 10px',
                    fontSize: '10px',
                    boxShadow: alt.is_selected ? '0 0 12px rgba(0, 229, 255, 0.1)' : undefined,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span className="font-mono" style={{ fontWeight: 800, color: alt.is_selected ? '#00e5ff' : '#f8fafc' }}>
                      {alt.route_id}
                    </span>
                    <span
                      className={`badge ${
                        alt.status === 'BLOCKED' ? 'badge-critical' : alt.is_selected ? 'badge-ready' : 'badge-neutral'
                      }`}
                    >
                      {alt.status}
                    </span>
                  </div>
                  <div style={{ color: '#94a3b8', marginBottom: '3px' }}>
                    Dist: <strong className="font-mono" style={{ color: '#cbd5e1' }}>{alt.distance_km} km</strong> | Risk:{' '}
                    <strong className="font-mono" style={{ color: '#cbd5e1' }}>{alt.risk_score.toFixed(2)}</strong>
                  </div>
                  <div style={{ color: alt.is_selected ? '#38bdf8' : '#64748b', fontSize: '9.5px', fontStyle: 'italic' }}>
                    {alt.reason}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Validation State Strip */}
        <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '10px' }}>
          <div
            style={{
              fontSize: '10px',
              color: '#64748b',
              textTransform: 'uppercase',
              marginBottom: '5px',
              fontFamily: 'var(--font-heading)',
              letterSpacing: '0.05em',
            }}
          >
            7-POINT VALIDATION CHECK
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', fontSize: '9px' }}>
            {Object.entries(recommendation.validation_state).map(([k, v]) => (
              <span
                key={k}
                className={`badge ${v === 'PASS' || v === 'READY' ? 'badge-ready' : 'badge-warning'}`}
              >
                {k}: {v}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
