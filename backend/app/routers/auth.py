import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")


class LoginIn(BaseModel):
    email: str
    password: str


def _issue_token(user: models.User) -> str:
    payload = {"sub": user.id, "email": user.email, "role": user.role,
               "exp": datetime.utcnow() + timedelta(hours=12)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return {"token": _issue_token(user), "user": {"id": user.id, "email": user.email,
                                                    "full_name": user.full_name, "isp_name": user.isp_name}}


@router.post("/demo-login")
def demo_login(db: Session = Depends(get_db)):
    """Clearly-separated demo credentials for the hackathon judge — no
    production credentials required (spec section 8)."""
    user = db.query(models.User).filter(models.User.email == "demo@netpulse.africa").first()
    if not user:
        user = models.User(
            email="demo@netpulse.africa",
            hashed_password=pwd_context.hash("demo-password-not-for-production"),
            full_name="Demo NOC Operator",
            role="admin",
            isp_name="Rift Valley Networks (Demo)",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"token": _issue_token(user), "user": {"id": user.id, "email": user.email,
                                                    "full_name": user.full_name, "isp_name": user.isp_name}}
