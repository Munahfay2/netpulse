import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, AlertOctagon, Users, WifiOff, Timer, TrendingUp } from "lucide-react";
import { api } from "../api/client";
import type { DashboardSummary, Incident } from "../types";
import { KpiCard } from "../components/KpiCard";
import { SeverityBadge, StatusBadge } from "../components/Badges";

const SIM_BUTTONS: { key: string; label: string; tone: "neutral" | "warning" | "critical" }[] = [
  { key: "normal", label: "Simulate Normal Network", tone: "neutral" },
  { key: "single-failure", label: "Simulate Single Customer Failure", tone: "warning" },
  { key: "high-latency", label: "Simulate High Latency", tone: "warning" },
  { key: "packet-loss", label: "Simulate Packet Loss", tone: "warning" },
  { key: "wan-failure", label: "Simulate WAN Failure", tone: "critical" },
  { key: "olt-failure", label: "Simulate OLT Failure", tone: "critical" },
  { key: "area-outage", label: "Simulate Area Outage", tone: "critical" },
  { key: "restore", label: "Restore All Services", tone: "neutral" },
];

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  async function refresh() {
    const [s, inc] = await Promise.all([api.dashboardSummary(), api.incidents()]);
    setSummary(s);
    setIncidents(inc.filter((i) => i.status !== "Resolved" && i.status !== "Closed").slice(0, 8));
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, []);

  async function runSimulation(key: string) {
    setBusy(key);
    try {
      await api.simulate(key);
      setToast(
        key === "restore"
          ? "Restoring services — telemetry will normalize within a few seconds."
          : `Scenario triggered: ${key.replace("-", " ")}. Watch the incidents table below.`
      );
      setTimeout(() => setToast(null), 4000);
    } finally {
      setBusy(null);
    }
  }

  if (!summary) return <div className="text-text-muted text-sm">Loading network state…</div>;

  const healthTone = summary.network_health_percent >= 98 ? "healthy" : summary.network_health_percent >= 90 ? "warning" : "critical";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Network Operations Center</h1>
          <p className="text-text-muted text-sm">Live view across all monitored infrastructure.</p>
        </div>
        {toast && (
          <div className="text-xs bg-pulse-dim text-pulse border border-pulse/30 rounded-md px-3 py-1.5 rise-in">
            {toast}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        <KpiCard label="Network Health" value={summary.network_health_percent} unit="%" tone={healthTone} icon={<Activity size={14} />} />
        <KpiCard label="Active Incidents" value={summary.active_incidents} tone={summary.active_incidents > 0 ? "critical" : "healthy"} icon={<AlertOctagon size={14} />} />
        <KpiCard label="Customers Affected" value={summary.customers_affected} tone={summary.customers_affected > 0 ? "warning" : "healthy"} icon={<Users size={14} />} />
        <KpiCard label="Devices Offline" value={summary.devices_offline} tone={summary.devices_offline > 0 ? "critical" : "healthy"} icon={<WifiOff size={14} />} />
        <KpiCard label="Avg. Resolution Time" value={summary.avg_resolution_minutes} unit="min" icon={<Timer size={14} />} />
        <KpiCard label="Incidents Today" value={summary.incidents_today} icon={<TrendingUp size={14} />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-surface border border-border rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium">Network Health Overview</h2>
          </div>
          <div className="grid grid-cols-4 gap-3">
            <HealthStat label="ONLINE" value={summary.devices_online} color="#34d399" />
            <HealthStat label="DEGRADED" value={summary.devices_degraded} color="#f5a524" />
            <HealthStat label="OFFLINE" value={summary.devices_offline} color="#f0465b" />
            <HealthStat label="TOTAL DEVICES" value={summary.devices_online + summary.devices_degraded + summary.devices_offline} color="#8b99a8" />
          </div>
          <div className="mt-5 h-2 rounded-full overflow-hidden bg-surface-raised flex">
            {(() => {
              const total = summary.devices_online + summary.devices_degraded + summary.devices_offline || 1;
              return (
                <>
                  <div style={{ width: `${(summary.devices_online / total) * 100}%`, backgroundColor: "#34d399" }} />
                  <div style={{ width: `${(summary.devices_degraded / total) * 100}%`, backgroundColor: "#f5a524" }} />
                  <div style={{ width: `${(summary.devices_offline / total) * 100}%`, backgroundColor: "#f0465b" }} />
                </>
              );
            })()}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-5">
          <h2 className="text-sm font-medium mb-4">Fault Simulator</h2>
          <div className="grid grid-cols-1 gap-2">
            {SIM_BUTTONS.map((b) => (
              <button
                key={b.key}
                onClick={() => runSimulation(b.key)}
                disabled={busy !== null}
                className={`text-left text-xs px-3 py-2 rounded-md border transition-colors disabled:opacity-50 ${
                  b.tone === "critical"
                    ? "border-critical/30 text-critical hover:bg-critical/10"
                    : b.tone === "warning"
                    ? "border-warning/30 text-warning hover:bg-warning/10"
                    : "border-border-strong text-text-muted hover:text-text hover:bg-surface-raised"
                }`}
              >
                {busy === b.key ? "Running…" : b.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg">
        <div className="flex items-center justify-between p-5 pb-3">
          <h2 className="text-sm font-medium">Active Incidents</h2>
          <Link to="/incidents" className="text-xs text-pulse hover:underline">View all</Link>
        </div>
        {incidents.length === 0 ? (
          <div className="px-5 pb-6 text-sm text-text-muted">No active incidents. Network is healthy.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-text-faint text-xs border-t border-border">
                <Th>ID</Th><Th>Location</Th><Th>Type</Th><Th>Severity</Th>
                <Th>Affected</Th><Th>OLT</Th><Th>Duration</Th><Th>Status</Th><Th>Technician</Th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((i) => (
                <tr key={i.id} className="border-t border-border hover:bg-surface-raised/50">
                  <Td><Link to={`/incidents/${i.id}`} className="font-mono text-pulse hover:underline">{i.id}</Link></Td>
                  <Td>{i.location_name ?? "—"}</Td>
                  <Td className="text-text-muted">{i.incident_type}</Td>
                  <Td><SeverityBadge severity={i.severity} /></Td>
                  <Td className="font-mono">{i.affected_customer_count}</Td>
                  <Td className="font-mono text-text-muted">{i.olt_id ?? "—"}</Td>
                  <Td className="font-mono text-text-muted">{i.duration_minutes} min</Td>
                  <Td><StatusBadge status={i.status} /></Td>
                  <Td className="text-text-muted">{i.assigned_technician_name ?? "Unassigned"}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function HealthStat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="text-[10px] text-text-faint font-mono tracking-wide mb-1">{label}</div>
      <div className="text-xl font-semibold font-mono" style={{ color }}>{value.toLocaleString()}</div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left font-normal px-5 py-2">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-5 py-3 ${className}`}>{children}</td>;
}
