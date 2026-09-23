from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth_utils import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(db: Session = Depends(get_db)):
    total_devices = db.query(models.Device).count() or 1
    online = db.query(models.Device).filter(models.Device.health == "healthy").count()
    degraded = db.query(models.Device).filter(models.Device.health == "degraded").count()
    offline = db.query(models.Device).filter(models.Device.health == "offline").count()

    active_incidents_q = db.query(models.Incident).filter(
        models.Incident.status.notin_(["Resolved", "Closed"])
    )
    active_incidents = active_incidents_q.count()
    customers_affected = sum(i.affected_customer_count for i in active_incidents_q.all())

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    incidents_today = db.query(models.Incident).filter(models.Incident.detected_at >= today_start).count()

    resolved = (
        db.query(models.Incident)
        .filter(models.Incident.status.in_(["Resolved", "Closed"]), models.Incident.resolved_at.isnot(None))
        .all()
    )
    if resolved:
        avg_minutes = sum(
            (i.resolved_at - i.detected_at).total_seconds() / 60 for i in resolved
        ) / len(resolved)
    else:
        avg_minutes = 0.0

    network_health = round(online / total_devices * 100, 1)

    return schemas.DashboardSummary(
        network_health_percent=network_health,
        active_incidents=active_incidents,
        customers_affected=customers_affected,
        devices_offline=offline,
        avg_resolution_minutes=round(avg_minutes, 1),
        incidents_today=incidents_today,
        devices_online=online,
        devices_degraded=degraded,
    )
