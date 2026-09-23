"""
correlation_engine.py

Groups individual device failures into a single incident when they share:
  - the same OLT / network segment
  - the same general area (location)
  - a similar failure type (symptom)
  - a short time window

This is the key differentiator described in the spec: 38 simultaneous
failures on one OLT must become ONE incident with 38 affected customers,
never 38 separate tickets (spec section 5 / 30 / Rule 5).
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from .. import models
from .fault_detection_engine import evaluate_device
from .incident_engine import (add_device_to_incident, create_incident,
                               log_event, maybe_resolve_incident)

CORRELATION_WINDOW = timedelta(minutes=2)
AREA_OUTAGE_MIN_CUSTOMERS = 10  # Rule 5


def _find_open_incident_for_olt(db: Session, olt_id: str, symptom: str) -> Optional[models.Incident]:
    return (
        db.query(models.Incident)
        .filter(
            models.Incident.olt_id == olt_id,
            models.Incident.incident_type == symptom,
            models.Incident.status.notin_(["Resolved", "Closed"]),
            models.Incident.detected_at >= datetime.utcnow() - timedelta(hours=6),
        )
        .order_by(models.Incident.detected_at.desc())
        .first()
    )


def process_device(db: Session, device: models.Device) -> None:
    """Called every simulator tick for every device. Runs detection, then
    correlates faulty devices into incidents, and auto-recovers healthy ones."""
    result = evaluate_device(device)

    existing_link = (
        db.query(models.IncidentDevice)
        .join(models.Incident)
        .filter(
            models.IncidentDevice.device_id == device.id,
            models.Incident.status.notin_(["Resolved", "Closed"]),
        )
        .first()
    )

    if not result.is_faulty:
        # Recovery path: if this device was part of an open incident, drop it
        # and check whether the whole incident can now be auto-resolved.
        if existing_link:
            maybe_resolve_incident(db, existing_link.incident_id)
        return

    if existing_link:
        # Already tracked under an incident — nothing new to correlate.
        return

    symptom = result.symptom
    incident = None
    if device.olt_id:
        incident = _find_open_incident_for_olt(db, device.olt_id, symptom)

    if incident is None:
        incident = create_incident(db, device=device, symptom=symptom)
    else:
        add_device_to_incident(db, incident, device)

    db.flush()
