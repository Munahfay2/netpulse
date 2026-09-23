from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth_utils import get_current_user

router = APIRouter(prefix="/api/devices", tags=["devices"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[schemas.DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    olt_id: Optional[str] = None,
    health: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = db.query(models.Device)
    if olt_id:
        q = q.filter(models.Device.olt_id == olt_id)
    if health:
        q = q.filter(models.Device.health == health)
    q = q.order_by(models.Device.id).offset((page - 1) * page_size).limit(page_size)
    return q.all()


@router.get("/{device_id}", response_model=schemas.DeviceOut)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(models.Device).get(device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    return device
