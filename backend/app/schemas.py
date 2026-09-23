from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class LocationOut(BaseModel):
    id: str
    name: str
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class OLTOut(BaseModel):
    id: str
    name: Optional[str] = None
    status: str
    location: Optional[LocationOut] = None
    model_config = ConfigDict(from_attributes=True)


class DeviceOut(BaseModel):
    id: str
    customer_id: Optional[str] = None
    olt_id: Optional[str] = None
    router_status: str
    wan_status: str
    lan_status: str
    internet_reachable: bool
    latency_ms: float
    packet_loss_percent: float
    health: str
    last_seen: datetime
    model_config = ConfigDict(from_attributes=True)


class CustomerOut(BaseModel):
    id: str
    name: str
    masked_phone: str
    plan: str
    olt_id: Optional[str] = None
    location: Optional[LocationOut] = None
    device_health: Optional[str] = None
    active_incident_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class TechnicianOut(BaseModel):
    id: str
    name: str
    phone: str
    region: Optional[str] = None
    status: str
    active_incidents: int = 0
    model_config = ConfigDict(from_attributes=True)


class IncidentEventOut(BaseModel):
    timestamp: datetime
    message: str
    event_type: str
    model_config = ConfigDict(from_attributes=True)


class IncidentOut(BaseModel):
    id: str
    title: str
    incident_type: str
    severity: str
    status: str
    olt_id: Optional[str] = None
    location_name: Optional[str] = None
    affected_customer_count: int
    probable_cause: Optional[str] = None
    probable_cause_confidence: Optional[str] = None
    probable_cause_reasons: List[str] = []
    recommended_checks: List[str] = []
    assigned_technician_name: Optional[str] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    events: List[IncidentEventOut] = []


class DashboardSummary(BaseModel):
    network_health_percent: float
    active_incidents: int
    customers_affected: int
    devices_offline: int
    avg_resolution_minutes: float
    incidents_today: int
    devices_online: int
    devices_degraded: int


class NotificationOut(BaseModel):
    id: str
    recipient_type: str
    masked_destination: str
    channel: str
    message: str
    status: str
    incident_id: Optional[str] = None
    created_at: datetime
    simulated: bool
    model_config = ConfigDict(from_attributes=True)


class AssignTechnicianIn(BaseModel):
    technician_id: str


class IncidentStatusUpdateIn(BaseModel):
    status: str
