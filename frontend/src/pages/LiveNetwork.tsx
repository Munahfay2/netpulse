import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { LocationSummary } from "../types";

const STATUS_COLOR: Record<string, string> = {
  healthy: "#34d399",
  warning: "#f5a524",
  critical: "#f0465b",
};

export default function LiveNetwork() {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [selectedOlt, setSelectedOlt] = useState<{ locationName: string; id: string; name: string; online: number; degraded: number; offline: number; active_incidents: number; status: string } | null>(null);

  useEffect(() => {
    const refresh = () => api.networkOverview().then(setLocations);
    refresh();
    const iv = setInterval(refresh, 4000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Live Network</h1>
        <p className="text-text-muted text-sm">Simulated regional view — node color reflects live OLT health.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {locations.map((loc) => (
          <div key={loc.id} className="bg-surface border border-border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="font-medium">{loc.name}</div>
              <span className="text-[10px] text-text-faint font-mono">{loc.region}</span>
            </div>
            <div className="space-y-2">
              {loc.olts.map((olt) => (
                <button
                  key={olt.id}
                  onClick={() => setSelectedOlt({ locationName: loc.name, ...olt })}
                  className="w-full flex items-center justify-between text-sm bg-surface-raised hover:bg-surface-raised/70 rounded-md px-3 py-2 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${olt.status === "critical" ? "pulse-live" : ""}`}
                      style={{ backgroundColor: STATUS_COLOR[olt.status] }}
                    />
                    <span className="font-mono">{olt.id}</span>
                  </span>
                  <span className="text-text-faint font-mono text-xs">
                    {olt.online}/{olt.online + olt.degraded + olt.offline} online
                  </span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {selectedOlt && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedOlt(null)}>
          <div className="bg-surface border border-border rounded-lg p-6 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold font-mono">{selectedOlt.id}</h3>
              <span
                className="text-xs font-mono px-2 py-0.5 rounded"
                style={{ color: STATUS_COLOR[selectedOlt.status], backgroundColor: STATUS_COLOR[selectedOlt.status] + "22" }}
              >
                {selectedOlt.status.toUpperCase()}
              </span>
            </div>
            <p className="text-text-muted text-sm mb-4">{selectedOlt.locationName}</p>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div><div className="text-lg font-mono text-healthy">{selectedOlt.online}</div><div className="text-[10px] text-text-faint">ONLINE</div></div>
              <div><div className="text-lg font-mono text-warning">{selectedOlt.degraded}</div><div className="text-[10px] text-text-faint">DEGRADED</div></div>
              <div><div className="text-lg font-mono text-critical">{selectedOlt.offline}</div><div className="text-[10px] text-text-faint">OFFLINE</div></div>
            </div>
            <div className="mt-4 text-sm text-text-muted">
              Active incidents: <span className="text-text">{selectedOlt.active_incidents}</span>
            </div>
            <button
              onClick={() => setSelectedOlt(null)}
              className="mt-5 w-full text-sm border border-border-strong rounded-md py-2 hover:text-text text-text-muted"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
