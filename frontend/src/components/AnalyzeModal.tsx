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
        backdropFilter: 'blur(8px)',
      }}
    >
      <div
        style={{
          width: '520px',
          backgroundColor: '#0c1322',
          border: '1px solid #38bdf8',
          borderRadius: '8px',
          padding: '24px',
          boxShadow: 'var(--shadow-lg), 0 0 35px rgba(56, 189, 248, 0.25)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="pulse-indicator" style={{ backgroundColor: isComplete ? '#10b981' : '#38bdf8' }} />
            <span style={{ fontSize: '13px', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.04em' }}>
              {isComplete ? 'NETWORK ANALYSIS COMPLETE' : 'PRAVAH INTELLIGENCE PIPELINE'}
            </span>
          </div>
          {isComplete && (
            <button
              onClick={onClose}
              className="btn btn-secondary"
              style={{ padding: '2px 8px', fontSize: '10px' }}
            >
              ✕ CLOSE
            </button>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
          {stages.map((st, i) => {
            const status = getStageStatus(st.id);
            return (
              <div
                key={st.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '10px 12px',
                  borderRadius: '4px',
                  backgroundColor:
                    status === 'ACTIVE'
                      ? 'rgba(56, 189, 248, 0.08)'
                      : status === 'COMPLETED'
                      ? 'rgba(16, 185, 129, 0.06)'
                      : 'rgba(255, 255, 255, 0.02)',
                  border:
                    status === 'ACTIVE'
                      ? '1px solid #38bdf8'
                      : status === 'COMPLETED'
                      ? '1px solid rgba(16, 185, 129, 0.3)'
                      : '1px solid var(--border-subtle)',
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
                        ? '#38bdf8'
                        : '#1e293b',
                    color: status === 'PENDING' ? '#64748b' : '#0f172a',
                  }}
                >
                  {status === 'COMPLETED' ? '✓' : i + 1}
                </div>
                <div>
                  <div
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      color: status === 'ACTIVE' ? '#38bdf8' : status === 'COMPLETED' ? '#10b981' : '#64748b',
                    }}
                  >
                    {st.label}
                  </div>
                  <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '2px' }}>
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
            style={{ width: '100%', padding: '8px' }}
          >
            VIEW COMMAND CENTER RESULTS ➔
          </button>
        )}
      </div>
    </div>
  );
};
