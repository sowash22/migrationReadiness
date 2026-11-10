"""Flask app shared by local preview and Vercel serverless."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from flask import Flask, Response, jsonify, request, redirect

from migration_readiness.catalog import UnknownMerchantError, known_merchant_ids
from migration_readiness.orchestrator import MigrationOrchestrator
from migration_readiness.scenarios import scenarios_for_api
from migration_readiness.state import StateStore
from migration_readiness.web_page import DEFAULT_REQUEST, PAGE

MAX_BODY_BYTES = 8_192


def _run_case(user_request: str, auto_approve: bool = True) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="migration-preview-"))
    try:
        store = StateStore(tmp / "state")
        reports_dir = tmp / "reports"
        orch = MigrationOrchestrator(
            store=store,
            reports_dir=reports_dir,
            auto_approve=auto_approve,
        )
        result = orch.run(user_request)
        report_preview = ""
        logical_report = None
        if result.state.report_path:
            report_preview = Path(result.state.report_path).read_text(encoding="utf-8")[
                :4000
            ]
            logical_report = f"reports/{result.state.case_id}-migration-readiness.md"
        return {
            "case_id": result.state.case_id,
            "stage": result.state.stage,
            "approved": result.approved,
            "readiness": (
                result.state.readiness.__dict__ if result.state.readiness else None
            ),
            "report_path": logical_report,
            "report_preview": report_preview,
            "agents": [
                {"agent": r.agent, "summary": r.summary, "details": r.details}
                for r in result.results
            ],
            "blockers": [
                g.__dict__ for g in result.state.gaps if g.severity == "blocker"
            ],
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def create_app() -> Flask:
    app = Flask(__name__)

    def page() -> Response:
        return Response(PAGE, mimetype="text/html; charset=utf-8")

    def health():
        return jsonify({"ok": True, "service": "migration-readiness"})

    def scenarios():
        return jsonify(
            {
                "scenarios": scenarios_for_api(),
                "known_merchants": known_merchant_ids(),
            }
        )

    def run():
        if request.content_length and request.content_length > MAX_BODY_BYTES:
            return jsonify({"error": "Request body too large."}), 413
        raw = request.get_data(cache=False, as_text=False) or b"{}"
        if len(raw) > MAX_BODY_BYTES:
            return jsonify({"error": "Request body too large."}), 413
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON body."}), 400
        user_request = str(payload.get("request") or DEFAULT_REQUEST)
        auto_approve = bool(payload.get("auto_approve", True))
        try:
            return jsonify(_run_case(user_request, auto_approve=auto_approve))
        except UnknownMerchantError as exc:
            return (
                jsonify(
                    {
                        "error": str(exc),
                        "known_merchants": known_merchant_ids(),
                    }
                ),
                400,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc)}), 500

    # Primary routes
    app.add_url_rule("/", view_func=page, methods=["GET"])
    app.add_url_rule("/index.html", view_func=page, methods=["GET"])
    app.add_url_rule("/health", view_func=health, methods=["GET"])
    app.add_url_rule("/api/scenarios", view_func=scenarios, methods=["GET"])
    app.add_url_rule("/api/run", view_func=run, methods=["POST"])

    # Vercel /api-prefix fallbacks when the function is mounted under /api
    app.add_url_rule("/api", view_func=lambda: redirect("/", code=307), methods=["GET"])
    app.add_url_rule("/api/", view_func=page, methods=["GET"])
    app.add_url_rule("/api/health", view_func=health, methods=["GET"])
    app.add_url_rule("/api/api/scenarios", view_func=scenarios, methods=["GET"])
    app.add_url_rule("/api/api/run", view_func=run, methods=["POST"])

    @app.errorhandler(404)
    def not_found(_err):
        return (
            jsonify(
                {
                    "error": "not_found",
                    "path": request.path,
                    "method": request.method,
                    "hint": "Expected /, /health, /api/scenarios, or POST /api/run",
                }
            ),
            404,
        )

    return app


app = create_app()
