# Self-Triggered CI/CD Update System - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

- Python 3.8+
- CI/CD system access (GitHub Actions, GitLab CI, Jenkins, etc.)
- API credentials for your CI/CD provider

### Step 1: Basic Setup (30 seconds)

```python
from core.self_update_orchestrator import SelfUpdateOrchestrator
from core.cicd_integrator import CICDConfig, CICDProvider

# Initialize
orchestrator = SelfUpdateOrchestrator(
    check_interval=3600,      # Check every hour
    auto_update_enabled=True  # Enable automatic updates
)
```

### Step 2: Configure CI/CD (1 minute)

```python
# For GitHub Actions
cicd_config = CICDConfig(
    provider=CICDProvider.GITHUB_ACTIONS,
    endpoint="https://api.github.com",
    auth_token="ghp_your_token_here",
    repository="your-org/your-repo",
    branch="main",
    workflow_file=".github/workflows/deploy.yml",
    additional_params={}
)

orchestrator = SelfUpdateOrchestrator(
    check_interval=3600,
    auto_update_enabled=True,
    cicd_config=cicd_config
)
```

### Step 3: Register Components (30 seconds)

```python
# Register current versions
orchestrator.register_component_version("api_server", "2.0.0")
orchestrator.register_component_version("worker", "1.5.0")
orchestrator.register_component_version("database", "3.2.0")
```

### Step 4: Start Orchestrator (10 seconds)

```python
import asyncio

async def main():
    # Start the orchestrator
    await orchestrator.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        await orchestrator.stop()

# Run
asyncio.run(main())
```

### Step 5: Monitor Updates (ongoing)

```python
# Check status
stats = orchestrator.get_statistics()
print(f"Active workflows: {stats['workflows']['active']}")
print(f"Success rate: {stats['workflows']['success_rate']:.1%}")

# Get pending approvals
pending = orchestrator.get_pending_approvals()
for workflow in pending:
    print(f"Workflow {workflow.workflow_id} needs approval")
    print(f"Component: {workflow.component} v{workflow.version}")
```

## 📡 REST API Quick Reference

### Start/Stop

```bash
# Start orchestrator
curl -X POST http://localhost:8000/api/self-update/start

# Get status
curl http://localhost:8000/api/self-update/status

# Stop orchestrator
curl -X POST http://localhost:8000/api/self-update/stop
```

### Updates

```bash
# Check for updates
curl -X POST http://localhost:8000/api/self-update/check-updates

# Get workflows
curl http://localhost:8000/api/self-update/workflows

# Get pending approvals
curl http://localhost:8000/api/self-update/pending-approvals

# Approve workflow
curl -X POST http://localhost:8000/api/self-update/approve/{workflow_id}
```

### Configuration

```bash
# Register component
curl -X POST http://localhost:8000/api/self-update/register-component \
  -H "Content-Type: application/json" \
  -d '{"component": "api_server", "version": "2.0.0"}'

# Get policies
curl http://localhost:8000/api/self-update/policies

# Export state
curl http://localhost:8000/api/self-update/export-state
```

## 🎯 Common Use Cases

### 1. Automatic Updates for Non-Critical Components

```python
# The orchestrator will automatically:
# 1. Detect new versions
# 2. Run simulations
# 3. Evaluate policies
# 4. Deploy if approved
# 5. Monitor and rollback if needed

# Just register and start!
orchestrator.register_component_version("background_worker", "1.0.0")
await orchestrator.start()
```

### 2. Manual Approval for Critical Components

```python
# Critical updates require manual approval by default
# The system will:
# 1. Detect update
# 2. Run simulation
# 3. Wait for manual approval

# Check pending
pending = orchestrator.get_pending_approvals()

# Approve when ready
if pending:
    workflow = pending[0]
    await orchestrator.approve_workflow(workflow.workflow_id)
```

### 3. Custom Deployment Windows

```python
from core.update_policy_engine import UpdatePolicy, UpdateDecision

# Deploy only during maintenance windows
policy = UpdatePolicy(
    name="maintenance_window_only",
    enabled=True,
    priority=90,
    conditions={
        "in_maintenance_window": True
    },
    actions={
        "decision": UpdateDecision.APPROVE.value
    },
    description="Deploy only during maintenance windows"
)

orchestrator.policy_engine.add_policy(policy)
```

### 4. Canary Deployments for High-Risk Updates

```python
from core.rollout_controller import RolloutConfig, RolloutStrategy

# The orchestrator automatically uses canary deployments
# for high-risk updates. You can customize:

config = RolloutConfig(
    strategy=RolloutStrategy.CANARY,
    canary_percentage=5,           # Start with 5%
    monitoring_duration_seconds=600, # Monitor for 10 min
    health_check_interval=30,       # Check every 30 sec
    error_threshold=0.005,          # 0.5% error rate max
    auto_rollback_enabled=True,
    progressive_steps=[5, 25, 50, 100]
)
```

## 🛠️ Troubleshooting

### Problem: No updates detected

```python
# Force manual check
await orchestrator.check_and_process_updates()

# Verify registration
print(orchestrator.version_detector.current_versions)
```

### Problem: All updates rejected

```python
# Check policy decisions
stats = orchestrator.policy_engine.get_statistics()
print(stats['recent_evaluations'])

# Review policies
for policy in orchestrator.policy_engine.policies:
    print(f"{policy.name}: enabled={policy.enabled}")
```

### Problem: Deployments failing

```python
# Check CI/CD integration
cicd_stats = orchestrator.cicd_integrator.get_statistics()
print(f"Success rate: {cicd_stats['success_rate']}")

# Review recent deployments
for deployment in orchestrator.cicd_integrator.completed_deployments[-5:]:
    print(f"{deployment.trigger_id}: {deployment.status.value}")
    if deployment.errors:
        print(f"Errors: {deployment.errors}")
```

## 📚 Next Steps

1. **Read Full Documentation**: See `SELF_UPDATE_README.md`
2. **Run Example**: `python examples/self_update_example.py`
3. **Run Tests**: `pytest tests/test_self_update_system.py -v`
4. **Customize Policies**: Add your own update policies
5. **Configure Monitoring**: Set up alerts and dashboards

## 💡 Pro Tips

1. **Start Conservative**: Begin with `auto_update_enabled=False` and manual approvals
2. **Test Thoroughly**: Always run simulations before production
3. **Monitor Closely**: Set up alerts for rollbacks and failures
4. **Use Maintenance Windows**: Schedule risky updates appropriately
5. **Keep Rollback Ready**: Always enable automatic rollback
6. **Review Regularly**: Check policy effectiveness monthly

## 🎓 Learn More

- **Architecture**: See implementation summary
- **API Reference**: Check README for complete API docs
- **Best Practices**: Review security and deployment sections
- **Examples**: Explore `examples/self_update_example.py`

---

**Ready to Deploy?** You're all set! Start the orchestrator and let it manage your updates autonomously. 🚀
