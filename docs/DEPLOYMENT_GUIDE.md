# PRAVAH — Production Deployment & Operations Guide

> **Smart India Hackathon (SIH) PS 26251**  
> **Predictive Logistics Intelligence & Forward Supply Chain Resilience Engine**  
> *Target Architecture*: Render (FastAPI Backend) + Vercel (React Frontend)

---

## 1. System Architecture

PRAVAH operates as a decoupled cloud demonstration deployment designed for maximum resilience, zero-overhead maintenance, and deterministic reproducibility:

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Browser                         │
│   (Chrome / Firefox / Edge - Desktop & Presentation Screen) │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS (Port 443)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Frontend: Vercel (Edge CDN)                 │
│  - React 19 + TypeScript + Vite 8 SPA                       │
│  - Environment: VITE_API_BASE_URL (points to Render backend)│
│  - Client-side Routing: vercel.json rewrite rules           │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS REST API Calls
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Backend: Render (Web Service)                │
│  - Python 3.11+ / FastAPI / Uvicorn (ASGI)                  │
│  - Discrete-time simulation engine (15 nodes, 28 routes)    │
│  - XGBoost Multi-quantile Forecaster (P50 / P80 / P95)      │
│  - Continuous Multi-Commodity Linear Flow Solver (HiGHS LP) │
│  - Counterfactual evaluation & safety validation gates      │
│  - Embedded zero-config SQLite persistence (pravah.db)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

### Local Development & Build Toolchain
- **Python**: `3.11+` (tested on 3.11, 3.12, 3.13)
- **Node.js**: `v18.0.0+` or `v20.0.0+` (Vite 8 & React 19 compatible)
- **Package Managers**: `pip` (Python) and `npm` (Node)
- **Git**: Version 2.30+

### Cloud Provider Accounts
- **Render** (`https://render.com`) for hosting the FastAPI backend web service.
- **Vercel** (`https://vercel.com`) for hosting the React static web application.

---

## 3. Local Development

