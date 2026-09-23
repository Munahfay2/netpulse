# NetPulse Architecture

## Design goal

Keep every layer swappable so today's simulator can be replaced by real ISP
hardware later without touching detection, correlation, incident management,
or notifications.

```
┌─────────────────────┐
│  Telemetry Source    │  simulator today → SNMP / OpenWrt / Raspberry Pi /
│  (TelemetrySource)   │  CPE-ONT vendor APIs later
└──────────┬───────────┘
           │ writes Telemetry rows, updates Device state
           ▼
┌─────────────────────┐
│ Fault Detection      │  deterministic rules (Rules 1-4) — never ML in the
│ Engine                │  MVP; produces a *symptom*, not a confirmed fault
└──────────┬───────────┘
           ▼
┌─────────────────────┐
│ Correlation Engine    │  groups simultaneous failures sharing an OLT +
│                       │  symptom + short time window into ONE incident
└──────────┬───────────┘
           ▼
┌─────────────────────┐
│ Incident Engine       │  severity thresholds, probable-cause reasoning,
│                       │  recommended checks, lifecycle transitions,
│                       │  auto-recovery detection
└──────────┬───────────┘
           ▼
┌─────────────────────┐
│ Notification Engine   │  africastalking_service.py — SMS to customers/
│ (Africa's Talking)    │  technicians, USSD self-service, demo-mode fallback
└─────────────────────┘
```

## Why this separation matters

Every arrow above is a real interface boundary in the code, not just a
diagram:

- **TelemetrySource** (`telemetry_simulator.py`) is an abstract base class.
  `SimulatedTelemetrySource` is the only implementation today, but
  `POST /api/telemetry` already accepts telemetry from an external source in
  the same shape the simulator produces, so a real agent can start posting
  to it without any other code changing.
- **Fault detection** never talks to Africa's Talking or touches the
  database beyond reading a `Device`. It's a pure function:
  `Device -> DetectionResult`.
- **Correlation** only decides *grouping* — which existing incident (if any)
  a newly-faulty device belongs to. It doesn't decide severity or send
  notifications itself; it calls into the incident engine for that.
- **Incident engine** owns severity, probable cause text, and lifecycle. It
  calls the notification service, but the notification service has no idea
  what an "incident" is beyond the ID it's tagging messages with — it just
  sends SMS and handles USSD.

This means, for example, swapping severity thresholds, adding a fifth
detection rule, or pointing the whole system at a different SMS aggregator
are each single-file changes.

## Network model

```
Customer → Router/CPE → ONT/ONU → Access Fibre → ODF → OLT
         → Aggregation Network → ISP Core → Internet
```

Reflected in the schema as:

- `customers` — one per subscriber
- `devices` — the customer's CPE/router; the unit telemetry is collected on
- `onts` — ONT terminating the fibre into the premises
- `odfs` — Optical Distribution Frame per OLT
- `olts` — the aggregation point NetPulse correlates failures around
- `network_locations` — the physical area (Nakuru, Njoro, etc.)

## Detection rules (deterministic, no ML)

| Rule | Condition | Symptom |
|---|---|---|
| 1 | router unreachable | Device unreachable |
| 2 | router reachable, WAN down | WAN/access connectivity issue |
| 3 | internet unreachable + packet loss > 80% | Severe connectivity degradation |
| 4 | latency > 200ms + packet loss > 10% | Network degradation/congestion |
| 5 (correlation) | ≥10 customers, same OLT, failure window ≤2 min | Group into one area-outage incident |

Severity is derived from affected-customer count, not from the rule that
fired, and thresholds are configurable in
`incident_engine.SEVERITY_THRESHOLDS`:

| Customers affected | Severity |
|---|---|
| 20+ | Critical |
| 10–19 | High |
| 3–9 | Medium |
| 1–2 | Low |

## Probable cause vs. confirmed fault

NetPulse is deliberately careful about this distinction throughout the UI
and the API:

- `observed telemetry` — raw fields on a `Device`/`Telemetry` row.
- `detected symptom` — the output of the fault detection engine (e.g. "WAN
  down").
- `probable cause` — the incident engine's plain-English hypothesis (e.g.
  "Access network disruption"), always shown with a confidence level
  (Low/Medium/High, derived from how many customers corroborate it) and the
  specific reasons behind it.
- `recommended investigation` — a checklist for the technician, never a
  claim that (say) the fibre is physically cut.

No part of the system ever asserts a confirmed physical fault.

## Database

SQLAlchemy models in `backend/app/models.py` map directly onto the schema
in the spec: `users`, `customers`, `devices`, `onts`, `odfs`, `olts`,
`network_locations`, `technicians`, `telemetry`, `incidents`,
`incident_devices` (join table), `incident_events`, `tickets`,
`notifications`, `ussd_sessions`, `service_status`.

Key relationships:
- Customer → Device (1:1 in this MVP; a customer has one CPE)
- Device → ONT → OLT → Location
- Incident ↔ Device via `incident_devices` (many-to-many — an incident
  affects many devices, though in the MVP a device is only ever active in
  one open incident at a time)
- Incident → IncidentEvent (1:many, the timeline)
- Incident → Technician (nullable FK, assigned on dispatch)
- Notification → Incident (nullable FK; test SMS aren't tied to an incident)
- Ticket → Customer, optionally → Incident

Indexes are placed on `device_id`, `olt_id`, and `timestamp` columns used in
the hot paths (telemetry lookups, correlation queries).

Defaults to SQLite (`netpulse.db`) for zero-setup local development;
`DATABASE_URL` swaps to Postgres/Supabase with no code changes because
everything goes through the ORM.

## Real-time updates

The MVP uses short-interval polling (4-6 seconds) from the frontend rather
than WebSockets/Supabase Realtime, to keep the demo dependency-free. The
telemetry simulator itself ticks every `TELEMETRY_INTERVAL_SECONDS` (default
5s) in a background thread started at FastAPI startup. Swapping polling for
Supabase Realtime subscriptions is a frontend-only change — the backend
already treats the database as the single source of truth.

## Security notes

- No API keys are ever sent to the frontend; Africa's Talking calls happen
  server-side only, inside `africastalking_service.py`.
- Customer phone numbers are stored in full (needed to actually send SMS)
  but only ever exposed to the frontend/API responses in masked form
  (`Customer.masked_phone`, `africastalking_service.mask_phone`).
- JWTs are issued on login/demo-login and expected as a Bearer token on
  authenticated requests (the demo frontend currently gates routes on token
  presence rather than validating server-side on every call — production
  hardening would add a proper auth dependency to each router).
- USSD and SMS webhook handlers never raise on malformed input; they always
  degrade to a safe `END` response or a logged failure rather than crashing
  (see `ussd.py`'s try/except and `main.py`'s general error posture).

## What's explicitly out of scope for this MVP

Real OLT configuration, real fibre control, automatic physical repair,
firmware modification, billing/payments/SIM management, real geolocation,
and machine learning — matching the spec's "do not overbuild" section.
Locations on the Live Network map use approximate coordinates for Kenyan
towns, not live GPS.
