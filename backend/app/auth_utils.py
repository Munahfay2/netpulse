"""
auth_utils.py

Shared FastAPI dependency that verifies the JWT issued by /api/auth/login or
/api/auth/demo-login. Applied to every router that shouldn't be reachable
without a session — see main.py for exactly which routers require it.

Deliberately NOT applied to:
  - /api/auth/*        (that's how you get a token in the first place)
  - /api/health         (liveness probe)
  - /api/ussd           (Africa's Talking calls this directly — a customer's
                         feature phone has no NetPulse session)
  - /api/sms/*          (Africa's Talking webhook callbacks — same reason)
"""
import os

from dotenv import load_dotenv
from fastapi import Header, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from fastapi import Depends

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> models.User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    user = db.query(models.User).get(user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="User for this token no longer exists")
    return user
