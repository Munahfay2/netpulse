import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { NotificationItem } from "../types";

export default function Notifications() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [demoMode, setDemoMode] = useState<{ demo_sms_mode: boolean; banner: string | null } | null>(null);

  useEffect(() => {
    const refresh = () => api.notifications().then(setNotifications);
    refresh();
    api.demoModeStatus().then(setDemoMode);
    const iv = setInterval(refresh, 5000);
    return () => clearInterval(iv);
  }, []);

  const sent = notifications.filter((n) => n.status === "sent" || n.status === "simulated").length;
  const delivered = notifications.filter((n) => n.status === "delivered").length;
  const failed = notifications.filter((n) => n.status === "failed").length;
  const technicianAlerts = notifications.filter((n) => n.recipient_type === "technician").length;
  const customerAlerts = notifications.filter((n) => n.recipient_type === "customer").length;

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold">Notification Center</h1>
          <p className="text-text-muted text-sm">Every SMS and USSD interaction NetPulse has sent or received.</p>
        </div>
        {demoMode?.demo_sms_mode && (
          <span className="text-[11px] font-mono uppercase bg-warning/10 text-warning border border-warning/30 rounded px-2.5 py-1.5">
            {demoMode.banner}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Stat label="SMS Sent" value={sent} />
        <Stat label="SMS Delivered" value={delivered} />
        <Stat label="SMS Failed" value={failed} tone="critical" />
        <Stat label="Technician Alerts" value={technicianAlerts} />
        <Stat label="Customer Alerts" value={customerAlerts} />
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-text-faint text-xs">
              <Th>Recipient</Th><Th>Destination</Th><Th>Channel</Th><Th>Message</Th>
              <Th>Status</Th><Th>Incident</Th><Th>Time</Th>
            </tr>
          </thead>
          <tbody>
            {notifications.map((n) => (
              <tr key={n.id} className="border-t border-border hover:bg-surface-raised/50 align-top">
                <Td className="text-text-muted capitalize">{n.recipient_type}</Td>
                <Td className="font-mono text-text-muted">{n.masked_destination}</Td>
                <Td className="font-mono text-text-muted">{n.channel}</Td>
                <Td className="max-w-md text-text-muted">{n.message}</Td>
                <Td>
                  <span className={`font-mono text-xs ${n.status === "failed" ? "text-critical" : n.simulated ? "text-warning" : "text-healthy"}`}>
                    {n.simulated ? "SIMULATED" : n.status.toUpperCase()}
                  </span>
                </Td>
                <Td className="font-mono text-text-muted text-xs">{n.incident_id ?? "—"}</Td>
                <Td className="text-text-muted text-xs">{new Date(n.created_at).toLocaleTimeString()}</Td>
              </tr>
            ))}
            {notifications.length === 0 && (
              <tr><td colSpan={7} className="text-center text-text-muted py-8">No notifications yet — trigger a fault on the dashboard.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: "critical" }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="text-xs text-text-muted mb-1">{label}</div>
      <div className={`text-xl font-semibold font-mono ${tone === "critical" ? "text-critical" : "text-text"}`}>{value}</div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left font-normal px-5 py-2.5">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-5 py-3 ${className}`}>{children}</td>;
}
