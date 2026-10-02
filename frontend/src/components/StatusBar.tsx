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
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            SYSTEM STATUS:
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: 600, color: '#10b981' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            {systemStatus || 'READY'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
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

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            FORECAST HORIZON:
          </span>
          <span style={{ fontWeight: 600, color: '#cbd5e1', fontFamily: 'var(--font-mono)' }}>
            {forecastHorizonDays} DAYS
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            ACTIVE SCENARIO:
          </span>
          <span style={{ fontWeight: 600, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
            {activeScenario || 'COMPOUND_DISRUPTION'}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#64748b' }}>
        <span style={{ textTransform: 'uppercase', letterSpacing: '0.04em' }}>LAST TELEMETRY REFRESH:</span>
        <span style={{ fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
          {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'LIVE'}
        </span>
      </div>
    </div>
  );
};
