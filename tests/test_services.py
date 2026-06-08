from datetime import datetime

from opsledger.sample_data import seed_work_orders
from opsledger.services import dashboard_summary, filter_work_orders, group_by_team


def test_filter_work_orders_by_status_and_team():
    orders = seed_work_orders(datetime(2026, 6, 8, 9, 0))

    result = filter_work_orders(orders, status="open", team="Facilities")

    assert [order.id for order in result] == [2, 4]


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

