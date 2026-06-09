from datetime import datetime

from opsledger.models import ActivityLog, OnCallEngineer, WorkOrder
from opsledger.sample_data import seed_work_orders
from opsledger.services import (
    VALID_ESCALATION_STATUSES,
    dashboard_summary,
    escalation_status_for,
    export_escalation_csv,
    filter_work_orders,
    group_by_team,
    recommend_oncall,
)


def test_filter_work_orders_by_status_and_team():
    orders = seed_work_orders(datetime(2026, 6, 8, 9, 0))

    result = filter_work_orders(orders, status="open", team="Facilities")

    assert [order.id for order in result] == [2, 4]


def test_filter_work_orders_by_assignee():
    orders = seed_work_orders(datetime(2026, 6, 8, 9, 0))

    result = filter_work_orders(orders, assignee="Iris")

    assert len(result) == 1
    assert result[0].id == 1


def test_filter_work_orders_by_escalation_level():
    orders = seed_work_orders(datetime(2026, 6, 8, 9, 0))

    result = filter_work_orders(orders, escalation_level=1)

    assert len(result) == 1
    assert result[0].id == 4


def test_filter_work_orders_by_escalation_level_zero():
    orders = seed_work_orders(datetime(2026, 6, 8, 9, 0))

    result = filter_work_orders(orders, escalation_level=0)

    assert len(result) == 4


def test_filter_work_orders_by_escalation_status_none():
    orders = seed_work_orders(datetime(2026, 6, 8, 9, 0))

    result = filter_work_orders(orders, escalation_status="none")

    assert len(result) == 4
    assert all(o.escalation_level == 0 for o in result)


def test_filter_work_orders_by_escalation_status_escalated():
    orders = seed_work_orders(datetime(2026, 6, 8, 9, 0))

    result = filter_work_orders(orders, escalation_status="escalated")

    assert len(result) == 1
    assert result[0].id == 4


def test_escalation_status_for_returns_correct_value():
    base = datetime(2026, 6, 8, 9, 0)
    order_none = WorkOrder(1, "A", "IT", "low", "open", base, "X", "Y")
    order_esc = WorkOrder(2, "B", "IT", "low", "open", base, "X", "Y", escalation_level=2)

    assert escalation_status_for(order_none) == "none"
    assert escalation_status_for(order_esc) == "escalated"


def test_valid_escalation_statuses_constant():
    assert "none" in VALID_ESCALATION_STATUSES
    assert "escalated" in VALID_ESCALATION_STATUSES


def test_dashboard_summary_counts_statuses_and_priority():
    orders = seed_work_orders(datetime(2026, 6, 8, 9, 0))

    summary = dashboard_summary(orders)

    assert summary == {
        "total": 5,
        "open": 3,
        "blocked": 1,
        "done": 1,
        "high_priority": 2,
    }


def test_group_by_team_counts_each_team():
    orders = seed_work_orders(datetime(2026, 6, 8, 9, 0))

    assert group_by_team(orders)["Facilities"] == 2


def test_recommend_oncall_prefers_matching_team_and_low_load():
    base = datetime(2026, 6, 8, 9, 0)
    order = WorkOrder(1, "Test", "Security", "high", "open", base, "Iris", "A")
    engineers = [
        OnCallEngineer("Alice", ["Security"], current_load=0),
        OnCallEngineer("Bob", ["Facilities"], current_load=0),
        OnCallEngineer("Carol", ["Security"], current_load=3),
    ]

    result = recommend_oncall(order, engineers, now=base)

    assert result[0]["name"] == "Alice"
    assert result[0]["score"] > result[-1]["score"]


def test_recommend_oncall_sla_urgency_bonus():
    from datetime import timedelta

    base = datetime(2026, 6, 8, 9, 0)
    order = WorkOrder(1, "Urgent", "IT", "high", "open", base + timedelta(hours=2), "X", "A")
    engineers = [
        OnCallEngineer("Alice", ["IT"], current_load=2),
        OnCallEngineer("Bob", ["IT"], current_load=2),
    ]

    result = recommend_oncall(order, engineers, now=base)

    assert result[0]["score"] > result[1]["score"]


def test_recommend_oncall_empty_engineers():
    base = datetime(2026, 6, 8, 9, 0)
    order = WorkOrder(1, "Test", "Security", "high", "open", base, "Iris", "A")

    assert recommend_oncall(order, [], now=base) == []


def test_export_escalation_csv_filters_escalated_only():
    logs = [
        ActivityLog(1, 1, "created", "sys", datetime(2026, 1, 1), "init"),
        ActivityLog(2, 1, "escalated", "Bob", datetime(2026, 1, 2), "Escalated to X: urgent"),
        ActivityLog(3, 2, "escalated", "Alice", datetime(2026, 1, 3), "Escalated to Y: sla risk"),
    ]

    csv_text = export_escalation_csv(logs)
    lines = csv_text.strip().split("\n")

    assert lines[0] == "id,work_order_id,actor,created_at,detail,escalation_status"
    assert len(lines) == 3
    assert "Bob" in lines[1]
    assert "Alice" in lines[2]


def test_export_escalation_csv_with_work_orders_enrichment():
    base = datetime(2026, 6, 8, 9, 0)
    logs = [
        ActivityLog(1, 1, "escalated", "Bob", datetime(2026, 1, 2), "Escalated to X"),
    ]
    work_orders = [
        WorkOrder(1, "WO", "IT", "high", "open", base, "X", "Y", escalation_level=2),
    ]

    csv_text = export_escalation_csv(logs, work_orders)
    lines = csv_text.strip().split("\n")

    assert "escalated" in lines[1]


def test_export_escalation_csv_empty_when_no_escalations():
    logs = [ActivityLog(1, 1, "created", "sys", datetime(2026, 1, 1), "init")]

    csv_text = export_escalation_csv(logs)
    lines = csv_text.strip().split("\n")

    assert len(lines) == 1
