import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PulseLogo } from "../components/Layout";
import { api } from "../api/client";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDemoLogin() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.demoLogin();
      localStorage.setItem("netpulse_token", res.token);
      localStorage.setItem("netpulse_user", JSON.stringify(res.user));
      navigate("/");
    } catch (e: any) {
      setError("Could not reach the NetPulse API. Is the backend running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("Production sign-in isn't wired up in this demo — use Demo Login below.");
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <PulseLogo size={44} />
          <h1 className="mt-4 text-xl font-semibold tracking-tight">NetPulse</h1>
          <p className="text-text-muted text-sm mt-1 font-mono">Detect. Diagnose. Notify. Restore.</p>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-text-muted mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@isp.africa"
                className="w-full bg-surface-raised border border-border rounded-md px-3 py-2 text-sm outline-none focus:border-pulse"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-surface-raised border border-border rounded-md px-3 py-2 text-sm outline-none focus:border-pulse"
              />
            </div>
            {error && <p className="text-xs text-warning">{error}</p>}
            <button
              type="submit"
              className="w-full bg-surface-raised border border-border-strong text-text rounded-md py-2 text-sm font-medium hover:border-pulse transition-colors"
            >
              Sign in
            </button>
          </form>

          <div className="flex items-center gap-3 my-5">
            <div className="h-px bg-border flex-1" />
            <span className="text-[11px] text-text-faint">FOR HACKATHON JUDGES</span>
            <div className="h-px bg-border flex-1" />
          </div>

          <button
            onClick={handleDemoLogin}
            disabled={loading}
            className="w-full bg-pulse text-[#04231f] rounded-md py-2 text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Demo Login"}
          </button>
          <p className="text-[11px] text-text-faint mt-2 text-center">
            Uses a separate demo account — no production credentials required.
          </p>
        </div>
      </div>
    </div>
  );
}
