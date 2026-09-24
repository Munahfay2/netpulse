"""
USSD endpoint. Implements the Africa's Talking USSD webhook contract
(CON = continue session, END = end session) so it can be pointed at a real
Africa's Talking USSD channel with no code changes (spec section 25).

The browser-based USSD simulator (spec section 46) calls this same endpoint
with a `customer_id` instead of a real telecom-assigned phone number, since
sandbox test devices won't match our seeded demo customers.
"""
import json

from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services import africastalking_service as at

router = APIRouter(tags=["ussd"])

ISSUE_TYPES = {"1": "No Internet", "2": "Slow Internet", "3": "Intermittent Connection", "4": "Other"}

MAIN_MENU = (
    "Welcome to NetPulse\n"
    "1. Check my connection\n"
    "2. Report a problem\n"
    "3. Check outage status\n"
    "4. Contact support"
)

REPORT_MENU = (
    "Select problem:\n"
    "1. No Internet\n"
    "2. Slow Internet\n"
    "3. Intermittent Connection\n"
    "4. Other"
)


def _resolve_customer(db: Session, phone_number: str, customer_id: str = None):
    if customer_id:
        return db.query(models.Customer).get(customer_id)
    return db.query(models.Customer).filter(models.Customer.phone == phone_number).first()


def _active_incident_for_customer(db: Session, customer: models.Customer):
    if not customer or not customer.device:
        return None
    link = (
        db.query(models.IncidentDevice)
        .join(models.Incident)
        .filter(
            models.IncidentDevice.device_id == customer.device.id,
            models.Incident.status.notin_(["Resolved", "Closed"]),
        )
        .first()
    )
    return link.incident if link else None


@router.post("/api/ussd", response_class=PlainTextResponse)
@router.post("/ussd", response_class=PlainTextResponse)
def ussd_webhook(
    sessionId: str = Form(...),
    phoneNumber: str = Form(""),
    text: str = Form(""),
    customer_id: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        parts = [p for p in text.split("*") if p != ""] if text else []
        response = _handle_flow(db, sessionId, phoneNumber, parts, customer_id)
    except Exception as exc:
        # Spec section 44: never crash on a malformed USSD request.
        response = f"END NetPulse is temporarily unavailable. Please try again shortly."
        print(f"[ussd] error: {exc}")

    db.add(models.UssdSession(session_id=sessionId, phone_number=phoneNumber, text=text))
    db.commit()
    return response


def _handle_flow(db: Session, session_id: str, phone_number: str, parts, customer_id: str) -> str:
    customer = _resolve_customer(db, phone_number, customer_id)

    if len(parts) == 0:
        return f"CON {MAIN_MENU}"

    choice = parts[0]

    if choice == "1":
        # Check my connection
        if not customer or not customer.device:
            return "END We couldn't find a connection registered to this number."
        device = customer.device
        incident = _active_incident_for_customer(db, customer)
        if incident:
            return (
                "END Your connection status:\n"
                "Status: Service disruption detected\n"
                "Area outage: Yes"
            )
        return (
            "END Your connection status:\n"
            "Status: Online\n"
            f"Latency: {round(device.latency_ms)}ms\n"
            f"Packet loss: {round(device.packet_loss_percent)}%"
        )

    if choice == "2":
        if len(parts) == 1:
            return f"CON {REPORT_MENU}"
        issue_choice = parts[1]
        issue_type = ISSUE_TYPES.get(issue_choice, "Other")
        if not customer:
            return "END We couldn't find an account registered to this number."
        ticket = models.Ticket(customer_id=customer.id, issue_type=issue_type, channel="USSD")
        db.add(ticket)
        db.flush()
        at.send_ticket_confirmation_sms(db, customer, ticket)
        return f"END Your issue has been recorded.\nTicket ID: {ticket.id}"

    if choice == "3":
        # Check outage status
        incident = _active_incident_for_customer(db, customer) if customer else None
        if not incident:
            return "END No active outage has been detected in your area."
        return (
            "END Network issue detected in your area.\n"
            f"Affected customers: {incident.affected_customer_count}\n"
            "Status: Technicians investigating.\n"
            "You will receive an SMS when service is restored."
        )

    if choice == "4":
        return "END Please call customer support or wait for an SMS update."

    return f"CON {MAIN_MENU}"
