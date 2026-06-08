from __future__ import annotations

from datetime import datetime, timedelta

from .models import ActivityLog, WorkOrder


def seed_work_orders(now: datetime | None = None) -> list[WorkOrder]:
    base = now or datetime(2026, 6, 8, 9, 0)
    return [
        WorkOrder(1, "Replace lobby access reader", "Security", "high", "open", base + timedelta(hours=4), "Iris", "HQ Lobby", ["Vendor badge reader failed twice."]),
        WorkOrder(2, "Inspect chilled water pump", "Facilities", "medium", "open", base + timedelta(days=1), "Mason", "Plant Room", ["Vibration alert from BMS."]),
        WorkOrder(3, "Patch visitor kiosk", "IT", "low", "blocked", base + timedelta(days=3), "Nora", "Reception", ["Waiting for kiosk maintenance window."]),
        WorkOrder(4, "Repair loading dock sensor", "Facilities", "high", "open", base - timedelta(hours=2), "Lena", "Dock A", ["False closed signal blocks deliveries."]),
        WorkOrder(5, "Replace pantry freezer seal", "Hospitality", "medium", "done", base - timedelta(days=1), "Owen", "Floor 9", ["Completed after part arrived."]),
    ]


def seed_logs(now: datetime | None = None) -> list[ActivityLog]:
    base = now or datetime(2026, 6, 8, 9, 0)
    return [
        ActivityLog(1, 1, "created", "system", base - timedelta(days=2), "Imported from weekly inspection."),
        ActivityLog(2, 4, "escalated", "Lena", base - timedelta(hours=3), "Dock manager reported delivery impact."),
    ]

