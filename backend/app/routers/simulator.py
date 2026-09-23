from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..auth_utils import get_current_user
from ..services import telemetry_simulator as sim

router = APIRouter(prefix="/api/simulator", tags=["simulator"], dependencies=[Depends(get_current_user)])


def _biggest_olt(db: Session) -> str:
    from sqlalchemy import func
    row = (
        db.query(models.Device.olt_id, func.count(models.Device.id).label("n"))
        .group_by(models.Device.olt_id)
        .order_by(func.count(models.Device.id).desc())
        .first()
    )
    return row[0] if row else None


@router.post("/normal")
def simulate_normal(db: Session = Depends(get_db)):
    sim.set_scenario("normal")
    return {"scenario": "normal"}


@router.post("/single-failure")
def single_failure(db: Session = Depends(get_db)):
    device = db.query(models.Device).order_by(models.Device.id).first()
    sim.set_scenario("single_failure", target_olt=device.id if device else None)
    return {"scenario": "single_failure", "target_device": device.id if device else None}


@router.post("/high-latency")
def high_latency(db: Session = Depends(get_db)):
    olt_id = _biggest_olt(db)
    sim.set_scenario("high_latency", target_olt=olt_id)
    return {"scenario": "high_latency", "target_olt": olt_id}


@router.post("/packet-loss")
def packet_loss(db: Session = Depends(get_db)):
    olt_id = _biggest_olt(db)
    sim.set_scenario("packet_loss", target_olt=olt_id)
    return {"scenario": "packet_loss", "target_olt": olt_id}


@router.post("/wan-failure")
def wan_failure(db: Session = Depends(get_db)):
    olt_id = _biggest_olt(db)
    sim.set_scenario("wan_failure", target_olt=olt_id)
    return {"scenario": "wan_failure", "target_olt": olt_id}


@router.post("/olt-failure")
def olt_failure(db: Session = Depends(get_db)):
    olt_id = _biggest_olt(db)
    sim.set_scenario("olt_failure", target_olt=olt_id)
    return {"scenario": "olt_failure", "target_olt": olt_id}


@router.post("/area-outage")
def area_outage(db: Session = Depends(get_db)):
    olt_id = _biggest_olt(db)
    sim.set_scenario("area_outage", target_olt=olt_id)
    return {"scenario": "area_outage", "target_olt": olt_id}


@router.post("/restore")
def restore(db: Session = Depends(get_db)):
    sim.restore_all(db)
    db.commit()
    return {"scenario": "normal", "message": "All services restored."}


@router.get("/status")
def status():
    return sim.get_scenario()
