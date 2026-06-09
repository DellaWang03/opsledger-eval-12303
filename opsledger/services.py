from __future__ import annotations

import csv
import io
from collections import Counter
from datetime import datetime

from .models import ActivityLog, OnCallEngineer, WorkOrder


VALID_ESCALATION_STATUSES = ("none", "escalated")


def escalation_status_for(order: WorkOrder) -> str:
    return "escalated" if order.escalation_level > 0 else "none"


def filter_work_orders(
    work_orders: list[WorkOrder],
    status: str | None = None,
    priority: str | None = None,
    team: str | None = None,
    assignee: str | None = None,
    escalation_level: int | None = None,
    escalation_status: str | None = None,
) -> list[WorkOrder]:
    filtered = work_orders
    if status:
        filtered = [order for order in filtered if order.status == status]
    if priority:
        filtered = [order for order in filtered if order.priority == priority]
    if team:
        filtered = [order for order in filtered if order.team == team]
    if assignee:
        filtered = [order for order in filtered if order.assignee == assignee]
    if escalation_level is not None:
        filtered = [order for order in filtered if order.escalation_level == escalation_level]
    if escalation_status:
        filtered = [order for order in filtered if escalation_status_for(order) == escalation_status]
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


def recommend_oncall(
    order: WorkOrder,
    engineers: list[OnCallEngineer],
    now: datetime | None = None,
) -> list[dict]:
    """Score and rank on-call engineers for a work order.

    Scoring:
      - Team skill match: +10
      - Lower load is better: +(5 - current_load), min 0
      - SLA urgency bonus (due within 4h): +3 for lowest-load candidate
    """
    now = now or datetime.now()
    hours_until_due = (order.due_at - now).total_seconds() / 3600
    sla_urgent = hours_until_due < 4

    scored: list[dict] = []
    for eng in engineers:
        score = 0
        if order.team in eng.teams:
            score += 10
        score += max(0, 5 - eng.current_load)
        scored.append({"name": eng.name, "score": score, "load": eng.current_load})

    scored.sort(key=lambda x: (-x["score"], x["load"]))

    if sla_urgent and scored:
        scored[0]["score"] += 3

    scored.sort(key=lambda x: (-x["score"], x["load"]))
    return scored


def export_escalation_csv(logs: list[ActivityLog], work_orders: list[WorkOrder] | None = None) -> str:
    escalation_logs = [log for log in logs if log.action == "escalated"]
    wo_map: dict[int, WorkOrder] = {}
    if work_orders:
        wo_map = {wo.id: wo for wo in work_orders}
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["id", "work_order_id", "actor", "created_at", "detail", "escalation_status"])
    for log in escalation_logs:
        wo = wo_map.get(log.work_order_id)
        es = escalation_status_for(wo) if wo else "escalated"
        writer.writerow([
            log.id,
            log.work_order_id,
            log.actor,
            log.created_at.isoformat(),
            log.detail,
            es,
        ])
    return output.getvalue()
