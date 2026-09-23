import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Customer } from "../types";

function newSessionId() {
  return `sim-${Math.random().toString(36).slice(2, 10)}`;
}

export default function UssdSimulator() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerId, setCustomerId] = useState<string>("");
  const [sessionId, setSessionId] = useState(newSessionId());
  const [path, setPath] = useState<string[]>([]);
  const [screen, setScreen] = useState("Dial *384*NETPULSE# to begin.");
  const [ended, setEnded] = useState(true);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.customers().then((c) => {
      setCustomers(c);
      if (c.length) setCustomerId(c[0].id);
    });
  }, []);

  async function send(nextPath: string[]) {
    setLoading(true);
    try {
      const text = nextPath.join("*");
      const res = await api.ussd({ sessionId, phoneNumber: "254700000000", text, customer_id: customerId });
      const isEnd = res.startsWith("END");
      setScreen(res.replace(/^CON |^END /, ""));
      setEnded(isEnd);
      setPath(nextPath);
    } finally {
      setLoading(false);
    }
  }

  function dial() {
    const sid = newSessionId();
    setSessionId(sid);
    setPath([]);
    setInput("");
    send([]);
  }

  function submit() {
    if (!input.trim()) return;
    const next = [...path, input.trim()];
    setInput("");
    send(next);
  }

  function hangUp() {
    setEnded(true);
    setPath([]);
    setScreen("Dial *384*NETPULSE# to begin.");
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">USSD Simulator</h1>
        <p className="text-text-muted text-sm">
          Try the customer self-service flow exactly as it runs on a feature phone — no telecom SIM required.
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-6 items-start">
        <div className="w-full max-w-[280px] mx-auto md:mx-0">
          <div className="bg-surface border-2 border-border-strong rounded-[28px] p-3 shadow-xl">
            <div className="bg-black rounded-2xl p-4 min-h-[320px] flex flex-col">
              <div className="text-center text-[10px] text-healthy font-mono mb-2">● NETPULSE NETWORK</div>
              <div className="flex-1 bg-[#0d1a12] text-[#7ef7a0] font-mono text-[13px] leading-relaxed rounded-md p-3 whitespace-pre-wrap">
                {loading ? "Sending…" : screen}
              </div>
              {!ended && (
                <input
                  autoFocus
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && submit()}
                  placeholder="Type your choice…"
                  className="mt-2 bg-[#0d1a12] text-[#7ef7a0] font-mono text-sm rounded-md px-2 py-1.5 outline-none border border-[#1c3324]"
                />
              )}
            </div>
            <div className="flex gap-2 mt-3">
              {ended ? (
                <button
                  onClick={dial}
                  className="flex-1 bg-pulse text-[#04231f] rounded-md py-2 text-sm font-semibold"
                >
                  Dial *384*NETPULSE#
                </button>
              ) : (
                <>
                  <button
                    onClick={submit}
                    disabled={loading}
                    className="flex-1 bg-pulse text-[#04231f] rounded-md py-2 text-sm font-semibold disabled:opacity-60"
                  >
                    Send
                  </button>
                  <button onClick={hangUp} className="px-3 rounded-md border border-critical/40 text-critical text-sm">
                    End
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-5 flex-1 w-full">
          <h2 className="text-sm font-medium mb-3">Simulated Subscriber</h2>
          <p className="text-xs text-text-muted mb-3">
            Choose which customer's account this session belongs to — in production the phone number
            from the real USSD request resolves this automatically.
          </p>
          <select
            value={customerId}
            onChange={(e) => { setCustomerId(e.target.value); hangUp(); }}
            className="w-full bg-surface-raised border border-border rounded-md px-3 py-2 text-sm outline-none focus:border-pulse"
          >
            {customers.map((c) => (
              <option key={c.id} value={c.id}>{c.name} — {c.id} ({c.olt_id ?? "no OLT"})</option>
            ))}
          </select>

          <div className="mt-5 text-xs text-text-faint space-y-1.5 font-mono">
            <div>1. Check my connection</div>
            <div>2. Report a problem</div>
            <div>3. Check outage status</div>
            <div>4. Contact support</div>
          </div>
          <p className="text-[11px] text-text-faint mt-4">
            Tip: trigger "Simulate Area Outage" on the Dashboard first, then dial in and select
            option 3 to see the outage reflected here in real time.
          </p>
        </div>
      </div>
    </div>
  );
}
