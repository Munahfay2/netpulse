import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Radio, AlertTriangle, Users, Router,
  Share2, Wrench, BarChart3, Bell, Smartphone, Settings, LogOut,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/live-network", label: "Live Network", icon: Radio },
  { to: "/incidents", label: "Incidents", icon: AlertTriangle },
  { to: "/customers", label: "Customers", icon: Users },
  { to: "/devices", label: "Devices", icon: Router },
  { to: "/topology", label: "Topology", icon: Share2 },
  { to: "/technicians", label: "Technicians", icon: Wrench },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/ussd", label: "USSD Simulator", icon: Smartphone },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const [userName, setUserName] = useState("Demo NOC Operator");
  const [ispName, setIspName] = useState("Rift Valley Networks (Demo)");
  const [activeIncidents, setActiveIncidents] = useState(0);

  useEffect(() => {
    const raw = localStorage.getItem("netpulse_user");
    if (raw) {
      const u = JSON.parse(raw);
      setUserName(u.full_name);
      setIspName(u.isp_name);
    }
    const poll = () => api.dashboardSummary().then((d) => setActiveIncidents(d.active_incidents)).catch(() => {});
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, []);

  function logout() {
    localStorage.removeItem("netpulse_token");
    localStorage.removeItem("netpulse_user");
    navigate("/login");
  }

  return (
    <div className="flex h-screen bg-base text-text">
      <aside className="w-60 shrink-0 border-r border-border bg-surface flex flex-col">
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-border">
          <PulseLogo />
          <div>
            <div className="font-semibold tracking-tight leading-none">NetPulse</div>
            <div className="text-[10px] text-text-faint font-mono leading-none mt-1">NOC CONSOLE</div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-surface-raised text-text font-medium"
                    : "text-text-muted hover:text-text hover:bg-surface-raised/60"
                }`
              }
            >
              <item.icon size={16} strokeWidth={2} />
              {item.label}
              {item.to === "/incidents" && activeIncidents > 0 && (
                <span className="ml-auto text-[10px] font-mono bg-critical/20 text-critical px-1.5 py-0.5 rounded">
                  {activeIncidents}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={logout}
          className="flex items-center gap-3 px-5 py-3.5 text-sm text-text-muted hover:text-text border-t border-border"
        >
          <LogOut size={16} /> Sign out
        </button>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 shrink-0 border-b border-border bg-surface/60 backdrop-blur flex items-center justify-between px-6">
          <div className="text-sm text-text-muted">{ispName}</div>
          <div className="flex items-center gap-4">
            <button className="relative text-text-muted hover:text-text">
              <Bell size={18} />
              {activeIncidents > 0 && (
                <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-critical" />
              )}
            </button>
            <div className="w-px h-5 bg-border" />
            <div className="flex items-center gap-2 text-sm">
              <div className="w-7 h-7 rounded-full bg-pulse-dim text-pulse flex items-center justify-center text-xs font-semibold">
                {userName.split(" ").map((n) => n[0]).slice(0, 2).join("")}
              </div>
              {userName}
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}

export function PulseLogo({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <circle cx="16" cy="16" r="15" stroke="#2dd4bf" strokeWidth="1.5" opacity="0.35" />
      <path
        d="M3 17h5l2-7 4 14 3-11 2 4h10"
        stroke="#2dd4bf"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}
