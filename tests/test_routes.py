from datetime import datetime

from opsledger import create_app
from opsledger.store import WorkOrderStore


def make_client():
    app = create_app({"TESTING": True, "STORE": WorkOrderStore(datetime(2026, 6, 8, 9, 0))})
    return app.test_client()


def test_dashboard_renders_summary():
    response = make_client().get("/")

    assert response.status_code == 200
    assert b"Operations dashboard" in response.data
    assert b"High priority" in response.data


def test_work_orders_filter_by_priority():
    response = make_client().get("/work-orders?priority=high")

    assert response.status_code == 200
    assert b"Replace lobby access reader" in response.data
    assert b"Inspect chilled water pump" not in response.data


def test_api_work_orders_returns_filtered_json():
    response = make_client().get("/api/work-orders?status=blocked")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Patch visitor kiosk"

