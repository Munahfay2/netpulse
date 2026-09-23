"""
incident_engine.py

Owns incident creation, severity calculation, the probable-cause engine,
recommended technician checks, lifecycle transitions, and automatic recovery
detection. Also fires notifications via africastalking_service, so a single
call from the correlation engine results in a fully-formed, communicated
incident (spec sections 15, 16, 17, 18, 19, 31, 32).
"""
import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from .. import models
from . import africastalking_service as at

# Configurable severity thresholds (spec section 31).
SEVERITY_THRESHOLDS = [
    (20, models.Severity.critical),
    (10, models.Severity.high),
    (3, models.Severity.medium),
    (1, models.Severity.low),
]

RECOMMENDED_CHECKS = {
    "WAN/access connectivity issue": [
        "Check OLT port status.",
        "Check ONT optical levels.",
        "Check fibre route.",
        "Check ODF connections.",
        "Check recent maintenance activity.",
        "Check whether neighboring OLTs are affected.",
    ],
    "Device unreachable": [
        "Check router power.",
        "Check CPE LAN cabling.",
        "Confirm ONT optical levels.",
        "Check whether the customer's account/status is active.",
    ],
    "Severe connectivity degradation": [
        "Check upstream congestion at the OLT.",
        "Check fibre route continuity.",
        "Check for recent optical degradation.",
    ],
    "Network degradation/congestion": [
        "Check for upstream congestion.",
        "Check OLT port utilization.",
        "Check for interference or oversubscription.",
    ],
}

PROBABLE_CAUSE = {
    "WAN/access connectivity issue": "Access network disruption",
    "Device unreachable": "Customer-side device or power issue",
    "Severe connectivity degradation": "Severe access network degradation",
    "Network degradation/congestion": "Network congestion",
}


def severity_for_count(count: int) -> models.Severity:
    for threshold, severity in SEVERITY_THRESHOLDS:
        if count >= threshold:
            return severity
    return models.Severity.low


def log_event(db: Session, incident: models.Incident, message: str, event_type: str = "info"):
    db.add(models.IncidentEvent(incident_id=incident.id, message=message, event_type=event_type))


def _build_reasons(count: int, olt_id: str, symptom: str) -> List[str]:
    reasons = [f"{count} customer(s) affected"]
    if olt_id:
        reasons.append(f"customers share {olt_id}")
    reasons.append("failures occurred within a short time window")
    if symptom == "WAN/access connectivity issue":
        reasons.append("WAN connectivity is unavailable")
        reasons.append("local LAN status remains normal")
    return reasons


def _confidence_for(count: int) -> str:
    if count >= 10:
        return "High"
    if count >= 3:
        return "Medium"
    return "Low"


def create_incident(db: Session, device: models.Device, symptom: str) -> models.Incident:
    location_name = device.location.name if device.location else "Unknown area"
    incident = models.Incident(
        title=f"{location_name} {symptom.split('/')[0] if False else _incident_title_type(symptom)}",
        incident_type=symptom,
        location_id=device.location_id,
        olt_id=device.olt_id,
        severity=severity_for_count(1),
        status=models.IncidentStatus.detected,
        probable_cause=PROBABLE_CAUSE.get(symptom, "Unknown — requires investigation"),
        probable_cause_confidence=_confidence_for(1),
        probable_cause_reasons=json.dumps(_build_reasons(1, device.olt_id, symptom)),
        recommended_checks=json.dumps(RECOMMENDED_CHECKS.get(symptom, ["Dispatch technician to investigate."])),
        affected_customer_count=1,
        detected_at=datetime.utcnow(),
    )
    db.add(incident)
    db.flush()

    db.add(models.IncidentDevice(incident_id=incident.id, device_id=device.id))
    log_event(db, incident, "First CPE became unreachable." if symptom == "Device unreachable"
              else "First customer failure detected.")
    log_event(db, incident, f"1 customer affected.")
    incident.status = models.IncidentStatus.investigating
    log_event(db, incident, "NetPulse correlated failures.")
    log_event(db, incident, f"Incident {incident.id} created.", event_type="status_change")

    _notify_for_incident(db, incident)
    return incident


def _incident_title_type(symptom: str) -> str:
    return {
        "WAN/access connectivity issue": "Access Network Outage",
        "Device unreachable": "Router Unreachable",
        "Severe connectivity degradation": "Severe Connectivity Degradation",
        "Network degradation/congestion": "High Latency",
    }.get(symptom, "Network Issue")


