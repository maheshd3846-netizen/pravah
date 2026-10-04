import React from 'react';
import { tokens } from '../tokens';

export type PipelineStage =
  | 'IDLE'
  | 'DEMAND'
  | 'RISK'
  | 'OPTIMIZE'
  | 'COUNTERFACTUAL'
  | 'RECOMMEND'
  | 'COMPLETE';

interface AnalyzeModalProps {
  isOpen: boolean;
  currentStage: PipelineStage;
  onClose: () => void;
}

export const AnalyzeModal: React.FC<AnalyzeModalProps> = ({
  isOpen,
  currentStage,
  onClose,
}) => {
  if (!isOpen) return null;

  const stages: { id: PipelineStage; name: string; label: string; desc: string }[] = [
    {
      id: 'DEMAND',
      name: 'Predict',
      label: 'Demand & Quantile Uncertainty Inference',
      desc: 'Executing XGBoost quantile inference across P50, P80, and P95 planning horizons.',
    },
    {
      id: 'RISK',
      name: 'Risk',
      label: 'Multi-Factor Sector Risk Assessment',
      desc: 'Running Monte Carlo stockout simulations and network-wide risk propagation.',
    },
    {
      id: 'OPTIMIZE',
      name: 'Optimize',
      label: 'Optimizing Supply Allocation & Routing',
      desc: 'Solving continuous multi-commodity linear network flow via SciPy HiGHS solver.',
    },
    {
      id: 'COUNTERFACTUAL',
      name: 'Verify',
      label: 'Closed-Loop Counterfactual Simulation',
      desc: 'Simulating baseline vs. intervention outcomes under identical disruption conditions.',
    },
    {
      id: 'RECOMMEND',
      name: 'Decide',
      label: 'Synthesizing Auditable Decision Recommendations',
      desc: 'Detecting fleet/route conflicts and assembling fact-grounded explanations.',
    },
  ];

  const getStageStatus = (stageId: PipelineStage) => {
    const order: PipelineStage[] = ['DEMAND', 'RISK', 'OPTIMIZE', 'COUNTERFACTUAL', 'RECOMMEND', 'COMPLETE'];
    const currentIdx = order.indexOf(currentStage);
    const stageIdx = order.indexOf(stageId);

    if (currentIdx > stageIdx) return 'COMPLETED';
    if (currentIdx === stageIdx) return 'ACTIVE';
    return 'PENDING';
  };

  const isComplete = currentStage === 'COMPLETE';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(7, 17, 31, 0.82)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 300,
        backdropFilter: 'blur(6px)',
      }}
    >
      <div
        style={{
          width: '520px',
          backgroundColor: tokens.colors.background.elevated,
          border: `1px solid ${tokens.colors.border.default}`,
          borderRadius: tokens.radii.container,
          padding: '20px',
          boxShadow: '0 12px 32px rgba(0, 0, 0, 0.6)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="pulse-indicator" style={{ backgroundColor: isComplete ? tokens.colors.status.healthy : tokens.colors.brand.primary }} />
            <span
              style={{
                fontSize: '13.5px',
                fontWeight: 700,
                color: tokens.colors.text.primary,
                letterSpacing: '0.02em',
                fontFamily: tokens.typography.fontSans,
              }}
            >
              {isComplete ? 'Network Analysis Complete' : 'Analyzing Network'}
            </span>
            <span style={{ display: 'none' }}>PRAVAH INTELLIGENCE PIPELINE</span>
          </div>
          {isComplete && (
            <button
              onClick={onClose}
              className="btn btn-secondary"
              style={{ padding: '2px 8px', fontSize: '10px' }}
            >
              ✕ Close
            </button>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '18px' }}>
          {stages.map((st) => {
            const status = getStageStatus(st.id);
            return (
              <div
                key={st.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: tokens.radii.card,
                  backgroundColor:
                    status === 'ACTIVE'
                      ? tokens.colors.brand.primarySoft
                      : status === 'COMPLETED'
                      ? tokens.colors.status.healthySoft
                      : tokens.colors.background.secondary,
                  border: `1px solid ${
                    status === 'ACTIVE'
                      ? tokens.colors.brand.primaryBorder
                      : status === 'COMPLETED'
                      ? tokens.colors.status.healthyBorder
                      : tokens.colors.border.subtle
                  }`,
                }}
              >
                <div
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    fontWeight: 700,
                    flexShrink: 0,
                    backgroundColor:
                      status === 'COMPLETED'
                        ? tokens.colors.status.healthy
                        : status === 'ACTIVE'
                        ? tokens.colors.brand.primary
                        : 'transparent',
                    color: status === 'PENDING' ? tokens.colors.text.muted : '#07111F',
                    border: status === 'PENDING' ? `1px solid ${tokens.colors.border.default}` : 'none',
                  }}
                >
                  {status === 'COMPLETED' ? '✓' : status === 'ACTIVE' ? '●' : '○'}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        fontSize: '12px',
                        fontWeight: 700,
                        color:
                          status === 'ACTIVE'
                            ? tokens.colors.brand.primary
                            : status === 'COMPLETED'
                            ? tokens.colors.status.healthy
                            : tokens.colors.text.primary,
                      }}
                    >
                      {st.name}
                    </span>
                    <span style={{ fontSize: '11px', color: tokens.colors.text.muted }}>•</span>
                    <span style={{ fontSize: '11.5px', color: tokens.colors.text.secondary }}>
                      {st.label}
                    </span>
                  </div>
                  <div style={{ fontSize: '10px', color: tokens.colors.text.muted, marginTop: '2px', lineHeight: 1.35 }}>
                    {st.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {isComplete && (
          <button
            onClick={onClose}
            className="btn btn-primary"
            style={{ width: '100%', padding: '8px', fontSize: '11px' }}
          >
            VIEW COMMAND CENTER RESULTS ➔
          </button>
        )}
      </div>
    </div>
  );
};

export default AnalyzeModal;
