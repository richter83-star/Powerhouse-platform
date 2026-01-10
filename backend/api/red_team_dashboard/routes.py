from __future__ import annotations

import json
import logging
import os
from functools import wraps

from flask import abort, jsonify, render_template

from core.security.rbac import Permission, rbac_manager

from . import red_team_bp

logger = logging.getLogger(__name__)


def _results_file() -> str:
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "core",
        "robustness",
        "dashboard",
        "red_team_results.json",
    )


def require_permission(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = "admin"  # In production, get from JWT
            tenant_id = "default"
            if not rbac_manager.has_permission(user_id, tenant_id, permission):
                abort(403, f"Access denied: {permission.value}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def audit_log(action: str, user: str = "admin") -> None:
    logger.info("Audit: %s performed %s", user, action)


@red_team_bp.route("/dashboard")
@require_permission(Permission.SYSTEM_ADMIN)
def dashboard():
    results_file = _results_file()
    if os.path.exists(results_file):
        with open(results_file, "r") as handle:
            results = json.load(handle)
    else:
        results = {"total_attacks": 0, "successful_attacks": 0, "vulnerabilities": []}

    vulnerabilities = results.get("vulnerabilities", [])
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for vuln in vulnerabilities:
        sev = vuln.get("severity", "low")
        if sev in severity_counts:
            severity_counts[sev] += 1

    metrics = {
        "total_attacks": results.get("total_attacks", 0),
        "successful_attacks": results.get("successful_attacks", 0),
        "total_vulnerabilities": len(vulnerabilities),
        "severity_counts": severity_counts,
    }
    return render_template("dashboard.html", metrics=metrics)


@red_team_bp.route("/trigger_scan", methods=["POST"])
@require_permission(Permission.SYSTEM_ADMIN)
def trigger_scan():
    audit_log("triggered red team scan")
    from .sandbox_runner import run_red_team_tests

    result = run_red_team_tests()
    return jsonify({"status": "success", "message": "Scan triggered", "result": result})


@red_team_bp.route("/api/results")
@require_permission(Permission.SYSTEM_ADMIN)
def get_results():
    results_file = _results_file()
    if os.path.exists(results_file):
        with open(results_file, "r") as handle:
            results = json.load(handle)
    else:
        results = {"total_attacks": 0, "successful_attacks": 0, "vulnerabilities": []}
    return jsonify(results)
