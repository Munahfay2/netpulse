from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..auth_utils import get_current_user

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"], dependencies=[Depends(get_current_user)])


class TelemetryPoint(BaseModel):
    latency_ms: float
    packet_loss_percent: float
    wan_status: str
    internet_reachable: bool
    timestamp: str


@router.get("/{device_id}", response_model=List[TelemetryPoint])
def get_telemetry(device_id: str, limit: int = 50, db: Session = Depends(get_db)):
    device = db.query(models.Device).get(device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    rows = (
        db.query(models.Telemetry)
        .filter(models.Telemetry.device_id == device_id)
        .order_by(models.Telemetry.timestamp.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()
    return [
        TelemetryPoint(
            latency_ms=r.latency_ms,
            packet_loss_percent=r.packet_loss_percent,
            wan_status=r.wan_status,
            internet_reachable=r.internet_reachable,
            timestamp=r.timestamp.isoformat(),
        )
        for r in rows
    ]


class IngestTelemetryIn(BaseModel):
    device_id: str
    router_status: str
    wan_status: str
    lan_status: str
    internet_reachable: bool
    latency_ms: float
    packet_loss_percent: float


@router.post("")
def ingest_telemetry(payload: IngestTelemetryIn, db: Session = Depends(get_db)):
    """Entry point for a *real* telemetry agent (spec section 50). Applies the
    same detection/correlation pipeline as the simulator."""
    from ..services import correlation_engine
    from ..services.fault_detection_engine import compute_device_health

    device = db.query(models.Device).get(payload.device_id)
    if not device:
        raise HTTPException(404, "Unknown device_id")

    for field in ("router_status", "wan_status", "lan_status", "internet_reachable",
                  "latency_ms", "packet_loss_percent"):
        setattr(device, field, getattr(payload, field))

    db.add(models.Telemetry(
        device_id=device.id,
        router_status=device.router_status,
        wan_status=device.wan_status,
        lan_status=device.lan_status,
        internet_reachable=device.internet_reachable,
        latency_ms=device.latency_ms,
        packet_loss_percent=device.packet_loss_percent,
    ))
    correlation_engine.process_device(db, device)
    device.health = compute_device_health(device)
    db.commit()
    return {"status": "ok"}
