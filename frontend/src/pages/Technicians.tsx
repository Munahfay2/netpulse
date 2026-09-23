import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Technician } from "../types";

const STATUS_COLORS: Record<string, string> = {
  Available: "text-healthy",
  "On Job": "text-warning",
  Offline: "text-text-faint",
};

export default function Technicians() {
  const [technicians, setTechnicians] = useState<Technician[]>([]);

  useEffect(() => {
    const refresh = () => api.technicians().then(setTechnicians);
    refresh();
    const iv = setInterval(refresh, 5000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Technicians</h1>
        <p className="text-text-muted text-sm">Field team availability and current assignments.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {technicians.map((t) => (
          <div key={t.id} className="bg-surface border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="font-medium">{t.name}</div>
              <span className={`text-xs font-mono ${STATUS_COLORS[t.status]}`}>{t.status}</span>
            </div>
            <div className="text-text-muted text-sm mt-1">{t.region}</div>
            <div className="flex items-center justify-between mt-3 text-xs text-text-faint font-mono">
              <span>{t.phone.slice(0, 5)}*****{t.phone.slice(-2)}</span>
              <span>{t.active_incidents} active incident{t.active_incidents === 1 ? "" : "s"}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
