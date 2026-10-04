import React from 'react';
import { tokens } from '../tokens';

interface SituationBarProps {
  activeScenario?: string;
  blockedRoutes?: string[];
  degradedRoutes?: string[];
  criticalNodes?: string[];
  totalNodes?: number;
  overallRiskScore?: number;
  overallRiskLevel?: string;
  stockoutExposedCount?: number;
  onViewAnalysis: () => void;
  onViewNetworkDetails: () => void;
}

export const SituationBar: React.FC<SituationBarProps> = ({
  activeScenario = 'COMPOUND_DISRUPTION',
  blockedRoutes = [],
  degradedRoutes = [],
  criticalNodes = [],
  totalNodes = 15,
  overallRiskScore = 0.72,
  overallRiskLevel = 'HIGH',
  stockoutExposedCount = 2,
  onViewAnalysis,
  onViewNetworkDetails,
}) => {
  const isDisrupted =
    activeScenario !== 'NORMAL' ||
    blockedRoutes.length > 0 ||
    criticalNodes.length > 0 ||
    overallRiskScore > 0.4;

  const scenarioFormatted = activeScenario
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

  // Dynamic operational statement based on real application state
  let dynamicDetail = '';
  if (!isDisrupted) {
    dynamicDetail = 'Network operating normally • No critical operational exposure detected.';
  } else {
    const parts: string[] = [];
    if (blockedRoutes.length > 0) {
      parts.push(`${blockedRoutes.slice(0, 2).join(', ')} blocked`);
    } else if (degradedRoutes.length > 0) {
      parts.push(`${degradedRoutes.slice(0, 2).join(', ')} degraded`);
    } else {
      parts.push('Corridor disruption detected');
    }

    if (criticalNodes.length > 0) {
      parts.push(`${criticalNodes.slice(0, 2).join(', ')} demand pressure rising`);
    } else {
      parts.push('Forward demand surge detected');
    }

    parts.push('downstream exposure detected');
    dynamicDetail = parts.join(' • ');
  }

  const getRiskColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return tokens.colors.status.critical;
      case 'HIGH':
        return tokens.colors.status.highRisk;
      case 'MODERATE':
        return tokens.colors.status.warning;
      default:
        return tokens.colors.status.healthy;
    }
  };

  return (
    <section
      className="situation-bar"
      aria-label="Current Operational Situation"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 20px',
        backgroundColor: tokens.colors.background.surface,
        borderBottom: `1px solid ${tokens.colors.border.default}`,
        flexShrink: 0,
        gap: '24px',
        flexWrap: 'wrap',
      }}
    >
      {/* Left: Situation Summary */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: '1 1 auto', minWidth: '320px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <div
            style={{
              fontSize: '10.5px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: tokens.colors.text.muted,
              fontFamily: tokens.typography.fontSans,
            }}
          >
            Current Situation
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span
              style={{
                fontSize: '13.5px',
                fontWeight: 600,
                color: isDisrupted ? tokens.colors.text.primary : tokens.colors.status.healthy,
                letterSpacing: '-0.01em',
              }}
            >
              {isDisrupted ? scenarioFormatted : 'Normal Operations'}
            </span>
            <span
              style={{
                fontSize: '12.5px',
                color: tokens.colors.text.secondary,
                fontWeight: 400,
              }}
            >
              {dynamicDetail}
            </span>
          </div>
        </div>

        {isDisrupted && (
          <button
            onClick={onViewAnalysis}
            className="btn btn-secondary"
            style={{
              fontSize: '11.5px',
              padding: '4px 10px',
              color: tokens.colors.brand.primary,
              borderColor: tokens.colors.brand.primaryBorder,
              backgroundColor: tokens.colors.brand.primarySoft,
              flexShrink: 0,
            }}
          >
            View Analysis →
          </button>
        )}
      </div>

      {/* Right: Decision-Relevant Compact Inline Metrics */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '20px',
          flexShrink: 0,
        }}
      >
        {/* Network Nodes */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
          <span
            style={{
              fontSize: '10.5px',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: tokens.colors.text.muted,
            }}
          >
            Network
          </span>
          <span
            className="font-mono"
            style={{ fontSize: '13px', fontWeight: 600, color: tokens.colors.text.primary }}
          >
            {totalNodes} Nodes
          </span>
        </div>

        <span style={{ color: tokens.colors.border.default, userSelect: 'none' }}>•</span>

        {/* Overall Network Risk */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
          <span
            style={{
              fontSize: '10.5px',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: tokens.colors.text.muted,
            }}
          >
            Risk
          </span>
          <span
            className="font-mono"
            style={{
              fontSize: '13px',
              fontWeight: 700,
              color: getRiskColor(overallRiskLevel),
            }}
          >
            {overallRiskScore.toFixed(2)}
          </span>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: getRiskColor(overallRiskLevel),
              textTransform: 'capitalize',
            }}
          >
            {overallRiskLevel.toLowerCase()}
          </span>
        </div>

        <span style={{ color: tokens.colors.border.default, userSelect: 'none' }}>•</span>

        {/* Stockout Exposure */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
          <span
            style={{
              fontSize: '10.5px',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: tokens.colors.text.muted,
            }}
          >
            Stockout Exposure
          </span>
          <span
            className="font-mono"
            style={{
              fontSize: '13px',
              fontWeight: 600,
              color: stockoutExposedCount > 0 ? tokens.colors.status.highRisk : tokens.colors.status.healthy,
            }}
          >
            {stockoutExposedCount} {stockoutExposedCount === 1 ? 'Node' : 'Nodes'}
          </span>
        </div>

        <button
          onClick={onViewNetworkDetails}
          className="btn btn-secondary"
          style={{
            fontSize: '11px',
            padding: '3px 8px',
            color: tokens.colors.text.secondary,
            marginLeft: '4px',
          }}
          title="Open full network topology and asset inventory"
        >
          View Network Details →
        </button>
      </div>
    </section>
  );
};

export default SituationBar;
