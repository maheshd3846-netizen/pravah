import React, { useState } from 'react';
import type { CounterfactualEvaluationResponse } from '../types';

interface ScenarioSimulatorProps {
  evaluation?: CounterfactualEvaluationResponse | null;
  onRunScenario: (scenarioName: string, overrides: Record<string, any>) => void;
  isRunning?: boolean;
}

export const ScenarioSimulator: React.FC<ScenarioSimulatorProps> = ({
  evaluation,
  onRunScenario,
  isRunning = false,
}) => {
  const [selectedPreset, setSelectedPreset] = useState<string>('COMPOUND_DISRUPTION');
  const [routeCorridor, setRouteCorridor] = useState<string>('BLOCKED');
  const [demandSurge, setDemandSurge] = useState<string>('SURGE_30');
  const [weatherCondition, setWeatherCondition] = useState<string>('SEVERE_BLIZZARD');
  const [fleetStatus, setFleetStatus] = useState<string>('REDUCED_20');

  const handleApplyPreset = (preset: string) => {
    setSelectedPreset(preset);
    if (preset === 'COMPOUND_DISRUPTION') {
      setRouteCorridor('BLOCKED');
      setDemandSurge('SURGE_30');
      setWeatherCondition('SEVERE_BLIZZARD');
      setFleetStatus('REDUCED_20');
    } else if (preset === 'BASELINE') {
      setRouteCorridor('AVAILABLE');
      setDemandSurge('NORMAL');
      setWeatherCondition('NORMAL');
      setFleetStatus('NORMAL');
    }
  };

  const handleExecute = () => {
    onRunScenario(selectedPreset, {
      routeStatus: routeCorridor,
      demandSurge,
      weather: weatherCondition,
      fleet: fleetStatus,
    });
  };

  const base = evaluation?.baseline;
  const opt = evaluation?.optimized;
  const deltas = evaluation?.deltas;

  return (
    <div className="card-panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: '#f59e0b' }}>🎮</span> WHAT-IF DISRUPTION SIMULATOR & CAUSAL EVALUATION
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => handleApplyPreset('COMPOUND_DISRUPTION')}
            className="btn btn-secondary"
            style={{
              padding: '2px 8px',
              fontSize: '10px',
              borderColor: selectedPreset === 'COMPOUND_DISRUPTION' ? '#f59e0b' : undefined,
              color: selectedPreset === 'COMPOUND_DISRUPTION' ? '#f59e0b' : undefined,
            }}
          >
            COMPOUND DISRUPTION PRESET
          </button>
          <button
            onClick={() => handleApplyPreset('BASELINE')}
            className="btn btn-secondary"
            style={{
              padding: '2px 8px',
              fontSize: '10px',
              borderColor: selectedPreset === 'BASELINE' ? '#38bdf8' : undefined,
              color: selectedPreset === 'BASELINE' ? '#38bdf8' : undefined,
            }}
          >
            NORMAL BASELINE
          </button>
        </div>
      </div>

      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Controls Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr) auto',
            gap: '10px',
            alignItems: 'flex-end',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            padding: '10px',
            borderRadius: '4px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
              PRIMARY ROUTE R-01 / R-22
            </label>
            <select
              value={routeCorridor}
              onChange={(e) => setRouteCorridor(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-surface-elevated)',
                color: '#f8fafc',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '5px 8px',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <option value="BLOCKED">BLOCKED (Severe Landslide)</option>
              <option value="DEGRADED">DEGRADED (Reduced Cap)</option>
              <option value="AVAILABLE">AVAILABLE (Open Highway)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
              FORWARD DEMAND SURGE
            </label>
            <select
              value={demandSurge}
              onChange={(e) => setDemandSurge(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-surface-elevated)',
                color: '#f8fafc',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '5px 8px',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <option value="SURGE_30">+30% Combat Post Surge</option>
              <option value="SURGE_15">+15% Tactical Alert</option>
              <option value="NORMAL">Standard Baseline Demand</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
              WEATHER SEVERITY
            </label>
            <select
              value={weatherCondition}
              onChange={(e) => setWeatherCondition(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-surface-elevated)',
                color: '#f8fafc',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '5px 8px',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <option value="SEVERE_BLIZZARD">Severe Alpine Blizzard</option>
              <option value="MODERATE">Moderate Mountain Flurry</option>
              <option value="NORMAL">Clear Visibility</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
              CONVOY FLEET CAPACITY
            </label>
            <select
              value={fleetStatus}
              onChange={(e) => setFleetStatus(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-surface-elevated)',
                color: '#f8fafc',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '5px 8px',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <option value="REDUCED_20">-20% Sub-Zero Maintenance</option>
              <option value="REDUCED_10">-10% Vehicle Hold</option>
              <option value="NORMAL">100% Full Fleet Availability</option>
            </select>
          </div>

          <div>
            <button
              onClick={handleExecute}
              disabled={isRunning}
              className="btn btn-primary"
              style={{ padding: '6px 14px' }}
            >
              {isRunning ? 'SIMULATING...' : '▶ RUN SCENARIO'}
            </button>
          </div>
        </div>

        {/* Results: Baseline vs Intervention Side-by-Side Table */}
        {base && opt ? (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
                CLOSED-LOOP CAUSAL COMPARISON (BASELINE VS OPTIMIZED)
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '11px', color: '#64748b' }}>VERDICT:</span>
                <span
                  className={`badge ${
                    evaluation?.status === 'VERIFIED'
                      ? 'badge-verified'
                      : evaluation?.status === 'MIXED'
                      ? 'badge-mixed'
                      : 'badge-rejected'
                  }`}
                >
                  {evaluation?.status}
                </span>
              </div>
            </div>

            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '11px',
                backgroundColor: '#070b13',
                borderRadius: '4px',
                overflow: 'hidden',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <thead>
                <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.04)', color: '#94a3b8', textAlign: 'left' }}>
                  <th style={{ padding: '8px 12px' }}>OPERATIONAL METRIC</th>
                  <th style={{ padding: '8px 12px', textAlign: 'right' }}>BASELINE (NO ACTION)</th>
                  <th style={{ padding: '8px 12px', textAlign: 'right' }}>INTERVENTION (PRAVAH)</th>
                  <th style={{ padding: '8px 12px', textAlign: 'right' }}>CAUSAL DELTA</th>
                  <th style={{ padding: '8px 12px', textAlign: 'center' }}>DIRECTION</th>
                </tr>
              </thead>
              <tbody>
                {/* 1. Unmet Demand */}
                <tr style={{ borderTop: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: '#f8fafc' }}>Unmet Supply Demand</td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right', color: '#ef4444' }}>
                    {base.total_unmet_demand.toFixed(1)} u
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right', color: '#10b981' }}>
                    {opt.total_unmet_demand.toFixed(1)} u
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right', color: '#10b981', fontWeight: 700 }}>
                    {deltas?.unmet_demand?.absolute_delta !== undefined
                      ? `${deltas.unmet_demand.absolute_delta.toFixed(1)} u (${deltas.unmet_demand.relative_delta_percent.toFixed(1)}%)`
                      : '—'}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <span className="badge badge-ready">IMPROVED</span>
                  </td>
                </tr>

                {/* 2. Stockout Duration */}
                <tr style={{ borderTop: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: '#f8fafc' }}>Stockout Duration</td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {base.stockout_duration_hours} hrs ({base.total_stockout_events} events)
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {opt.stockout_duration_hours} hrs ({opt.total_stockout_events} events)
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right', color: '#10b981', fontWeight: 700 }}>
                    {deltas?.stockout_events?.absolute_delta !== undefined
                      ? `${deltas.stockout_events.absolute_delta.toFixed(0)} events`
                      : '—'}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <span className="badge badge-ready">IMPROVED</span>
                  </td>
                </tr>

                {/* 3. Fulfillment Rate */}
                <tr style={{ borderTop: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: '#f8fafc' }}>Fulfillment Rate</td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {base.fulfillment_rate_percent.toFixed(2)}%
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right', color: '#10b981' }}>
                    {opt.fulfillment_rate_percent.toFixed(2)}%
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right', color: '#10b981', fontWeight: 700 }}>
                    {deltas?.fulfillment_rate_percent?.absolute_delta !== undefined
                      ? `+${deltas.fulfillment_rate_percent.absolute_delta.toFixed(2)}% pts`
                      : '—'}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <span className="badge badge-ready">IMPROVED</span>
                  </td>
                </tr>

                {/* 4. Transport Distance */}
                <tr style={{ borderTop: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: '#f8fafc' }}>Transport Distance</td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {base.total_transport_distance_km.toFixed(1)} km
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {opt.total_transport_distance_km.toFixed(1)} km
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right', color: '#f59e0b' }}>
                    {deltas?.total_transport_distance_km?.absolute_delta !== undefined
                      ? `+${deltas.total_transport_distance_km.absolute_delta.toFixed(1)} km`
                      : '—'}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <span className="badge badge-warning">INCREASED</span>
                  </td>
                </tr>

                {/* 5. Transit Delay */}
                <tr style={{ borderTop: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: '#f8fafc' }}>Average Transit Delay</td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {base.average_delay_hours.toFixed(2)} hrs
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {opt.average_delay_hours.toFixed(2)} hrs
                  </td>
                  <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right', color: '#f59e0b' }}>
                    {deltas?.average_delay_hours?.absolute_delta !== undefined
                      ? `+${deltas.average_delay_hours.absolute_delta.toFixed(2)} hrs`
                      : '—'}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <span className="badge badge-warning">INCREASED</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : (
          <div
            style={{
              padding: '24px',
              textAlign: 'center',
              backgroundColor: 'rgba(255, 255, 255, 0.02)',
              borderRadius: '4px',
              border: '1px dashed var(--border-subtle)',
              color: '#64748b',
              fontSize: '11px',
            }}
          >
            Configure scenario controls above and click "RUN SCENARIO" to trigger baseline vs. optimized counterfactual simulation.
          </div>
        )}
      </div>
    </div>
  );
};
