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
      value: totalNodes !== null ? totalNodes : 'Unavailable',
      color: '#38bdf8',
      desc: '1 Depot / 3 Hubs / 5 Transit / 6 Posts',
    },
    {
      label: 'ROUTES',
      value: totalRoutes !== null ? totalRoutes : 'Unavailable',
      color: '#cbd5e1',
      desc: 'Highways, Alpine Passes, Trails',
    },
    {
      label: 'VEHICLES',
      value: totalVehicles !== null ? totalVehicles : 'Unavailable',
      color: '#cbd5e1',
      desc: 'Heavy, Medium, All-Terrain Fleets',
    },
    {
      label: 'HIGH-RISK NODES',
      value: highRiskNodesCount !== null ? highRiskNodesCount : 'Unavailable',
      color: highRiskNodesCount && highRiskNodesCount > 0 ? '#ef4444' : '#10b981',
      desc: 'Nodes with overall risk ≥ 0.35',
    },
    {
      label: 'ACTIVE RECOMMENDATIONS',
      value: activeRecommendationsCount !== null ? activeRecommendationsCount : 'Unavailable',
      color: '#10b981',
      desc: 'Conflict-free prioritized actions',
    },
  ];

  return (
    <div className="kpi-strip" role="region" aria-label="Key Performance Indicators">
      {cards.map((card, idx) => (
        <div key={idx} className="kpi-card">
          <div className="kpi-label">{card.label}</div>
          <div className="kpi-value" style={{ color: card.color }}>
            {isLoading ? '...' : card.value}
          </div>
          <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>{card.desc}</div>
        </div>
      ))}
    </div>
  );
};
