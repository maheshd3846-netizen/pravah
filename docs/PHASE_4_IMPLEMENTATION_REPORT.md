# PRAVAH — Phase 4 Implementation Report
## Command Center UI/UX & Intelligence Integration

**Smart India Hackathon PS 26251 — Indian Army Predictive Logistics & Forward Supply Chain**  
**Date:** October 2026  
**Branch:** `phase-4-command-center`  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary

Phase 4 builds a high-density, professional command-center web application for PRAVAH (**Predictive Logistics Intelligence & Resilience Engine**). It exposes the full, verified backend pipeline:

$$\text{PREDICT} \longrightarrow \text{UNDERSTAND RISK} \longrightarrow \text{OPTIMIZE} \longrightarrow \text{SIMULATE} \longrightarrow \text{VERIFY} \longrightarrow \text{EXPLAIN} \longrightarrow \text{RECOMMEND}$$

Designed for rapid comprehension by Smart India Hackathon evaluators within 2–3 minutes, the UI communicates a single unified operational story:
1. **What is happening?** (Network state, active disruptions, road pass blockages)
2. **What will happen?** (XGBoost quantile demand forecasting, P50/P80/P95 uncertainty bands)
3. **Where is the risk?** (Monte Carlo stockout probabilities, time-to-safety-stock, time-to-zero)
4. **What can we do?** (HiGHS linear network flow optimization, alternate corridor routing)
5. **Will it actually help?** (Counterfactual closed-loop simulation verifying causal deltas)
6. **Why this decision?** (Deterministic, fact-grounded evidence and tradeoff analysis)

Zero mock or fabricated numbers were used. The frontend consumes the existing production APIs directly.

---

## 2. Existing Backend Integration

The frontend integrates directly with all existing backend routers without modifying or weakening any mathematical or simulation algorithms:
- `GET /api/network`: 15 synthetic nodes, 28 corridors, and 12 vehicle assets.
- `POST /api/forecast/run` & `GET /api/forecast/{node_id}/{item_id}`: XGBoost quantile demand inference.
- `GET /api/risk/overview` & `POST /api/risk/recalculate`: Multi-factor risk scores and propagation.
- `GET /api/alerts`: Early warning operational alerts.
- `POST /api/optimization/solve`: SciPy HiGHS linear network flow optimization.
- `POST /api/optimization/evaluate`: Closed-loop counterfactual simulation.
- `POST /api/recommendations/generate` & `GET /api/recommendations`: Auditable, conflict-free recommendations.
- `GET /api/decision/summary`: Executive situational readiness overview.

---

## 3. Command Center Architecture

Built with **React 19 + TypeScript + Vite 8**:
- `frontend/src/types/`: Strict TypeScript data models mirroring backend Pydantic schemas.
- `frontend/src/api/`: Modular API client layer (`client.ts`, `network.ts`, `forecast.ts`, `risk.ts`, `alerts.ts`, `optimization.ts`, `counterfactual.ts`, `recommendations.ts`, `decision.ts`, `scenarios.ts`).
- `frontend/src/components/`:
  - `Header.tsx`: Top navigation bar, system status, synthetic simulation label, Demo Mode toggle, and "ANALYZE NETWORK" one-click button.
  - `StatusBar.tsx`: Telemetry indicators, Data Quality gate (`READY` / `DEGRADED` / `INSUFFICIENT`), and active scenario.
  - `KpiStrip.tsx`: 5 high-value KPI cards with live backend counts and fallback handling.
  - `DigitalTwinMap.tsx`: Vector SVG GIS digital twin of the Northern Sector logistics grid with echelon markers, corridor condition states, and interactive drawers.
  - `RiskPanel.tsx`: Critical alerts list and normalized 5-factor risk component breakdown.
  - `ForecastPanel.tsx`: Multi-quantile demand curve visualization (P50, P80, P95) and projected stock trajectory.
  - `DecisionCenter.tsx`: The primary decision-support panel featuring recommended actions, deterministic rationales, clickable evidence, and parallel corridor comparisons.
  - `VerificationPanel.tsx`: Side-by-side expected vs. verified outcomes and multi-dimensional operational tradeoffs.
  - `ScenarioSimulator.tsx`: What-if disruption toggles (landslide pass blockages, demand surges, blizzards, fleet reductions) and baseline vs. optimized comparison table.
  - `RecommendationsView.tsx`: Multi-attribute filterable table of all tactical shipments with audit drawers.
  - `AuditTrailView.tsx`: Visual causal lineage chain from scenario disruption to verified dispatch.
  - `DemoTour.tsx`: Structured 12-step guided presenter walkthrough.
  - `AnalyzeModal.tsx`: Real-time 5-stage pipeline execution modal.

---

## 4. UI/UX Design

The application adheres strictly to the non-generic product design guidelines:
- **Aesthetic**: Deep dark command-center theme (`#0a0e17` base, `#101623` surface, `#182235` elevated) with high information density, clean monospace telemetry accents, and subtle borders.
- **Color Discipline**: Tactical cyan (`#06b6d4`), military blue (`#3b82f6`), verified emerald (`#10b981`), caution amber (`#f59e0b`), and critical rose (`#ef4444`). Avoids arbitrary gradients or neon gaming styling.
- **Hierarchy**: Three-zone desktop layout where the Digital Twin map visually dominates the upper half, supported by risk telemetry, inventory projections, and the central Decision Center.
- **Responsiveness**: Primary target `1920 × 1080`, secondary `1440 × 900`, fully adaptable down to `1366 × 768`.

---

## 5. GIS Digital Twin

