from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..auth_utils import get_current_user

router = APIRouter(prefix="/api/network", tags=["network"], dependencies=[Depends(get_current_user)])


class OltSummary(BaseModel):
    id: str
    name: str
    status: str
    online: int
    degraded: int
    offline: int
    active_incidents: int


class LocationSummary(BaseModel):
    id: str
    name: str
    region: str | None = None
    olts: List[OltSummary]


@router.get("/overview", response_model=List[LocationSummary])
def overview(db: Session = Depends(get_db)):
    locations = db.query(models.NetworkLocation).all()
    result = []
    for loc in locations:
        olts_out = []
        for olt in loc.olts:
            devices = db.query(models.Device).filter(models.Device.olt_id == olt.id).all()
            online = sum(1 for d in devices if d.health == "healthy")
            degraded = sum(1 for d in devices if d.health == "degraded")
            offline = sum(1 for d in devices if d.health == "offline")
            active = (
                db.query(models.Incident)
                .filter(models.Incident.olt_id == olt.id,
                         models.Incident.status.notin_(["Resolved", "Closed"]))
                .count()
            )
            status = "critical" if offline > 0 else "warning" if degraded > 0 else "healthy"
            olts_out.append(OltSummary(
                id=olt.id, name=olt.name or olt.id, status=status,
                online=online, degraded=degraded, offline=offline, active_incidents=active,
            ))
        result.append(LocationSummary(id=loc.id, name=loc.name, region=loc.region, olts=olts_out))
    return result
