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


def test_work_orders_filter_by_assignee():
    response = make_client().get("/work-orders?assignee=Iris")

    assert response.status_code == 200
    assert b"Replace lobby access reader" in response.data
    assert b"Inspect chilled water pump" not in response.data


def test_work_orders_filter_by_escalation_level():
    response = make_client().get("/work-orders?escalation_level=1")

    assert response.status_code == 200
    assert b"Repair loading dock sensor" in response.data
    assert b"Replace lobby access reader" not in response.data


def test_api_work_orders_returns_filtered_json():
    response = make_client().get("/api/work-orders?status=blocked")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Patch visitor kiosk"


def test_api_work_orders_includes_escalation_fields():
    response = make_client().get("/api/work-orders?assignee=Lena")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["escalation_level"] == 1
    assert payload[0]["escalated_to"] == "Mason"
    assert payload[0]["escalation_status"] == "escalated"


def test_api_work_orders_filter_by_escalation_level():
    response = make_client().get("/api/work-orders?escalation_level=0")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 4
    assert all(o["escalation_level"] == 0 for o in payload)


def test_work_order_detail_shows_recommendations():
    response = make_client().get("/work-orders/1")

    assert response.status_code == 200
    assert b"Recommended On-Call" in response.data
    assert b"Escalate" in response.data


def test_work_order_detail_shows_escalation_info():
    response = make_client().get("/work-orders/4")

    assert response.status_code == 200
    assert b"Escalation Level" in response.data
    assert b"Escalated To" in response.data


def test_escalate_work_order_post():
    app = create_app({"TESTING": True, "STORE": WorkOrderStore(datetime(2026, 6, 8, 9, 0))})
    client = app.test_client()

    response = client.post(
        "/work-orders/1/escalate",
        data={"target": "Raj", "actor": "Admin", "reason": "SLA breach imminent"},
    )

    assert response.status_code == 302

    store: WorkOrderStore = app.config["STORE"]
    order = store.get_work_order(1)
    assert order.escalation_level == 1
    assert order.escalated_to == "Raj"

    logs = store.logs_for(1)
    esc_logs = [l for l in logs if l.action == "escalated"]
    assert len(esc_logs) == 1
    assert "Raj" in esc_logs[0].detail
    assert "Admin" == esc_logs[0].actor


def test_escalate_work_order_missing_fields_returns_400():
    client = make_client()

    response = client.post("/work-orders/1/escalate", data={"target": "Raj"})

    assert response.status_code == 400


def test_escalate_work_order_not_found_returns_404():
    client = make_client()

    response = client.post(
        "/work-orders/999/escalate",
        data={"target": "Raj", "actor": "Admin", "reason": "test"},
    )

    assert response.status_code == 404


def test_api_recommend_oncall():
    response = make_client().get("/api/work-orders/1/recommend-oncall")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) > 0
    assert "name" in payload[0]
    assert "score" in payload[0]
    assert "load" in payload[0]


def test_api_recommend_oncall_not_found():
    response = make_client().get("/api/work-orders/999/recommend-oncall")

    assert response.status_code == 404


def test_api_escalation_audit_csv():
    response = make_client().get("/api/escalation-audit/csv")

    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"
    text = response.data.decode()
    lines = text.strip().split("\n")
    assert lines[0] == "id,work_order_id,actor,created_at,detail,escalation_status"
    assert len(lines) == 2
    assert "Lena" in lines[1]
    assert "escalated" in lines[1]


def test_api_escalation_audit_csv_after_new_escalation():
    app = create_app({"TESTING": True, "STORE": WorkOrderStore(datetime(2026, 6, 8, 9, 0))})
    client = app.test_client()

    client.post(
        "/work-orders/1/escalate",
        data={"target": "Nora", "actor": "Admin", "reason": "Urgent"},
    )

    response = client.get("/api/escalation-audit/csv")
    text = response.data.decode()
    lines = text.strip().split("\n")
    assert len(lines) == 3


def test_api_work_orders_filter_by_escalation_status_none():
    response = make_client().get("/api/work-orders?escalation_status=none")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 4
    assert all(o["escalation_status"] == "none" for o in payload)


def test_api_work_orders_filter_by_escalation_status_escalated():
    response = make_client().get("/api/work-orders?escalation_status=escalated")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["escalation_status"] == "escalated"
    assert payload[0]["id"] == 4


def test_api_work_orders_invalid_escalation_status_returns_400():
    response = make_client().get("/api/work-orders?escalation_status=bogus")

    assert response.status_code == 400


def test_api_work_orders_invalid_escalation_level_returns_400():
    response = make_client().get("/api/work-orders?escalation_level=abc")

    assert response.status_code == 400


def test_work_orders_invalid_escalation_status_returns_400():
    response = make_client().get("/work-orders?escalation_status=invalid")

    assert response.status_code == 400


def test_work_orders_invalid_escalation_level_returns_400():
    response = make_client().get("/work-orders?escalation_level=-1")

    assert response.status_code == 400


def test_work_orders_filter_by_escalation_status_escalated():
    response = make_client().get("/work-orders?escalation_status=escalated")

    assert response.status_code == 200
    assert b"Repair loading dock sensor" in response.data
    assert b"Replace lobby access reader" not in response.data


def test_api_work_orders_escalation_status_field_present():
    response = make_client().get("/api/work-orders")

    assert response.status_code == 200
    payload = response.get_json()
    for item in payload:
        assert "escalation_status" in item
        assert item["escalation_status"] in ("none", "escalated")
