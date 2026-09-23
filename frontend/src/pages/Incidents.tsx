import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Incident } from "../types";
import { SeverityBadge, StatusBadge } from "../components/Badges";

const FILTERS = ["All", "Detected", "Investigating", "Assigned", "In Progress", "Resolved", "Closed"];

export default function Incidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [filter, setFilter] = useState("All");

  async function refresh() {
    const data = await api.incidents(filter === "All" ? undefined : filter);
    setIncidents(data);
  }

  useEffect(() => {
    refresh();
    const iv = setInterval(refresh, 5000);
    return () => clearInterval(iv);
  }, [filter]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Incidents</h1>
        <p className="text-text-muted text-sm">Every correlated incident — active and historical.</p>
      </div>

      <div className="flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
              filter === f ? "border-pulse text-pulse bg-pulse-dim" : "border-border-strong text-text-muted hover:text-text"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-text-faint text-xs">
              <Th>ID</Th><Th>Location</Th><Th>Type</Th><Th>Severity</Th>
              <Th>Affected</Th><Th>OLT</Th><Th>Detected</Th><Th>Duration</Th><Th>Status</Th><Th>Technician</Th>
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
                <Td className="text-text-muted">{new Date(i.detected_at).toLocaleString()}</Td>
                <Td className="font-mono text-text-muted">{i.duration_minutes} min</Td>
                <Td><StatusBadge status={i.status} /></Td>
                <Td className="text-text-muted">{i.assigned_technician_name ?? "Unassigned"}</Td>
              </tr>
            ))}
            {incidents.length === 0 && (
              <tr><td colSpan={10} className="text-center text-text-muted py-8">No incidents match this filter.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left font-normal px-5 py-2.5">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-5 py-3 ${className}`}>{children}</td>;
}
