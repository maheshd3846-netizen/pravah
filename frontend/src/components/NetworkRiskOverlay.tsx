import React from 'react';
import { tokens } from '../tokens';

interface NetworkRiskOverlayProps {
  score?: number;
  level?: string;
  topDrivers?: string[];
  onViewRisk: () => void;
}

export const NetworkRiskOverlay: React.FC<NetworkRiskOverlayProps> = ({
  score = 0.72,
  level = 'HIGH',
  topDrivers = ['Route', 'Demand', 'Inventory'],
  onViewRisk,
}) => {
  const getLevelColor = (lvl: string) => {
    switch (lvl.toUpperCase()) {
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

  const color = getLevelColor(level);

  return (
    <div
      className="network-risk-overlay"
      aria-label="Network Risk Summary Overlay"
      style={{
        position: 'absolute',
        top: '16px',
        right: '16px',
        width: '210px',
        backgroundColor: 'rgba(13, 24, 40, 0.90)',
        backdropFilter: 'blur(8px)',
        border: `1px solid ${tokens.colors.border.default}`,
        borderRadius: tokens.radii.card,
        padding: '14px 16px',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.35)',
        zIndex: 20,
        pointerEvents: 'auto',
      }}
    >
      <div
        style={{
          fontSize: '10.5px',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: tokens.colors.text.muted,
          fontFamily: tokens.typography.fontSans,
          marginBottom: '8px',
        }}
      >
        Network Risk
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '12px' }}>
        <span
          className="font-mono"
          style={{
            fontSize: '24px',
            fontWeight: 700,
            color: color,
            letterSpacing: '-0.02em',
            lineHeight: 1,
          }}
        >
          {score.toFixed(2)}
        </span>
        <span
          style={{
            fontSize: '11.5px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: color,
          }}
        >
          {level}
        </span>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <div
          style={{
            fontSize: '10.5px',
            fontWeight: 600,
            color: tokens.colors.text.muted,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            marginBottom: '4px',
          }}
        >
          Top drivers:
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {topDrivers.map((driver) => (
            <div
              key={driver}
              style={{
                fontSize: '12px',
                color: tokens.colors.text.secondary,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span style={{ color: color, fontSize: '10px' }}>•</span>
              <span>{driver}</span>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={onViewRisk}
        className="btn btn-secondary"
        style={{
          width: '100%',
          justifyContent: 'center',
          fontSize: '11px',
          padding: '5px 10px',
          color: tokens.colors.text.primary,
        }}
      >
        View Risk →
      </button>
    </div>
  );
};

export default NetworkRiskOverlay;
