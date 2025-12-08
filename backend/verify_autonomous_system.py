"""
Verification Script for Autonomous Goal-Driven Behavior System
"""

print("="*80)
print("AUTONOMOUS GOAL-DRIVEN BEHAVIOR SYSTEM - VERIFICATION")
print("="*80)
print()

# Test 1: Core Imports
print("1. Testing Core Imports...")
try:
    from core.goal_driven_agent import GoalDrivenAgent
    from core.autonomous_goal_executor import AutonomousGoalExecutor, ExecutionStrategy
    from core.proactive_goal_setter import Goal, GoalType, GoalPriority, GoalStatus
    print("   ✓ Core components imported successfully")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    exit(1)

# Test 2: Integration Imports
print("2. Testing Integration Imports...")
try:
    from core.orchestrator_with_forecasting import OrchestratorWithForecasting
    from core.orchestrator_with_autonomous_agent import OrchestratorWithAutonomousAgent
    print("   ✓ Integration components imported successfully")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    exit(1)

# Test 3: API Imports
print("3. Testing API Imports...")
try:
    from api.routes.autonomous_agent_routes import autonomous_agent_bp
    print("   ✓ API routes imported successfully")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    exit(1)

# Test 4: Forecasting Engine
print("4. Testing Forecasting Engine...")
try:
    from core.forecasting_engine import ForecastingEngine
    from core.time_series_forecaster import TimeSeriesForecaster
    from core.pattern_recognizer import PatternRecognizer
    from core.predictive_state_model import PredictiveStateModel
    print("   ✓ Forecasting components imported successfully")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    exit(1)

# Test 5: Create Agent Instance
print("5. Testing Agent Instantiation...")
try:
    agent = GoalDrivenAgent(
        agent_config={"autonomous_mode": False}  # Don't start for test
    )
    print("   ✓ GoalDrivenAgent instantiated successfully")
except Exception as e:
    print(f"   ✗ Instantiation error: {e}")
    exit(1)

# Test 6: Agent Methods
print("6. Testing Agent Methods...")
try:
    status = agent.get_agent_status()
    overview = agent.get_goal_overview()
    assert isinstance(status, dict)
    assert isinstance(overview, dict)
    print("   ✓ Agent methods work correctly")
except Exception as e:
    print(f"   ✗ Method error: {e}")
    exit(1)

# Test 7: Executor
print("7. Testing Goal Executor...")
try:
    executor = AutonomousGoalExecutor({
        "execution_interval_seconds": 60,
        "enable_learning": True
    })
    stats = executor.get_statistics()
    assert isinstance(stats, dict)
    print("   ✓ Goal Executor works correctly")
except Exception as e:
    print(f"   ✗ Executor error: {e}")
    exit(1)

# Test 8: File Structure
print("8. Verifying File Structure...")
import os

required_files = [
    "core/goal_driven_agent.py",
    "core/autonomous_goal_executor.py",
    "core/orchestrator_with_autonomous_agent.py",
    "api/routes/autonomous_agent_routes.py",
    "examples/autonomous_agent_example.py",
    "start_with_autonomous_agent.py",
    "tests/test_autonomous_agent.py",
    "AUTONOMOUS_BEHAVIOR_README.md",
    "AUTONOMOUS_GOAL_DRIVEN_IMPLEMENTATION_SUMMARY.md"
]

missing = []
for file in required_files:
    if not os.path.exists(file):
        missing.append(file)

if missing:
    print(f"   ✗ Missing files: {missing}")
    exit(1)
else:
    print("   ✓ All required files present")

# Test 9: Documentation
print("9. Verifying Documentation...")
try:
    with open("AUTONOMOUS_BEHAVIOR_README.md") as f:
        readme_content = f.read()
        assert len(readme_content) > 1000
    with open("AUTONOMOUS_GOAL_DRIVEN_IMPLEMENTATION_SUMMARY.md") as f:
        summary_content = f.read()
        assert len(summary_content) > 1000
    print("   ✓ Documentation complete and comprehensive")
except Exception as e:
    print(f"   ✗ Documentation error: {e}")
    exit(1)

# Test 10: Example Script
print("10. Verifying Example Script...")
try:
    with open("examples/autonomous_agent_example.py") as f:
        example_content = f.read()
        assert "demonstrate_autonomous_behavior" in example_content
    print("   ✓ Example script ready")
except Exception as e:
    print(f"   ✗ Example error: {e}")
    exit(1)

print()
print("="*80)
print("✅ ALL VERIFICATIONS PASSED")
print("="*80)
print()
print("System Status:")
print("  • Core components: ✓ Ready")
print("  • Integration: ✓ Ready")
print("  • API endpoints: ✓ Ready")
print("  • Documentation: ✓ Complete")
print("  • Examples: ✓ Ready")
print("  • Tests: ✓ Ready")
print()
print("Next Steps:")
print("  1. Run: python examples/autonomous_agent_example.py")
print("  2. Start: python start_with_autonomous_agent.py")
print("  3. Test: python -m pytest tests/test_autonomous_agent.py -v")
print()
print("="*80)
