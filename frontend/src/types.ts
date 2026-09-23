export interface DashboardSummary {
  network_health_percent: number;
  active_incidents: number;
  customers_affected: number;
  devices_offline: number;
  avg_resolution_minutes: number;
  incidents_today: number;
  devices_online: number;
  devices_degraded: number;
}

export interface Location {
  id: string;
  name: string;
  region?: string;
  latitude?: number;
  longitude?: number;
}

export interface IncidentEvent {
  timestamp: string;
  message: string;
  event_type: string;
}

export interface Incident {
  id: string;
  title: string;
  incident_type: string;
  severity: "Low" | "Medium" | "High" | "Critical";
  status: "Detected" | "Investigating" | "Assigned" | "In Progress" | "Resolved" | "Closed";
  olt_id?: string;
  location_name?: string;
  affected_customer_count: number;
  probable_cause?: string;
  probable_cause_confidence?: string;
  probable_cause_reasons: string[];
  recommended_checks: string[];
  assigned_technician_name?: string;
  detected_at: string;
  resolved_at?: string;
  duration_minutes?: number;
  events: IncidentEvent[];
}

export interface Device {
  id: string;
  customer_id?: string;
  olt_id?: string;
  router_status: string;
  wan_status: string;
  lan_status: string;
  internet_reachable: boolean;
  latency_ms: number;
  packet_loss_percent: number;
  health: "healthy" | "degraded" | "offline";
  last_seen: string;
}

export interface Customer {
  id: string;
  name: string;
  masked_phone: string;
  plan: string;
  olt_id?: string;
  location?: Location;
  device_health?: string;
  active_incident_id?: string;
}

export interface Technician {
  id: string;
  name: string;
  phone: string;
  region?: string;
  status: "Available" | "On Job" | "Offline";
  active_incidents: number;
}

export interface OltSummary {
  id: string;
  name: string;
  status: "healthy" | "warning" | "critical";
  online: number;
  degraded: number;
  offline: number;
  active_incidents: number;
}

export interface LocationSummary {
  id: string;
  name: string;
  region?: string;
  olts: OltSummary[];
}

export interface NotificationItem {
  id: string;
  recipient_type: string;
  masked_destination: string;
  channel: string;
  message: string;
  status: string;
  incident_id?: string;
  created_at: string;
  simulated: boolean;
}
