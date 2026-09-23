import type {
  Customer, DashboardSummary, Device, Incident, LocationSummary, NotificationItem, Technician,
} from "../types";

// In local dev, Vite's dev server proxies a relative "/api" straight to the
// backend (see vite.config.ts), so VITE_API_URL can stay unset. When the
// frontend and backend are deployed to separate hosts (e.g. Vercel +
// Render), set VITE_API_URL to the backend's full URL and it's used here
// instead — see frontend/.env.example.
const API_ROOT = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "";
const BASE = `${API_ROOT}/api`;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("netpulse_token");
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${path} failed: ${res.status} ${text}`);
  }
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  // @ts-expect-error - plain text response (USSD)
  return res.text();
}

export const api = {
  demoLogin: () => request<{ token: string; user: any }>("/auth/demo-login", { method: "POST" }),

  dashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),

  incidents: (statusFilter?: string) =>
    request<Incident[]>(`/incidents${statusFilter ? `?status_filter=${statusFilter}` : ""}`),
  incident: (id: string) => request<Incident>(`/incidents/${id}`),
  updateIncidentStatus: (id: string, status: string) =>
    request<Incident>(`/incidents/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
  assignTechnician: (id: string, technicianId: string) =>
    request<Incident>(`/incidents/${id}/assign`, {
      method: "POST",
      body: JSON.stringify({ technician_id: technicianId }),
    }),

  devices: (params: Record<string, string> = {}) =>
    request<Device[]>(`/devices?${new URLSearchParams(params).toString()}`),
  telemetry: (deviceId: string) =>
    request<any[]>(`/telemetry/${deviceId}`),

  customers: (q?: string) =>
    request<Customer[]>(`/customers${q ? `?q=${encodeURIComponent(q)}` : ""}`),

  technicians: () => request<Technician[]>("/technicians"),

  notifications: (incidentId?: string) =>
    request<NotificationItem[]>(`/notifications${incidentId ? `?incident_id=${incidentId}` : ""}`),
  demoModeStatus: () => request<{ demo_sms_mode: boolean; banner: string | null }>("/notifications/demo-mode"),

  simulate: (scenario: string) => request<any>(`/simulator/${scenario}`, { method: "POST" }),
  simulatorStatus: () => request<{ scenario: string; target_olt: string | null }>("/simulator/status"),

  networkOverview: () => request<LocationSummary[]>("/network/overview"),

  ussd: (payload: { sessionId: string; phoneNumber: string; text: string; customer_id?: string }) =>
    fetch(`${BASE}/ussd`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams(payload as any).toString(),
    }).then((r) => r.text()),

  resetDemo: () => request<any>("/demo/reset", { method: "POST" }),
};
