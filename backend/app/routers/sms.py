from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/sms", tags=["sms"])


@router.post("/callback")
def incoming_sms_callback(
    from_: str = Form(None, alias="from"),
    text: str = Form(""),
    to: str = Form(None),
    db: Session = Depends(get_db),
):
    """Receives inbound SMS from Africa's Talking (e.g. a customer texting
    support). Kept isolated from business logic per spec section 25 — for
    the MVP we just log it as a ticket-worthy event."""
    customer = db.query(models.Customer).filter(models.Customer.phone == from_).first()
    ticket = models.Ticket(
        customer_id=customer.id if customer else None,
        issue_type="Other",
        channel="SMS",
    )
    db.add(ticket)
    db.commit()
    return {"status": "received", "ticket_id": ticket.id}


@router.post("/delivery-report")
def delivery_report(
    id: str = Form(None),
    status: str = Form(None),
    phoneNumber: str = Form(None),
    db: Session = Depends(get_db),
):
    """Receives delivery reports from Africa's Talking and updates the
    matching notification's status where possible."""
    if id:
        notif = (
            db.query(models.Notification)
            .filter(models.Notification.message.contains(id))
            .first()
        )
        if notif and status:
            notif.status = status.lower()
            db.commit()
    return {"status": "ok"}
