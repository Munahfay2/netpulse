# NetPulse

**Detect. Diagnose. Notify. Restore.**

NetPulse is a hackathon MVP for telecom/ISP network monitoring and outage
management, built for small and medium-sized African ISPs and WISPs. It's a
lightweight, affordable network-assurance layer that combines telemetry
monitoring with automated customer and technician communication over
Africa's Talking — it doesn't claim to replace enterprise network-assurance
platforms, and it doesn't claim to invent network monitoring.

## The problem

Most small ISPs still depend on customers to report outages: a customer
loses connectivity, calls support, a ticket gets created, a technician
investigates, and only then does anyone discover that 38 other customers on
the same OLT are down too — each of whom may have already called in
separately.

NetPulse flips that around:

```
Network telemetry detects problem
        → NetPulse analyzes it
        → ISP is alerted
        → affected customers are notified
        → technician investigates
        → service is restored
        → customers are notified
```

The key differentiator is **correlation**: when 12+ customers on one OLT go
down within a short window, NetPulse creates **one** incident affecting all
of them — never a pile of duplicate tickets.

## What's real vs. simulated

- **Real**: the detection rules, the correlation engine, incident lifecycle,
  severity calculation, probable-cause reasoning, the FastAPI backend, the
  database schema, and the React dashboard are all fully working code — no
  mocked UI states.
- **Simulated**: there's no real ISP hardware here. A telemetry simulator
  stands in for real routers/OLTs/ONTs, implementing the same
  `TelemetrySource` interface a real SNMP collector or CPE agent would use
  later (see `ARCHITECTURE.md`).
- **SMS**: if Africa's Talking sandbox credentials aren't configured, SMS
  sending runs in **Demo SMS Mode** — messages are logged to the
  notification center and clearly labeled `SIMULATED`, never faked as a real
  API response.

NetPulse also never claims a network fault as confirmed truth. Every
diagnosis is shown as "probable cause" with a confidence level and the
reasoning behind it — see the Probable Cause Engine on any incident's detail
page.

## Architecture at a glance

```
Telemetry Source (simulator today, real agent later)
        ↓
Fault Detection Engine   (deterministic rules)
        ↓
Correlation Engine       (groups failures by OLT/area/time)
        ↓
Incident Engine          (severity, probable cause, lifecycle)
        ↓
Notification Engine      (Africa's Talking SMS + USSD)
```

See `ARCHITECTURE.md` for the full breakdown and `API.md` for endpoint docs.

**Stack**: FastAPI + SQLAlchemy (SQLite by default, swappable to Supabase
Postgres) on the backend; React + TypeScript + Tailwind + Recharts on the
frontend; Africa's Talking for SMS/USSD.

## Running it locally

### Option A: Docker Compose (fastest)

```bash
docker compose up --build
```
Backend on `http://localhost:8000`, frontend on `http://localhost:5173`. Set
`AFRICASTALKING_USERNAME`/`AFRICASTALKING_API_KEY` as environment variables
before running (or in a `.env` file next to `docker-compose.yml`) if you
have sandbox credentials — otherwise it runs in Demo SMS Mode automatically.

### Option B: Run backend and frontend directly

#### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

On first startup the backend creates the SQLite database and seeds it with
5 locations, 10 OLTs, 120+ customers/devices, 10 technicians, and 3
historical (resolved) incidents. No Africa's Talking or Supabase credentials
are required to run the demo — see `.env.example` for what each variable
does.

API docs (Swagger UI) are then available at `http://localhost:8000/docs`.

Every endpoint except `/api/auth/*`, `/api/health`, `/api/ussd`, and
`/api/sms/*` requires a valid session token (a real `401` is returned
without one — see `API.md` and `tests/test_api.py`). The frontend handles
this automatically once you're logged in.

To run the test suite:
```bash
pip install -r requirements-dev.txt
pytest
```
30 tests cover the detection rules, the correlation engine's flagship
"many customers, one incident" behavior, severity/probable-cause logic,
SMS demo-mode behavior, the USSD flow, and API-level auth enforcement.

#### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. In dev, Vite proxies `/api/*` to
`http://localhost:8000` (see `vite.config.ts`), so no CORS configuration is
needed locally.

Click **Demo Login** on the login screen — it uses a separate demo account
seeded automatically, no production credentials required.

## The 5-minute demo

1. Open the Dashboard — network health is 100%, no active incidents.
2. Open **Topology** — everything nominal.
3. Back on the Dashboard, click **Simulate Area Outage**.
4. Watch the KPI cards and the Active Incidents table update within a few
   seconds — the telemetry simulator ticks every 5 seconds by default.
5. Open the incident. You'll see: affected customer count, the OLT, 100%
   packet loss / WAN down telemetry, the probable cause with its confidence
   and reasoning, recommended technician checks, and a full timeline.
