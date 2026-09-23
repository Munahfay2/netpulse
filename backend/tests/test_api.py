import time

PROTECTED_ENDPOINTS = [
    "/api/dashboard/summary",
    "/api/devices",
    "/api/incidents",
    "/api/customers",
    "/api/technicians",
    "/api/notifications",
    "/api/network/overview",
]


def test_protected_endpoints_reject_missing_auth(client):
    for path in PROTECTED_ENDPOINTS:
        res = client.get(path)
        assert res.status_code == 401, f"{path} should require auth, got {res.status_code}"


def test_protected_endpoints_reject_garbage_token(client):
    res = client.get("/api/dashboard/summary", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_protected_endpoints_accept_valid_token(client, auth_headers):
    for path in PROTECTED_ENDPOINTS:
        res = client.get(path, headers=auth_headers)
        assert res.status_code == 200, f"{path} failed: {res.text}"


def test_health_endpoint_is_public(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_demo_login_is_idempotent_and_public(client):
    res1 = client.post("/api/auth/demo-login")
    res2 = client.post("/api/auth/demo-login")
    assert res1.status_code == 200 and res2.status_code == 200
    assert res1.json()["user"]["email"] == res2.json()["user"]["email"]


def test_dashboard_summary_shape(client, auth_headers):
    res = client.get("/api/dashboard/summary", headers=auth_headers)
    body = res.json()
    for key in ("network_health_percent", "active_incidents", "customers_affected",
                "devices_offline", "avg_resolution_minutes", "incidents_today"):
        assert key in body


def test_simulator_area_outage_end_to_end_via_api(client, auth_headers):
    """The flagship demo scenario, exercised purely through the HTTP API —
    as close as an automated test gets to a judge clicking the button."""
    res = client.post("/api/simulator/area-outage", headers=auth_headers)
    assert res.status_code == 200
    target_olt = res.json()["target_olt"]
    assert target_olt

    # Manually advance the simulator since the background ticker is
    # disabled under TESTING=1.
    from app.database import SessionLocal
    from app.services.telemetry_simulator import SimulatedTelemetrySource
    db = SessionLocal()
    try:
        SimulatedTelemetrySource().poll(db)
        db.commit()
    finally:
        db.close()

    incidents = client.get("/api/incidents", headers=auth_headers).json()
    matching = [i for i in incidents if i["olt_id"] == target_olt and i["status"] != "Resolved"]
    assert len(matching) == 1, "area outage must correlate into exactly one incident"
    incident = matching[0]
    assert incident["affected_customer_count"] >= 10
    assert incident["probable_cause_confidence"] in ("Medium", "High")
    assert len(incident["recommended_checks"]) > 0
    assert len(incident["events"]) > 0

    incident_detail = client.get(f"/api/incidents/{incident['id']}", headers=auth_headers).json()
    assert incident_detail["id"] == incident["id"]

    # Restore and confirm resolution.
    client.post("/api/simulator/restore", headers=auth_headers)
    db = SessionLocal()
    try:
        SimulatedTelemetrySource().poll(db)
        db.commit()
    finally:
        db.close()

    resolved = client.get(f"/api/incidents/{incident['id']}", headers=auth_headers).json()
    assert resolved["status"] == "Resolved"


def test_incident_status_update_and_technician_assignment(client, auth_headers):
    incidents = client.get("/api/incidents", headers=auth_headers).json()
    assert incidents, "seed data should include at least one historical incident"
    incident_id = incidents[-1]["id"]

    technicians = client.get("/api/technicians", headers=auth_headers).json()
    technician_id = technicians[0]["id"]

    res = client.post(
        f"/api/incidents/{incident_id}/assign",
        headers=auth_headers,
        json={"technician_id": technician_id},
    )
    assert res.status_code == 200
    assert res.json()["assigned_technician_name"] == technicians[0]["name"]

    res = client.patch(
        f"/api/incidents/{incident_id}",
        headers=auth_headers,
        json={"status": "In Progress"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "In Progress"


def test_reset_demo_requires_auth_and_reseeds(client, auth_headers):
    res = client.post("/api/demo/reset")
    assert res.status_code == 401

    res = client.post("/api/demo/reset", headers=auth_headers)
    assert res.status_code == 200

    summary = client.get("/api/dashboard/summary", headers=auth_headers).json()
    assert summary["devices_online"] > 0
