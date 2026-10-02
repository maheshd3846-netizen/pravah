import React, { useState } from 'react';
import type { RecommendationItem, RecommendationStatus } from '../types';

interface RecommendationsViewProps {
  recommendations: RecommendationItem[];
  onSelectRecommendation: (rec: RecommendationItem) => void;
  selectedRecommendationId?: string | null;
}

export const RecommendationsView: React.FC<RecommendationsViewProps> = ({
  recommendations,
  onSelectRecommendation,
  selectedRecommendationId,
}) => {
  const [filterAction, setFilterAction] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [filterItem, setFilterItem] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filtered = recommendations.filter((r) => {
    if (filterAction !== 'ALL' && r.action_type !== filterAction) return false;
    if (filterStatus !== 'ALL' && r.status !== filterStatus) return false;
    if (filterItem !== 'ALL' && r.item !== filterItem) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const match =
        r.destination_node.toLowerCase().includes(term) ||
        r.source_node.toLowerCase().includes(term) ||
        r.route.toLowerCase().includes(term) ||
        r.vehicle.toLowerCase().includes(term) ||
        r.recommendation_id.toLowerCase().includes(term);
      if (!match) return false;
    }
    return true;
  });

  const getStatusBadge = (status: RecommendationStatus) => {
    switch (status) {
      case 'VERIFIED':
        return 'badge-verified';
      case 'MIXED':
        return 'badge-mixed';
      case 'REJECTED':
        return 'badge-rejected';
      case 'PROPOSED':
        return 'badge-proposed';
      default:
        return 'badge-inconclusive';
    }
  };

  const selectedRec = recommendations.find((r) => r.recommendation_id === selectedRecommendationId);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedRec ? '1.8fr 1.2fr' : '1fr', gap: '14px', height: '100%' }}>
      {/* Table Section */}
      <div className="card-panel" style={{ height: '100%' }}>
        <div className="panel-header">
          <div className="panel-title">
            <span>📋</span> ALL TACTICAL LOGISTICS RECOMMENDATIONS ({filtered.length} / {recommendations.length})
          </div>

          {/* Filter Bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="text"
              placeholder="Search node, route, vehicle..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                color: '#f8fafc',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '11px',
                width: '180px',
              }}
            />

            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                color: '#f8fafc',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '11px',
              }}
            >
              <option value="ALL">All Actions</option>
              <option value="MOVE">MOVE</option>
              <option value="REROUTE">REROUTE</option>
              <option value="REALLOCATE">REALLOCATE</option>
              <option value="PRIORITIZE">PRIORITIZE</option>
              <option value="HOLD">HOLD</option>
              <option value="DEFER">DEFER</option>
            </select>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                color: '#f8fafc',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '11px',
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="VERIFIED">VERIFIED</option>
              <option value="MIXED">MIXED</option>
              <option value="PROPOSED">PROPOSED</option>
              <option value="REJECTED">REJECTED</option>
            </select>

            <select
              value={filterItem}
              onChange={(e) => setFilterItem(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                color: '#f8fafc',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '11px',
              }}
            >
              <option value="ALL">All Items</option>
              <option value="FUEL">FUEL</option>
              <option value="RATIONS">RATIONS</option>
              <option value="AMMUNITION">AMMUNITION</option>
              <option value="MEDICAL">MEDICAL</option>
              <option value="WATER">WATER</option>
            </select>
          </div>
        </div>

        <div className="panel-body" style={{ padding: 0 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.04)', color: '#94a3b8', borderBottom: '1px solid var(--border-subtle)' }}>
                <th style={{ padding: '8px 12px' }}>PRIORITY</th>
                <th style={{ padding: '8px 12px' }}>ACTION</th>
                <th style={{ padding: '8px 12px' }}>DESTINATION</th>
                <th style={{ padding: '8px 12px' }}>SOURCE</th>
                <th style={{ padding: '8px 12px' }}>ITEM</th>
                <th style={{ padding: '8px 12px', textAlign: 'right' }}>QUANTITY</th>
                <th style={{ padding: '8px 12px' }}>ROUTE</th>
                <th style={{ padding: '8px 12px' }}>STATUS</th>
                <th style={{ padding: '8px 12px' }}>CONFIDENCE</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const isSelected = selectedRecommendationId === r.recommendation_id;
                return (
                  <tr
                    key={r.recommendation_id}
                    onClick={() => onSelectRecommendation(r)}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      backgroundColor: isSelected ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                      cursor: 'pointer',
                      transition: 'background-color 0.1s ease',
                    }}
                  >
                    <td style={{ padding: '8px 12px' }}>
                      <span className="font-mono" style={{ fontWeight: 700, color: r.priority === 1 ? '#ef4444' : '#f59e0b' }}>
                        P{r.priority}
                      </span>
                    </td>
                    <td style={{ padding: '8px 12px', fontWeight: 700, color: '#f8fafc' }}>
                      {r.action_type}
                    </td>
                    <td className="font-mono" style={{ padding: '8px 12px', color: '#38bdf8' }}>
                      {r.destination_node}
                    </td>
                    <td className="font-mono" style={{ padding: '8px 12px', color: '#94a3b8' }}>
                      {r.source_node}
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      <span className="badge badge-neutral" style={{ fontSize: '9px' }}>
                        {r.item}
                      </span>
                    </td>
                    <td className="font-mono" style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 700 }}>
                      {r.quantity.toFixed(0)} u
                    </td>
                    <td className="font-mono" style={{ padding: '8px 12px', color: '#cbd5e1' }}>
                      {r.route}
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      <span className={`badge ${getStatusBadge(r.status)}`} style={{ fontSize: '9px' }}>
                        {r.status}
                      </span>
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      <span
                        className={`badge ${
                          r.confidence.level === 'HIGH' ? 'badge-ready' : 'badge-warning'
                        }`}
                        style={{ fontSize: '9px' }}
                      >
                        {r.confidence.level}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Recommendation Detail Drawer */}
      {selectedRec && (
        <div className="card-panel" style={{ height: '100%', overflowY: 'auto' }}>
          <div className="panel-header">
            <div className="panel-title">
              <span>🔍</span> RECOMMENDATION PROVENANCE & AUDIT
            </div>
            <span className={`badge ${getStatusBadge(selectedRec.status)}`}>
              {selectedRec.status}
            </span>
          </div>

          <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <div style={{ fontSize: '10px', color: '#64748b' }}>RECOMMENDATION ID</div>
              <div className="font-mono" style={{ fontSize: '12px', color: '#38bdf8', fontWeight: 700 }}>
                {selectedRec.recommendation_id}
              </div>
            </div>

            <div style={{ backgroundColor: 'rgba(255,255,255,0.02)', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginBottom: '2px' }}>
                WHY (DETERMINISTIC RATIONALE)
              </div>
              <div style={{ fontSize: '11px', color: '#cbd5e1', lineHeight: 1.5 }}>
                {selectedRec.reason}
              </div>
            </div>

            {/* Traceability Audit Trail */}
            <div>
              <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                PROVENANCE AUDIT TRAIL
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '10px' }}>
                {Object.entries(selectedRec.audit_trail).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 6px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: '2px' }}>
                    <span style={{ color: '#94a3b8' }}>{k}:</span>
                    <span className="font-mono" style={{ color: '#cbd5e1' }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Evidence Checklist */}
            <div>
              <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                STRUCTURED EVIDENCE LIST
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {selectedRec.evidence.map((ev, idx) => (
                  <div key={idx} style={{ padding: '6px 8px', backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: '4px', border: '1px solid var(--border-subtle)', fontSize: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, color: '#38bdf8' }}>
                      <span>{ev.type}</span>
                      <span className="font-mono">{String(ev.value)}</span>
                    </div>
                    <div style={{ color: '#64748b', marginTop: '2px' }}>{ev.details} (Source: {ev.source})</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
