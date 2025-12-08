
"""
Self-Update System Example
========================

Demonstrates the complete self-triggered CI/CD update system
"""

import asyncio
import logging
from datetime import datetime

from core.self_update_orchestrator import SelfUpdateOrchestrator
from core.cicd_integrator import CICDConfig, CICDProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main example"""
    
    print("\n" + "="*70)
    print("Self-Triggered CI/CD Update System Example")
    print("="*70 + "\n")
    
    # Configure CI/CD integration
    cicd_config = CICDConfig(
        provider=CICDProvider.GITHUB_ACTIONS,
        endpoint="https://api.github.com",
        auth_token="ghp_mock_token_12345",
        repository="powerhouse/platform",
        branch="main",
        workflow_file=".github/workflows/deploy.yml",
        additional_params={}
    )
    
    # Initialize orchestrator
    orchestrator = SelfUpdateOrchestrator(
        check_interval=3600,  # Check every hour
        auto_update_enabled=True,
        cicd_config=cicd_config
    )
    
    print("Step 1: Register current component versions")
    print("-" * 70)
    
    # Register current versions
    orchestrator.register_component_version("core_orchestrator", "2.0.0")
    orchestrator.register_component_version("performance_monitor", "1.4.0")
    orchestrator.register_component_version("dynamic_config_manager", "1.2.0")
    
    print("✓ Registered 3 components")
    print()
    
    # Start orchestrator
    print("Step 2: Start self-update orchestrator")
    print("-" * 70)
    
    await orchestrator.start()
    print("✓ Orchestrator started")
    print()
    
    # Wait for initial check
    print("Step 3: Checking for updates...")
    print("-" * 70)
    
    await asyncio.sleep(2)
    
    # Manual check
    await orchestrator.check_and_process_updates()
    
    # Get version comparisons
    comparisons = orchestrator.version_detector.get_all_comparisons()
    
    print(f"Found {len(comparisons)} components:\n")
    for comp in comparisons:
        status = "✓ Update available" if comp.is_update_available else "• Up to date"
        print(f"{status} {comp.component}:")
        print(f"  Current: {comp.current_version}")
        print(f"  Available: {comp.available_version}")
        print(f"  Priority: {comp.priority.value}")
        print(f"  Recommendation: {comp.recommendation}")
        print()
    
    # Wait for workflows to process
    print("Step 4: Processing update workflows...")
    print("-" * 70)
    
    await asyncio.sleep(5)
    
    # Check workflow status
    workflows = list(orchestrator.active_workflows.values()) + orchestrator.completed_workflows[-5:]
    
    if workflows:
        print(f"\nWorkflows ({len(workflows)}):\n")
        for workflow in workflows:
            status_icon = "✓" if workflow.success else "✗" if workflow.completed_at else "⟳"
            print(f"{status_icon} {workflow.workflow_id}")
            print(f"  Component: {workflow.component} v{workflow.version}")
            print(f"  Stage: {workflow.current_stage}")
            print(f"  Started: {workflow.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if workflow.policy_evaluation:
                print(f"  Decision: {workflow.policy_evaluation.decision.value}")
                print(f"  Risk: {workflow.policy_evaluation.risk_level.value}")
            
            if workflow.errors:
                print(f"  Errors: {workflow.errors[0]}")
            
            print()
    
    # Check pending approvals
    print("Step 5: Checking for pending approvals...")
    print("-" * 70)
    
    pending = orchestrator.get_pending_approvals()
    
    if pending:
        print(f"\nPending approvals ({len(pending)}):\n")
        for workflow in pending:
            print(f"• {workflow.workflow_id}")
            print(f"  Component: {workflow.component} v{workflow.version}")
            print(f"  Reasons: {', '.join(workflow.policy_evaluation.reasons[:2])}")
            print()
    else:
        print("No workflows awaiting approval")
        print()
    
    # Get statistics
    print("Step 6: System statistics")
    print("-" * 70)
    
    stats = orchestrator.get_statistics()
    
    print("\nOrchestrator:")
    print(f"  Running: {stats['orchestrator']['running']}")
    print(f"  Auto-update: {stats['orchestrator']['auto_update_enabled']}")
    print(f"  Check interval: {stats['orchestrator']['check_interval_seconds']}s")
    
    print("\nWorkflows:")
    print(f"  Active: {stats['workflows']['active']}")
    print(f"  Completed: {stats['workflows']['total_completed']}")
    print(f"  Success rate: {stats['workflows']['success_rate']:.1%}")
    print(f"  Awaiting approval: {stats['workflows']['awaiting_approval']}")
    
    print("\nVersion Detector:")
    vd_stats = stats['components']['version_detector']
    print(f"  Registered components: {vd_stats['registered_components']}")
    print(f"  Updates available: {vd_stats['components_with_updates']}")
    print(f"  Total checks: {vd_stats['total_checks']}")
    
    print("\nSimulator:")
    sim_stats = stats['components']['simulator']
    print(f"  Completed: {sim_stats['total_completed']}")
    print(f"  Success rate: {sim_stats['success_rate']:.1%}")
    print(f"  Avg duration: {sim_stats['avg_duration_seconds']:.1f}s")
    
    print("\nCI/CD Integrator:")
    cicd_stats = stats['components']['cicd_integrator']
    print(f"  Provider: {cicd_stats['provider']}")
    print(f"  Active deployments: {cicd_stats['active_deployments']}")
    print(f"  Success rate: {cicd_stats['success_rate']:.1%}")
    
    print("\nRollout Controller:")
    rollout_stats = stats['components']['rollout_controller']
    print(f"  Active rollouts: {rollout_stats['active_rollouts']}")
    print(f"  Success rate: {rollout_stats['success_rate']:.1%}")
    print()
    
    # Demonstrate manual approval
    if pending:
        print("Step 7: Manual approval demo")
        print("-" * 70)
        
        workflow_to_approve = pending[0]
        print(f"\nApproving workflow: {workflow_to_approve.workflow_id}")
        
        try:
            new_workflow = await orchestrator.approve_workflow(workflow_to_approve.workflow_id)
            print(f"✓ Approved - new workflow: {new_workflow.workflow_id}")
        except Exception as e:
            print(f"✗ Approval failed: {e}")
        
        print()
    
    # Export state
    print("Step 8: Export system state")
    print("-" * 70)
    
    state = orchestrator.export_state()
    print(f"\nExported state:")
    print(f"  Active workflows: {len(state['active_workflows'])}")
    print(f"  Recent workflows: {len(state['recent_workflows'])}")
    print(f"  Last version check: {state['version_detector_state']['last_check']}")
    print()
    
    # Cleanup
    print("Step 9: Stopping orchestrator")
    print("-" * 70)
    
    await orchestrator.stop()
    print("✓ Orchestrator stopped")
    
    print("\n" + "="*70)
    print("Example completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
