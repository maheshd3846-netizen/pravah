import React from 'react';
import type { AlertItem, NodeRiskDetail } from '../types';
import { tokens } from '../tokens';

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
          <span style={{ color: tokens.colors.status.critical, fontSize: '13px' }}>⚠</span>
          <span>CRITICAL RISKS & EARLY WARNINGS</span>
        </div>
        <span className="badge badge-critical">
          {alerts.length} ALERTS
        </span>
      </div>

      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {/* Overall Network Risk & 5-Factor Risk Intelligence */}
        {activeAssessment && (
          <div
            style={{
              backgroundColor: tokens.colors.background.secondary,
              border: `1px solid ${tokens.colors.border.subtle}`,
              borderRadius: tokens.radii.card,
              padding: '10px 12px',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px',
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: tokens.colors.text.primary,
                    letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                  }}
                >
                  Overall Network Risk
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                  <span
                    className="font-mono"
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      color: tokens.colors.brand.primary,
                    }}
                  >
                    {activeAssessment.node_code}
                  </span>
                  <span style={{ fontSize: '9.5px', color: tokens.colors.text.muted }}>
                    // Targeted Outpost Vector
                  </span>
                </div>
              </div>
              <span
                className={`badge ${
                  activeAssessment.level === 'CRITICAL'
                    ? 'badge-critical'
                    : activeAssessment.level === 'HIGH'
                    ? 'badge-high'
                    : 'badge-healthy'
                }`}
              >
                {activeAssessment.level} ({activeAssessment.overall_risk.toFixed(2)})
              </span>
            </div>

            {/* Structured 5-Factor Risk Intelligence Bars */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              {[
                { name: 'Inventory', val: activeAssessment.components.inventory, color: tokens.colors.status.critical },
                { name: 'Demand', val: activeAssessment.components.demand, color: tokens.colors.status.highRisk },
                { name: 'Route', val: activeAssessment.components.route, color: tokens.colors.status.warning },
                { name: 'Transport', val: activeAssessment.components.transport, color: tokens.colors.status.info },
                { name: 'Environment', val: activeAssessment.components.environment, color: tokens.colors.brand.primary },
              ].map((driver) => {
                const pct = Math.min(100, Math.max(0, driver.val * 100));
                return (
                  <div
                    key={driver.name}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '78px 1fr 34px',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '11px',
                    }}
                  >
                    <span style={{ color: tokens.colors.text.secondary, fontSize: '10px' }}>
                      {driver.name}
                    </span>
                    <div
                      style={{
                        height: '5px',
                        backgroundColor: tokens.colors.background.elevated,
                        borderRadius: '2px',
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          height: '100%',
                          width: `${pct}%`,
                          backgroundColor: driver.color,
                          borderRadius: '2px',
                          transition: 'width 0.25s ease-out',
                        }}
                      />
                    </div>
                    <span
                      className="font-mono"
                      style={{
                        textAlign: 'right',
                        color: tokens.colors.text.primary,
                        fontSize: '9.5px',
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

        {/* Network Risk Propagation Chain (Section 12) */}
        <div
          style={{
            backgroundColor: tokens.colors.background.secondary,
            border: `1px solid ${tokens.colors.border.subtle}`,
            borderRadius: tokens.radii.card,
            padding: '10px 12px',
          }}
        >
          <div
            style={{
              fontSize: '9.5px',
              color: tokens.colors.text.muted,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              fontWeight: 700,
              marginBottom: '6px',
            }}
          >
            NETWORK RISK PROPAGATION PATH
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '6px 8px',
              backgroundColor: tokens.colors.background.surface,
              borderRadius: tokens.radii.badge,
              border: `1px solid ${tokens.colors.border.subtle}`,
              fontSize: '10px',
              fontFamily: tokens.typography.fontMono,
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: tokens.colors.status.critical, fontWeight: 700 }}>R-22</div>
              <div style={{ fontSize: '8.5px', color: tokens.colors.status.critical }}>BLOCKED</div>
            </div>
            <div style={{ color: tokens.colors.text.muted }}>➔</div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: tokens.colors.status.warning, fontWeight: 700 }}>HUB-02</div>
              <div style={{ fontSize: '8.5px', color: tokens.colors.status.warning }}>DEGRADED</div>
            </div>
            <div style={{ color: tokens.colors.text.muted }}>➔</div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: tokens.colors.status.critical, fontWeight: 700 }}>FP-04</div>
              <div style={{ fontSize: '8.5px', color: tokens.colors.status.critical }}>STOCKOUT</div>
            </div>
            <div style={{ color: tokens.colors.text.muted }}>➔</div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: tokens.colors.status.highRisk, fontWeight: 700 }}>FP-05</div>
              <div style={{ fontSize: '8.5px', color: tokens.colors.status.highRisk }}>ISOLATED</div>
            </div>
          </div>
        </div>

        {/* Operational Early Warnings List (Section 14: Clean Timeline List) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, overflowY: 'auto' }}>
          <div
            style={{
              fontSize: '11px',
              color: tokens.colors.text.muted,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              fontWeight: 600,
              marginBottom: '6px',
            }}
          >
            Early Warnings ({criticalAlerts.length})
          </div>

          {isLoading ? (
            <div style={{ color: tokens.colors.text.muted, fontSize: '11px', textAlign: 'center', padding: '12px' }}>
              Loading telemetry alerts...
            </div>
          ) : criticalAlerts.length === 0 ? (
            <div
              style={{
                color: tokens.colors.status.healthy,
                fontSize: '11px',
                textAlign: 'center',
                padding: '12px',
                backgroundColor: tokens.colors.status.healthySoft,
                borderRadius: tokens.radii.card,
                border: `1px solid ${tokens.colors.status.healthyBorder}`,
              }}
            >
              ✓ No critical stockout alerts active in the sector.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {criticalAlerts.map((alert, idx) => {
                const isSelected =
                  selectedNodeId === alert.node_id || selectedNodeId === alert.node_code;
                const dotColor =
                  alert.severity === 'CRITICAL'
                    ? tokens.colors.status.critical
                    : alert.severity === 'HIGH'
                    ? tokens.colors.status.highRisk
                    : tokens.colors.status.warning;

                return (
                  <div
                    key={alert.alert_id}
                    onClick={() => onSelectNode(alert.node_id || alert.node_code)}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '10px',
                      padding: '8px 6px',
                      borderBottom: idx < criticalAlerts.length - 1 ? `1px solid ${tokens.colors.border.subtle}` : 'none',
                      backgroundColor: isSelected ? tokens.colors.background.elevated : 'transparent',
                      borderRadius: tokens.radii.badge,
                      cursor: 'pointer',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    {/* Semantic Status Dot */}
                    <span
                      style={{
                        color: dotColor,
                        fontSize: '11px',
                        lineHeight: '16px',
                        userSelect: 'none',
                      }}
                    >
                      ●
                    </span>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontSize: '12px', fontWeight: 600, color: tokens.colors.text.primary }}>
                            {alert.node_code}
                          </span>
                          <span style={{ fontSize: '11px', color: tokens.colors.text.secondary }}>
                            {alert.item}
                          </span>
                        </div>
                        <span
                          className={`badge ${
                            alert.severity === 'CRITICAL'
                              ? 'badge-critical'
                              : alert.severity === 'HIGH'
                              ? 'badge-high'
                              : 'badge-warning'
                          }`}
                          style={{ fontSize: '9px', padding: '1px 5px' }}
                        >
                          {alert.severity}
                        </span>
                      </div>

                      <div style={{ fontSize: '11.5px', color: tokens.colors.text.secondary, lineHeight: 1.35, marginBottom: '3px' }}>
                        {alert.explanation}
                      </div>

                      <div style={{ fontSize: '10.5px', color: tokens.colors.text.muted, display: 'flex', gap: '8px' }}>
                        <span>+{alert.time_horizon_hours}h forecast</span>
                        <span>•</span>
                        <span>{(alert.probability * 100).toFixed(0)}% prob</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskPanel;
