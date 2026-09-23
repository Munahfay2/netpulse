import { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line,
} from "recharts";
import { api } from "../api/client";
import type { Incident } from "../types";

const RANGES = [
  { key: "today", label: "Today", days: 1 },
  { key: "7d", label: "7 Days", days: 7 },
  { key: "30d", label: "30 Days", days: 30 },
  { key: "90d", label: "90 Days", days: 90 },
];

const PIE_COLORS = ["#2dd4bf", "#5b9dfa", "#f5a524", "#f0465b", "#34d399"];

export default function Analytics() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [range, setRange] = useState("30d");

  useEffect(() => {
    api.incidents().then(setIncidents);
    const iv = setInterval(() => api.incidents().then(setIncidents), 8000);
    return () => clearInterval(iv);
  }, []);

  const filtered = useMemo(() => {
    const days = RANGES.find((r) => r.key === range)?.days ?? 30;
    const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
    return incidents.filter((i) => new Date(i.detected_at).getTime() >= cutoff);
  }, [incidents, range]);

  const byDay = useMemo(() => {
    const map = new Map<string, number>();
    for (const i of filtered) {
      const day = new Date(i.detected_at).toLocaleDateString(undefined, { month: "short", day: "numeric" });
      map.set(day, (map.get(day) ?? 0) + 1);
    }
    return Array.from(map.entries()).map(([day, count]) => ({ day, count }));
  }, [filtered]);

  const byType = useMemo(() => {
    const map = new Map<string, number>();
    for (const i of filtered) map.set(i.incident_type, (map.get(i.incident_type) ?? 0) + 1);
    return Array.from(map.entries()).map(([name, value]) => ({ name, value }));
  }, [filtered]);

  const byLocation = useMemo(() => {
    const map = new Map<string, number>();
    for (const i of filtered) {
      const loc = i.location_name ?? "Unknown";
      map.set(loc, (map.get(loc) ?? 0) + 1);
    }
    return Array.from(map.entries()).map(([name, incidents]) => ({ name, incidents }));
  }, [filtered]);

  const byOlt = useMemo(() => {
    const map = new Map<string, number>();
    for (const i of filtered) {
      if (!i.olt_id) continue;
      map.set(i.olt_id, (map.get(i.olt_id) ?? 0) + i.affected_customer_count);
    }
    return Array.from(map.entries())
      .map(([olt_id, customers]) => ({ olt_id, customers }))
      .sort((a, b) => b.customers - a.customers)
      .slice(0, 6);
  }, [filtered]);

  const resolved = filtered.filter((i) => i.resolved_at);
  const avgResolution = resolved.length
    ? resolved.reduce((sum, i) => sum + (i.duration_minutes ?? 0), 0) / resolved.length
    : 0;
  const totalCustomersAffected = filtered.reduce((sum, i) => sum + i.affected_customer_count, 0);
  const repeatOlts = byOlt.filter((o) => o.customers > 0).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Analytics</h1>
          <p className="text-text-muted text-sm">Network reliability trends across the selected period.</p>
        </div>
        <div className="flex gap-2">
          {RANGES.map((r) => (
            <button
              key={r.key}
              onClick={() => setRange(r.key)}
              className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
                range === r.key ? "border-pulse text-pulse bg-pulse-dim" : "border-border-strong text-text-muted hover:text-text"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Incidents" value={filtered.length} />
        <Stat label="Customers Affected" value={totalCustomersAffected} />
        <Stat label="Avg. Resolution" value={`${avgResolution.toFixed(1)} min`} />
        <Stat label="OLTs With Incidents" value={repeatOlts} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Incidents Per Day">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={byDay}>
              <CartesianGrid stroke="#232d38" vertical={false} />
              <XAxis dataKey="day" stroke="#5b6b7a" fontSize={11} />
              <YAxis stroke="#5b6b7a" fontSize={11} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#111820", border: "1px solid #232d38", fontSize: 12 }} />
              <Line type="monotone" dataKey="count" stroke="#2dd4bf" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Incidents By Type">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={byType} dataKey="value" nameKey="name" innerRadius={45} outerRadius={80} paddingAngle={2}>
                {byType.map((_, idx) => <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#111820", border: "1px solid #232d38", fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Incidents By Location">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byLocation}>
              <CartesianGrid stroke="#232d38" vertical={false} />
              <XAxis dataKey="name" stroke="#5b6b7a" fontSize={11} />
              <YAxis stroke="#5b6b7a" fontSize={11} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#111820", border: "1px solid #232d38", fontSize: 12 }} />
              <Bar dataKey="incidents" fill="#5b9dfa" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Most Affected OLTs (customers impacted)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byOlt} layout="vertical">
              <CartesianGrid stroke="#232d38" horizontal={false} />
              <XAxis type="number" stroke="#5b6b7a" fontSize={11} allowDecimals={false} />
              <YAxis type="category" dataKey="olt_id" stroke="#5b6b7a" fontSize={11} width={70} />
              <Tooltip contentStyle={{ background: "#111820", border: "1px solid #232d38", fontSize: 12 }} />
              <Bar dataKey="customers" fill="#f5a524" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="text-xs text-text-muted mb-1">{label}</div>
      <div className="text-xl font-semibold font-mono">{value}</div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      <h2 className="text-sm font-medium mb-3">{title}</h2>
      {children}
    </div>
  );
}
