from datetime import date

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.models import User


def _override_user():
    return User(id=1, username="admin", role_id=1, password_hash="x")


def test_health_endpoint(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200


def test_create_transaction_api(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)

    payload = {
        "company_id": 1,
        "fiscal_year_id": 1,
        "date": str(date(2026, 1, 2)),
        "vendor": "메타",
        "description": "인스타 광고",
        "amount": 10000,
        "vat_included": True,
        "supply_amount": 9091,
        "vat_amount": 909,
        "payment_method": "보통예금",
        "evidence_type": "세금계산서",
        "memo": "",
    }
    r = client.post("/api/transactions", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] in ["suggested", "review_needed"]
