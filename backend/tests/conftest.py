"""
Shared pytest fixtures.

Each test session gets its own throwaway SQLite file (never the developer's
netpulse.db) so tests are hermetic and can be run repeatedly without manual
cleanup. TESTING=1 also disables the background telemetry ticker (see
app/main.py) so tests control simulation ticks explicitly and deterministically.
"""
import os
import tempfile

import pytest

# Must be set before importing the app so app.database picks up the test DB.
_tmp_dir = tempfile.mkdtemp(prefix="netpulse_test_")
_TEST_DB_PATH = os.path.join(_tmp_dir, "test_netpulse.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ["TESTING"] = "1"
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ["AFRICASTALKING_USERNAME"] = ""
os.environ["AFRICASTALKING_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    """Create schema once for the whole test session; FastAPI's startup
    event (which also seeds demo data) runs automatically via TestClient's
    context manager below."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers(client):
    res = client.post("/api/auth/demo-login")
    assert res.status_code == 200, res.text
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
