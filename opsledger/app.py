from __future__ import annotations

from datetime import datetime

from flask import Flask, abort, jsonify, render_template, request

from .services import dashboard_summary, filter_work_orders, group_by_team
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
        orders = filter_work_orders(
            store.list_work_orders(),
            status=request.args.get("status") or None,
            priority=request.args.get("priority") or None,
            team=request.args.get("team") or None,
        )
        return render_template("work_orders.html", orders=orders, filters=request.args)

    @app.get("/work-orders/<int:work_order_id>")
    def work_order_detail(work_order_id: int):
        store: WorkOrderStore = app.config["STORE"]
        order = store.get_work_order(work_order_id)
        if not order:
            abort(404)
        return render_template("detail.html", order=order, logs=store.logs_for(work_order_id))

    @app.get("/api/work-orders")
    def api_work_orders():
        store: WorkOrderStore = app.config["STORE"]
        orders = filter_work_orders(
            store.list_work_orders(),
            status=request.args.get("status") or None,
            priority=request.args.get("priority") or None,
            team=request.args.get("team") or None,
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
                }
                for order in orders
            ]
        )

    return app

