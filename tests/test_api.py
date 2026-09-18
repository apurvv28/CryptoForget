import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from src.db.database import drop_db, init_db

client = TestClient(app)


def setup_module():
    drop_db()
    init_db()


def test_health_and_recommend_endpoints():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    click_res = client.post("/clicks", json={"user_id": "U1000", "news_id": "N1234"})
    assert click_res.status_code == 200
    assert click_res.json()["status"] == "recorded"

    rec_res = client.post(
        "/recommend",
        json={"user_id": "U1000", "candidate_news_ids": ["N1234", "N5678"], "top_k": 5},
    )
    assert rec_res.status_code == 200
    assert len(rec_res.json()["recommendations"]) > 0


def test_user_agent_endpoints():
    users_res = client.get("/api/v1/users")
    assert users_res.status_code == 200
    users = users_res.json()
    assert len(users) >= 15

    onboard_res = client.post(
        "/api/v1/users/onboard",
        json={"user_id": "U1999", "name": "Test User", "email": "test@example.com"},
    )
    assert onboard_res.status_code == 200
    assert onboard_res.json()["user_id"] == "U1999"


def test_unlearning_and_certificate_flow():
    # Submit Path B deletion request
    del_res = client.post(
        "/api/v1/delete-user",
        json={"user_id": "U1002", "deletion_type": "Path B"},
    )
    assert del_res.status_code == 200
    body = del_res.json()
    assert body["status"] == "COMPLETED"
    cert = body["certificate"]
    assert cert["user_id"] == "U1002"
    assert cert["ecdsa_signature"] != ""

    # Verify certificate
    verify_res = client.post(
        "/api/v1/verify-certificate",
        json={"certificate": cert},
    )
    assert verify_res.status_code == 200
    v_body = verify_res.json()
    assert v_body["is_valid"] is True
    assert v_body["verification_time_ms"] < 100.0


def test_auditor_endpoints():
    audit_res = client.get("/api/v1/auditor/audit-trail")
    assert audit_res.status_code == 200
    assert audit_res.json()["ledger_integrity_valid"] is True

    drift_res = client.get("/api/v1/auditor/drift-metrics")
    assert drift_res.status_code == 200
    assert "dataset_drift" in drift_res.json()

    mia_res = client.get("/api/v1/auditor/mia-benchmark")
    assert mia_res.status_code == 200
    assert mia_res.json()["target_random_guessing_baseline"] == 0.50
