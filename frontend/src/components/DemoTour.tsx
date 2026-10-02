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