def add_device_to_incident(db: Session, incident: models.Incident, device: models.Device) -> None:
    db.add(models.IncidentDevice(incident_id=incident.id, device_id=device.id))
    incident.affected_customer_count += 1
    incident.severity = severity_for_count(incident.affected_customer_count)
    incident.probable_cause_confidence = _confidence_for(incident.affected_customer_count)
    incident.probable_cause_reasons = json.dumps(
        _build_reasons(incident.affected_customer_count, incident.olt_id, incident.incident_type)
    )
    log_event(db, incident, f"Additional customer affected — {incident.affected_customer_count} total.")

    # Notify the newly-affected customer too.
    if device.customer:
        at.send_customer_outage_sms(db, device.customer, incident)
        log_event(db, incident, f"Customer notified ({device.customer.masked_phone}).",
                   event_type="notification")

    _notify_technician_if_newly_eligible(db, incident)


def _notify_technician_if_newly_eligible(db: Session, incident: models.Incident) -> None:
    """As correlation grows an incident, its severity can cross the
    Medium/High/Critical threshold after creation — make sure a technician
    still gets alerted the moment that happens, not just at creation time."""
    if incident.severity not in (models.Severity.medium, models.Severity.high, models.Severity.critical):
        return
    already_notified = (
        db.query(models.Notification)
        .filter(models.Notification.incident_id == incident.id,
                 models.Notification.recipient_type == "technician")
        .first()
    )
    if already_notified:
        return
    technician = (
        db.query(models.Technician)
        .filter(models.Technician.status == models.TechnicianStatus.available)
        .first()
    )
    if technician:
        location_name = incident.location.name if incident.location else "the affected area"
        at.send_technician_alert(db, technician, incident, location_name)
        log_event(db, incident, f"Technician notified via SMS ({technician.name}).",
                  event_type="notification")


def _notify_for_incident(db: Session, incident: models.Incident) -> None:
    # Technician alert for anything Medium severity or above.
    if incident.severity in (models.Severity.medium, models.Severity.high, models.Severity.critical):
        technician = (
            db.query(models.Technician)
            .filter(models.Technician.status == models.TechnicianStatus.available)
            .first()
        )
        if technician:
            location_name = incident.location.name if incident.location else "the affected area"
            at.send_technician_alert(db, technician, incident, location_name)
            log_event(db, incident, f"Technician notified via SMS ({technician.name}).",
                      event_type="notification")

    # Notify the first affected customer.
    device_link = incident.affected_devices[0] if incident.affected_devices else None
    if device_link and device_link.device and device_link.device.customer:
        at.send_customer_outage_sms(db, device_link.device.customer, incident)
        log_event(db, incident, "Affected customer(s) notified.", event_type="notification")


def assign_technician(db: Session, incident: models.Incident, technician: models.Technician) -> None:
    incident.assigned_technician_id = technician.id
    if incident.status in (models.IncidentStatus.detected, models.IncidentStatus.investigating):
        incident.status = models.IncidentStatus.assigned
    technician.status = models.TechnicianStatus.on_job
    location_name = incident.location.name if incident.location else "the affected area"
    at.send_technician_alert(db, technician, incident, location_name)
    log_event(db, incident, f"Assigned to technician {technician.name}.", event_type="status_change")


def update_status(db: Session, incident: models.Incident, new_status: str) -> None:
    incident.status = models.IncidentStatus(new_status)
    log_event(db, incident, f"Status changed to {new_status}.", event_type="status_change")
    if incident.status in (models.IncidentStatus.resolved, models.IncidentStatus.closed):
        incident.resolved_at = incident.resolved_at or datetime.utcnow()
        if incident.assigned_technician:
            incident.assigned_technician.status = models.TechnicianStatus.available


def maybe_resolve_incident(db: Session, incident_id: str) -> None:
    """Called when a device recovers. If every affected device on this
    incident is now healthy, auto-resolve the incident and send restoration
    SMS to every affected customer (spec section 17 / 32)."""
    incident = db.query(models.Incident).get(incident_id)
    if not incident or incident.status in (models.IncidentStatus.resolved, models.IncidentStatus.closed):
        return

    from .fault_detection_engine import evaluate_device  # local import avoids cycle

    still_faulty = False
    for link in incident.affected_devices:
        device = link.device
        if device and evaluate_device(device).is_faulty:
            still_faulty = True
            break

    if still_faulty:
        return

    incident.status = models.IncidentStatus.resolved
    incident.resolved_at = datetime.utcnow()
    log_event(db, incident, "Connectivity restored.")
    log_event(db, incident, "Incident automatically marked recovered.", event_type="status_change")

    if incident.assigned_technician:
        incident.assigned_technician.status = models.TechnicianStatus.available

    for link in incident.affected_devices:
        if link.device and link.device.customer:
            at.send_customer_restoration_sms(db, link.device.customer, incident)
    log_event(db, incident, "Customer restoration SMS sent.", event_type="notification")
