from app import models
from app.services import africastalking_service as at


def test_demo_mode_is_active_without_credentials():
    # conftest clears AFRICASTALKING_USERNAME/API_KEY for the test process.
    assert at.DEMO_SMS_MODE is True
    assert at.demo_mode_banner() == "SIMULATED — Sandbox credentials not configured"


def test_send_sms_in_demo_mode_never_claims_real_delivery(db_session):
    db = db_session
    notification = at.send_sms(
        db, to="254712345678", message="Test message", recipient_type="test", recipient_id="TEST-1",
    )
    db.commit()

    assert notification.status == "simulated"
    assert notification.simulated is True
    # Full number must never be persisted to the outbound notification log.
    assert notification.masked_destination != "254712345678"
    assert notification.masked_destination.startswith("25471")
    assert "*" in notification.masked_destination


def test_mask_phone_handles_short_numbers():
    assert at.mask_phone("12345") == "*****"
    assert at.mask_phone("") == ""


def test_customer_outage_and_restoration_sms_wording(db_session):
    db = db_session
    customer = db.query(models.Customer).first()
    incident = models.Incident(
        title="Test Incident", incident_type="WAN/access connectivity issue",
        severity=models.Severity.low, affected_customer_count=1,
    )
    db.add(incident)
    db.flush()

    outage_notif = at.send_customer_outage_sms(db, customer, incident)
    assert "detected a connectivity issue" in outage_notif.message
    assert "will receive another update" in outage_notif.message

    restoration_notif = at.send_customer_restoration_sms(db, customer, incident)
    assert "restored" in restoration_notif.message
    db.commit()
