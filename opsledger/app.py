from __future__ import annotations

from datetime import datetime

from flask import Flask, Response, abort, jsonify, redirect, render_template, request, url_for

from .services import (
    VALID_ESCALATION_STATUSES,
    dashboard_summary,
    escalation_status_for,
    export_escalation_csv,
    filter_work_orders,
    group_by_team,
    recommend_oncall,
)
from .store import WorkOrderStore


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.update(test_config or {})
    app.config["STORE"] = app.config.get("STORE") or WorkOrderStore()

    @app.get("/")
    def dashboard():
        store: WorkOrderStore = app.config["STORE"]
        orders = store.list_work_orders()
        return render_template(
            "dashboard.html",
            summary=dashboard_summary(orders, datetime.now()),
            teams=group_by_team(orders),
            orders=orders,
        )

    @app.get("/work-orders")
    def work_orders():
        store: WorkOrderStore = app.config["STORE"]
        escalation_raw = request.args.get("escalation_level")
        if escalation_raw is not None and escalation_raw != "":
            if not escalation_raw.isdigit():
                abort(400)
            escalation_level: int | None = int(escalation_raw)
        else:
            escalation_level = None
        escalation_status = request.args.get("escalation_status") or None
        if escalation_status and escalation_status not in VALID_ESCALATION_STATUSES:
            abort(400)
        orders = filter_work_orders(
            store.list_work_orders(),
            status=request.args.get("status") or None,
            priority=request.args.get("priority") or None,
            team=request.args.get("team") or None,
            assignee=request.args.get("assignee") or None,
            escalation_level=escalation_level,
            escalation_status=escalation_status,
        )
        return render_template("work_orders.html", orders=orders, filters=request.args)

    @app.get("/work-orders/<int:work_order_id>")
    def work_order_detail(work_order_id: int):
        store: WorkOrderStore = app.config["STORE"]
        order = store.get_work_order(work_order_id)
        if not order:
            abort(404)
        recommendations = recommend_oncall(order, store.list_oncall_engineers())
        return render_template(
            "detail.html",
            order=order,
            logs=store.logs_for(work_order_id),
            recommendations=recommendations,
        )

    @app.post("/work-orders/<int:work_order_id>/escalate")
    def escalate_work_order(work_order_id: int):
        store: WorkOrderStore = app.config["STORE"]
        order = store.get_work_order(work_order_id)
        if not order:
            abort(404)
        target = request.form.get("target", "").strip()
        actor = request.form.get("actor", "").strip()
        reason = request.form.get("reason", "").strip()
        if not target or not actor or not reason:
            abort(400)
        store.escalate_work_order(work_order_id, target, actor, reason, datetime.now())
        return redirect(url_for("work_order_detail", work_order_id=work_order_id))

    @app.get("/api/work-orders")
    def api_work_orders():
        store: WorkOrderStore = app.config["STORE"]
        escalation_raw = request.args.get("escalation_level")
        if escalation_raw is not None and escalation_raw != "":
            if not escalation_raw.isdigit():
                abort(400)
            escalation_level: int | None = int(escalation_raw)
        else:
            escalation_level = None
        escalation_status = request.args.get("escalation_status") or None
        if escalation_status and escalation_status not in VALID_ESCALATION_STATUSES:
            abort(400)
        orders = filter_work_orders(
            store.list_work_orders(),
            status=request.args.get("status") or None,
            priority=request.args.get("priority") or None,
            team=request.args.get("team") or None,
            assignee=request.args.get("assignee") or None,
            escalation_level=escalation_level,
            escalation_status=escalation_status,
        )
        return jsonify(
            [
                {
                    "id": order.id,
                    "title": order.title,
                    "team": order.team,
                    "priority": order.priority,
                    "status": order.status,
                    "due_at": order.due_at.isoformat(),
                    "assignee": order.assignee,
                    "location": order.location,
                    "escalation_level": order.escalation_level,
                    "escalated_to": order.escalated_to,
                    "escalation_status": escalation_status_for(order),
                }
                for order in orders
            ]
        )

    @app.get("/api/work-orders/<int:work_order_id>/recommend-oncall")
    def api_recommend_oncall(work_order_id: int):
        store: WorkOrderStore = app.config["STORE"]
        order = store.get_work_order(work_order_id)
        if not order:
            abort(404)
        recommendations = recommend_oncall(order, store.list_oncall_engineers())
        return jsonify(recommendations)

    @app.get("/api/escalation-audit/csv")
    def api_escalation_audit_csv():
        store: WorkOrderStore = app.config["STORE"]
        csv_content = export_escalation_csv(store.all_logs(), store.list_work_orders())
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=escalation_audit.csv"},
        )

    return app
