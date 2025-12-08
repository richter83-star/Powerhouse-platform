#!/usr/bin/env python3
"""
Self-Update System Verification Script
====================================

Verifies that all components are properly installed and functional.
"""

import sys
import os

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def verify_imports():
    """Verify all imports work"""
    print("\n" + "="*70)
    print("1. Verifying Imports")
    print("="*70)
    
    try:
        from core.version_detector import (
            VersionDetector, VersionInfo, VersionComparison,
            UpdateSource, UpdatePriority
        )
        print_success("Version Detector imports")
        
        from core.update_simulator import (
            UpdateSimulator, SimulationResult, SimulationConfig,
            SimulationStatus, TestType
        )
        print_success("Update Simulator imports")
        
        from core.update_policy_engine import (
            UpdatePolicyEngine, PolicyEvaluation, UpdatePolicy,
            UpdateDecision, RiskLevel
        )
        print_success("Policy Engine imports")
        
        from core.cicd_integrator import (
            CICDIntegrator, CICDConfig, CICDProvider,
            DeploymentTrigger, DeploymentResult, DeploymentStatus
        )
        print_success("CI/CD Integrator imports")
        
        from core.rollout_controller import (
            RolloutController, RolloutConfig, RolloutStrategy,
            RolloutStatus, RolloutPhase
        )
        print_success("Rollout Controller imports")
        
        from core.self_update_orchestrator import (
            SelfUpdateOrchestrator, UpdateWorkflow
        )
        print_success("Self-Update Orchestrator imports")
        
        return True
    except Exception as e:
        print_error(f"Import failed: {e}")
        return False

def verify_api_routes():
    """Verify API routes exist"""
    print("\n" + "="*70)
    print("2. Verifying API Routes")
    print("="*70)
    
    api_file = "api/self_update_routes.py"
    if os.path.exists(api_file):
        with open(api_file, 'r') as f:
            lines = len(f.readlines())
        print_success(f"API routes file exists ({lines} lines)")
        
        # Check if blueprint is defined
        with open(api_file, 'r') as f:
            content = f.read()
            if 'self_update_bp' in content and 'Blueprint' in content:
                print_success("Blueprint properly defined")
                
                # Count endpoints
                endpoint_count = content.count('@self_update_bp.route(')
                print_info(f"Found {endpoint_count} API endpoints")
                return True
            else:
                print_error("Blueprint not properly defined")
                return False
    else:
        print_error("API routes file not found")
        return False

def verify_tests():
    """Verify test file exists"""
    print("\n" + "="*70)
    print("3. Verifying Tests")
    print("="*70)
    
    test_file = "tests/test_self_update_system.py"
    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            lines = len(f.readlines())
        print_success(f"Test file exists ({lines} lines)")
        return True
    else:
        print_error("Test file not found")
        return False

def verify_documentation():
    """Verify documentation files exist"""
    print("\n" + "="*70)
    print("4. Verifying Documentation")
    print("="*70)
    
    docs = [
        "SELF_UPDATE_README.md",
        "SELF_UPDATE_IMPLEMENTATION_SUMMARY.md",
        "SELF_UPDATE_QUICKSTART.md"
    ]
    
    all_exist = True
    for doc in docs:
        if os.path.exists(doc):
            with open(doc, 'r') as f:
                lines = len(f.readlines())
            print_success(f"{doc} ({lines} lines)")
        else:
            print_error(f"{doc} not found")
            all_exist = False
    
    return all_exist

def verify_examples():
    """Verify example files exist"""
    print("\n" + "="*70)
    print("5. Verifying Examples")
    print("="*70)
    
    example_file = "examples/self_update_example.py"
    if os.path.exists(example_file):
        with open(example_file, 'r') as f:
            lines = len(f.readlines())
        print_success(f"Example file exists ({lines} lines)")
        return True
    else:
        print_error("Example file not found")
        return False

def verify_component_instantiation():
    """Verify components can be instantiated"""
    print("\n" + "="*70)
    print("6. Verifying Component Instantiation")
    print("="*70)
    
    try:
        from core.version_detector import VersionDetector
        detector = VersionDetector(check_interval=60)
        print_success("VersionDetector instantiated")
        
        from core.update_simulator import UpdateSimulator
        simulator = UpdateSimulator()
        print_success("UpdateSimulator instantiated")
        
        from core.update_policy_engine import UpdatePolicyEngine
        engine = UpdatePolicyEngine()
        print_success("UpdatePolicyEngine instantiated")
        
        from core.cicd_integrator import CICDIntegrator
        integrator = CICDIntegrator()
        print_success("CICDIntegrator instantiated")
        
        from core.rollout_controller import RolloutController
        controller = RolloutController()
        print_success("RolloutController instantiated")
        
        from core.self_update_orchestrator import SelfUpdateOrchestrator
        orchestrator = SelfUpdateOrchestrator(auto_update_enabled=False)
        print_success("SelfUpdateOrchestrator instantiated")
        
        return True
    except Exception as e:
        print_error(f"Instantiation failed: {e}")
        return False

def count_total_files():
    """Count total implementation files"""
    print("\n" + "="*70)
    print("7. File Summary")
    print("="*70)
    
    files = [
        "core/version_detector.py",
        "core/update_simulator.py",
        "core/update_policy_engine.py",
        "core/cicd_integrator.py",
        "core/rollout_controller.py",
        "core/self_update_orchestrator.py",
        "api/self_update_routes.py",
        "examples/self_update_example.py",
        "tests/test_self_update_system.py"
    ]
    
    total_lines = 0
    for file in files:
        if os.path.exists(file):
            with open(file, 'r') as f:
                lines = len(f.readlines())
                total_lines += lines
                print(f"  {file}: {lines} lines")
    
    print_info(f"Total implementation: {total_lines} lines of code")
    return total_lines

def main():
    """Main verification"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*10 + "Self-Triggered CI/CD Update System" + " "*24 + "║")
    print("║" + " "*18 + "Verification Script" + " "*31 + "║")
    print("╚" + "="*68 + "╝")
    
    results = []
    
    # Run verifications
    results.append(("Imports", verify_imports()))
    results.append(("API Routes", verify_api_routes()))
    results.append(("Tests", verify_tests()))
    results.append(("Documentation", verify_documentation()))
    results.append(("Examples", verify_examples()))
    results.append(("Instantiation", verify_component_instantiation()))
    
    # Count files
    total_lines = count_total_files()
    
    # Print summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{name:.<40} {status}")
    
    print("="*70)
    
    if passed == total:
        print(f"\n{GREEN}✅ All verifications passed!{RESET}")
        print(f"\n{BLUE}System is ready for deployment 🚀{RESET}")
        return 0
    else:
        print(f"\n{RED}✗ {total - passed} verification(s) failed{RESET}")
        print(f"\n{YELLOW}Please review the errors above{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
