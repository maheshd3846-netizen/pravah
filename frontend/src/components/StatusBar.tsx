import React from 'react';
import { tokens } from '../tokens';

interface StatusBarProps {
  systemStatus: string;
  dataQuality: string;
  forecastHorizonDays: number;
  activeScenario: string;
  lastUpdated: string;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  systemStatus,
  dataQuality,
  forecastHorizonDays,
  activeScenario,
  lastUpdated,
}) => {
  return (
    <div className="status-bar" role="region" aria-label="Global System Status">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* System Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              color: tokens.colors.text.muted,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '10px',
              fontWeight: 600,
            }}
          >
            SYSTEM STATUS:
          </span>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontWeight: 700,
              color: tokens.colors.status.healthy,
              fontFamily: tokens.typography.fontMono,
              fontSize: '10.5px',
              backgroundColor: tokens.colors.status.healthySoft,
              padding: '1px 6px',
              borderRadius: tokens.radii.badge,
              border: `1px solid ${tokens.colors.status.healthyBorder}`,
            }}
          >
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: tokens.colors.status.healthy }} />
            {systemStatus || 'READY'}
          </span>
        </div>

        <span style={{ color: tokens.colors.border.subtle }}>|</span>

        {/* Data Quality */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              color: tokens.colors.text.muted,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '10px',
              fontWeight: 600,
            }}
          >
            DATA QUALITY:
          </span>
          <span
            className={`badge ${
              dataQuality === 'READY'
                ? 'badge-healthy'
                : dataQuality === 'DEGRADED'
                ? 'badge-warning'
                : 'badge-critical'
            }`}
          >
            {dataQuality || 'READY'}
          </span>
        </div>

        <span style={{ color: tokens.colors.border.subtle }}>|</span>

        {/* Forecast Horizon */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              color: tokens.colors.text.muted,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '10px',
              fontWeight: 600,
            }}
          >
            FORECAST HORIZON:
          </span>
          <span
            style={{
              fontWeight: 600,
              color: tokens.colors.text.primary,
              fontFamily: tokens.typography.fontMono,
              backgroundColor: tokens.colors.background.secondary,
              padding: '1px 6px',
              borderRadius: tokens.radii.badge,
              border: `1px solid ${tokens.colors.border.subtle}`,
            }}
          >
            {forecastHorizonDays} DAYS
          </span>
        </div>

        <span style={{ color: tokens.colors.border.subtle }}>|</span>

        {/* Active Scenario */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              color: tokens.colors.text.muted,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '10px',
              fontWeight: 600,
            }}
          >
            ACTIVE SCENARIO:
          </span>
          <span
            style={{
              fontWeight: 700,
              color: tokens.colors.status.warning,
              fontFamily: tokens.typography.fontMono,
              backgroundColor: tokens.colors.status.warningSoft,
              border: `1px solid ${tokens.colors.status.warningBorder}`,
              padding: '1px 6px',
              borderRadius: tokens.radii.badge,
            }}
          >
            {activeScenario || 'COMPOUND_DISRUPTION'}
          </span>
        </div>
      </div>

      {/* Right: Telemetry & Link Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', color: tokens.colors.text.secondary, fontFamily: tokens.typography.fontMono }}>
          <span style={{ color: tokens.colors.brand.primary }}>⚡</span>
          <span>SATCOM: ONLINE</span>
          <span style={{ color: tokens.colors.border.default }}>•</span>
          <span style={{ color: tokens.colors.status.healthy }}>GEO-REDUNDANT</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: tokens.colors.text.muted, fontSize: '10.5px' }}>
          <span style={{ textTransform: 'uppercase', letterSpacing: '0.04em', fontSize: '10px' }}>
            LAST TELEMETRY REFRESH:
          </span>
          <span style={{ fontFamily: tokens.typography.fontMono, color: tokens.colors.text.secondary }}>
            {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'LIVE'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
