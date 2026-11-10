"""API tests (need fastapi + httpx):  python -m pytest backend/tests/test_api.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

VALID = {"category": "Electronics", "region": "Northern", "quantity": 2,
         "unit_price": 45000, "discount_rate": 0.1, "returned": 0}


def test_health_and_summary():                       # T01 / T02
    with TestClient(app) as c:
        assert c.get("/api/health").json()["status"] == "ok"
        assert c.get("/api/summary").json()["total_orders"] > 0


def test_valid_prediction_is_bounded():              # T04
    with TestClient(app) as c:
        r = c.post("/api/predict-late-delivery", json=VALID)
        assert r.status_code == 200 and 0 <= r.json()["probability"] <= 1


def test_invalid_discount_rejected():                # T05
    with TestClient(app) as c:
        assert c.post("/api/predict-late-delivery", json={**VALID, "discount_rate": 0.9}).status_code == 422


def test_unknown_filter_rejected():
    with TestClient(app) as c:
        assert c.get("/api/summary", params={"category": "Toys"}).status_code == 422
