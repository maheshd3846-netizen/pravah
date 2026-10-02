import React from 'react';

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

  const stages: { id: PipelineStage; label: string; desc: string }[] = [
    {
      id: 'DEMAND',
      label: 'Analyzing Demand & Quantile Uncertainty...',
      desc: 'Executing XGBoost quantile inference across P50, P80, and P95 planning horizons.',
    },
    {
      id: 'RISK',
      label: 'Assessing Multi-Factor Sector Risk...',
      desc: 'Running Monte Carlo stockout simulations and network-wide risk propagation.',
    },
    {
      id: 'OPTIMIZE',
      label: 'Optimizing Supply Allocation & Routing...',
      desc: 'Solving multi-commodity linear network flow via SciPy HiGHS solver.',
    },
    {
      id: 'COUNTERFACTUAL',
      label: 'Running Closed-Loop Counterfactual Simulation...',
      desc: 'Simulating baseline vs. intervention outcomes under identical disruption conditions.',
    },
    {
      id: 'RECOMMEND',
      label: 'Synthesizing Auditable Decision Recommendations...',
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
        backgroundColor: 'rgba(5, 8, 15, 0.85)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 300,
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
      }}
    >
      <div
        style={{
          width: '540px',
          backgroundColor: 'rgba(11, 18, 32, 0.96)',
          border: '1px solid rgba(0, 229, 255, 0.45)',
          borderRadius: '8px',
          padding: '24px',
          boxShadow: 'var(--shadow-lg), 0 0 40px rgba(0, 229, 255, 0.2)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="pulse-indicator" style={{ backgroundColor: isComplete ? '#10b981' : '#00e5ff' }} />
            <span
              style={{
                fontSize: '14px',
                fontWeight: 800,
                color: '#f8fafc',
                letterSpacing: '0.06em',
                fontFamily: 'var(--font-heading)',
              }}
            >
              {isComplete ? 'NETWORK ANALYSIS COMPLETE' : 'PRAVAH INTELLIGENCE PIPELINE'}
            </span>
          </div>
          {isComplete && (
            <button
              onClick={onClose}
              className="btn btn-secondary"
              style={{ padding: '3px 9px', fontSize: '10px' }}
            >
              ✕ CLOSE
            </button>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '22px' }}>
          {stages.map((st, i) => {
            const status = getStageStatus(st.id);
            return (
              <div
                key={st.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '11px 13px',
                  borderRadius: '5px',
                  backgroundColor:
                    status === 'ACTIVE'
                      ? 'rgba(0, 229, 255, 0.08)'
                      : status === 'COMPLETED'
                      ? 'rgba(16, 185, 129, 0.06)'
                      : 'rgba(255, 255, 255, 0.02)',
                  border:
                    status === 'ACTIVE'
                      ? '1px solid rgba(0, 229, 255, 0.5)'
                      : status === 'COMPLETED'
                      ? '1px solid rgba(16, 185, 129, 0.35)'
                      : '1px solid rgba(255, 255, 255, 0.06)',
                  boxShadow: status === 'ACTIVE' ? '0 0 12px rgba(0, 229, 255, 0.15)' : undefined,
                }}
              >
                <div
                  style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    flexShrink: 0,
                    backgroundColor:
                      status === 'COMPLETED'
                        ? '#10b981'
                        : status === 'ACTIVE'
                        ? '#00e5ff'
                        : '#1e293b',
                    color: status === 'PENDING' ? '#64748b' : '#070b13',
                  }}
                >
                  {status === 'COMPLETED' ? '✓' : i + 1}
                </div>
                <div>
                  <div
                    style={{
                      fontSize: '11.5px',
                      fontWeight: 700,
                      color: status === 'ACTIVE' ? '#00e5ff' : status === 'COMPLETED' ? '#10b981' : '#64748b',
                      fontFamily: 'var(--font-heading)',
                      letterSpacing: '0.04em',
                    }}
                  >
                    {st.label}
                  </div>
                  <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '2px', lineHeight: 1.4 }}>
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
            style={{ width: '100%', padding: '10px', fontSize: '12px' }}
          >
            VIEW COMMAND CENTER RESULTS ➔
          </button>
        )}
      </div>
    </div>
  );
};
