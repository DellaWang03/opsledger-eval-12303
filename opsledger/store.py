from __future__ import annotations

from datetime import datetime

from .models import ActivityLog, WorkOrder
from .sample_data import seed_logs, seed_work_orders


class WorkOrderStore:
    def __init__(self, now: datetime | None = None) -> None:
        self.work_orders = seed_work_orders(now)
        self.activity_logs = seed_logs(now)

    def list_work_orders(self) -> list[WorkOrder]:
        return list(self.work_orders)

    def get_work_order(self, work_order_id: int) -> WorkOrder | None:
        return next((order for order in self.work_orders if order.id == work_order_id), None)

    def logs_for(self, work_order_id: int) -> list[ActivityLog]:
        return [log for log in self.activity_logs if log.work_order_id == work_order_id]

    def add_log(self, work_order_id: int, action: str, actor: str, detail: str, created_at: datetime) -> ActivityLog:
        next_id = max((log.id for log in self.activity_logs), default=0) + 1
        log = ActivityLog(next_id, work_order_id, action, actor, created_at, detail)
        self.activity_logs.append(log)
        return log

