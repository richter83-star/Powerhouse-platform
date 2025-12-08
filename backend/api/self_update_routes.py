
"""
Self-Update API Routes
===================

REST API for self-triggered CI/CD update system
"""

from flask import Blueprint, jsonify, request
from typing import Optional
import logging

from core.self_update_orchestrator import SelfUpdateOrchestrator
from core.version_detector import UpdateSource, UpdatePriority
from core.update_policy_engine import UpdatePolicy
from core.cicd_integrator import CICDConfig, CICDProvider

logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator: Optional[SelfUpdateOrchestrator] = None

# Create blueprint
self_update_bp = Blueprint('self_update', __name__, url_prefix='/api/self-update')


def init_orchestrator(check_interval: int = 3600, auto_update: bool = True):
    """Initialize the orchestrator"""
    global orchestrator
    if orchestrator is None:
        orchestrator = SelfUpdateOrchestrator(
            check_interval=check_interval,
            auto_update_enabled=auto_update
        )
    return orchestrator


@self_update_bp.route('/start', methods=['POST'])
async def start_orchestrator():
    """Start the self-update orchestrator"""
    try:
        if orchestrator is None:
            init_orchestrator()
        
        await orchestrator.start()
        
        return jsonify({
            "status": "success",
            "message": "Self-update orchestrator started"
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to start orchestrator: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/stop', methods=['POST'])
async def stop_orchestrator():
    """Stop the self-update orchestrator"""
    try:
        if orchestrator:
            await orchestrator.stop()
        
        return jsonify({
            "status": "success",
            "message": "Self-update orchestrator stopped"
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to stop orchestrator: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/status', methods=['GET'])
def get_status():
    """Get orchestrator status"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "not_initialized",
                "running": False
            }), 200
        
        stats = orchestrator.get_statistics()
        
        return jsonify({
            "status": "initialized",
            "running": orchestrator._running,
            "statistics": stats
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/check-updates', methods=['POST'])
async def check_updates():
    """Manually trigger update check"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 400
        
        await orchestrator.check_and_process_updates()
        
        comparisons = orchestrator.version_detector.get_all_comparisons()
        
        return jsonify({
            "status": "success",
            "updates_found": len([c for c in comparisons if c.is_update_available]),
            "comparisons": [
                {
                    "component": c.component,
                    "current_version": c.current_version,
                    "available_version": c.available_version,
                    "is_update_available": c.is_update_available,
                    "priority": c.priority.value,
                    "recommendation": c.recommendation
                }
                for c in comparisons
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to check updates: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/workflows', methods=['GET'])
def get_workflows():
    """Get all workflows"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 400
        
        active = list(orchestrator.active_workflows.values())
        completed = orchestrator.completed_workflows[-20:]  # Last 20
        
        return jsonify({
            "status": "success",
            "active_workflows": [
                {
                    "workflow_id": w.workflow_id,
                    "component": w.component,
                    "version": w.version,
                    "current_stage": w.current_stage,
                    "started_at": w.started_at.isoformat(),
                    "success": w.success
                }
                for w in active
            ],
            "completed_workflows": [
                {
                    "workflow_id": w.workflow_id,
                    "component": w.component,
                    "version": w.version,
                    "current_stage": w.current_stage,
                    "started_at": w.started_at.isoformat(),
                    "completed_at": w.completed_at.isoformat() if w.completed_at else None,
                    "success": w.success,
                    "errors": w.errors
                }
                for w in completed
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get workflows: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/workflows/<workflow_id>', methods=['GET'])
def get_workflow_detail(workflow_id: str):
    """Get detailed workflow information"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 400
        
        workflow = orchestrator.get_workflow_status(workflow_id)
        
        if not workflow:
            return jsonify({
                "status": "error",
                "message": "Workflow not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "workflow": {
                "workflow_id": workflow.workflow_id,
                "component": workflow.component,
                "version": workflow.version,
                "current_stage": workflow.current_stage,
                "started_at": workflow.started_at.isoformat(),
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "success": workflow.success,
                "errors": workflow.errors,
                "version_comparison": {
                    "current_version": workflow.version_comparison.current_version,
                    "available_version": workflow.version_comparison.available_version,
                    "recommendation": workflow.version_comparison.recommendation
                } if workflow.version_comparison else None,
                "simulation_result": {
                    "simulation_id": workflow.simulation_result.simulation_id,
                    "status": workflow.simulation_result.status.value,
                    "tests_run": workflow.simulation_result.tests_run,
                    "tests_passed": workflow.simulation_result.tests_passed,
                    "tests_failed": workflow.simulation_result.tests_failed,
                    "recommendation": workflow.simulation_result.recommendation
                } if workflow.simulation_result else None,
                "policy_evaluation": {
                    "decision": workflow.policy_evaluation.decision.value,
                    "risk_level": workflow.policy_evaluation.risk_level.value,
                    "recommended_action": workflow.policy_evaluation.recommended_action,
                    "reasons": workflow.policy_evaluation.reasons
                } if workflow.policy_evaluation else None
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get workflow detail: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/pending-approvals', methods=['GET'])
def get_pending_approvals():
    """Get workflows awaiting manual approval"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 400
        
        pending = orchestrator.get_pending_approvals()
        
        return jsonify({
            "status": "success",
            "count": len(pending),
            "workflows": [
                {
                    "workflow_id": w.workflow_id,
                    "component": w.component,
                    "version": w.version,
                    "started_at": w.started_at.isoformat(),
                    "policy_decision": w.policy_evaluation.decision.value if w.policy_evaluation else None,
                    "risk_level": w.policy_evaluation.risk_level.value if w.policy_evaluation else None,
                    "reasons": w.policy_evaluation.reasons if w.policy_evaluation else []
                }
                for w in pending
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get pending approvals: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/approve/<workflow_id>', methods=['POST'])
async def approve_workflow(workflow_id: str):
    """Approve a workflow for deployment"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 400
        
        workflow = await orchestrator.approve_workflow(workflow_id)
        
        return jsonify({
            "status": "success",
            "message": f"Workflow {workflow_id} approved",
            "new_workflow_id": workflow.workflow_id
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to approve workflow: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/register-component', methods=['POST'])
def register_component():
    """Register current version of a component"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 400
        
        data = request.json
        component = data.get('component')
        version = data.get('version')
        
        if not component or not version:
            return jsonify({
                "status": "error",
                "message": "component and version are required"
            }), 400
        
        orchestrator.register_component_version(component, version)
        
        return jsonify({
            "status": "success",
            "message": f"Registered {component} version {version}"
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to register component: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/policies', methods=['GET'])
def get_policies():
    """Get all update policies"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 400
        
        policies = orchestrator.policy_engine.policies
        
        return jsonify({
            "status": "success",
            "count": len(policies),
            "policies": [
                {
                    "name": p.name,
                    "enabled": p.enabled,
                    "priority": p.priority,
                    "description": p.description,
                    "conditions": p.conditions,
                    "actions": p.actions
                }
                for p in policies
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get policies: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/policies/<policy_name>', methods=['PUT'])
def update_policy(policy_name: str):
    """Update a policy"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 400
        
        data = request.json
        
        success = orchestrator.policy_engine.update_policy(policy_name, data)
        
        if not success:
            return jsonify({
                "status": "error",
                "message": f"Policy {policy_name} not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "message": f"Policy {policy_name} updated"
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to update policy: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@self_update_bp.route('/export-state', methods=['GET'])
def export_state():
    """Export complete orchestrator state"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 400
        
        state = orchestrator.export_state()
        
        return jsonify({
            "status": "success",
            "state": state
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to export state: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
