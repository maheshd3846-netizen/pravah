import React from 'react';
import { tokens } from '../tokens';

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
  const metrics = [
    {
      label: 'Network',
      value: totalNodes !== null ? totalNodes : 'Unavailable',
      status: 'Nodes',
      subtext: '1 Depot • 3 Hubs • 6 Posts',
    },
    {
      label: 'Corridors',
      value: totalRoutes !== null ? totalRoutes : 'Unavailable',
      status: 'Active',
      subtext: 'Highways & mountain passes',
    },
    {
      label: 'Fleet',
      value: totalVehicles !== null ? totalVehicles : 'Unavailable',
      status: 'Ready',
      subtext: 'Heavy & all-terrain vehicles',
    },
    {
      label: 'Stockout',
      value: highRiskNodesCount !== null ? highRiskNodesCount : 'Unavailable',
      status: highRiskNodesCount && highRiskNodesCount > 0 ? 'At Risk' : 'Nominal',
      statusColor: highRiskNodesCount && highRiskNodesCount > 0 ? tokens.colors.status.highRisk : tokens.colors.status.healthy,
      subtext: 'Nodes near safety threshold',
    },
    {
      label: 'Decisions',
      value: activeRecommendationsCount !== null ? activeRecommendationsCount : 'Unavailable',
      status: 'Candidates',
      statusColor: tokens.colors.brand.primary,
      subtext: 'LP solved & validated',
    },
  ];

  return (
    <div className="kpi-strip" role="region" aria-label="Key Performance Indicators">
      {metrics.map((metric, idx) => (
        <div key={idx} className="kpi-metric-item">
          <div className="kpi-metric-label">{metric.label}</div>
          <div className="kpi-metric-value-row">
            <span className="kpi-metric-value">
              {isLoading ? '...' : metric.value}
            </span>
            <span
              className="kpi-metric-status"
              style={{ color: metric.statusColor || tokens.colors.text.secondary }}
            >
              {metric.status}
            </span>
          </div>
          <div
            style={{
              fontSize: '11px',
              color: tokens.colors.text.muted,
              marginTop: '2px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {metric.subtext}
          </div>
        </div>
      ))}
    </div>
  );
};

export default KpiStrip;
