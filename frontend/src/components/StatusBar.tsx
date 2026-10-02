import React from 'react';

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
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* System Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'var(--font-heading)', fontSize: '11px', fontWeight: 600 }}>
            SYSTEM STATUS:
          </span>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              fontWeight: 700,
              color: '#10b981',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              background: 'rgba(16, 185, 129, 0.08)',
              padding: '1px 6px',
              borderRadius: '2px',
              border: '1px solid rgba(16, 185, 129, 0.25)',
            }}
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981', boxShadow: '0 0 6px #10b981' }} />
            {systemStatus || 'READY'}
          </span>
        </div>

        <span style={{ color: 'rgba(255, 255, 255, 0.1)' }}>|</span>

        {/* Data Quality */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'var(--font-heading)', fontSize: '11px', fontWeight: 600 }}>
            DATA QUALITY:
          </span>
          <span
            className={`badge ${
              dataQuality === 'READY'
                ? 'badge-ready'
                : dataQuality === 'DEGRADED'
                ? 'badge-warning'
                : 'badge-critical'
            }`}
          >
            {dataQuality || 'READY'}
          </span>
        </div>

        <span style={{ color: 'rgba(255, 255, 255, 0.1)' }}>|</span>

        {/* Forecast Horizon */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'var(--font-heading)', fontSize: '11px', fontWeight: 600 }}>
            FORECAST HORIZON:
          </span>
          <span
            style={{
              fontWeight: 600,
              color: '#e2e8f0',
              fontFamily: 'var(--font-mono)',
              background: 'rgba(255, 255, 255, 0.04)',
              padding: '1px 6px',
              borderRadius: '2px',
            }}
          >
            {forecastHorizonDays} DAYS
          </span>
        </div>

        <span style={{ color: 'rgba(255, 255, 255, 0.1)' }}>|</span>

        {/* Active Scenario */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'var(--font-heading)', fontSize: '11px', fontWeight: 600 }}>
            ACTIVE SCENARIO:
          </span>
          <span
            style={{
              fontWeight: 700,
              color: '#38bdf8',
              fontFamily: 'var(--font-mono)',
              background: 'rgba(56, 189, 248, 0.08)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              padding: '1px 7px',
              borderRadius: '2px',
            }}
          >
            {activeScenario || 'COMPOUND_DISRUPTION'}
          </span>
        </div>
      </div>

      {/* Right: Telemetry & Link Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
          <span style={{ color: '#06b6d4' }}>⚡</span>
          <span>SATCOM: ONLINE</span>
          <span style={{ color: 'rgba(255, 255, 255, 0.2)' }}>•</span>
          <span style={{ color: '#10b981' }}>GEO-REDUNDANT</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#64748b' }}>
          <span style={{ textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'var(--font-heading)', fontSize: '11px' }}>
            LAST TELEMETRY REFRESH:
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
            {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'LIVE'}
          </span>
        </div>
      </div>
    </div>
  );
};
