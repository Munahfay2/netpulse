import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth_utils import get_current_user
from ..services import incident_engine

router = APIRouter(prefix="/api/incidents", tags=["incidents"], dependencies=[Depends(get_current_user)])


def _to_out(incident: models.Incident) -> schemas.IncidentOut:
    duration = None
    end = incident.resolved_at or None
    if end:
        duration = round((end - incident.detected_at).total_seconds() / 60, 1)
    else:
        from datetime import datetime
        duration = round((datetime.utcnow() - incident.detected_at).total_seconds() / 60, 1)

    return schemas.IncidentOut(
        id=incident.id,
        title=incident.title,
        incident_type=incident.incident_type,
        severity=incident.severity.value if hasattr(incident.severity, "value") else incident.severity,
        status=incident.status.value if hasattr(incident.status, "value") else incident.status,
        olt_id=incident.olt_id,
        location_name=incident.location.name if incident.location else None,
        affected_customer_count=incident.affected_customer_count,
        probable_cause=incident.probable_cause,
        probable_cause_confidence=incident.probable_cause_confidence,
        probable_cause_reasons=json.loads(incident.probable_cause_reasons or "[]"),
        recommended_checks=json.loads(incident.recommended_checks or "[]"),
        assigned_technician_name=incident.assigned_technician.name if incident.assigned_technician else None,
        detected_at=incident.detected_at,
        resolved_at=incident.resolved_at,
        duration_minutes=duration,
        events=[schemas.IncidentEventOut.model_validate(e) for e in incident.events],
    )


@router.get("", response_model=List[schemas.IncidentOut])
def list_incidents(status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Incident)
    if status_filter:
        q = q.filter(models.Incident.status == status_filter)
    q = q.order_by(models.Incident.detected_at.desc())
    return [_to_out(i) for i in q.all()]


@router.get("/{incident_id}", response_model=schemas.IncidentOut)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(models.Incident).get(incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return _to_out(incident)


@router.patch("/{incident_id}", response_model=schemas.IncidentOut)
def update_incident_status(incident_id: str, payload: schemas.IncidentStatusUpdateIn, db: Session = Depends(get_db)):
    incident = db.query(models.Incident).get(incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    try:
        incident_engine.update_status(db, incident, payload.status)
    except ValueError:
        raise HTTPException(400, "Invalid status")
    db.commit()
    db.refresh(incident)
    return _to_out(incident)


@router.post("/{incident_id}/assign", response_model=schemas.IncidentOut)
def assign_technician(incident_id: str, payload: schemas.AssignTechnicianIn, db: Session = Depends(get_db)):
    incident = db.query(models.Incident).get(incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    technician = db.query(models.Technician).get(payload.technician_id)
    if not technician:
        raise HTTPException(404, "Technician not found")
    incident_engine.assign_technician(db, incident, technician)
    db.commit()
    db.refresh(incident)
    return _to_out(incident)
