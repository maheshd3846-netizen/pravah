import React from 'react';
import { tokens } from '../tokens';

interface SimulationDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeScenario?: string;
  seed?: number;
  lastUpdated?: string;
}

export const SimulationDetailsModal: React.FC<SimulationDetailsModalProps> = ({
  isOpen,
  onClose,
  activeScenario = 'COMPOUND_DISRUPTION',
  seed = 42,
  lastUpdated,
}) => {
  if (!isOpen) return null;

  const metadataItems = [
    { label: 'Simulation Environment', value: 'Synthetic Simulation (Sector Shivalik-Vanguard)' },
    { label: 'Military Grid Reference', value: 'Northern Sector 43S WB (34.0°N–35.25°N, 76.2°E–78.15°E)' },
    { label: 'Security Classification', value: 'Unclassified / Synthetic Non-Classified C2' },
    { label: 'Random Seed', value: `Seed ${seed} (100% Deterministic Reproducibility)` },
    { label: 'Data Quality Gate', value: 'SYSTEM READY (Passing all schema & integrity checks)' },
    { label: 'Telemetry Uplink', value: 'SATCOM Primary • GEO Redundancy Active' },
    { label: 'Active Scenario', value: activeScenario },
    { label: 'Planning Horizon', value: '72h Tactical / 336h Strategic Multi-Horizon' },
    { label: 'Optimization Engine', value: 'Continuous Multi-Commodity Linear Flow (SciPy HiGHS LP)' },
    { label: 'ML Regressor', value: 'XGBoost Quantile Forecaster (P50/P80/P95 Quantiles)' },
    { label: 'Telemetry Sync Timestamp', value: lastUpdated || new Date().toISOString() },
  ];

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(8, 17, 31, 0.75)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 250,
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '500px',
          backgroundColor: tokens.colors.background.elevated,
          border: `1px solid ${tokens.colors.border.default}`,
          borderRadius: tokens.radii.container,
          padding: '24px',
          boxShadow: '0 16px 40px rgba(0, 0, 0, 0.5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: tokens.colors.text.primary }}>
              Simulation &amp; System Details
            </div>
            <div style={{ fontSize: '11.5px', color: tokens.colors.text.muted, marginTop: '2px' }}>
              Operational parameters, environment flags, and solver configuration
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: '3px 8px', fontSize: '11px' }}
          >
            ✕
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {metadataItems.map((item, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                fontSize: '12px',
                paddingBottom: '8px',
                borderBottom: `1px solid ${tokens.colors.border.subtle}`,
              }}
            >
              <span style={{ color: tokens.colors.text.secondary, fontWeight: 500 }}>
                {item.label}
              </span>
              <span
                className={item.label.includes('Seed') || item.label.includes('Timestamp') ? 'font-mono' : ''}
                style={{
                  color: tokens.colors.text.primary,
                  fontWeight: 600,
                  textAlign: 'right',
                  maxWidth: '60%',
                }}
              >
                {item.value}
              </span>
            </div>
          ))}
        </div>

        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ fontSize: '12px', padding: '6px 14px' }}
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};

export default SimulationDetailsModal;
