"""
This is the single most important behavioral test in the spec (section 56):
when many customers on the same OLT fail within a short window, NetPulse
must create exactly ONE incident — never one ticket per customer — and must
auto-resolve it with restoration notifications once telemetry recovers.
"""
from app import models
from app.services import telemetry_simulator as sim
from app.services.telemetry_simulator import SimulatedTelemetrySource


def _devices_on_olt(db, olt_id):
    return db.query(models.Device).filter(models.Device.olt_id == olt_id).all()


def test_area_outage_creates_one_incident_not_many(db_session):
    db = db_session
    # Pick whichever OLT the seed data grouped the most customers under.
    from sqlalchemy import func
    olt_id, device_count = (
        db.query(models.Device.olt_id, func.count(models.Device.id))
        .group_by(models.Device.olt_id)
        .order_by(func.count(models.Device.id).desc())
        .first()
    )
    assert device_count >= 10, "seed data should give at least one OLT with 10+ customers"

    sim.set_scenario("area_outage", target_olt=olt_id)
    source = SimulatedTelemetrySource()
    source.poll(db)
    db.commit()

    incidents = (
        db.query(models.Incident)
        .filter(models.Incident.olt_id == olt_id, models.Incident.status != models.IncidentStatus.resolved)
        .all()
    )
    assert len(incidents) == 1, f"expected exactly ONE incident, got {len(incidents)}"

    incident = incidents[0]
    assert incident.affected_customer_count == device_count
    assert incident.incident_type == "WAN/access connectivity issue"
    assert incident.probable_cause == "Access network disruption"
    assert incident.severity in (models.Severity.high, models.Severity.critical)

    # Every device on that OLT should be linked to the SAME incident.
    linked_incident_ids = {
        link.incident_id
        for d in _devices_on_olt(db, olt_id)
        for link in db.query(models.IncidentDevice).filter(models.IncidentDevice.device_id == d.id).all()
    }
    assert linked_incident_ids == {incident.id}

    # Customer + technician notifications should have gone out (simulated,
    # since no Africa's Talking credentials are configured in tests).
    notifications = db.query(models.Notification).filter(models.Notification.incident_id == incident.id).all()
    assert any(n.recipient_type == "customer" for n in notifications)
    assert any(n.recipient_type == "technician" for n in notifications)
    assert all(n.simulated for n in notifications)

    # --- restore and verify auto-recovery ---
    sim.restore_all(db)
    db.commit()
    source.poll(db)
    db.commit()

    db.refresh(incident)
    assert incident.status == models.IncidentStatus.resolved
    assert incident.resolved_at is not None

    restoration_notifications = (
        db.query(models.Notification)
        .filter(models.Notification.incident_id == incident.id, models.Notification.recipient_type == "customer")
        .all()
    )
    # One outage SMS + one restoration SMS per affected customer.
    assert len(restoration_notifications) >= device_count


def test_single_customer_failure_creates_low_severity_incident(db_session):
    db = db_session
    sim.set_scenario("normal")
    SimulatedTelemetrySource().poll(db)
    db.commit()

    device = db.query(models.Device).first()
    device.router_status = "offline"
    db.add(models.Telemetry(
        device_id=device.id, router_status="offline", wan_status="up", lan_status="normal",
        internet_reachable=False, latency_ms=0, packet_loss_percent=100,
    ))
    from app.services import correlation_engine
    from app.services.fault_detection_engine import compute_device_health
    correlation_engine.process_device(db, device)
    device.health = compute_device_health(device)
    db.commit()

    incident = (
        db.query(models.Incident)
        .filter(models.Incident.status != models.IncidentStatus.resolved)
        .order_by(models.Incident.detected_at.desc())
        .first()
    )
    assert incident.affected_customer_count == 1
    assert incident.severity == models.Severity.low
    assert incident.probable_cause == "Customer-side device or power issue"

    sim.set_scenario("normal")
