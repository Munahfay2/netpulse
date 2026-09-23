import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { api } from "../api/client";
import type { Incident, Technician, NotificationItem } from "../types";
import { SeverityBadge, StatusBadge } from "../components/Badges";

const STATUS_FLOW = ["Detected", "Investigating", "Assigned", "In Progress", "Resolved", "Closed"];

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    if (!id) return;
    const [inc, techs, notifs] = await Promise.all([
      api.incident(id), api.technicians(), api.notifications(id),
    ]);
    setIncident(inc);
    setTechnicians(techs);
    setNotifications(notifs);
  }

  useEffect(() => {
    refresh();
    const iv = setInterval(refresh, 4000);
    return () => clearInterval(iv);
  }, [id]);

  if (!incident) return <div className="text-text-muted text-sm">Loading incident…</div>;

  async function assign(techId: string) {
    if (!id) return;
    setBusy(true);
    await api.assignTechnician(id, techId);
    await refresh();
    setBusy(false);
  }

  async function setStatus(status: string) {
    if (!id) return;
    setBusy(true);
    await api.updateIncidentStatus(id, status);
    await refresh();
    setBusy(false);
  }

  const isResolved = incident.status === "Resolved" || incident.status === "Closed";
  const wanDown = incident.incident_type === "WAN/access connectivity issue";

  return (
    <div className="space-y-6 max-w-5xl">
      <Link to="/incidents" className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text">
        <ArrowLeft size={15} /> Back to incidents
      </Link>

      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold">{incident.title}</h1>
            <SeverityBadge severity={incident.severity} />
          </div>
          <p className="text-text-muted text-sm mt-1 font-mono">{incident.id}</p>
        </div>
        {isResolved && (
          <div className="flex items-center gap-1.5 text-healthy text-sm bg-[#132a22] px-3 py-1.5 rounded-md">
            <CheckCircle2 size={16} /> Resolved
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Fact label="Status"><StatusBadge status={incident.status} /></Fact>
        <Fact label="Affected customers">{incident.affected_customer_count}</Fact>
        <Fact label="OLT">{incident.olt_id ?? "—"}</Fact>
        <Fact label="Area">{incident.location_name ?? "—"}</Fact>
        <Fact label="Detected">{new Date(incident.detected_at).toLocaleTimeString()}</Fact>
        <Fact label="Duration">{incident.duration_minutes} min</Fact>
        <Fact label="Technician">{incident.assigned_technician_name ?? "Unassigned"}</Fact>
        <Fact label="Type">{incident.incident_type}</Fact>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-surface border border-border rounded-lg p-5">
          <h2 className="text-sm font-medium mb-3">Telemetry</h2>
          <div className="grid grid-cols-2 gap-3 text-sm font-mono">
            <TelemetryRow label="Router Reachability" value="ONLINE" tone="healthy" />
            <TelemetryRow label="WAN" value={wanDown ? "DOWN" : "UP"} tone={wanDown ? "critical" : "healthy"} />
            <TelemetryRow label="LAN" value="NORMAL" tone="healthy" />
            <TelemetryRow label="Internet Reachability" value={isResolved ? "RESTORED" : "FAILED"} tone={isResolved ? "healthy" : "critical"} />
            <TelemetryRow label="Packet Loss" value={isResolved ? "0%" : "100%"} tone={isResolved ? "healthy" : "critical"} />
            <TelemetryRow label="Affected CPEs" value={String(incident.affected_customer_count)} tone="neutral" />
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium">Probable Cause Engine</h2>
            <span className="text-[10px] font-mono text-text-faint uppercase">AI-assisted, not confirmed</span>
          </div>
          <div className="text-lg font-semibold">{incident.probable_cause}</div>
          <div className="text-xs text-text-muted mt-1">
            Confidence: <span className="text-text">{incident.probable_cause_confidence}</span>
          </div>
          <div className="mt-3">
            <div className="text-xs text-text-faint mb-1.5">Why?</div>
            <ul className="text-sm space-y-1 list-disc list-inside text-text-muted">
              {incident.probable_cause_reasons.map((r, idx) => <li key={idx}>{r}</li>)}
            </ul>
          </div>
          <p className="text-[11px] text-text-faint mt-3 border-t border-border pt-3">
            This is a probable diagnosis based on correlated telemetry — not a confirmed physical fault.
          </p>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg p-5">
        <h2 className="text-sm font-medium mb-3">Recommended Investigation</h2>
        <ol className="text-sm space-y-1.5 list-decimal list-inside text-text-muted">
          {incident.recommended_checks.map((c, idx) => <li key={idx}>{c}</li>)}
        </ol>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-surface border border-border rounded-lg p-5">
          <h2 className="text-sm font-medium mb-3">Incident Timeline</h2>
          <ol className="space-y-3 max-h-72 overflow-y-auto pr-1">
            {incident.events.map((e, idx) => (
              <li key={idx} className="flex gap-3 text-sm">
                <span className="font-mono text-text-faint w-16 shrink-0">
                  {new Date(e.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
                <span className="text-text-muted">{e.message}</span>
              </li>
            ))}
          </ol>
        </div>

        <div className="bg-surface border border-border rounded-lg p-5 space-y-5">
          <div>
            <h2 className="text-sm font-medium mb-2">Assign Technician</h2>
            <div className="flex flex-wrap gap-2">
              {technicians.filter((t) => t.status !== "Offline").slice(0, 6).map((t) => (
                <button
                  key={t.id}
                  disabled={busy}
                  onClick={() => assign(t.id)}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-border-strong hover:border-pulse hover:text-pulse transition-colors disabled:opacity-50"
                >
                  {t.name} · {t.region}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h2 className="text-sm font-medium mb-2">Update Status</h2>
            <div className="flex flex-wrap gap-2">
              {STATUS_FLOW.map((s) => (
                <button
                  key={s}
                  disabled={busy || s === incident.status}
                  onClick={() => setStatus(s)}
                  className={`text-xs px-2.5 py-1.5 rounded-md border transition-colors disabled:opacity-40 ${
                    s === incident.status
                      ? "border-pulse text-pulse bg-pulse-dim"
                      : "border-border-strong text-text-muted hover:text-text"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h2 className="text-sm font-medium mb-2">Notifications sent for this incident</h2>
            <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
              {notifications.length === 0 && <p className="text-xs text-text-faint">None yet.</p>}
              {notifications.map((n) => (
                <div key={n.id} className="text-xs flex items-center justify-between gap-2 text-text-muted">
                  <span>{n.recipient_type === "technician" ? "📟" : "📱"} {n.masked_destination}</span>
                  <span className="font-mono text-text-faint">{n.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-surface border border-border rounded-lg px-3.5 py-3">
      <div className="text-[10px] text-text-faint uppercase tracking-wide mb-1">{label}</div>
      <div className="text-sm">{children}</div>
    </div>
  );
}

function TelemetryRow({ label, value, tone }: { label: string; value: string; tone: "healthy" | "critical" | "neutral" }) {
  const color = tone === "healthy" ? "text-healthy" : tone === "critical" ? "text-critical" : "text-text";
  return (
    <div className="bg-surface-raised rounded-md px-3 py-2">
      <div className="text-[10px] text-text-faint">{label}</div>
      <div className={color}>{value}</div>
    </div>
  );
}