### Backend Setup
1. Clone the repository and navigate to root:
   ```bash
   git clone https://github.com/maheshd3846-netizen/pravah.git
   cd pravah
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment template:
   ```bash
   cp .env.example .env
   ```
5. Start local backend server:
   ```bash
   uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   Interactive Swagger API docs: `http://127.0.0.1:8000/docs`

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```
2. Copy frontend environment template:
   ```bash
   cp .env.example .env
   ```
   *(By default in local dev, leaving `VITE_API_BASE_URL` empty routes all `/api/*` calls through Vite's local proxy to `http://127.0.0.1:8000`)*
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open `http://localhost:3000` (or `http://localhost:5173`) in your browser.

---

## 4. Backend Deployment (Render)

### Step 4.1: Create Render Web Service
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** > **Web Service**.
3. Connect the GitHub repository: `https://github.com/maheshd3846-netizen/pravah`.
4. Configure service settings:
   - **Name**: `pravah-backend` (or custom name)
   - **Region**: Closest region (e.g., Singapore `singapore` or Frankfurt `frankfurt`)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (repository root)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free or Starter
   - **Health Check Path**: `/health`

Alternatively, if deploying via **Render Blueprint**, use the committed [`render.yaml`](file:///c:/Users/HP/Desktop/Pravah/render.yaml) specification in the root of the repository.

### Step 4.2: Backend Environment Variables
In the Render Service **Environment** tab, set:

| Variable | Value | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | Python runtime version |
| `ENVIRONMENT` | `production` | Deployment environment |
| `FRONTEND_ORIGIN` | `https://<your-app>.vercel.app` | Comma-separated list of allowed frontend origins |
| `RANDOM_SEED` | `42` | Deterministic simulation baseline seed |

*Note: Render automatically injects `$PORT` (typically 10000). The server binds dynamically to `0.0.0.0:$PORT`.*

### Step 4.3: Verify Backend
Once Render finishes deploying:
1. Note the HTTPS URL: `https://<render-service-name>.onrender.com`
2. Test root endpoint:
   ```bash
   curl https://<render-service-name>.onrender.com/
   ```
   Expected response:
   ```json
   {"engine":"PRAVAH","description":"Predictive Logistics & Forward Supply Chain Intelligence","status":"online","docs_url":"/docs","api_v1":"/api"}
   ```
3. Test health probe:
   ```bash
   curl https://<render-service-name>.onrender.com/health
   ```
   Expected response:
   ```json
   {"status":"healthy","engine":"PRAVAH"}
   ```

---

## 5. Frontend Deployment (Vercel)

### Step 5.1: Create Vercel Project
1. Log in to [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** > **Project**.
3. Import the GitHub repository: `maheshd3846-netizen/pravah`.
4. Configure Build and Output Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### Step 5.2: Frontend Environment Variables
In the Vercel **Environment Variables** configuration section:

| Key | Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `https://<your-render-backend>.onrender.com` | Live HTTPS backend endpoint |

*(Do NOT append `/api`, the client handles normalization automatically)*

### Step 5.3: Deploy and Obtain Live Domain
1. Click **Deploy**.
2. Vercel executes `tsc -b && vite build` and deploys the assets to global Edge CDN.
3. Note the assigned HTTPS domain: `https://<app-name>.vercel.app`.

---

## 6. CORS Configuration & Linkage

PRAVAH implements zero-leakage, fine-grained CORS security:
1. `backend/main.py` parses `FRONTEND_ORIGIN` and `CORS_ORIGINS`.
2. It additionally supports regex matching for all secure Vercel production and preview domains (`^https://.*\.vercel\.app$`).
3. Local development origins (`http://localhost:3000`, `http://localhost:5173`, `http://127.0.0.1:3000`, `http://127.0.0.1:5173`) are preserved by default.
4. If you assign a custom domain to Vercel (e.g. `https://pravah.example.com`), simply add it to `FRONTEND_ORIGIN` in the Render dashboard:
   ```env
   FRONTEND_ORIGIN=https://pravah.example.com,https://<your-app>.vercel.app
   ```

---

## 7. Production Smoke Test & Verification

Perform this end-to-end verification against the live deployment:

| Step | Action | Expected Result |
|---|---|---|
| **A** | Navigate to `https://<your-app>.vercel.app` | Command Center UI renders immediately, dark military tactical theme |
| **B** | Inspect Browser DevTools Console | Zero CORS errors, zero HTTP 4xx/5xx failures, zero mixed content warnings |
| **C** | Verify Network Calls | Requests go to `https://<your-backend>.onrender.com/api/*` |
| **D** | Command Center KPI Strip | 15 Nodes, 28 Corridors, 12 Fleet units populated |
| **E** | Disruption Scenario | Select `COMPOUND_DISRUPTION` |
| **F** | Predictive Analytics | Demand forecast graphs render P50, P80, P95 quantiles |
| **G** | Optimization Engine | HiGHS LP solves with 55 candidate dispatches; status `OPTIMAL` |
| **H** | Counterfactual & Safety Gates | Status evaluates to `DEGRADED`; recommendations safely filtered (12 feasible / 43 filtered) |
| **I** | Audit Trail View | Click Audit Trail tab: verification evidence logs visible |
| **J** | Guided Demo Tour | Launch demo tour from header: all steps cycle smoothly |

---

## 8. SIH Demonstration Checklist

- [ ] Backend is warm (Render free-tier instances may sleep after 15 min of inactivity; ping `/health` 2 minutes prior to jury evaluation).
- [ ] Scenario dropdown defaults to or has `COMPOUND_DISRUPTION` selected.
- [ ] Seed is verified as `42`.
- [ ] Horizon is 72 hours.
- [ ] Defense Post inventory levels and alerts correspond to canonical runbook values.
- [ ] Presentation screens tested for high-contrast visibility.

---

## 9. Known Limitations & Architectural Disclaimers

1. **Synthetic Data**:
   - The logistics network, coordinates (Sector Shivalik-Vanguard, 34.0°N–35.25°N), depot inventories, forward post names, vehicle telemetry, and disruption events are 100% synthetically generated for demonstration.
   - **No classified, real, or operational Indian Armed Forces data is used or stored.**
2. **Broker & Streaming Integrations (Kafka / MQTT)**:
   - Kafka and MQTT represent proposed production enterprise telemetry integrations outlined in architectural proposals; they are intentionally not required for this zero-dependency, self-contained SIH demonstration prototype.
3. **Database State**:
   - Default persistence uses an embedded SQLite database (`pravah.db`). In-memory run caches reset upon cloud container cold starts.
4. **GIS / ERP Integration**:
   - Live integration with military ERPs (e.g. CICP / GSAMS) or real GIS mapping layers is designated for future operational staging.
