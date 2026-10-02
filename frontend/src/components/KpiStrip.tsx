import React from 'react';

interface KpiStripProps {
  totalNodes: number | null;
  totalRoutes: number | null;
  totalVehicles: number | null;
  highRiskNodesCount: number | null;
  activeRecommendationsCount: number | null;
  isLoading?: boolean;
}

export const KpiStrip: React.FC<KpiStripProps> = ({
  totalNodes,
  totalRoutes,
  totalVehicles,
  highRiskNodesCount,
  activeRecommendationsCount,
  isLoading = false,
}) => {
  const cards = [
    {
      label: 'NODES',
      code: 'ECHELON-GRID',
      value: totalNodes !== null ? totalNodes : 'Unavailable',
      color: '#38bdf8',
      desc: '1 Depot / 3 Hubs / 5 Transit / 6 Posts',
      indicatorColor: '#0284c7',
    },
    {
      label: 'ROUTES',
      code: 'TERRAIN-PASSES',
      value: totalRoutes !== null ? totalRoutes : 'Unavailable',
      color: '#e2e8f0',
      desc: 'Highways, Alpine Passes, Trails',
      indicatorColor: '#64748b',
    },
    {
      label: 'VEHICLES',
      code: 'FLEET-TELEMETRY',
      value: totalVehicles !== null ? totalVehicles : 'Unavailable',
      color: '#e2e8f0',
      desc: 'Heavy, Medium, All-Terrain Fleets',
      indicatorColor: '#64748b',
    },
    {
      label: 'HIGH-RISK NODES',
      code: 'CRITICAL-STOCKOUT',
      value: highRiskNodesCount !== null ? highRiskNodesCount : 'Unavailable',
      color: highRiskNodesCount && highRiskNodesCount > 0 ? '#ef4444' : '#10b981',
      desc: 'Nodes with overall risk ≥ 0.35',
      indicatorColor: highRiskNodesCount && highRiskNodesCount > 0 ? '#ef4444' : '#10b981',
    },
    {
      label: 'ACTIVE RECOMMENDATIONS',
      code: 'DECISION-SUPPORT',
      value: activeRecommendationsCount !== null ? activeRecommendationsCount : 'Unavailable',
      color: '#10b981',
      desc: 'Conflict-free prioritized actions',
      indicatorColor: '#10b981',
    },
  ];

  return (
    <div className="kpi-strip" role="region" aria-label="Key Performance Indicators">
      {cards.map((card, idx) => (
        <div key={idx} className="kpi-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="kpi-label">{card.label}</div>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '9px',
                color: 'var(--text-dim)',
                letterSpacing: '0.04em',
              }}
            >
              {card.code}
            </span>
          </div>

          <div
            className="kpi-value"
            style={{
              color: card.color,
              textShadow: card.color === '#ef4444' ? '0 0 12px rgba(239, 68, 68, 0.4)' : undefined,
            }}
          >
            {isLoading ? '...' : card.value}
          </div>

          <div
            style={{
              fontSize: '10px',
              color: 'var(--text-muted)',
              marginTop: '2px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {card.desc}
          </div>

          {/* Micro Progress Bar / Activity Indicator */}
          <div
            style={{
              marginTop: '6px',
              height: '2px',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '1px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: '60%',
                backgroundColor: card.indicatorColor,
                opacity: 0.8,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};
