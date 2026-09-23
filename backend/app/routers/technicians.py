from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth_utils import get_current_user

router = APIRouter(prefix="/api/technicians", tags=["technicians"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[schemas.TechnicianOut])
def list_technicians(db: Session = Depends(get_db)):
    technicians = db.query(models.Technician).all()
    out = []
    for t in technicians:
        active = (
            db.query(models.Incident)
            .filter(models.Incident.assigned_technician_id == t.id,
                     models.Incident.status.notin_(["Resolved", "Closed"]))
            .count()
        )
        out.append(schemas.TechnicianOut(
            id=t.id, name=t.name, phone=t.phone, region=t.region,
            status=t.status.value if hasattr(t.status, "value") else t.status,
            active_incidents=active,
        ))
    return out
