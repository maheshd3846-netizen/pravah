import React from 'react';
import { tokens } from '../tokens';

export type PipelineStageKey = 'PREDICT' | 'RISK' | 'OPTIMIZE' | 'VERIFY' | 'DECIDE';

interface StageConfig {
  key: PipelineStageKey;
  label: string;
  stepNumber: string;
  subtext: string;
  tabTarget: 'FORECAST' | 'RISK' | 'OPTIMIZATION' | 'SIMULATION' | 'RECOMMENDATIONS';
}

const STAGES: StageConfig[] = [
  {
    key: 'PREDICT',
    label: 'PREDICT',
    stepNumber: '01',
    subtext: 'Quantiles P50/P80/P95',
    tabTarget: 'FORECAST',
  },
  {
    key: 'RISK',
    label: 'RISK',
    stepNumber: '02',
    subtext: '5-Dimension Assessment',
    tabTarget: 'RISK',
  },
  {
    key: 'OPTIMIZE',
    label: 'OPTIMIZE',
    stepNumber: '03',
    subtext: 'HiGHS LP + Fleet Heuristic',
    tabTarget: 'OPTIMIZATION',
  },
  {
    key: 'VERIFY',
    label: 'VERIFY',
    stepNumber: '04',
    subtext: 'Counterfactual Simulation',
    tabTarget: 'SIMULATION',
  },
  {
    key: 'DECIDE',
    label: 'DECIDE',
    stepNumber: '05',
    subtext: 'Verified Action Dispatch',
    tabTarget: 'RECOMMENDATIONS',
  },
];

interface DecisionPipelineStepperProps {
  activeStage?: PipelineStageKey;
  onStageSelect?: (stage: PipelineStageKey, tabTarget: string) => void;
}

export const DecisionPipelineStepper: React.FC<DecisionPipelineStepperProps> = ({
  activeStage = 'DECIDE',
  onStageSelect,
}) => {
  return (
    <nav
      className="decision-pipeline-stepper"
      aria-label="Decision Pipeline Stepper"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 20px',
        backgroundColor: tokens.colors.background.surface,
        borderBottom: `1px solid ${tokens.colors.border.default}`,
        flexShrink: 0,
        gap: '8px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginRight: '8px' }}>
        <span
          style={{
            fontSize: '10px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: tokens.colors.text.muted,
          }}
        >
          DECISION PIPELINE:
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', flex: 1, gap: '6px' }}>
        {STAGES.map((stage, idx) => {
          const isActive = activeStage === stage.key;
          const isPassed = STAGES.findIndex((s) => s.key === activeStage) >= idx;

          return (
            <React.Fragment key={stage.key}>
              <button
                type="button"
                onClick={() => onStageSelect?.(stage.key, stage.tabTarget)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 12px',
                  borderRadius: tokens.radii.button,
                  border: `1px solid ${
                    isActive
                      ? tokens.colors.brand.primaryBorder
                      : isPassed
                      ? tokens.colors.border.hover
                      : tokens.colors.border.subtle
                  }`,
                  backgroundColor: isActive
                    ? tokens.colors.brand.primarySoft
                    : tokens.colors.background.secondary,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  flex: 1,
                  textAlign: 'left',
                }}
              >
                <span
                  className="font-mono"
                  style={{
                    fontSize: '9.5px',
                    fontWeight: 700,
                    color: isActive ? tokens.colors.brand.primary : tokens.colors.text.muted,
                  }}
                >
                  {stage.stepNumber}
                </span>

                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: '11px',
                      fontWeight: isActive ? 700 : 600,
                      letterSpacing: '0.04em',
                      color: isActive
                        ? tokens.colors.brand.primary
                        : isPassed
                        ? tokens.colors.text.primary
                        : tokens.colors.text.secondary,
                    }}
                  >
                    {stage.label}
                  </div>
                  <div
                    style={{
                      fontSize: '9.5px',
                      color: tokens.colors.text.muted,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {stage.subtext}
                  </div>
                </div>
              </button>

              {idx < STAGES.length - 1 && (
                <span
                  style={{
                    color: isPassed ? tokens.colors.brand.primary : tokens.colors.text.muted,
                    fontSize: '11px',
                    fontWeight: 700,
                    userSelect: 'none',
                  }}
                >
                  →
                </span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </nav>
  );
};

export default DecisionPipelineStepper;
