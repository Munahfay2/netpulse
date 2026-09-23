"""
Seeds NetPulse with a realistic-looking demo network: 5 locations, 10 OLTs,
100+ customers/devices, 10 technicians, and a handful of historical
(already-resolved) incidents, per spec sections 51-52.

Fictional names and phone numbers only — no real personal data.
"""
import json
import random
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

LOCATIONS = [
    ("Nakuru", "Rift Valley", -0.3031, 36.0800),
    ("Njoro", "Rift Valley", -0.3339, 35.9391),
    ("Naivasha", "Rift Valley", -0.7167, 36.4333),
    ("Eldoret", "Rift Valley", 0.5143, 35.2698),
    ("Kisumu", "Nyanza", -0.0917, 34.7680),
]

FIRST_NAMES = ["Brian", "Achieng", "Kiptoo", "Wanjiru", "Otieno", "Chebet", "Njoroge", "Amina",
               "Kamau", "Wafula", "Njeri", "Mutiso", "Cherono", "Wekesa", "Adhiambo", "Kiplangat",
               "Mwangi", "Auma", "Korir", "Nafula"]
LAST_NAMES = ["Kariuki", "Odhiambo", "Chege", "Rotich", "Wambui", "Barasa", "Kimani", "Onyango",
              "Cheruiyot", "Muthoni", "Simiyu", "Akinyi", "Langat", "Nyambura", "Too", "Wairimu"]

TECH_NAMES = [
    ("Brian Otieno", "Nakuru"), ("Faith Chebet", "Njoro"), ("Kevin Mwangi", "Naivasha"),
    ("Sharon Wafula", "Eldoret"), ("Dennis Korir", "Kisumu"), ("Grace Njeri", "Nakuru"),
    ("Peter Kiptoo", "Njoro"), ("Lilian Auma", "Naivasha"), ("Samuel Barasa", "Eldoret"),
    ("Mercy Adhiambo", "Kisumu"),
]


def _phone() -> str:
    return "2547" + "".join(str(random.randint(0, 9)) for _ in range(8))


