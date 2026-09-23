import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Device } from "../types";
import { HealthDot } from "../components/Badges";

const FILTERS = [
  { key: "", label: "All" },
  { key: "healthy", label: "Online" },
  { key: "degraded", label: "Degraded" },
  { key: "offline", label: "Offline" },
];

export default function Devices() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [filter, setFilter] = useState("");

  async function refresh() {
    setDevices(await api.devices(filter ? { health: filter } : {}));
  }

  useEffect(() => {
    refresh();
    const iv = setInterval(refresh, 4000);
    return () => clearInterval(iv);
  }, [filter]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Devices</h1>
        <p className="text-text-muted text-sm">Customer premises equipment across the network.</p>
      </div>

      <div className="flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
              filter === f.key ? "border-pulse text-pulse bg-pulse-dim" : "border-border-strong text-text-muted hover:text-text"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-text-faint text-xs">
              <Th>Device ID</Th><Th>OLT</Th><Th>Router</Th><Th>WAN</Th><Th>LAN</Th>
              <Th>Latency</Th><Th>Packet Loss</Th><Th>Health</Th><Th>Last Seen</Th>
            </tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.id} className="border-t border-border hover:bg-surface-raised/50">
                <Td className="font-mono text-text-muted">{d.id}</Td>
                <Td className="font-mono text-text-muted">{d.olt_id}</Td>
                <Td className="font-mono">{d.router_status}</Td>
                <Td className="font-mono">{d.wan_status}</Td>
                <Td className="font-mono">{d.lan_status}</Td>
                <Td className="font-mono">{d.latency_ms.toFixed(0)} ms</Td>
                <Td className="font-mono">{d.packet_loss_percent.toFixed(1)}%</Td>
                <Td><HealthDot health={d.health} /></Td>
                <Td className="text-text-muted">{new Date(d.last_seen).toLocaleTimeString()}</Td>
              </tr>
            ))}
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
