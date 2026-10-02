import React from 'react';
import type { AlertItem, NodeRiskDetail } from '../types';

interface RiskPanelProps {
  alerts: AlertItem[];
  nodeRisks: Record<string, NodeRiskDetail>;
  selectedNodeId?: string | null;
  onSelectNode: (nodeId: string) => void;
  isLoading?: boolean;
}

export const RiskPanel: React.FC<RiskPanelProps> = ({
  alerts,
  nodeRisks,
  selectedNodeId,
  onSelectNode,
  isLoading = false,
}) => {
  // Find current risk assessment for selected node or default to highest risk node
  const activeAssessment = selectedNodeId
    ? nodeRisks[selectedNodeId]
    : Object.values(nodeRisks).sort((a, b) => b.overall_risk - a.overall_risk)[0];

  const criticalAlerts = alerts.filter(
    (a) => a.severity === 'CRITICAL' || a.severity === 'HIGH'
  );

  return (
    <div className="card-panel" style={{ height: '100%' }}>
      {/* Panel Header */}
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: '#ef4444', fontSize: '13px' }}>⚠</span>
          <span>CRITICAL RISKS & EARLY WARNINGS</span>
        </div>
        <span
          className="badge badge-critical"
          style={{
            boxShadow: '0 0 10px rgba(239, 68, 68, 0.3)',
          }}
        >
          {alerts.length} ALERTS
        </span>
      </div>

      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Active Node Risk Breakdown HUD */}
        {activeAssessment && (
          <div
            style={{
              backgroundColor: 'rgba(16, 24, 40, 0.75)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '5px',
              padding: '12px',
              boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.05)',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '10px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  className="font-mono"
                  style={{
                    fontSize: '14px',
                    fontWeight: 800,
                    color: '#f8fafc',
                    letterSpacing: '0.04em',
                  }}
                >
                  {activeAssessment.node_code}
                </span>
                <span
                  style={{
                    fontSize: '10px',
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-heading)',
                    letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                  }}
                >
                  5-FACTOR RISK MATRIX
                </span>
              </div>
              <span
                className={`badge ${
                  activeAssessment.level === 'CRITICAL' || activeAssessment.level === 'HIGH'
                    ? 'badge-critical'
                    : 'badge-ready'
                }`}
              >
                {activeAssessment.level} ({activeAssessment.overall_risk.toFixed(2)})
              </span>
            </div>

            {/* Normalized 5-Factor Risk Breakdown Bars */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
              {[
                { name: 'Inventory', val: activeAssessment.components.inventory, color: '#ef4444' },
                { name: 'Demand', val: activeAssessment.components.demand, color: '#f59e0b' },
                { name: 'Route', val: activeAssessment.components.route, color: '#00e5ff' },
                { name: 'Transport', val: activeAssessment.components.transport, color: '#a855f7' },
                { name: 'Environment', val: activeAssessment.components.environment, color: '#10b981' },
              ].map((driver) => {
                const pct = Math.min(100, Math.max(0, driver.val * 100));
                return (
                  <div
                    key={driver.name}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '74px 1fr 38px',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '11px',
                    }}
                  >
                    <span style={{ color: '#94a3b8', fontSize: '10px', fontFamily: 'var(--font-heading)', letterSpacing: '0.04em' }}>
                      {driver.name}
                    </span>
                    <div
                      style={{
                        height: '6px',
                        backgroundColor: 'rgba(255, 255, 255, 0.06)',
                        borderRadius: '3px',
                        overflow: 'hidden',
                        boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.4)',
                      }}
                    >
                      <div
                        style={{
                          height: '100%',
                          width: `${pct}%`,
                          backgroundColor: driver.color,
                          borderRadius: '3px',
                          boxShadow: `0 0 8px ${driver.color}66`,
                          transition: 'width 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
                        }}
                      />
                    </div>
                    <span
                      className="font-mono"
                      style={{
                        textAlign: 'right',
                        color: '#cbd5e1',
                        fontSize: '10px',
                        fontWeight: 600,
                      }}
                    >
                      {driver.val.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Operational Alerts List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, overflowY: 'auto' }}>
          <div
            style={{
              fontSize: '10px',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              fontFamily: 'var(--font-heading)',
              fontWeight: 700,
            }}
          >
            OPERATIONAL EARLY WARNINGS ({criticalAlerts.length})
          </div>

          {isLoading ? (
            <div style={{ color: '#64748b', fontSize: '11px', textAlign: 'center', padding: '16px' }}>
              Loading telemetry alerts...
            </div>
          ) : criticalAlerts.length === 0 ? (
            <div
              style={{
                color: '#10b981',
                fontSize: '11px',
                textAlign: 'center',
                padding: '16px',
                backgroundColor: 'rgba(16, 185, 129, 0.05)',
                borderRadius: '4px',
                border: '1px solid rgba(16, 185, 129, 0.2)',
              }}
            >
              ✓ No critical stockout alerts active in the sector.
            </div>
          ) : (
            criticalAlerts.map((alert) => {
              const isSelected =
                selectedNodeId === alert.node_id || selectedNodeId === alert.node_code;
              return (
                <div
                  key={alert.alert_id}
                  onClick={() => onSelectNode(alert.node_id || alert.node_code)}
                  style={{
                    backgroundColor: isSelected
                      ? 'rgba(18, 30, 50, 0.9)'
                      : 'rgba(13, 20, 32, 0.7)',
                    border: isSelected
                      ? '1px solid #00e5ff'
                      : alert.severity === 'CRITICAL'
                      ? '1px solid rgba(239, 68, 68, 0.35)'
                      : '1px solid var(--border-subtle)',
                    borderLeft: alert.severity === 'CRITICAL' ? '3px solid #ef4444' : '3px solid #f59e0b',
                    borderRadius: '4px',
                    padding: '9px 12px',
                    cursor: 'pointer',
                    boxShadow: isSelected ? '0 0 14px rgba(0, 229, 255, 0.2)' : 'var(--shadow-sm)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '5px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className="font-mono" style={{ fontWeight: 800, color: '#f8fafc', fontSize: '12px' }}>
                        {alert.node_code}
                      </span>
                      <span className="badge badge-cyan" style={{ fontSize: '9px', padding: '1px 5px' }}>
                        {alert.item}
                      </span>
                    </div>
                    <span className={`badge ${alert.severity === 'CRITICAL' ? 'badge-critical' : 'badge-warning'}`}>
                      {alert.severity}
                    </span>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      gap: '14px',
                      fontSize: '11px',
                      color: '#cbd5e1',
                      marginBottom: '4px',
                    }}
                  >
                    <span>
                      Stockout Prob: <strong style={{ color: '#ef4444', fontFamily: 'var(--font-mono)' }}>{(alert.probability * 100).toFixed(0)}%</strong>
                    </span>
                    <span>
                      Horizon: <strong className="font-mono" style={{ color: '#38bdf8' }}>{alert.time_horizon_hours}h</strong>
                    </span>
                  </div>

                  {alert.causes && alert.causes.length > 0 && (
                    <div style={{ fontSize: '10px', color: '#94a3b8', display: 'flex', gap: '4px', alignItems: 'center' }}>
                      <span style={{ color: '#64748b' }}>Causes:</span>
                      <span>{alert.causes.join(', ')}</span>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
