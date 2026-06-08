from __future__ import annotations

from collections import Counter
from datetime import datetime

from .models import WorkOrder


def filter_work_orders(
    work_orders: list[WorkOrder],
    status: str | None = None,
    priority: str | None = None,
    team: str | None = None,
) -> list[WorkOrder]:
    filtered = work_orders
    if status:
        filtered = [order for order in filtered if order.status == status]
    if priority:
        filtered = [order for order in filtered if order.priority == priority]
    if team:
        filtered = [order for order in filtered if order.team == team]
    return filtered


def dashboard_summary(work_orders: list[WorkOrder], now: datetime | None = None) -> dict[str, int]:
    del now
    counts = Counter(order.status for order in work_orders)
    return {
        "total": len(work_orders),
        "open": counts["open"],
        "blocked": counts["blocked"],
        "done": counts["done"],
        "high_priority": sum(1 for order in work_orders if order.priority == "high"),
    }


def group_by_team(work_orders: list[WorkOrder]) -> dict[str, int]:
    return dict(Counter(order.team for order in work_orders))

