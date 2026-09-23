import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { api } from "../api/client";
import type { Customer } from "../types";
import { HealthDot } from "../components/Badges";

export default function Customers() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [q, setQ] = useState("");

  async function refresh() {
    setCustomers(await api.customers(q || undefined));
  }

  useEffect(() => {
    const t = setTimeout(refresh, 250);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    const iv = setInterval(refresh, 6000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Customers</h1>
          <p className="text-text-muted text-sm">{customers.length} shown · phone numbers are masked by default.</p>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-faint" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by name…"
            className="bg-surface border border-border rounded-md pl-8 pr-3 py-1.5 text-sm outline-none focus:border-pulse w-56"
          />
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-text-faint text-xs">
              <Th>Customer ID</Th><Th>Name</Th><Th>Phone</Th><Th>Plan</Th><Th>OLT</Th><Th>Location</Th><Th>Status</Th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id} className="border-t border-border hover:bg-surface-raised/50">
                <Td className="font-mono text-text-muted">{c.id}</Td>
                <Td>{c.name}</Td>
                <Td className="font-mono text-text-muted">{c.masked_phone}</Td>
                <Td className="text-text-muted">{c.plan}</Td>
                <Td className="font-mono text-text-muted">{c.olt_id ?? "—"}</Td>
                <Td className="text-text-muted">{c.location?.name ?? "—"}</Td>
                <Td>
                  {c.device_health && <HealthDot health={c.device_health} label={c.device_health === "healthy" ? "Online" : c.device_health === "degraded" ? "Degraded" : "Offline"} />}
                </Td>
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
