"""
telemetry_simulator.py

Generates realistic customer/network telemetry so the whole detect -> notify
-> restore pipeline can be demonstrated without any real ISP hardware.

Design note (spec section 50): this implements the TelemetrySource
interface. A future real deployment can swap this module for an SNMP
collector, an OpenWrt/Raspberry Pi agent, or direct CPE/ONT telemetry
without changing anything downstream — detection, correlation, incidents
and notifications all just consume Telemetry rows / Device state.
"""
import abc
import random
import threading
import time
from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session

from .. import models
from ..database import session_scope
from . import correlation_engine


class TelemetrySource(abc.ABC):
    """Interface any telemetry source (real or simulated) must implement."""

    @abc.abstractmethod
    def poll(self, db: Session) -> None:
        """Update every device's live telemetry fields for one tick."""
        raise NotImplementedError


# --- scenario state -----------------------------------------------------
# A simple in-memory flag set by /api/simulator/* endpoints. Kept separate
# from the DB so it can't drift or require a migration for a demo toggle.
SCENARIOS = (
    "normal", "single_failure", "high_latency", "packet_loss",
    "wan_failure", "olt_failure", "area_outage",
)

_state: Dict[str, str] = {"scenario": "normal", "target_olt": None}
_lock = threading.Lock()


def set_scenario(scenario: str, target_olt: str = None):
    with _lock:
        _state["scenario"] = scenario
        _state["target_olt"] = target_olt


def get_scenario() -> Dict[str, str]:
    with _lock:
        return dict(_state)


class SimulatedTelemetrySource(TelemetrySource):
    def poll(self, db: Session) -> None:
        scenario = get_scenario()
        devices = db.query(models.Device).all()
        if not devices:
            return

        target_olt = scenario.get("target_olt")
        area_outage_devices = []
        if scenario["scenario"] == "area_outage":
            olt_id = target_olt or self._pick_biggest_olt(db)
            area_outage_devices = [d.id for d in devices if d.olt_id == olt_id]

        for device in devices:
            self._apply_baseline(device)

            s = scenario["scenario"]
            if s == "single_failure" and device.id == target_olt:
                self._fail_wan(device)
            elif s == "high_latency" and (target_olt is None or device.olt_id == target_olt):
                device.latency_ms = random.uniform(220, 400)
                device.packet_loss_percent = random.uniform(12, 25)
            elif s == "packet_loss" and (target_olt is None or device.olt_id == target_olt):
                device.internet_reachable = False
                device.packet_loss_percent = random.uniform(85, 100)
            elif s == "wan_failure" and (target_olt is None or device.olt_id == target_olt):
                self._fail_wan(device)
            elif s == "olt_failure" and device.olt_id == target_olt:
                self._fail_wan(device)
            elif s == "area_outage" and device.id in area_outage_devices:
                self._fail_wan(device)

            device.last_seen = datetime.utcnow()
            device.uptime_seconds += 5

            db.add(models.Telemetry(
                device_id=device.id,
                router_status=device.router_status,
                wan_status=device.wan_status,
                lan_status=device.lan_status,
                internet_reachable=device.internet_reachable,
                latency_ms=device.latency_ms,
                packet_loss_percent=device.packet_loss_percent,
                timestamp=datetime.utcnow(),
            ))

            correlation_engine.process_device(db, device)
            from .fault_detection_engine import compute_device_health
            device.health = compute_device_health(device)

        db.flush()

    @staticmethod
    def _pick_biggest_olt(db: Session) -> str:
        from sqlalchemy import func
        row = (
            db.query(models.Device.olt_id, func.count(models.Device.id).label("n"))
            .group_by(models.Device.olt_id)
            .order_by(func.count(models.Device.id).desc())
            .first()
        )
        return row[0] if row else None

    @staticmethod
    def _apply_baseline(device: models.Device):
        device.router_status = "online"
        device.wan_status = "up"
        device.lan_status = "normal"
        device.internet_reachable = True
        device.latency_ms = round(random.uniform(15, 45), 1)
        device.packet_loss_percent = round(random.uniform(0, 1.5), 2)

    @staticmethod
    def _fail_wan(device: models.Device):
        device.router_status = "online"
        device.wan_status = "down"
        device.lan_status = "normal"
        device.internet_reachable = False
        device.latency_ms = 0.0
        device.packet_loss_percent = 100.0


_source: TelemetrySource = SimulatedTelemetrySource()
_thread = None
_stop_flag = threading.Event()


def _loop(interval_seconds: int):
    while not _stop_flag.is_set():
        try:
            with session_scope() as db:
                _source.poll(db)
        except Exception as exc:  # never let the simulator crash the app
            print(f"[telemetry_simulator] tick failed: {exc}")
        _stop_flag.wait(interval_seconds)


def start_background_loop(interval_seconds: int = 5):
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop_flag.clear()
    _thread = threading.Thread(target=_loop, args=(interval_seconds,), daemon=True)
    _thread.start()


def stop_background_loop():
    _stop_flag.set()


def restore_all(db: Session):
    set_scenario("normal")
    for device in db.query(models.Device).all():
        SimulatedTelemetrySource._apply_baseline(device)
        device.health = "healthy"
    db.flush()
