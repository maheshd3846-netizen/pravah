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
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: '#ef4444' }}>⚠</span> CRITICAL RISKS & EARLY WARNINGS
        </div>
        <span className="badge badge-critical">{alerts.length} ALERTS</span>
      </div>

      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Active Node Risk Breakdown */}
        {activeAssessment && (
          <div
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              padding: '10px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div>
                <span className="font-mono" style={{ fontSize: '13px', fontWeight: 800, color: '#f8fafc' }}>
                  {activeAssessment.node_code}
                </span>
                <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '6px' }}>RISK BREAKDOWN</span>
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {[
                { name: 'Inventory', val: activeAssessment.components.inventory, color: '#ef4444' },
                { name: 'Demand', val: activeAssessment.components.demand, color: '#f59e0b' },
                { name: 'Route', val: activeAssessment.components.route, color: '#38bdf8' },
                { name: 'Transport', val: activeAssessment.components.transport, color: '#8b5cf6' },
                { name: 'Environment', val: activeAssessment.components.environment, color: '#10b981' },
              ].map((driver) => {
                const pct = Math.min(100, Math.max(0, driver.val * 100));
                return (
                  <div key={driver.name} style={{ display: 'grid', gridTemplateColumns: '72px 1fr 36px', alignItems: 'center', gap: '6px', fontSize: '10px' }}>
                    <span style={{ color: '#94a3b8' }}>{driver.name}</span>
                    <div style={{ height: '5px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${pct}%`,
                          backgroundColor: driver.color,
                          borderRadius: '3px',
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>
                    <span className="font-mono" style={{ textAlign: 'right', color: '#cbd5e1' }}>
                      {(driver.val).toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Alerts List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, overflowY: 'auto' }}>
          <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            OPERATIONAL EARLY WARNINGS ({criticalAlerts.length})
          </div>

          {isLoading ? (
            <div style={{ color: '#64748b', fontSize: '11px', textAlign: 'center', padding: '16px' }}>
              Loading telemetry alerts...
            </div>
          ) : criticalAlerts.length === 0 ? (
            <div style={{ color: '#10b981', fontSize: '11px', textAlign: 'center', padding: '16px' }}>
              ✓ No critical stockout alerts active in the sector.
            </div>
          ) : (
            criticalAlerts.map((alert) => (
              <div
                key={alert.alert_id}
                onClick={() => onSelectNode(alert.node_id || alert.node_code)}
                style={{
                  backgroundColor: 'rgba(15, 23, 42, 0.7)',
                  border:
                    selectedNodeId === alert.node_id || selectedNodeId === alert.node_code
                      ? '1px solid #38bdf8'
                      : alert.severity === 'CRITICAL'
                      ? '1px solid rgba(239, 68, 68, 0.3)'
                      : '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '8px 10px',
                  cursor: 'pointer',
                  transition: 'border-color 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className="font-mono" style={{ fontWeight: 800, color: '#f8fafc' }}>
                      {alert.node_code}
                    </span>
                    <span className="badge badge-cyan" style={{ fontSize: '9px' }}>
                      {alert.item}
                    </span>
                  </div>
                  <span className={`badge ${alert.severity === 'CRITICAL' ? 'badge-critical' : 'badge-warning'}`}>
                    {alert.severity}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '12px', fontSize: '10px', color: '#cbd5e1', marginBottom: '4px' }}>
                  <span>
                    Stockout Prob: <strong style={{ color: '#ef4444' }}>{(alert.probability * 100).toFixed(0)}%</strong>
                  </span>
                  <span>
                    Horizon: <strong className="font-mono">{alert.time_horizon_hours}h</strong>
                  </span>
                </div>

                {alert.causes && alert.causes.length > 0 && (
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                    <span style={{ color: '#64748b' }}>Causes: </span>
                    {alert.causes.join(', ')}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
