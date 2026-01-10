from flask import render_template, request, jsonify 
import json 
import os
import logging 
from . import red_team_bp 
from core.security.rbac import rbac_manager, Permission 
from functools import wraps 
def require_permission(permission): 
    def decorator(func): 
        @wraps(func) 
            def wrapper(*args, **kwargs): 
                user_id = 'admin'  # In production, get from JWT 
                tenant_id = 'default' 
                if not rbac_manager.has_permission(user_id, tenant_id, permission): 
                    from flask import abort 
                    abort(403, f"Access denied: {permission.value}") 
                return func(*args, **kwargs) 
            return wrapper 
        return decorator 
@red_team_bp.route('/dashboard') 
@require_permission(Permission.SYSTEM_ADMIN) 
def dashboard(): 
    results_file = os.path.join(os.path.dirname(__file__), '..', '..', 'core', 'robustness', 'dashboard', 'red_team_results.json') 
    if os.path.exists(results_file): 
        with open(results_file, 'r') as f: 
            results = json.load(f) 
    else: 
        results = {"total_attacks": 0, "successful_attacks": 0, "vulnerabilities": []} 
    vulnerabilities = results.get('vulnerabilities', []) 
    severity_counts = {'high': 0, 'medium': 0, 'low': 0} 
    for vuln in vulnerabilities: 
        sev = vuln.get('severity', 'low') 
        if sev in severity_counts: 
            severity_counts[sev] += 1 
    metrics = { 
        'total_attacks': results.get('total_attacks', 0), 
        'successful_attacks': results.get('successful_attacks', 0), 
        'total_vulnerabilities': len(vulnerabilities), 
        'severity_counts': severity_counts 
    } 
    return render_template('dashboard.html', metrics=metrics) 
`ndef audit_log(action, user='admin'):`n    logging.info(f'Audit: {user} performed {action}')
`n@red_team_bp.route('/trigger_scan', methods=['POST'])`n@require_permission(Permission.SYSTEM_ADMIN)`ndef trigger_scan():`n    audit_log('triggered red team scan')`n    from .sandbox_runner import run_red_team_tests`n    result = run_red_team_tests()`n    return jsonify({'status': 'success', 'message': 'Scan triggered', 'result': result})`n`n@red_team_bp.route('/api/results')`n@require_permission(Permission.SYSTEM_ADMIN)`ndef get_results():`n    results_file = os.path.join(os.path.dirname(__file__), '..', '..', 'core', 'robustness', 'dashboard', 'red_team_results.json')`n    if os.path.exists(results_file):`n        with open(results_file, 'r') as f:`n            results = json.load(f)`n    else:`n        results = {"total_attacks: 0, successful_attacks: 0, vulnerabilities: []}`n return jsonify(results)
