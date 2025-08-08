#!/usr/bin/env python3
"""
LTMC Orchestration Integration Test Runner

Runs comprehensive integration tests for all orchestration services.
Validates real Redis integration, performance improvements, and error recovery.
"""

import sys
import subprocess
import time
from pathlib import Path

def main():
    """Run orchestration integration tests with comprehensive reporting."""
    print("🚀 LTMC Orchestration Integration Test Suite")
    print("=" * 60)
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    test_categories = [
        ("Service Integration", "TestOrchestrationServiceIntegration"),
        ("Performance Validation", "TestPerformanceValidation"), 
        ("Error Recovery", "TestErrorRecoveryScenarios"),
        ("Backward Compatibility", "TestBackwardCompatibility")
    ]
    
    results = {}
    total_start = time.time()
    
    for category_name, test_class in test_categories:
        print(f"\n🧪 Running {category_name} Tests...")
        print("-" * 50)
        
        start_time = time.time()
        
        # Run tests for this category
        result = subprocess.run([
            "python", "-m", "pytest",
            f"tests/orchestration/test_service_integration.py::{test_class}",
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=project_root)
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {category_name}: ALL PASSED ({duration:.2f}s)")
            results[category_name] = "PASSED"
        else:
            print(f"❌ {category_name}: SOME FAILED ({duration:.2f}s)")
            results[category_name] = "FAILED"
            
        # Show key output lines
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "PASSED" in line or "FAILED" in line or "ERROR" in line:
                    if len(line.strip()) > 0:
                        print(f"   {line.strip()}")
    
    total_duration = time.time() - total_start
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for status in results.values() if status == "PASSED")
    total_count = len(results)
    
    for category, status in results.items():
        icon = "✅" if status == "PASSED" else "❌"
        print(f"{icon} {category}: {status}")
    
    print(f"\nOverall: {passed_count}/{total_count} test categories passed")
    print(f"Total execution time: {total_duration:.2f} seconds")
    
    if passed_count == total_count:
        print("\n🎉 ALL ORCHESTRATION INTEGRATION TESTS PASSED!")
        print("✅ Redis orchestration layer is ready for production")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test categories failed")
        print("❌ Please fix failing tests before deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())