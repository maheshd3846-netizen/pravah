import React, { useState } from 'react';

interface DemoTourProps {
  onStepChange: (stepIndex: number) => void;
  onClose: () => void;
}

export const DemoTour: React.FC<DemoTourProps> = ({ onStepChange, onClose }) => {
  const [currentStep, setCurrentStep] = useState<number>(0);

  const steps = [
    {
      title: '1. NORMAL LOGISTICS TOPOLOGY',
      desc: 'Inspect the 15-node synthetic Northern Sector logistics grid. Base depot CD-01 connects through 3 regional hubs to 6 forward combat outposts across 28 multi-terrain corridors.',
      action: 'VIEW GRID',
    },
    {
      title: '2. TRIGGER COMPOUND DISRUPTION',
      desc: 'Simulate high-altitude operational disruptions: Primary corridor R-01/R-22 blocked by landslide, +30% combat demand surge, severe alpine blizzard, and -20% fleet reduction.',
      action: 'INJECT DISRUPTIONS',
    },
    {
      title: '3. RISK INTELLIGENCE ESCALATION',
      desc: 'Watch real-time risk propagation. Multi-factor assessment alerts critical nodes facing imminent stockout (overall risk ≥ 0.35).',
      action: 'INSPECT RISKS',
    },
    {
      title: '4. DRILL INTO FORWARD OUTPOST (FP-01 / FP-04)',
      desc: 'Select forward combat post. Telemetry confirms fuel reserves depleted to critical thresholds under supply isolation.',
      action: 'INSPECT NODE',
    },
    {
      title: '5. PROBABILISTIC DEMAND FORECAST',
      desc: 'Observe machine learning XGBoost quantile projections. P50 median, P80 operational planning, and P95 surge stress bands quantify future consumption uncertainty.',
      action: 'VIEW FORECAST',
    },
    {
      title: '6. MONTE CARLO STOCKOUT RISK',
      desc: 'Monte Carlo simulation reveals stockout probability elevated to near 100%, and Time to Zero stockout is projected within the planning horizon.',
      action: 'VIEW OUTLOOK',
    },
    {
      title: '7. MATHEMATICAL NETWORK FLOW OPTIMIZATION',
      desc: 'The linear network flow solver executes via SciPy HiGHS. In <15ms, it solves optimal multi-commodity distribution across alternate feasible corridors.',
      action: 'OPTIMIZE DISPATCH',
    },
    {
      title: '8. BYPASS CORRIDOR IDENTIFICATION',
      desc: 'Primary route R-01 is blocked; optimizer selects alternate bypass route R-11, accepting +15km travel distance to avoid complete interdiction.',
      action: 'INSPECT ROUTE',
    },
    {
      title: '9. CLOSED-LOOP COUNTERFACTUAL SIMULATION',
      desc: 'Simulator evaluates the optimization plan against the exact baseline under identical disruption to verify real causal benefit.',
      action: 'RUN VERIFICATION',
    },
    {
      title: '10. EMPIRICAL VERIFICATION RESULT',
      desc: 'Verification proves unmet demand decreased by over 70%, stockouts mitigated, while transport distance increased—a realistic operational tradeoff.',
      action: 'INSPECT DELTAS',
    },
    {
      title: '11. AUDITABLE DECISION RECOMMENDATION',
      desc: 'Decision Engine produces REALLOCATE recommendation with assigned convoy vehicle, departure window, and verified delivery volume.',
      action: 'VIEW RECOMMENDATION',
    },
    {
      title: '12. DETERMINISTIC FACT-GROUNDED EXPLANATION',
      desc: 'Every recommendation provides structured bulleted evidence and full causal lineage from sensor disruption to verified dispatch.',
      action: 'FINISH TOUR',
    },
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      const next = currentStep + 1;
      setCurrentStep(next);
      onStepChange(next);
    } else {
      onClose();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      const prev = currentStep - 1;
      setCurrentStep(prev);
      onStepChange(prev);
    }
  };

  const step = steps[currentStep];

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '560px',
        backgroundColor: '#0c1322',
        border: '1px solid #38bdf8',
        borderRadius: '8px',
        padding: '16px 20px',
        boxShadow: 'var(--shadow-lg), 0 0 25px rgba(56, 189, 248, 0.2)',
        zIndex: 200,
        backdropFilter: 'blur(10px)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-cyan" style={{ fontSize: '9px' }}>
            DEMO MODE (STEP {currentStep + 1} OF {steps.length})
          </span>
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#f8fafc' }}>
            {step.title}
          </span>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '13px' }}
        >
          ✕
        </button>
      </div>

      <div style={{ fontSize: '11px', color: '#cbd5e1', lineHeight: 1.5, marginBottom: '12px' }}>
        {step.desc}
      </div>

      {/* Progress Bar */}
      <div style={{ height: '3px', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '2px', overflow: 'hidden', marginBottom: '12px' }}>
        <div
          style={{
            height: '100%',
            width: `${((currentStep + 1) / steps.length) * 100}%`,
            backgroundColor: '#38bdf8',
            transition: 'width 0.2s ease',
          }}
        />
      </div>

      {/* Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          onClick={handlePrev}
          disabled={currentStep === 0}
          className="btn btn-secondary"
          style={{ padding: '4px 10px', fontSize: '10px' }}
        >
          ◀ PREVIOUS
        </button>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => onStepChange(currentStep)}
            className="btn btn-secondary"
            style={{ padding: '4px 10px', fontSize: '10px', color: '#38bdf8', borderColor: '#38bdf8' }}
          >
            {step.action}
          </button>
          <button
            onClick={handleNext}
            className="btn btn-primary"
            style={{ padding: '4px 12px', fontSize: '10px' }}
          >
            {currentStep === steps.length - 1 ? 'COMPLETE' : 'NEXT STEP ▶'}
          </button>
        </div>
      </div>
    </div>
  );
};
