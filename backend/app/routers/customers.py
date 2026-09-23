from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth_utils import get_current_user

router = APIRouter(prefix="/api/customers", tags=["customers"], dependencies=[Depends(get_current_user)])


def _to_out(c: models.Customer) -> schemas.CustomerOut:
    device_health = c.device.health.value if (c.device and hasattr(c.device.health, "value")) else (
        c.device.health if c.device else None
    )
    active_incident_id = None
    if c.device:
        link = (
            None
        )
    return schemas.CustomerOut(
        id=c.id,
        name=c.name,
        masked_phone=c.masked_phone,
        plan=c.plan,
        olt_id=c.device.olt_id if c.device else None,
        location=schemas.LocationOut.model_validate(c.location) if c.location else None,
        device_health=device_health,
        active_incident_id=active_incident_id,
    )


@router.get("", response_model=List[schemas.CustomerOut])
def list_customers(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    query = db.query(models.Customer)
    if q:
        query = query.filter(models.Customer.name.ilike(f"%{q}%"))
    query = query.order_by(models.Customer.id).offset((page - 1) * page_size).limit(page_size)
    return [_to_out(c) for c in query.all()]


@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    c = db.query(models.Customer).get(customer_id)
    if not c:
        raise HTTPException(404, "Customer not found")
    return _to_out(c)