- Plots all 15 nodes using synthetic geographical coordinates (lat 34.1–35.4, lng 76.2–78.8) with elevation contours.
- Differentiates echelons: Central Base Depot Alpha (CD-01), 3 Regional Supply Hubs (RH-01..03), 5 Staging Bases (SB-01..05), and 6 Forward Defense Posts (FP-01..06).
- Displays 28 corridors with status-coded styling: `AVAILABLE` (solid blue/cyan), `DEGRADED` (amber dashed), and `BLOCKED` (red dashed with barrier indicators).
- Interactivity: Pan, zoom, reset, label toggling, and instant drawer inspection for node inventory and route alternatives.

---

## 6. Forecast Visualization

- Graphs demand rate (units/hr) across the planning horizon with confidence intervals.
- Plots P50 (median estimate), P80 (operational planning benchmark), and P95 (stress peak) with clear "Prediction Interval / Quantile Forecast" labeling.
- Interactive tooltip tracking individual hourly consumption projections.

---

## 7. Risk Intelligence

- Visualizes real-time sector risk alerts with stockout probability, time-to-zero, and root causes.
- Normalizes and renders the 5-factor risk decomposition:
  - Inventory Risk ($R_{inv}$)
  - Demand Volatility Risk ($R_{demand}$)
  - Route Disruption Risk ($R_{route}$)
  - Transport Fleet Risk ($R_{transport}$)
  - Environmental & Weather Risk ($R_{env}$)

---

## 8. Optimization Visualization

- Displays solver classification: `HYBRID (Continuous Multi-Commodity Linear Flow LP via SciPy HiGHS + Heuristic Fleet Dispatch)`.
- Shows selected movements, volume, transport cost, shortage penalties, and execution time (<15ms).

---

## 9. Counterfactual Verification

- Prominently isolates **Expected Effect** (analytical model projection) from **Verified Effect** (empirical closed-loop simulation delta).
- Displays causal metrics:
  - Unmet Demand: Decreased by -50% to -79%
  - Stockout Events: Reduced by -60%+
  - Fulfillment Rate: Increased (+2% to +4% points)
  - Transport Distance: Increased (honest tradeoff)
  - Transit Delay: Increased (honest tradeoff)

---

## 10. Decision Center

- Centralized presentation of executable actions: `MOVE`, `REROUTE`, `REALLOCATE`, `PRIORITIZE`, `HOLD`, `DEFER`.
- Identifies source depot, destination node, assigned vehicle, route corridor, quantity, and departure/arrival windows.
- Highlights parallel corridor trade-offs (e.g. why bypass route R-11 was chosen over blocked primary highway R-01).

---

## 11. Recommendation Evidence

- Displays structured `DecisionEvidenceItem` elements directly mapped to system fields:
  - `STOCKOUT_PROBABILITY`
  - `TIME_TO_ZERO`
  - `ROUTE_STATUS`
  - `SOURCE_INVENTORY`
  - `VEHICLE_CAPACITY`
  - `COUNTERFACTUAL_DELTA`
- Clicking any evidence tag automatically focuses the relevant diagnostic panel.

---

## 12. Audit Trail

- Renders an interactive 6-step visual provenance chain:
  $$\text{Scenario Disruption} \longrightarrow \text{Quantile Forecast} \longrightarrow \text{Risk State} \longrightarrow \text{Optimization Run} \longrightarrow \text{Counterfactual Simulation} \longrightarrow \text{Recommendation}$$
- Displays exact run IDs, timestamps, and parameters to ensure total auditability for defense evaluators.

---

## 13. Demo Mode

- Integrated presenter tour guiding evaluators through the 12-step story in 2–3 minutes:
  1. Inspect normal network grid
  2. Inject compound disruption
  3. Observe risk escalation on forward posts
  4. Select forward post FP-01
  5. Inspect probabilistic demand forecast
  6. Review stockout probability & time to zero
  7. Run HiGHS network flow optimization
  8. Inspect bypass route R-11
  9. Execute closed-loop counterfactual simulation
  10. Verify empirical demand reduction
  11. Generate auditable REALLOCATE recommendation
  12. Inspect fact-grounded explanation and audit trail

---

## 14. API Integration & Error Handling

- Centralized API client with strict error handling, response typing, and error banners with retry capabilities.
- Zero mock data in production demo flows; fallback states gracefully indicate "Unavailable" rather than fabricating numbers.

---

## 15. Testing & Validation

### Frontend Tests (Vitest + Testing Library)
- `src/test/commandCenter.test.tsx`: 13 test suites covering all panels, data binding, KPI fallbacks, and user interactions.
- Result: **13 passed / 0 failed** in 1.95s.

### Frontend Production Build
- `npm run build`: **PASS** in 171ms (Zero TypeScript or bundling errors).

### Backend Regression Tests
- `pytest -q`: **119 passed / 0 failed** in 44.43s (Phases 1, 2, 2.5, 3A, 3B, 3C intact).

---

## 16. Performance

- Pure SVG digital twin and vector charting avoid bulky WebGL map runtimes or external tile dependencies.
- Production bundle size: ~303 kB minified (~87 kB gzip).
- Fast cold start: Initial render and API synchronization within ~300ms.

---

## 17. Known Limitations

- Operates in a synthetic demonstration environment with fictionalized coordinates and simulated forward supply data.
- Relies on discrete hourly simulation steps rather than continuous real-time telemetry feeds.

---

## 18. Phase 5 Readiness

The system is fully prepared for Phase 5 (Live Deployment, Presentation Packaging, and Hackathon Evaluation Pitch):
- Core engine: Fully validated.
- Decision support: Transparent and auditable.
- User interface: Fully functional, responsive, and intuitive.
- Demo mode: Complete and reproducible.
