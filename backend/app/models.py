import enum
import uuid
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                         Integer, String, Text)
from sqlalchemy.orm import relationship

from .database import Base


def gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------- enums ----
class Severity(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class IncidentStatus(str, enum.Enum):
    detected = "Detected"
    investigating = "Investigating"
    assigned = "Assigned"
    in_progress = "In Progress"
    resolved = "Resolved"
    closed = "Closed"


class DeviceHealth(str, enum.Enum):
    healthy = "healthy"
    degraded = "degraded"
    offline = "offline"


class TechnicianStatus(str, enum.Enum):
    available = "Available"
    on_job = "On Job"
    offline = "Offline"


# --------------------------------------------------------------- tables ----
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: gen_id("USR"))
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="noc_operator")  # noc_operator | admin
    isp_name = Column(String, default="Rift Valley Networks")
    created_at = Column(DateTime, default=datetime.utcnow)


class NetworkLocation(Base):
    __tablename__ = "network_locations"
    id = Column(String, primary_key=True, default=lambda: gen_id("LOC"))
    name = Column(String, nullable=False)
    region = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)

    olts = relationship("OLT", back_populates="location")


class OLT(Base):
    __tablename__ = "olts"
    id = Column(String, primary_key=True)  # e.g. OLT-003
    location_id = Column(String, ForeignKey("network_locations.id"))
    name = Column(String)
    status = Column(Enum(DeviceHealth), default=DeviceHealth.healthy)

    location = relationship("NetworkLocation", back_populates="olts")
    odfs = relationship("ODF", back_populates="olt")
    onts = relationship("ONT", back_populates="olt")


class ODF(Base):
    __tablename__ = "odfs"
    id = Column(String, primary_key=True, default=lambda: gen_id("ODF"))
    olt_id = Column(String, ForeignKey("olts.id"))
    port_count = Column(Integer, default=48)
    status = Column(Enum(DeviceHealth), default=DeviceHealth.healthy)

    olt = relationship("OLT", back_populates="odfs")


class ONT(Base):
    __tablename__ = "onts"
    id = Column(String, primary_key=True, default=lambda: gen_id("ONT"))
    olt_id = Column(String, ForeignKey("olts.id"))
    optical_level_dbm = Column(Float, default=-18.0)
    status = Column(Enum(DeviceHealth), default=DeviceHealth.healthy)

    olt = relationship("OLT", back_populates="onts")
    device = relationship("Device", back_populates="ont", uselist=False)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True, default=lambda: gen_id("CUS"))
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)  # full number, only ever masked on the way out
    location_id = Column(String, ForeignKey("network_locations.id"))
    plan = Column(String, default="Home Fibre 10Mbps")
    created_at = Column(DateTime, default=datetime.utcnow)

    location = relationship("NetworkLocation")
    device = relationship("Device", back_populates="customer", uselist=False)
    tickets = relationship("Ticket", back_populates="customer")

    @property
    def masked_phone(self) -> str:
        p = self.phone or ""
        return p[:5] + "*" * max(len(p) - 7, 0) + p[-2:] if len(p) > 7 else "*" * len(p)


class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)  # e.g. CPE-001
    customer_id = Column(String, ForeignKey("customers.id"))
    ont_id = Column(String, ForeignKey("onts.id"))
    olt_id = Column(String, ForeignKey("olts.id"))
    location_id = Column(String, ForeignKey("network_locations.id"))

    router_status = Column(String, default="online")       # online | offline
    wan_status = Column(String, default="up")               # up | down
    lan_status = Column(String, default="normal")            # normal | degraded
    internet_reachable = Column(Boolean, default=True)
    latency_ms = Column(Float, default=30.0)
    packet_loss_percent = Column(Float, default=0.0)
    uptime_seconds = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    health = Column(Enum(DeviceHealth), default=DeviceHealth.healthy)

    customer = relationship("Customer", back_populates="device")
    ont = relationship("ONT", back_populates="device")
    olt = relationship("OLT")
    location = relationship("NetworkLocation")
    telemetry = relationship("Telemetry", back_populates="device")


class Telemetry(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("devices.id"), index=True)
    router_status = Column(String)
    wan_status = Column(String)
    lan_status = Column(String)
    internet_reachable = Column(Boolean)
    latency_ms = Column(Float)
    packet_loss_percent = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    device = relationship("Device", back_populates="telemetry")


class Technician(Base):
    __tablename__ = "technicians"
    id = Column(String, primary_key=True, default=lambda: gen_id("TEC"))
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    region = Column(String)
    status = Column(Enum(TechnicianStatus), default=TechnicianStatus.available)


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True, default=lambda: gen_id("NP-2026"))
    title = Column(String, nullable=False)
    incident_type = Column(String, nullable=False)   # e.g. "Access Network Outage"
    location_id = Column(String, ForeignKey("network_locations.id"))
    olt_id = Column(String, ForeignKey("olts.id"))
    severity = Column(Enum(Severity), default=Severity.low)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.detected)
    probable_cause = Column(String)
    probable_cause_confidence = Column(String)  # Low | Medium | High
    probable_cause_reasons = Column(Text)         # JSON-encoded list of strings
    recommended_checks = Column(Text)             # JSON-encoded list of strings
    affected_customer_count = Column(Integer, default=0)
    assigned_technician_id = Column(String, ForeignKey("technicians.id"), nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    location = relationship("NetworkLocation")
    olt = relationship("OLT")
    assigned_technician = relationship("Technician")
    events = relationship("IncidentEvent", back_populates="incident", order_by="IncidentEvent.timestamp")
    affected_devices = relationship("IncidentDevice", back_populates="incident")


class IncidentDevice(Base):
    """Join table: which devices/customers are part of an incident."""
    __tablename__ = "incident_devices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String, ForeignKey("incidents.id"), index=True)
    device_id = Column(String, ForeignKey("devices.id"), index=True)

    incident = relationship("Incident", back_populates="affected_devices")
    device = relationship("Device")


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String, ForeignKey("incidents.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message = Column(String, nullable=False)
    event_type = Column(String, default="info")  # info | status_change | notification

    incident = relationship("Incident", back_populates="events")


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True, default=lambda: gen_id("NP-TKT"))
    customer_id = Column(String, ForeignKey("customers.id"))
    issue_type = Column(String)  # No Internet | Slow Internet | Intermittent Connection | Other
    status = Column(String, default="Open")
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=True)
    channel = Column(String, default="USSD")
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="tickets")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=lambda: gen_id("NOTIF"))
    recipient_type = Column(String)  # customer | technician
    recipient_id = Column(String)
    masked_destination = Column(String)
    channel = Column(String, default="SMS")
    message = Column(Text)
    status = Column(String, default="sent")  # sent | delivered | failed | simulated
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    simulated = Column(Boolean, default=True)


class UssdSession(Base):
    __tablename__ = "ussd_sessions"
    id = Column(String, primary_key=True, default=lambda: gen_id("SESS"))
    session_id = Column(String)
    phone_number = Column(String)
    text = Column(String, default="")
    state = Column(String, default="menu")
    created_at = Column(DateTime, default=datetime.utcnow)


class ServiceStatus(Base):
    """Simple singleton-style table tracking simulator/demo state."""
    __tablename__ = "service_status"
    id = Column(Integer, primary_key=True, default=1)
    demo_mode = Column(Boolean, default=True)
    simulation_scenario = Column(String, default="normal")
    updated_at = Column(DateTime, default=datetime.utcnow)
