import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .auth_utils import get_current_user
from .database import Base, engine, session_scope
from .routers import (auth, customers, dashboard, devices, incidents,
                       network, notifications, simulator, sms, technicians,
                       telemetry, ussd)
from .seed import seed
from .services import telemetry_simulator

load_dotenv()

app = FastAPI(
    title="NetPulse API",
    description="Detect. Diagnose. Notify. Restore. — ISP fault detection & customer alert platform.",
    version="0.1.0",
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(incidents.router)
app.include_router(simulator.router)
app.include_router(customers.router)
app.include_router(technicians.router)
app.include_router(notifications.router)
app.include_router(ussd.router)
app.include_router(sms.router)
app.include_router(network.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with session_scope() as db:
        seed(db)
    # The test suite drives the detection/correlation pipeline directly and
    # deterministically (see tests/), so the background ticker is disabled
    # under TESTING=1 to avoid flaky timing-dependent assertions.
    if os.getenv("TESTING") != "1":
        interval = int(os.getenv("TELEMETRY_INTERVAL_SECONDS", "5"))
        telemetry_simulator.start_background_loop(interval)


@app.on_event("shutdown")
def on_shutdown():
    telemetry_simulator.stop_background_loop()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "netpulse-api"}


@app.post("/api/demo/reset")
def reset_demo(current_user: models.User = Depends(get_current_user)):
    """Resets all incidents, telemetry and simulation state (spec section 45)."""
    with session_scope() as db:
        db.query(models.Telemetry).delete()
        db.query(models.IncidentEvent).delete()
        db.query(models.IncidentDevice).delete()
        db.query(models.Notification).delete()
        db.query(models.Ticket).delete()
        db.query(models.Incident).delete()
        db.query(models.Customer).delete()
        db.query(models.Device).delete()
        db.query(models.ONT).delete()
        db.query(models.ODF).delete()
        db.query(models.OLT).delete()
        db.query(models.Technician).delete()
        db.query(models.NetworkLocation).delete()
        db.query(models.ServiceStatus).delete()
        # Users are intentionally NOT deleted here: resetting demo network
        # data should never invalidate an operator's current login session.
        db.commit()
        from .seed import seed as seed_fn
        seed_fn(db, force=True)
    telemetry_simulator.set_scenario("normal")
    return {"status": "reset"}
