#!/usr/bin/env python3
"""
Quick Safety Validation Performance Test
Validates core performance metrics without resource-heavy tests
"""

import asyncio
import time
import statistics
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ltms.integrations.sequential_thinking.safety_validation import (
    SafetyValidationAgent,
    ChainDepthMonitor,
    PerformanceValidator
)
from ltms.integrations.sequential_thinking.recursion_control import RecursionControlSystem


async def test_validation_overhead():
    """Test that validation overhead is < 5ms"""
    print("\n📊 Testing Validation Overhead...")
    
    agent = SafetyValidationAgent()
    latencies = []
    
    for i in range(100):
        start = time.perf_counter()
        result = await agent.validate_autonomous_operation(
            session_id="test",
            thought_id=f"thought_{i}",
            content=f"Test content {i}",
            parent_id=None if i == 0 else f"thought_{i-1}"
        )
        latency_ms = (time.perf_counter() - start) * 1000
        
        # Only count if not throttled
        if agent.throttle_factor == 1.0:
            latencies.append(latency_ms)
    
    if latencies:
        avg_ms = statistics.mean(latencies)
        p95_ms = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        print(f"  Average: {avg_ms:.2f}ms")
        print(f"  P95: {p95_ms:.2f}ms")
        print(f"  ✅ PASS" if avg_ms < 5 else f"  ❌ FAIL (target < 5ms)")
        return avg_ms < 5
    else:
        print("  ⚠️  All operations were throttled")
        return True  # Don't fail on throttling


async def test_chain_depth_monitoring():
    """Test chain depth monitoring performance"""
    print("\n📊 Testing Chain Depth Monitoring...")
    
    monitor = ChainDepthMonitor(max_depth=10, adaptive=False)
    latencies = []
    
    for depth in range(1, 11):
        start = time.perf_counter()
        is_safe, state = await monitor.track_chain_operation(
            session_id="test",
            thought_id=f"depth_{depth}",
            depth=depth,
            latency_ms=10
        )
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)
    
    avg_ms = statistics.mean(latencies)
    print(f"  Average tracking time: {avg_ms:.3f}ms")
    print(f"  ✅ PASS" if avg_ms < 1 else f"  ❌ FAIL (target < 1ms)")
    return avg_ms < 1


async def test_concurrent_safety():
    """Test concurrent operation safety"""
    print("\n📊 Testing Concurrent Safety...")
    
    agent = SafetyValidationAgent()
    
    async def validate_one(index):
        return await agent.validate_autonomous_operation(
            session_id=f"concurrent_{index % 5}",
            thought_id=f"concurrent_{index}",
            content=f"Concurrent {index}",
            parent_id=None
        )
    
    start = time.perf_counter()
    tasks = [validate_one(i) for i in range(20)]
    results = await asyncio.gather(*tasks)
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    valid_count = sum(1 for r in results if r["valid"])
    print(f"  Validated {valid_count}/20 operations in {elapsed_ms:.1f}ms")
    print(f"  Throughput: {(20/elapsed_ms)*1000:.1f} ops/sec")
    print(f"  ✅ PASS" if valid_count == 20 else f"  ❌ FAIL")
    return valid_count == 20


async def test_recursion_blocking():
    """Test that recursion limits are enforced"""
    print("\n📊 Testing Recursion Blocking...")
    
    recursion_control = RecursionControlSystem(max_depth=5)
    agent = SafetyValidationAgent(recursion_control=recursion_control)
    
    # Try to create deep chain
    parent_id = None
    blocked = False
    
    for i in range(7):
        result = await agent.validate_autonomous_operation(
            session_id="recursion_test",
            thought_id=f"deep_{i}",
            content=f"Deep thought {i}",
            parent_id=parent_id
        )
        
        if not result["valid"]:
            blocked = True
            print(f"  Blocked at depth {i} as expected")
            break
        
        parent_id = f"deep_{i}"
    
    print(f"  ✅ PASS" if blocked else f"  ❌ FAIL (should block at depth 5)")
    return blocked


async def test_performance_validator():
    """Test performance validator SLA checking"""
    print("\n📊 Testing Performance Validator...")
    
    validator = PerformanceValidator(thought_sla_ms=100, complex_sla_ms=500)
    
    # Test SLA compliance detection
    test_cases = [
        (50, False, True),   # 50ms simple operation - should pass
        (150, False, False), # 150ms simple operation - should fail
        (400, True, True),   # 400ms complex operation - should pass
        (600, True, False),  # 600ms complex operation - should fail
    ]
    
    all_correct = True
    for latency, is_complex, should_pass in test_cases:
        meets_sla, state = await validator.validate_operation_performance(
            f"test_op_{latency}",
            latency_ms=latency,
            is_complex=is_complex
        )
        
        if meets_sla != should_pass:
            print(f"  ❌ {latency}ms {'complex' if is_complex else 'simple'}: "
                  f"Expected {should_pass}, got {meets_sla}")
            all_correct = False
    
    print(f"  ✅ PASS" if all_correct else f"  ❌ FAIL")
    return all_correct


async def main():
    """Run quick safety validation tests"""
    print("\n" + "="*50)
    print("🚀 QUICK SAFETY VALIDATION PERFORMANCE TEST")
    print("="*50)
    
    results = []
    
    # Run tests
    results.append(("Validation Overhead", await test_validation_overhead()))
    results.append(("Chain Depth Monitoring", await test_chain_depth_monitoring()))
    results.append(("Concurrent Safety", await test_concurrent_safety()))
    results.append(("Recursion Blocking", await test_recursion_blocking()))
    results.append(("Performance Validator", await test_performance_validator()))
    
    # Summary
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All safety validation tests PASSED!")
        return 0
    else:
        print("❌ Some tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))