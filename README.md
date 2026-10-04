# PRAVAH -- Predictive Logistics Intelligence & Resilience Engine

> **Smart India Hackathon PS 26251** -- Indian Army Predictive Logistics & Forward Supply Chain

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Pytest](https://img.shields.io/badge/pytest-passing-brightgreen.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Technical Report](https://img.shields.io/badge/Documentation-Technical%20Report-blueviolet.svg)](TECHNICAL_REPORT.md)

> 📑 **Full Technical Report Available**: [**Read the PRAVAH Master Technical Report (SIH PS 26251)**](TECHNICAL_REPORT.md) for complete mathematical formulations, system architecture, quantile forecasting specs, HiGHS LP solver analysis, and empirical acceptance benchmarks.

---

## 1. Product Vision

PRAVAH is an AI-driven, discrete-time tactical logistics intelligence and forward supply chain resilience engine designed to answer four fundamental operational questions:

1. **What is happening?** Real-time multi-echelon inventory tracking, convoy in-transit status, weather degradation, and road connectivity across forward high-altitude military sectors.
2. **What is likely to happen?** Multi-attribute demand forecasting (seasonality, environmental, trends), stockout vulnerability projection, isolation risk evaluation, and bottleneck probability.
3. **What should be done?** Algorithmic supply pre-positioning, multi-route detour optimization, and convoy vehicle assignment mitigating forward post shortages.
4. **Did the recommended action actually improve the outcome?** Counterfactual simulation comparing baseline vs intervention outcomes with concrete measured deltas in stockouts and unmet demand.

### Closed-Loop Architecture:
```
DATA
  → FORECAST
  → UNCERTAINTY
  → INVENTORY PROJECTION
  → STOCKOUT PREDICTION
  → NETWORK RISK
  → DISRUPTION SIMULATION
  → OPTIMIZATION
  → RECOMMENDATION
  → RE-SIMULATION
  → MEASURED IMPACT
```

---

## 2. Synthetic Logistics World

To guarantee 100% reproducibility while strictly adhering to security guidelines, PRAVAH uses a **synthetic, non-classified high-altitude logistics grid** modeled in a fictional sector (*Sector Shivalik-Vanguard*, 34.0°N to 35.25°N, 76.2°E to 78.15°E):

- **15 Nodes**:
  - `1 Central Depot` (`CD-01`, Base Logistics Depot Alpha, 500,000 unit capacity)
  - `3 Regional Hubs` (`RH-01` Trishul, `RH-02` Garuda, `RH-03` Vajra, 150,000 units each)
  - `5 Staging Bases / Transit Points` (`SB-01` to `SB-05`, 50,000–60,000 units each)
  - `6 Forward Defense Posts` (`FP-01` to `FP-06`, elevations 4,300m–4,980m, priority 5)
- **28 Routes**:
  - Primary valley highways, mountain passes, and rugged bypass corridors with GeoJSON geometries, terrain classifications, and weather sensitivities.
- **12 Vehicles**:
  - Heavy Logistics Trucks (ALS-10T), Medium Tactical Vehicles (MATV-5T), All-Terrain Convoys (ATC-HighMobility), and Light 4x4 Fast Couriers.
- **5 Supply Categories**:
  - `FOOD`, `WATER`, `FUEL`, `MEDICAL`, `GENERAL_CRITICAL`.

---

## 3. Project Directory Structure

```
pravah/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI REST Endpoints (health, simulation, network, inventory, demand, scenarios)
│   │   ├── models/              # SQLAlchemy & PostgreSQL/PostGIS compatible models
│   │   ├── schemas/             # Pydantic request/response validation schemas
│   │   ├── services/            # Simulation execution & scenario management services
│   │   ├── simulation/          # Backend simulation adapter
│   │   ├── forecasting/         # Forecast service adapter
│   │   ├── risk/                # Topological isolation & vulnerability evaluator
│   │   ├── optimization/        # Optimization service adapter
│   │   └── recommendations/     # Actionable operational order generator
│   └── main.py                  # FastAPI application entry point
│
├── simulation/
│   ├── world_generator.py       # Deterministic world generator (15 nodes, routes, fleet)
│   ├── network_generator.py     # Graph generator with terrain & GeoJSON geometry
│   ├── demand_generator.py      # Multi-attribute demand generator
│   ├── weather_generator.py     # Continuous environmental state generator
│   ├── vehicle_generator.py     # Fleet generator with load & status tracking
│   ├── inventory_engine.py      # Non-negative balance engine: I[t+1]=I[t]+receipts-demand
│   ├── disruption_engine.py     # Shocks (route blocks, weather, surges, fleet cuts)
│   └── simulator.py             # 1-hour discrete-time simulator over configurable horizons
│
├── ml/
│   ├── baselines/               # Moving average and exponential smoothing forecasters
│   ├── features/                # Lag, rolling stats, cyclical time & weather features
│   ├── xgboost/                 # XGBoost regressor with uncertainty bounds
│   ├── evaluation/              # WAPE, RMSE, MAE, MAPE metrics
│   └── models/                  # Trained model checkpoints
│
├── optimization/
│   ├── model.py                 # SupplyDecision, OptimizationProblem, OptimizationPlan
│   ├── constraints.py           # Physical capacity, inventory, and route feasibility
│   ├── heuristic.py             # Deterministic Priority-Ranked Greedy Resupply Heuristic
│   ├── solver.py                # Unified solver interface (Heuristic + MILP abstraction)
│   └── evaluator.py             # Counterfactual resilience evaluator
│
├── data/
│   ├── generated/               # Generated datasets and training artifacts
│   └── scenarios/               # Scenario JSON configurations:
│       ├── normal.json
│       ├── demand_surge.json
│       ├── route_failure.json
│       ├── weather_degradation.json
│       ├── vehicle_shock.json
│       └── compound_disruption.json
│
├── frontend/
│   └── src/                     # React/TypeScript/Vite scaffold for Phase 2
│
├── tests/                       # Complete pytest test suite
├── scripts/
│   └── run_demo.py              # CLI demonstration script
├── requirements.txt             # Python dependency specification
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git ignore rules
└── README.md
```

---

## 4. Quick Start & Setup Instructions

### Prerequisites
- Python 3.11+
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/maheshd3846-netizen/pravah.git
cd pravah
```

### Step 2: Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
```bash
cp .env.example .env
```

---

## 5. Execution Commands

### Run the Simulation Demo
Executes the synthetic world generation, runs baseline normal operations (336 hours / 14 days), executes the compound disruption scenario, and prints actual calculated performance metrics:
```bash
python scripts/run_demo.py
```

### Run the Phase 2 Intelligence Demo
Executes feature engineering, baseline vs XGBoost quantile models (P50/P80/P95), multi-horizon forecasts (24h, 72h, 168h), inventory projection, Monte Carlo stockout analysis, risk engine, network risk propagation, and early warning alerts:
```bash
python scripts/run_intelligence_demo.py
```

### Start the FastAPI Server
Starts the high-performance REST API backend with automatic reload:
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive API Documentation (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Alternative API Documentation (ReDoc): [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Run Test Suite
Runs all 42 unit, simulation, ML, risk, and API tests with pytest:
```bash
python -m pytest -v
```

---

## 6. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health status and subsystem verification |
| `GET` | `/api/network` | Retrieves 15 nodes, routes, and vehicle fleet |
| `GET` | `/api/inventory` | Multi-echelon stock levels and days-of-supply |
| `GET` | `/api/demand` | Demand time series and category aggregation |
| `GET` | `/api/scenarios` | Lists all standard operational disruption scenarios |
| `POST` | `/api/scenarios` | Registers a new custom scenario |
| `POST` | `/api/simulation/run` | Executes 1-hour discrete-time simulation run |
| `GET` | `/api/simulation/{run_id}/state` | Inspects state and active shipments of a run |
| `POST` | `/api/forecast/train` | Trains feature pipeline, baselines, and XGBoost quantile models |
| `POST` | `/api/forecast/run` | Generates P50/P80/P95 forecasts and Monte Carlo stockout analysis |
| `GET` | `/api/forecast/{node_id}/{item_id}` | Retrieves current demand forecast and projection |
| `GET` | `/api/risk/overview` | Whole-network risk overview, critical nodes, and active alert counts |
| `GET` | `/api/risk/nodes` | Detailed risk components and criticality for all 15 nodes |
| `GET` | `/api/risk/{node_id}` | Node-specific risk breakdown, propagation sources, and criticality |
| `POST` | `/api/risk/recalculate` | Forces recalculation of network risk telemetry |
| `GET` | `/api/alerts` | Queries structured early warning alerts with audit evidence |

---

## 7. License

MIT License. Designed and engineered for Smart India Hackathon PS 26251.
