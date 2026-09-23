"""
africastalking_service.py

Single point of integration with Africa's Talking. Every outbound SMS and
every inbound USSD request flows through here, so swapping the sandbox for
production credentials — or swapping Africa's Talking for another aggregator
— never touches the rest of the codebase.

If AFRICASTALKING_USERNAME / AFRICASTALKING_API_KEY are not set, the service
runs in Demo SMS Mode: it never claims a fake HTTP 200 from Africa's Talking,
it clearly labels every message as SIMULATED, and stores it in the
notification log exactly like a real send would be.
"""
import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .. import models

load_dotenv()

AT_USERNAME = os.getenv("AFRICASTALKING_USERNAME", "").strip()
AT_API_KEY = os.getenv("AFRICASTALKING_API_KEY", "").strip()
AT_SENDER_ID = os.getenv("AFRICASTALKING_SENDER_ID", "NetPulse").strip()

DEMO_SMS_MODE = not (AT_USERNAME and AT_API_KEY)

_africastalking_sdk = None
_at_sms = None
if not DEMO_SMS_MODE:
    try:
        import africastalking as _africastalking_sdk  # type: ignore

        _africastalking_sdk.initialize(AT_USERNAME, AT_API_KEY)
        _at_sms = _africastalking_sdk.SMS
    except Exception:
        # Package not installed, or sandbox unreachable — fall back gracefully
        # rather than crashing the app (see spec section 44, error handling).
        DEMO_SMS_MODE = True


def mask_phone(phone: str) -> str:
    if not phone:
        return ""
    digits = phone
    if len(digits) <= 7:
        return "*" * len(digits)
    return digits[:5] + "*" * (len(digits) - 7) + digits[-2:]


def send_sms(db: Session, *, to: str, message: str, recipient_type: str,
             recipient_id: str, incident_id: Optional[str] = None) -> models.Notification:
    """Send (or simulate) a single SMS and log it to the notifications table."""
    status = "sent"
    simulated = DEMO_SMS_MODE

    if DEMO_SMS_MODE:
        # SIMULATED — Sandbox credentials not configured.
        # We deliberately do not fabricate a real Africa's Talking response.
        status = "simulated"
    else:
        try:
            _at_sms.send(message, [to], sender_id=AT_SENDER_ID or None)
            status = "sent"
        except Exception:
            status = "failed"

    notification = models.Notification(
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        masked_destination=mask_phone(to),
        channel="SMS",
        message=message,
        status=status,
        incident_id=incident_id,
        simulated=simulated,
    )
    db.add(notification)
    db.flush()
    return notification


def send_customer_outage_sms(db: Session, customer: models.Customer, incident: models.Incident):
    message = (
        "NetPulse: We have detected a connectivity issue affecting your area. "
        "Our technical team has been notified and is investigating. You will "
        "receive another update when service is restored."
    )
    return send_sms(
        db, to=customer.phone, message=message,
        recipient_type="customer", recipient_id=customer.id, incident_id=incident.id,
    )


def send_customer_restoration_sms(db: Session, customer: models.Customer, incident: models.Incident):
    message = "NetPulse: Your internet service has been restored. Thank you for your patience."
    return send_sms(
        db, to=customer.phone, message=message,
        recipient_type="customer", recipient_id=customer.id, incident_id=incident.id,
    )


def send_technician_alert(db: Session, technician: models.Technician, incident: models.Incident,
                           location_name: str):
    message = (
        f"NETPULSE ALERT: Possible {incident.incident_type.lower()} in {location_name}. "
        f"{incident.affected_customer_count} customers affected. OLT: {incident.olt_id}. "
        f"Please investigate OLT/optical/fibre path."
    )
    return send_sms(
        db, to=technician.phone, message=message,
        recipient_type="technician", recipient_id=technician.id, incident_id=incident.id,
    )


def send_ticket_confirmation_sms(db: Session, customer: models.Customer, ticket: models.Ticket):
    message = f"NetPulse: Your issue has been recorded. Ticket ID: {ticket.id}. We'll update you by SMS."
    return send_sms(
        db, to=customer.phone, message=message,
        recipient_type="customer", recipient_id=customer.id,
    )


def demo_mode_banner() -> Optional[str]:
    return "SIMULATED — Sandbox credentials not configured" if DEMO_SMS_MODE else None