6. Open **Notifications** — the customer and technician SMS are logged
   there (labeled `SIMULATED` unless you've configured a real sandbox key).
7. Open the **USSD Simulator**, pick one of the affected customers, dial in,
   and select "3. Check outage status" — it reflects the live incident.
8. Back on the Dashboard, click **Restore All Services**.
9. The incident automatically moves to **Resolved** and restoration SMS go
   out — check the incident timeline and Notifications again.
10. Open **Analytics** to see the incident reflected in the day's charts.

## Running the tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

30 tests cover the detection rules, severity/probable-cause logic, the
flagship "N simultaneous failures on one OLT become ONE incident, then
auto-resolve with restoration SMS" scenario, SMS demo-mode behavior, the
USSD flow, and full API/auth integration. Tests run against an isolated
temporary SQLite file — never your local `netpulse.db` — and the background
telemetry ticker is disabled so tests control simulation ticks explicitly.

## Authentication

Every API endpoint except `/api/auth/*`, `/api/health`, `/api/ussd`, and
`/api/sms/*` (the last two are Africa's Talking webhooks — a customer's
feature phone has no NetPulse session) requires a valid JWT, issued by
`/api/auth/login` or `/api/auth/demo-login`, sent as
`Authorization: Bearer <token>`. The frontend's API client already attaches
this automatically once you're logged in.

## Deployment

- **Docker Compose (local, one command)**: `docker compose up --build` —
  backend on `:8000`, frontend dev server on `:5173`.
- **Render**: `render.yaml` at the repo root deploys both the backend
  (Docker web service with a persistent disk for SQLite) and the frontend
  (static site) as a single Blueprint. After the first deploy, set
  `AFRICASTALKING_USERNAME` / `AFRICASTALKING_API_KEY` in the backend
  service's dashboard.
- **Fly.io** (backend alternative): `backend/fly.toml` — `fly launch
  --copy-config`, `fly volumes create netpulse_data --size 1`, `fly deploy`.
- **Vercel** (frontend alternative): `frontend/vercel.json` handles SPA
  routing; set `VITE_API_URL` to your deployed backend's URL in Vercel's
  project settings.
- **Frontend ↔ backend on separate hosts**: set `VITE_API_URL` (see
  `frontend/.env.example`) — the API client falls back to a relative `/api`
  (Vite's local dev proxy) only when it's unset.

## Africa's Talking setup

1. Create a sandbox account at <https://account.africastalking.com/>.
2. Copy your sandbox username (usually `sandbox`) and API key into
   `backend/.env`:
   ```
   AFRICASTALKING_USERNAME=sandbox
   AFRICASTALKING_API_KEY=your-sandbox-key
   AFRICASTALKING_SENDER_ID=NetPulse
   ```
3. Point your Africa's Talking sandbox USSD channel's callback URL at
   `POST /api/ussd` on your deployed backend, and the SMS delivery-report /
   inbound-SMS callbacks at `/api/sms/delivery-report` and `/api/sms/callback`.
4. Restart the backend. `GET /api/notifications/demo-mode` will report
   `demo_sms_mode: false` once credentials are picked up.

Until you do this, NetPulse runs entirely in Demo SMS Mode — this is
intentional so the dashboard demo never requires production credentials.

## Project structure

```
netpulse/
├── backend/
│   ├── app/
│   │   ├── main.py                    FastAPI app, startup/seed/simulator wiring
│   │   ├── models.py                  SQLAlchemy models (all 16 tables)
│   │   ├── schemas.py                 Pydantic response schemas
│   │   ├── database.py                Engine/session setup
│   │   ├── auth_utils.py              JWT verification dependency
│   │   ├── seed.py                    Demo data generator
│   │   ├── services/
│   │   │   ├── telemetry_simulator.py     TelemetrySource interface + simulator
│   │   │   ├── fault_detection_engine.py  Deterministic detection rules
│   │   │   ├── correlation_engine.py      Groups failures into incidents
│   │   │   ├── incident_engine.py         Severity, probable cause, lifecycle
│   │   │   └── africastalking_service.py  SMS/USSD integration + demo mode
│   │   └── routers/                   One router per resource (see API.md)
│   ├── tests/                         30 pytest tests (see API.md's auth notes)
│   ├── Dockerfile / .dockerignore / fly.toml
│   ├── requirements.txt / requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/                     One file per nav item + USSD simulator
│   │   ├── components/                Layout, KpiCard, badges
│   │   ├── api/client.ts              Typed fetch wrapper
│   │   └── types.ts
│   ├── vercel.json
│   └── package.json
├── docker-compose.yml                 One-command local startup
├── render.yaml                        Render blueprint (backend + frontend)
├── ARCHITECTURE.md
├── API.md
└── README.md   (this file)
```

## Roadmap (not built in this MVP — see ARCHITECTURE.md's AI section)

- Predictive outage detection from historical telemetry
- ML-assisted root-cause analysis (always labeled "AI-assisted diagnosis",
  never presented as guaranteed truth)
- Real hardware telemetry agents (OpenWrt, Raspberry Pi, SNMP, CPE/ONT
  vendor APIs) implementing the same `TelemetrySource` interface the
  simulator uses today
- Supabase Auth + Realtime in place of the current JWT + polling approach
- Billing, payments, SIM management — explicitly out of scope
