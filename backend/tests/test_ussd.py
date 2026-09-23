def test_ussd_main_menu(client):
    res = client.post("/api/ussd", data={"sessionId": "s1", "phoneNumber": "254700000001", "text": ""})
    assert res.status_code == 200
    assert res.text.startswith("CON Welcome to NetPulse")
    assert "1. Check my connection" in res.text


def test_ussd_check_connection_for_unknown_number(client):
    res = client.post("/api/ussd", data={"sessionId": "s2", "phoneNumber": "254799999999", "text": "1"})
    assert res.text.startswith("END")
    assert "couldn't find" in res.text.lower()


def test_ussd_report_problem_creates_ticket_and_confirmation_sms(client, auth_headers):
    customers = client.get("/api/customers", headers=auth_headers, params={"page_size": 1}).json()
    customer_id = customers[0]["id"]

    res = client.post("/api/ussd", data={
        "sessionId": "s3", "phoneNumber": "254700000002", "text": "2*1", "customer_id": customer_id,
    })
    assert res.text.startswith("END Your issue has been recorded.")
    assert "Ticket ID: NP-TKT-" in res.text

    notifications = client.get(
        "/api/notifications", headers=auth_headers, params={"limit": 5},
    ).json()
    assert any("Ticket ID" in n["message"] for n in notifications)


def test_ussd_check_outage_status_no_outage(client, auth_headers):
    # Other tests in this suite intentionally fault specific customers, so
    # explicitly pick one whose device is currently healthy rather than
    # assuming the first page is untouched.
    customers = client.get("/api/customers", headers=auth_headers, params={"page_size": 50}).json()
    healthy_customer = next(c for c in customers if c["device_health"] == "healthy")
    customer_id = healthy_customer["id"]
    res = client.post("/api/ussd", data={
        "sessionId": "s4", "phoneNumber": "254700000003", "text": "3", "customer_id": customer_id,
    })
    assert res.text == "END No active outage has been detected in your area."


def test_ussd_contact_support(client):
    res = client.post("/api/ussd", data={"sessionId": "s5", "phoneNumber": "254700000004", "text": "4"})
    assert "call customer support" in res.text.lower()


def test_ussd_malformed_request_never_crashes(client):
    """Spec section 44: a malformed USSD request must degrade gracefully,
    never 500 the app."""
    res = client.post("/api/ussd", data={
        "sessionId": "s6", "phoneNumber": "254700000005", "text": "99*garbage*???",
    })
    assert res.status_code == 200
    assert res.text.startswith("CON") or res.text.startswith("END")
