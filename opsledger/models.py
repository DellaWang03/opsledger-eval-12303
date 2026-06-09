from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkOrder:
    id: int
    title: str
    team: str
    priority: str
    status: str
    due_at: datetime
    assignee: str
    location: str
    notes: list[str] = field(default_factory=list)
    escalation_level: int = 0
    escalated_to: str | None = None


@dataclass
class ActivityLog:
    id: int
    work_order_id: int
    action: str
    actor: str
    created_at: datetime
    detail: str


@dataclass
class OnCallEngineer:
    name: str
    teams: list[str]
    current_load: int = 0
