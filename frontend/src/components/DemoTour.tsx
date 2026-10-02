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
      desc: 'Inspect the 15-node synthetic Northern Sector logistics grid. Base depot CD-01 connects through 3 regional hubs to 6 forward outposts across 28 multi-terrain corridors in a synthetic demonstration environment.',
      action: 'VIEW GRID',
    },
    {
      title: '2. TRIGGER COMPOUND DISRUPTION',
      desc: 'Simulate high-altitude operational disruptions: Primary corridor R-01/R-22 blocked by landslide, +30% forward demand surge, severe alpine blizzard, and -20% fleet reduction.',
      action: 'INJECT DISRUPTIONS',
    },
    {
      title: '3. RISK INTELLIGENCE & PROPAGATION',
      desc: 'Multi-factor risk assessment continuously monitors 5 dimensions: inventory, demand, route, transport, and environment. Propagated network risk alerts trigger before physical stockout occurs.',
      action: 'INSPECT RISKS',
    },
    {
      title: '4. DRILL INTO FORWARD OUTPOST (FP-01 / FP-04)',
      desc: 'Inspect forward post FP-01. Telemetry flags critical fuel depletion under supply corridor blockage, isolating the outpost unless alternate movements are dispatched.',
      action: 'INSPECT NODE',
    },
    {
      title: '5. UNCERTAINTY-AWARE DEMAND FORECAST',
      desc: 'Forecast Intelligence models future logistics demand across quantiles: P50 median, P80 operational planning, and P95 surge stress. Quantifies consumption uncertainty before inventory reaches zero.',
      action: 'VIEW FORECAST',
    },
    {
      title: '6. MONTE CARLO STOCKOUT RISK & TTZ',
      desc: 'Monte Carlo projection calculates stockout probability and Time to Zero (TTZ). Identifies exact operational window before critical safety stock breach, enabling proactive dispatch.',
      action: 'VIEW OUTLOOK',
    },
    {
      title: '7. CONTINUOUS MULTI-COMMODITY LP OPTIMIZATION',
      desc: 'Continuous Multi-Commodity Linear Flow LP solved using SciPy HiGHS (<15ms). Solves optimal multi-commodity movement candidates across alternate feasible corridors subject to conservation constraints.',
      action: 'OPTIMIZE DISPATCH',
    },
    {
      title: '8. PHYSICAL FLEET FEASIBILITY VALIDATION',
      desc: 'Physical validation filters mathematical LP flow candidates against physical fleet constraints. Eliminates simultaneous vehicle conflicts, ensuring only physically executable dispatches advance.',
      action: 'VALIDATE ACTIONS',
    },
    {
      title: '9. PAIRED COUNTERFACTUAL SIMULATION',
      desc: 'Closed-loop counterfactual simulation tests the intervention against the exact baseline under identical disruptions. Evaluates causal effects on unmet demand, stockouts, fulfillment, distance, and delay.',
      action: 'RUN SIMULATION',
    },
    {
      title: '10. EMPIRICAL VERIFICATION & SAFETY REJECTION',
      desc: 'Verification result: If the intervention improves outcomes, it is VERIFIED. If disruptions cause the plan to worsen service (DEGRADED), PRAVAH safely rejects it. Rejection is a trust feature, not a failure.',
      action: 'INSPECT VERDICT',
    },
    {
      title: '11. EVIDENCE-BACKED RECOMMENDATIONS',
      desc: 'Decision Center presents feasible, verified actions with assigned convoy vehicle, departure window, and destination. Non-viable actions explain rejection root causes in plain language.',
      action: 'VIEW RECOMMENDATIONS',
    },
    {
      title: '12. AUDITABLE EVIDENCE & PROVENANCE',
      desc: 'Full deterministic provenance links recommendations back to disruption, forecast, LP solve, physical validation, and counterfactual proof. "Predict before shortage. Verify before action."',
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
        width: '580px',
        backgroundColor: 'rgba(10, 16, 28, 0.94)',
        border: '1px solid rgba(0, 229, 255, 0.45)',
        borderRadius: '8px',
        padding: '16px 22px',
        boxShadow: 'var(--shadow-lg), 0 0 30px rgba(0, 229, 255, 0.2)',
        zIndex: 200,
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-cyan" style={{ fontSize: '9px', padding: '2px 6px' }}>
            DEMO MODE (STEP {currentStep + 1} OF {steps.length})
          </span>
          <span
            style={{
              fontSize: '12px',
              fontWeight: 700,
              color: '#f8fafc',
              fontFamily: 'var(--font-heading)',
              letterSpacing: '0.05em',
            }}
          >
            {step.title}
          </span>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            fontSize: '14px',
            padding: '2px',
          }}
          title="Exit Demo Tour"
        >
          ✕
        </button>
      </div>

      <div style={{ fontSize: '11px', color: '#cbd5e1', lineHeight: 1.55, marginBottom: '14px' }}>
        {step.desc}
      </div>

      {/* Progress Bar */}
      <div
        style={{
          height: '3px',
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
          borderRadius: '2px',
          overflow: 'hidden',
          marginBottom: '14px',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${((currentStep + 1) / steps.length) * 100}%`,
            background: 'linear-gradient(90deg, #0284c7 0%, #00e5ff 100%)',
            boxShadow: '0 0 8px #00e5ff',
            transition: 'width 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        />
      </div>

      {/* Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          onClick={handlePrev}
          disabled={currentStep === 0}
          className="btn btn-secondary"
          style={{ padding: '5px 12px', fontSize: '10px' }}
        >
          ◀ PREVIOUS
        </button>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => onStepChange(currentStep)}
            className="btn btn-secondary"
            style={{
              padding: '5px 12px',
              fontSize: '10px',
              color: '#00e5ff',
              borderColor: 'rgba(0, 229, 255, 0.4)',
            }}
          >
            {step.action}
          </button>
          <button
            onClick={handleNext}
            className="btn btn-primary"
            style={{ padding: '5px 14px', fontSize: '10px' }}
          >
            {currentStep === steps.length - 1 ? 'COMPLETE' : 'NEXT STEP ▶'}
          </button>
        </div>
      </div>
    </div>
  );
};
