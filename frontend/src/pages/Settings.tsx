import { useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";
import { api } from "../api/client";

export default function Settings() {
  const [demoMode, setDemoMode] = useState<{ demo_sms_mode: boolean; banner: string | null } | null>(null);
  const [resetting, setResetting] = useState(false);
  const [resetDone, setResetDone] = useState(false);
  const user = JSON.parse(localStorage.getItem("netpulse_user") || "{}");

  useEffect(() => {
    api.demoModeStatus().then(setDemoMode);
  }, []);

  async function resetDemo() {
    setResetting(true);
    setResetDone(false);
    try {
      await api.resetDemo();
      setResetDone(true);
    } finally {
      setResetting(false);
      setTimeout(() => setResetDone(false), 3000);
    }
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <div>
        <h1 className="text-lg font-semibold">Settings</h1>
        <p className="text-text-muted text-sm">Demo configuration for this NetPulse instance.</p>
      </div>

      <div className="bg-surface border border-border rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Demo Mode</div>
            <p className="text-xs text-text-muted mt-0.5">
              Simulated telemetry is active, faults can be triggered manually, and SMS/USSD run without
              real telecom infrastructure.
            </p>
          </div>
          <span className="text-xs font-mono uppercase bg-pulse-dim text-pulse rounded px-2.5 py-1">Enabled</span>
        </div>

        <div className="border-t border-border pt-4 flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Africa's Talking SMS</div>
            <p className="text-xs text-text-muted mt-0.5">
              {demoMode?.demo_sms_mode
                ? "No sandbox credentials configured — messages are simulated and clearly labeled."
                : "Connected to the Africa's Talking sandbox."}
            </p>
          </div>
          <span
            className={`text-xs font-mono uppercase rounded px-2.5 py-1 ${
              demoMode?.demo_sms_mode ? "bg-warning/10 text-warning" : "bg-healthy/10 text-healthy"
            }`}
          >
            {demoMode?.demo_sms_mode ? "Simulated" : "Live sandbox"}
          </span>
        </div>

        <div className="border-t border-border pt-4 flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Signed in as</div>
            <p className="text-xs text-text-muted mt-0.5">{user.full_name} · {user.email}</p>
          </div>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg p-5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Reset Demo</div>
            <p className="text-xs text-text-muted mt-0.5">
              Clears all incidents, telemetry and simulation state, and re-seeds the demo network from scratch.
            </p>
          </div>
          <button
            onClick={resetDemo}
            disabled={resetting}
            className="flex items-center gap-2 text-xs px-3 py-2 rounded-md border border-border-strong hover:border-critical hover:text-critical transition-colors disabled:opacity-50"
          >
            <RotateCcw size={14} className={resetting ? "animate-spin" : ""} />
            {resetting ? "Resetting…" : "Reset Demo"}
          </button>
        </div>
        {resetDone && <p className="text-xs text-healthy mt-3">Demo reset — fresh network state loaded.</p>}
      </div>
    </div>
  );
}
