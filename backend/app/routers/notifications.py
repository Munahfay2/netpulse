from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth_utils import get_current_user
from ..services import africastalking_service as at

router = APIRouter(prefix="/api/notifications", tags=["notifications"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[schemas.NotificationOut])
def list_notifications(limit: int = 100, incident_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Notification)
    if incident_id:
        q = q.filter(models.Notification.incident_id == incident_id)
    q = q.order_by(models.Notification.created_at.desc()).limit(limit)
    return q.all()


@router.get("/demo-mode")
def demo_mode_status():
    return {"demo_sms_mode": at.DEMO_SMS_MODE, "banner": at.demo_mode_banner()}


@router.post("/test")
def send_test_sms(to: str, message: str = "This is a test notification from NetPulse.",
                   db: Session = Depends(get_db)):
    n = at.send_sms(db, to=to, message=message, recipient_type="test", recipient_id="test")
    db.commit()
    return {"id": n.id, "status": n.status, "simulated": n.simulated}