def seed(db: Session, force: bool = False):
    if not force and db.query(models.Customer).count() > 0:
        return  # already seeded

    # --- demo user ---
    if not db.query(models.User).filter(models.User.email == "demo@netpulse.africa").first():
        db.add(models.User(
            email="demo@netpulse.africa",
            hashed_password=pwd_context.hash("demo-password-not-for-production"),
            full_name="Demo NOC Operator",
            role="admin",
            isp_name="Rift Valley Networks (Demo)",
        ))

    # --- locations ---
    locations = []
    for name, region, lat, lng in LOCATIONS:
        loc = models.NetworkLocation(name=name, region=region, latitude=lat, longitude=lng)
        db.add(loc)
        locations.append(loc)
    db.flush()

    # --- OLTs (10 total, 2 per location) + ODFs ---
    olts = []
    olt_counter = 1
    for loc in locations:
        for _ in range(2):
            olt_id = f"OLT-{olt_counter:03d}"
            olt = models.OLT(id=olt_id, location_id=loc.id, name=f"{loc.name} {olt_id}",
                              status=models.DeviceHealth.healthy)
            db.add(olt)
            olts.append(olt)
            olt_counter += 1
    db.flush()

    for olt in olts:
        db.add(models.ODF(olt_id=olt.id, port_count=48, status=models.DeviceHealth.healthy))
    db.flush()

    # --- technicians ---
    technicians = []
    for name, region in TECH_NAMES:
        t = models.Technician(name=name, phone=_phone(), region=region,
                               status=models.TechnicianStatus.available)
        db.add(t)
        technicians.append(t)
    db.flush()

    # --- customers + devices + onts, ~12-13 per OLT => 120+ total ---
    device_counter = 1
    customer_counter = 1
    all_devices = []
    for olt in olts:
        for _ in range(12):
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            customer_id = f"CUS-{customer_counter:04d}"
            customer = models.Customer(
                id=customer_id, name=name, phone=_phone(),
                location_id=olt.location_id, plan=random.choice(
                    ["Home Fibre 10Mbps", "Home Fibre 20Mbps", "Business Fibre 50Mbps"]
                ),
            )
            db.add(customer)

            ont = models.ONT(olt_id=olt.id, optical_level_dbm=round(random.uniform(-22, -14), 1),
                              status=models.DeviceHealth.healthy)
            db.add(ont)
            db.flush()

            device_id = f"CPE-{device_counter:04d}"
            device = models.Device(
                id=device_id, customer_id=customer.id, ont_id=ont.id, olt_id=olt.id,
                location_id=olt.location_id,
                router_status="online", wan_status="up", lan_status="normal",
                internet_reachable=True, latency_ms=round(random.uniform(15, 45), 1),
                packet_loss_percent=round(random.uniform(0, 1), 2),
                uptime_seconds=random.randint(3600, 500000),
                health=models.DeviceHealth.healthy,
            )
            db.add(device)
            all_devices.append(device)

            device_counter += 1
            customer_counter += 1
    db.flush()

    # --- historical (resolved) incidents, per spec section 52 ---
    now = datetime.utcnow()

    njoro = next(l for l in locations if l.name == "Njoro")
    nakuru = next(l for l in locations if l.name == "Nakuru")
    naivasha = next(l for l in locations if l.name == "Naivasha")
    olt_003 = next((o for o in olts if o.location_id == njoro.id), olts[0])
    olt_007 = next((o for o in olts if o.location_id == nakuru.id), olts[1])
    olt_002 = next((o for o in olts if o.location_id == naivasha.id), olts[2])

    def historical_incident(title, incident_type, olt, location, count, severity, days_ago, minutes_duration):
        detected = now - timedelta(days=days_ago, minutes=minutes_duration + 5)
        resolved = detected + timedelta(minutes=minutes_duration)
        incident = models.Incident(
            title=title, incident_type=incident_type, location_id=location.id, olt_id=olt.id,
            severity=severity, status=models.IncidentStatus.resolved,
            probable_cause="Access network disruption" if "Outage" in title else "Network degradation",
            probable_cause_confidence="High" if count >= 10 else "Medium",
            probable_cause_reasons=json.dumps([f"{count} customer(s) affected", f"customers share {olt.id}"]),
            recommended_checks=json.dumps(["Check OLT port status.", "Check ONT optical levels."]),
            affected_customer_count=count, detected_at=detected, resolved_at=resolved,
        )
        db.add(incident)
        db.flush()
        db.add(models.IncidentEvent(incident_id=incident.id, timestamp=detected,
                                     message="Incident created.", event_type="status_change"))
        db.add(models.IncidentEvent(incident_id=incident.id, timestamp=resolved,
                                     message="Incident automatically marked recovered.",
                                     event_type="status_change"))
        return incident

    historical_incident("Njoro Access Network Outage", "WAN/access connectivity issue",
                         olt_003, njoro, 38, models.Severity.critical, days_ago=3, minutes_duration=17)
    historical_incident("Nakuru High Latency", "Network degradation/congestion",
                         olt_007, nakuru, 7, models.Severity.medium, days_ago=1, minutes_duration=42)
    historical_incident("Naivasha Router Unreachable", "Device unreachable",
                         olt_002, naivasha, 1, models.Severity.low, days_ago=5, minutes_duration=9)

    existing_status = db.query(models.ServiceStatus).get(1)
    if existing_status:
        existing_status.demo_mode = True
        existing_status.simulation_scenario = "normal"
    else:
        db.add(models.ServiceStatus(id=1, demo_mode=True, simulation_scenario="normal"))
    db.commit()
    print(f"Seeded {len(locations)} locations, {len(olts)} OLTs, {len(all_devices)} customers/devices, "
          f"{len(technicians)} technicians, 3 historical incidents.")
