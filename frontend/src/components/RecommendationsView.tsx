import React, { useState } from 'react';
import type { RecommendationItem } from '../types';
import { tokens } from '../tokens';

interface RecommendationsViewProps {
  recommendations: RecommendationItem[];
  onSelectRecommendation: (rec: RecommendationItem) => void;
  selectedRecommendationId?: string | null;
  rejectionSummary?: string | null;
}

export const RecommendationsView: React.FC<RecommendationsViewProps> = ({
  recommendations,
  onSelectRecommendation,
  selectedRecommendationId,
  rejectionSummary,
}) => {
  const [filterAction, setFilterAction] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [filterItem, setFilterItem] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const totalCandidates = recommendations.length;
  const verifiedCount = recommendations.filter((r) => r.status === 'VERIFIED').length;
  const mixedCount = recommendations.filter((r) => r.status === 'MIXED').length;
  const rejectedCount = recommendations.filter((r) => r.status === 'REJECTED').length;
  const feasibleCount = verifiedCount + mixedCount;

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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
        return 'badge-healthy';
      case 'MIXED':
        return 'badge-warning';
      case 'DEGRADED':
        return 'badge-warning';
      case 'REJECTED':
        return 'badge-critical';
      case 'PROPOSED':
        return 'badge-neutral';
      default:
        return 'badge-neutral';
    }
  };

  const selectedRec = recommendations.find((r) => r.recommendation_id === selectedRecommendationId);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedRec ? '1.8fr 1.2fr' : '1fr', gap: '14px', height: '100%' }}>
      {/* Table Section */}
      <div className="card-panel" style={{ height: '100%' }}>
        <div className="panel-header">
          <div className="panel-title">
            <span style={{ color: tokens.colors.brand.primary }}>📋</span> ALL TACTICAL LOGISTICS RECOMMENDATIONS ({filtered.length} / {recommendations.length})
          </div>

          {/* Filter Bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <input
              type="text"
              placeholder="Search node, route, vehicle..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                backgroundColor: tokens.colors.background.app,
                color: tokens.colors.text.primary,
                border: `1px solid ${tokens.colors.border.default}`,
                borderRadius: tokens.radii.button,
                padding: '4px 8px',
                fontSize: '11px',
                width: '180px',
                outline: 'none',
              }}
            />

            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              style={{
                backgroundColor: tokens.colors.background.app,
                color: tokens.colors.text.primary,
                border: `1px solid ${tokens.colors.border.default}`,
                borderRadius: tokens.radii.button,
                padding: '4px 6px',
                fontSize: '10.5px',
                outline: 'none',
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
                backgroundColor: tokens.colors.background.app,
                color: tokens.colors.text.primary,
                border: `1px solid ${tokens.colors.border.default}`,
                borderRadius: tokens.radii.button,
                padding: '4px 6px',
                fontSize: '10.5px',
                outline: 'none',
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
                backgroundColor: tokens.colors.background.app,
                color: tokens.colors.text.primary,
                border: `1px solid ${tokens.colors.border.default}`,
                borderRadius: tokens.radii.button,
                padding: '4px 6px',
                fontSize: '10.5px',
                outline: 'none',
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
          {/* Feasibility Pipeline Status Strip (Section 14) */}
          <div
            style={{
              padding: '7px 12px',
              backgroundColor: tokens.colors.background.secondary,
              borderBottom: `1px solid ${tokens.colors.border.subtle}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '10.5px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: tokens.colors.text.muted, fontWeight: 600 }}>PIPELINE:</span>
              <span className="font-mono" style={{ color: tokens.colors.brand.primary, fontWeight: 700 }}>
                {totalCandidates} CANDIDATES
              </span>
              <span style={{ color: tokens.colors.text.muted }}>➔</span>
              <span style={{ color: tokens.colors.text.secondary }}>PHYSICAL VALIDATION</span>
              <span style={{ color: tokens.colors.text.muted }}>➔</span>
              <span style={{ color: tokens.colors.text.secondary }}>COUNTERFACTUAL EVALUATION</span>
              <span style={{ color: tokens.colors.text.muted }}>➔</span>
              <span className="font-mono" style={{ color: feasibleCount > 0 ? tokens.colors.status.healthy : tokens.colors.status.warning, fontWeight: 700 }}>
                {feasibleCount} FEASIBLE / VERIFIED
              </span>
              {rejectedCount > 0 && (
                <span className="font-mono" style={{ color: tokens.colors.status.critical, fontWeight: 600 }}>
                  ({rejectedCount} REJECTED)
                </span>
              )}
            </div>

            <div style={{ fontSize: '9.5px', color: tokens.colors.text.muted }}>
              Deterministic safety gating prevents unfeasible dispatches
            </div>
          </div>

          {/* All Recommendations Rejected Safe Suppression Message (Section 14) */}
          {recommendations.length > 0 && feasibleCount === 0 && (
            <div
              style={{
                margin: '12px',
                padding: '12px 14px',
                backgroundColor: tokens.colors.background.secondary,
                border: `1px solid ${tokens.colors.status.warningBorder}`,
                borderRadius: tokens.radii.card,
                fontSize: '11px',
              }}
            >
              <div style={{ fontWeight: 800, color: tokens.colors.status.warning, textTransform: 'uppercase', marginBottom: '3px' }}>
                NO VERIFIED ACTIONS
              </div>
              <div style={{ color: tokens.colors.text.primary, marginBottom: '4px' }}>
                PRAVAH SUPPRESSED THE GENERATED ACTIONS BECAUSE THE COUNTERFACTUAL SIMULATION SHOWED DEGRADATION.
              </div>
              <div style={{ color: tokens.colors.text.muted, fontSize: '10px' }}>
                Reason: Operating conditions changed after the original optimization state. This is an intentional safety decision.
              </div>
            </div>
          )}

          {/* Rejection Summary Banner */}
          {rejectionSummary && (
            <div
              style={{
                margin: '8px 12px',
                padding: '8px 12px',
                backgroundColor: tokens.colors.background.secondary,
                borderLeft: `3px solid ${tokens.colors.brand.primary}`,
                borderRadius: '0 4px 4px 0',
                fontSize: '10.5px',
                lineHeight: 1.45,
                color: tokens.colors.text.secondary,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                <span style={{ color: tokens.colors.brand.primary, fontWeight: 700, fontSize: '9.5px', textTransform: 'uppercase' }}>
                  🛡 FEASIBILITY & COUNTERFACTUAL VERIFICATION AUDIT
                </span>
              </div>
              <div>{rejectionSummary}</div>
            </div>
          )}

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: tokens.colors.background.secondary, color: tokens.colors.text.muted, borderBottom: `1px solid ${tokens.colors.border.subtle}` }}>
                <th style={{ padding: '7px 12px' }}>PRIORITY</th>
                <th style={{ padding: '7px 12px' }}>ACTION</th>
                <th style={{ padding: '7px 12px' }}>DESTINATION</th>
                <th style={{ padding: '7px 12px' }}>SOURCE</th>
                <th style={{ padding: '7px 12px' }}>ITEM</th>
                <th style={{ padding: '7px 12px', textAlign: 'right' }}>QUANTITY</th>
                <th style={{ padding: '7px 12px' }}>ROUTE</th>
                <th style={{ padding: '7px 12px' }}>STATUS</th>
                <th style={{ padding: '7px 12px' }}>CONFIDENCE</th>
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
                      borderBottom: `1px solid ${tokens.colors.border.subtle}`,
                      backgroundColor: isSelected ? tokens.colors.brand.primarySoft : 'transparent',
                      cursor: 'pointer',
                      transition: 'background-color 0.1s ease',
                    }}
                  >
                    <td style={{ padding: '7px 12px' }}>
                      <span className="font-mono" style={{ fontWeight: 700, color: r.priority === 1 ? tokens.colors.status.critical : tokens.colors.status.warning }}>
                        P{r.priority}
                      </span>
                    </td>
                    <td style={{ padding: '7px 12px', fontWeight: 700, color: tokens.colors.text.primary }}>
                      {r.action_type}
                    </td>
                    <td className="font-mono" style={{ padding: '7px 12px', color: tokens.colors.brand.primary }}>
                      {r.destination_node}
                    </td>
                    <td className="font-mono" style={{ padding: '7px 12px', color: tokens.colors.text.muted }}>
                      {r.source_node}
                    </td>
                    <td style={{ padding: '7px 12px' }}>
                      <span className="badge badge-neutral" style={{ fontSize: '8.5px' }}>
                        {r.item}
                      </span>
                    </td>
                    <td className="font-mono" style={{ padding: '7px 12px', textAlign: 'right', fontWeight: 700 }}>
                      {r.quantity.toFixed(0)} u
                    </td>
                    <td className="font-mono" style={{ padding: '7px 12px', color: tokens.colors.text.secondary }}>
                      {r.route}
                    </td>
                    <td style={{ padding: '7px 12px' }}>
                      <span className={`badge ${getStatusBadge(r.status)}`} style={{ fontSize: '8.5px' }}>
                        {r.status}
                      </span>
                    </td>
                    <td style={{ padding: '7px 12px' }}>
                      <span
                        className={`badge ${
                          r.confidence.level === 'HIGH' ? 'badge-healthy' : 'badge-warning'
                        }`}
                        style={{ fontSize: '8.5px' }}
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
              <span style={{ color: tokens.colors.brand.primary }}>🔍</span> RECOMMENDATION PROVENANCE & AUDIT
            </div>
            <span className={`badge ${getStatusBadge(selectedRec.status)}`}>
              {selectedRec.status}
            </span>
          </div>

          <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div>
              <div style={{ fontSize: '9.5px', color: tokens.colors.text.muted }}>RECOMMENDATION ID</div>
              <div className="font-mono" style={{ fontSize: '13px', color: tokens.colors.brand.primary, fontWeight: 700 }}>
                {selectedRec.recommendation_id}
              </div>
            </div>

            <div style={{ backgroundColor: tokens.colors.background.secondary, padding: '8px 10px', borderRadius: tokens.radii.badge, border: `1px solid ${tokens.colors.border.subtle}` }}>
              <div style={{ fontSize: '9.5px', color: tokens.colors.text.muted, textTransform: 'uppercase', marginBottom: '2px', fontWeight: 600 }}>
                WHY (DETERMINISTIC RATIONALE)
              </div>
              <div style={{ fontSize: '10.5px', color: tokens.colors.text.secondary, lineHeight: 1.45 }}>
                {selectedRec.reason}
              </div>
            </div>

            {/* Rejection Diagnostics if Rejected */}
            {selectedRec.status === 'REJECTED' && (
              <div
                style={{
                  backgroundColor: tokens.colors.status.criticalSoft,
                  padding: '8px 10px',
                  borderRadius: tokens.radii.badge,
                  border: `1px solid ${tokens.colors.status.criticalBorder}`,
                }}
              >
                <div style={{ fontSize: '9.5px', color: tokens.colors.status.critical, textTransform: 'uppercase', fontWeight: 700, marginBottom: '2px' }}>
                  REJECTION REASON & CONFLICT DETAILS
                </div>
                <div style={{ fontSize: '10.5px', color: '#fca5a5', lineHeight: 1.45 }}>
                  {selectedRec.conflict_details && selectedRec.conflict_details.length > 0
                    ? selectedRec.conflict_details.join('; ')
                    : 'Counterfactual simulation determined this candidate worsens logistics outcomes vs baseline under active disruption.'}
                </div>
              </div>
            )}

            {/* Traceability Audit Trail */}
            <div>
              <div style={{ fontSize: '9.5px', color: tokens.colors.text.muted, textTransform: 'uppercase', marginBottom: '4px', fontWeight: 600 }}>
                PROVENANCE AUDIT TRAIL
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', fontSize: '9.5px' }}>
                {selectedRec.audit_trail && Object.entries(selectedRec.audit_trail).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 6px', backgroundColor: tokens.colors.background.secondary, borderRadius: '2px' }}>
                    <span style={{ color: tokens.colors.text.muted }}>{k}:</span>
                    <span className="font-mono" style={{ color: tokens.colors.text.secondary }}>
                      {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Evidence Checklist */}
            <div>
              <div style={{ fontSize: '9.5px', color: tokens.colors.text.muted, textTransform: 'uppercase', marginBottom: '4px', fontWeight: 600 }}>
                STRUCTURED EVIDENCE LIST
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                {(selectedRec.evidence || []).map((ev, idx) => (
                  <div key={idx} style={{ padding: '5px 8px', backgroundColor: tokens.colors.background.secondary, borderRadius: tokens.radii.badge, border: `1px solid ${tokens.colors.border.subtle}`, fontSize: '9.5px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, color: tokens.colors.brand.primary }}>
                      <span>{ev.type}</span>
                      <span className="font-mono">{typeof ev.value === 'object' ? JSON.stringify(ev.value) : String(ev.value)}</span>
                    </div>
                    <div style={{ color: tokens.colors.text.muted, marginTop: '1px' }}>
                      {typeof ev.details === 'string'
                        ? ev.details
                        : (ev.description || (ev.details ? JSON.stringify(ev.details) : ''))} (Source: {ev.source})
                    </div>
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

export default RecommendationsView;
