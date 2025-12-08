#!/usr/bin/env python3
"""
Verification Script for Exponential Learning System

Checks that all components are properly installed and working.
"""

import sys
import os

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_check(text, status=True):
    symbol = "✅" if status else "❌"
    print(f"{symbol} {text}")

def verify_files():
    """Verify all expected files exist."""
    print_header("FILE VERIFICATION")
    
    files = [
        "core/learning_data_plugins.py",
        "core/agent_learning_coordinator.py",
        "deploy_exponential_learning.py",
        "api/routes/exponential_learning_routes.py",
        "examples/exponential_learning_example.py",
        "tests/test_exponential_learning.py",
        "EXPONENTIAL_LEARNING_README.md",
        "EXPONENTIAL_LEARNING_IMPLEMENTATION_SUMMARY.md",
        "EXPONENTIAL_LEARNING_FILES.txt"
    ]
    
    all_exist = True
    for file_path in files:
        exists = os.path.exists(file_path)
        print_check(f"{file_path}", exists)
        all_exist = all_exist and exists
    
    return all_exist

def verify_imports():
    """Verify all imports work."""
    print_header("IMPORT VERIFICATION")
    
    try:
        from core.learning_data_plugins import (
            LearningDataOrchestrator,
            CustomerSupportDataPlugin,
            SalesResearchDataPlugin,
            BenchmarkDatasetPlugin
        )
        print_check("Learning data plugins imported")
        
        from core.agent_learning_coordinator import AgentLearningCoordinator
        print_check("Agent learning coordinator imported")
        
        from api.routes.exponential_learning_routes import router
        print_check("API routes imported")
        
        return True
        
    except Exception as e:
        print_check(f"Import failed: {e}", False)
        return False

def verify_functionality():
    """Verify basic functionality."""
    print_header("FUNCTIONALITY VERIFICATION")
    
    try:
        from core.learning_data_plugins import (
            LearningDataOrchestrator,
            CustomerSupportDataPlugin,
            BenchmarkDatasetPlugin
        )
        
        # Test plugin creation
        plugin = CustomerSupportDataPlugin()
        print_check(f"Created CustomerSupportDataPlugin: {plugin.get_name()}")
        
        # Test task generation
        task = plugin.generate_task()
        print_check(f"Generated task: {task.get('type')}")
        
        # Test orchestrator
        orchestrator = LearningDataOrchestrator()
        orchestrator.register_plugin(plugin)
        orchestrator.register_plugin(BenchmarkDatasetPlugin())
        print_check(f"Registered {len(orchestrator.list_plugins())} plugins")
        
        # Test batch generation
        batch = orchestrator.generate_training_batch(5)
        print_check(f"Generated batch of {len(batch)} tasks")
        
        # Test stats
        stats = orchestrator.get_stats()
        print_check(f"Retrieved stats: {stats['total_tasks_generated']} tasks generated")
        
        return True
        
    except Exception as e:
        print_check(f"Functionality test failed: {e}", False)
        import traceback
        traceback.print_exc()
        return False

def verify_mini_learning():
    """Verify mini learning loop works."""
    print_header("MINI LEARNING LOOP TEST")
    
    try:
        from core.adaptive_orchestrator import AdaptiveOrchestrator
        from core.goal_driven_agent import GoalDrivenAgent
        from core.learning_data_plugins import (
            LearningDataOrchestrator,
            BenchmarkDatasetPlugin
        )
        from core.agent_learning_coordinator import AgentLearningCoordinator
        
        # Create components
        orchestrator = AdaptiveOrchestrator(
            agent_names=["react"],
            enable_adaptation=False
        )
        print_check("Created orchestrator")
        
        goal_agent = GoalDrivenAgent(
            agent_config={"autonomous_mode": False}
        )
        print_check("Created goal-driven agent")
        
        learning_data = LearningDataOrchestrator()
        learning_data.register_plugin(BenchmarkDatasetPlugin())
        print_check("Created learning data orchestrator")
        
        coordinator = AgentLearningCoordinator(
            orchestrator=orchestrator,
            goal_driven_agent=goal_agent,
            learning_data_orchestrator=learning_data
        )
        print_check("Created learning coordinator")
        
        # Run mini loop (2 iterations)
        print("\n  Running 2-iteration learning loop...")
        report = coordinator.start_exponential_learning_loop(
            iterations=2,
            batch_size=2,
            report_every=1
        )
        
        print_check(f"Completed {report['summary']['iterations_completed']} iterations")
        print_check(f"Executed {report['summary']['total_tasks_executed']} tasks")
        print_check(f"Final multiplier: {report['performance']['final_multiplier']:.2f}x")
        
        return True
        
    except Exception as e:
        print_check(f"Mini learning loop failed: {e}", False)
        import traceback
        traceback.print_exc()
        return False

def verify_api_endpoints():
    """Verify API endpoints are properly defined."""
    print_header("API ENDPOINT VERIFICATION")
    
    try:
        from api.routes.exponential_learning_routes import router
        
        routes = [route.path for route in router.routes]
        
        expected_endpoints = [
            "/api/learning/deploy",
            "/api/learning/start",
            "/api/learning/status",
            "/api/learning/stats",
            "/api/learning/report",
            "/api/learning/plugins/list",
            "/api/learning/plugins/generate",
            "/api/learning/stop"
        ]
        
        for endpoint in expected_endpoints:
            exists = endpoint in routes
            print_check(f"{endpoint}", exists)
        
        print(f"\n  Total endpoints: {len(routes)}")
        
        return True
        
    except Exception as e:
        print_check(f"API endpoint verification failed: {e}", False)
        return False

def main():
    """Run all verifications."""
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║     EXPONENTIAL LEARNING SYSTEM VERIFICATION                   ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    results = []
    
    # Run verifications
    results.append(("Files", verify_files()))
    results.append(("Imports", verify_imports()))
    results.append(("Functionality", verify_functionality()))
    results.append(("API Endpoints", verify_api_endpoints()))
    results.append(("Mini Learning Loop", verify_mini_learning()))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✅" if passed else "❌"
        print(f"{symbol} {name}: {status}")
        all_passed = all_passed and passed
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("   Exponential Learning System is ready for production.")
        print("="*70)
        print("\nQuick Start:")
        print("  $ python deploy_exponential_learning.py --quick-test")
        print("="*70)
        return 0
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        print("   Please check the errors above.")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
