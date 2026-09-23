import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Incident } from "../types";

const LAYERS = [
  { key: "core", label: "ISP Core", desc: "Upstream internet connectivity" },
  { key: "aggregation", label: "Aggregation Network", desc: "Regional backhaul" },
  { key: "olt", label: "OLT", desc: "Optical Line Terminal per area" },
  { key: "odf", label: "ODF", desc: "Optical Distribution Frame" },
  { key: "fibre", label: "Access Fibre", desc: "Fibre run to the customer" },
  { key: "ont", label: "ONT / ONU", desc: "Optical network terminal at the premises" },
  { key: "cpe", label: "Customer Router", desc: "The customer's own router / CPE" },
];

export default function Topology() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    const refresh = () =>
      api.incidents().then((all) => setIncidents(all.filter((i) => i.status !== "Resolved" && i.status !== "Closed")));
    refresh();
    const iv = setInterval(refresh, 4000);
    return () => clearInterval(iv);
  }, []);

  // Access-network incidents affect OLT/ODF/Fibre; device-level incidents affect ONT/CPE.
  const affectedLayers = new Set<string>();
  for (const i of incidents) {
    if (i.incident_type === "WAN/access connectivity issue" || i.incident_type === "Severe connectivity degradation") {
      affectedLayers.add("olt"); affectedLayers.add("odf"); affectedLayers.add("fibre");
    }
    if (i.incident_type === "Device unreachable") {
      affectedLayers.add("ont"); affectedLayers.add("cpe");
    }
    if (i.incident_type === "Network degradation/congestion") {
      affectedLayers.add("aggregation");
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Topology</h1>
        <p className="text-text-muted text-sm">
          Simplified network path. {incidents.length > 0 ? "Affected sections are highlighted." : "All sections nominal."}
        </p>
      </div>

      <div className="bg-surface border border-border rounded-lg p-8">
        <div className="flex flex-col items-center gap-2 max-w-md mx-auto">
          {LAYERS.map((layer, idx) => {
            const affected = affectedLayers.has(layer.key);
            return (
              <div key={layer.key} className="w-full">
                <button
                  onClick={() => setSelected(layer.key)}
                  className={`w-full flex items-center justify-between rounded-lg border px-4 py-3 transition-colors ${
                    affected
                      ? "border-critical/50 bg-critical/10 text-critical"
                      : "border-border-strong bg-surface-raised text-text hover:border-pulse/50"
                  } ${selected === layer.key ? "ring-1 ring-pulse" : ""}`}
                >
                  <span className="font-medium text-sm">{layer.label}</span>
                  {affected && <span className="text-[10px] font-mono uppercase">Affected</span>}
                </button>
                {idx < LAYERS.length - 1 && (
                  <div className="flex justify-center py-1">
                    <div className={`w-px h-4 ${affected || affectedLayers.has(LAYERS[idx + 1]?.key) ? "bg-critical/50" : "bg-border-strong"}`} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {selected && (
          <div className="mt-6 text-center text-sm text-text-muted">
            {LAYERS.find((l) => l.key === selected)?.desc}
          </div>
        )}
      </div>
    </div>
  );
}
