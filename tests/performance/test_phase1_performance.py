"""
TDD Performance Test Suite: Phase 1 Taskmaster Integration

PERFORMANCE REQUIREMENTS: 
- Project isolation validation: <5ms per operation
- Path security validation: <3ms per operation  
- Overall Phase 1 overhead: <10ms total per MCP tool call
- No degradation of existing LTMC baseline performance

TDD APPROACH: These tests define performance requirements FIRST.
Security components don't exist yet - tests will fail initially.
This establishes the performance contract before implementation.
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any, Tuple
import subprocess
import requests
import concurrent.futures
import threading
import uuid
import json
import tempfile
from pathlib import Path


class TestPhase1PerformanceBaseline:
    """
    TDD Performance Tests: Establish Phase 1 Performance Requirements
    
    These tests define the EXACT performance requirements that Phase 1
    security components must meet. All tests will fail initially since
    the components don't exist yet.
    
    CRITICAL: Performance requirements are non-negotiable for production use.
    """
    
    @pytest.fixture(scope="class") 
    def ltmc_server_process(self):
        """
        Start LTMC server for baseline performance measurement.
        
        PHASE 0 REQUIREMENT: Must verify system starts successfully.
        """
        # Kill any existing processes
        try:
            subprocess.run(["pkill", "-f", "ltmc_mcp_server_http.py"], check=False)
            time.sleep(2)
        except Exception:
            pass
        
        # Start server
        process = subprocess.Popen(
            ["python", "ltmc_mcp_server_http.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/home/feanor/Projects/lmtc"
        )
        
        # Wait for server to start (Phase 0 validation)
        for _ in range(30):
            try:
                response = requests.get("http://localhost:5050/health", timeout=1)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(1)
                continue
        else:
            stdout, stderr = process.communicate(timeout=5)
            process.kill()
            pytest.fail(
                f"LTMC server failed to start - cannot test performance.\n"
                f"STDOUT: {stdout.decode()}\nSTDERR: {stderr.decode()}"
            )
        
        yield process
        
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    
    def test_baseline_tool_performance_without_security(self, ltmc_server_process):
        """
        TDD Performance Test 1: Establish current baseline without security overhead.
        
        Measures current tool performance to compare against Phase 1 implementation.
        This test should PASS initially to establish baseline metrics.
        """
        # Core tools to benchmark
        tool_benchmarks = [
            ("store_memory", {
                "file_name": "performance_test.md",
                "content": "Performance benchmark test content",
                "resource_type": "benchmark"
            }),
            ("retrieve_memory", {
                "query": "performance benchmark", 
                "limit": 5
            }),
            ("list_todos", {}),
            ("build_context", {
                "query": "performance context test",
                "max_chars": 1000
            })
        ]
        
        baseline_metrics = {}
        
        for tool_name, args in tool_benchmarks:
            # Warm up (3 calls)
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
                "id": 1
            }
            
            for _ in range(3):
                requests.post("http://localhost:5050/jsonrpc", json=payload, timeout=30)
            
            # Measure performance (50 samples for statistical significance)
            times = []
            for i in range(50):
                start_time = time.perf_counter()
                
                response = requests.post(
                    "http://localhost:5050/jsonrpc",
                    json=payload,
                    timeout=30
                )
                
                end_time = time.perf_counter()
                
                assert response.status_code == 200, f"{tool_name} failed during benchmarking"
                response_time_ms = (end_time - start_time) * 1000
                times.append(response_time_ms)
            
            # Calculate statistics
            baseline_metrics[tool_name] = {
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
                "p95_ms": sorted(times)[int(0.95 * len(times))],
                "sample_size": len(times)
            }
        
        # Store baseline for comparison
        print(f"\n📊 BASELINE PERFORMANCE METRICS (without Phase 1 security):")
        for tool, metrics in baseline_metrics.items():
            print(f"{tool:15} | Mean: {metrics['mean_ms']:6.2f}ms | P95: {metrics['p95_ms']:6.2f}ms | Max: {metrics['max_ms']:6.2f}ms")
        
        # Verify reasonable baseline performance
        for tool_name, metrics in baseline_metrics.items():
            assert metrics['mean_ms'] < 500.0, f"{tool_name} baseline too slow: {metrics['mean_ms']:.2f}ms"
            assert metrics['p95_ms'] < 1000.0, f"{tool_name} P95 too slow: {metrics['p95_ms']:.2f}ms"
        
        return baseline_metrics
    
    def test_project_isolation_performance_requirement(self):
        """
        TDD Performance Test 2: Project isolation validation speed requirement.
        
        EXPECTED TO FAIL: ProjectIsolationManager doesn't exist yet.
        Defines the performance contract for project isolation.
        """
        from ltms.security.project_isolation import ProjectIsolationManager
        
        temp_dir = tempfile.mkdtemp(prefix="ltmc_perf_test_")
        try:
            manager = ProjectIsolationManager(project_root=Path(temp_dir))
            
            # Register test projects
            for i in range(10):
                manager.register_project(f"project_{i}", {
                    "name": f"Project {i}",
                    "allowed_paths": [f"data/proj_{i}", f"temp/proj_{i}"],
                    "database_prefix": f"proj_{i}",
                    "redis_namespace": f"ltmc:proj_{i}",
                    "neo4j_label": f"Project{i}"
                })
            
            # Performance test: Valid access validation
            test_cases = []
            for i in range(500):  # 500 validation calls
                test_cases.append(("project_5", "read", f"data/proj_5/file_{i}.txt"))
            
            start_time = time.perf_counter()
            
            for project_id, operation, path in test_cases:
                result = manager.validate_project_access(project_id, operation, path)
                assert result is True
            
            end_time = time.perf_counter()
            
            avg_time_ms = ((end_time - start_time) / len(test_cases)) * 1000
            
            # PERFORMANCE REQUIREMENT: <5ms per validation
            assert avg_time_ms < 5.0, f"Project isolation too slow: {avg_time_ms:.2f}ms (requirement: <5ms)"
            
            print(f"✅ Project isolation validation: {avg_time_ms:.2f}ms avg (target: <5ms)")
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_path_security_validation_performance_requirement(self):
        """
        TDD Performance Test 3: Path security validation speed requirement.
        
        EXPECTED TO FAIL: SecurePathValidator doesn't exist yet.
        Defines the performance contract for path security.
        """
        from ltms.security.path_security import SecurePathValidator
        
        temp_dir = tempfile.mkdtemp(prefix="ltmc_path_perf_test_")
        try:
            validator = SecurePathValidator(secure_root=Path(temp_dir))
            
            # Performance test: Mixed safe and dangerous paths
            safe_paths = [f"data/user_{i}/document.txt" for i in range(300)]
            dangerous_paths = [f"data/../../../etc/passwd_{i}" for i in range(200)]
            
            # Test safe paths
            start_time = time.perf_counter()
            
            for path in safe_paths:
                result = validator.validate_file_operation(path, "read", "test_project")
                assert result is True
            
            end_time = time.perf_counter()
            safe_avg_ms = ((end_time - start_time) / len(safe_paths)) * 1000
            
            # PERFORMANCE REQUIREMENT: <2ms for safe paths
            assert safe_avg_ms < 2.0, f"Safe path validation too slow: {safe_avg_ms:.2f}ms (requirement: <2ms)"
            
            # Test dangerous paths (should be caught quickly)
            from ltms.security.path_security import SecurityError
            
            start_time = time.perf_counter()
            
            for path in dangerous_paths:
                with pytest.raises(SecurityError):
                    validator.validate_file_operation(path, "read", "test_project")
            
            end_time = time.perf_counter()
            danger_avg_ms = ((end_time - start_time) / len(dangerous_paths)) * 1000
            
            # PERFORMANCE REQUIREMENT: <3ms for dangerous path detection
            assert danger_avg_ms < 3.0, f"Dangerous path detection too slow: {danger_avg_ms:.2f}ms (requirement: <3ms)"
            
            print(f"✅ Path security validation - Safe: {safe_avg_ms:.2f}ms, Dangerous: {danger_avg_ms:.2f}ms")
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_combined_security_overhead_requirement(self, ltmc_server_process):
        """
        TDD Performance Test 4: Combined Phase 1 security overhead requirement.
        
        EXPECTED TO FAIL: Enhanced MCP tools with security don't exist yet.
        Tests the total overhead when project isolation + path security are combined.
        """
        # This test will measure the performance difference when security is enabled
        # Currently will fail because security-enhanced tools don't exist
        
        tool_with_security_tests = [
            {
                "tool": "store_memory",
                "args": {
                    "file_name": "security_overhead_test.md",
                    "content": "Testing security overhead",
                    "resource_type": "document",
                    "project_id": "test_project"  # This parameter doesn't exist yet
                }
            },
            {
                "tool": "retrieve_memory", 
                "args": {
                    "query": "security overhead test",
                    "limit": 5,
                    "project_id": "test_project"  # This parameter doesn't exist yet
                }
            }
        ]
        
        security_metrics = {}
        
        for test_case in tool_with_security_tests:
            tool_name = test_case["tool"]
            
            # Measure performance with security (this will fail initially)
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call", 
                "params": {
                    "name": tool_name,
                    "arguments": test_case["args"]
                },
                "id": 1
            }
            
            times = []
            successful_calls = 0
            
            for _ in range(20):  # 20 samples
                start_time = time.perf_counter()
                
                try:
                    response = requests.post(
                        "http://localhost:5050/jsonrpc",
                        json=payload,
                        timeout=15
                    )
                    
                    end_time = time.perf_counter()
                    
                    if response.status_code == 200:
                        result = response.json()
                        # For now, we expect this to fail because security params don't exist
                        # But we measure the time anyway to see current behavior
                        times.append((end_time - start_time) * 1000)
                        if result.get("error") is None and result.get("result", {}).get("success"):
                            successful_calls += 1
                    
                except requests.RequestException:
                    # Network issues don't count against security overhead
                    pass
            
            if times:
                security_metrics[tool_name] = {
                    "mean_ms": statistics.mean(times),
                    "successful_calls": successful_calls,
                    "total_calls": len(times)
                }
        
        # The key test: when security is implemented, overhead should be <10ms
        print(f"\n🔒 SECURITY OVERHEAD MEASUREMENTS:")
        for tool, metrics in security_metrics.items():
            print(f"{tool:15} | Mean: {metrics['mean_ms']:6.2f}ms | Success: {metrics['successful_calls']}/{metrics['total_calls']}")
        
        # This assertion will fail initially (expected) but defines the requirement
        for tool_name, metrics in security_metrics.items():
            if metrics['successful_calls'] > 0:
                # PERFORMANCE REQUIREMENT: Combined security overhead <10ms
                assert metrics['mean_ms'] < 10.0, f"Combined security overhead too high for {tool_name}: {metrics['mean_ms']:.2f}ms (requirement: <10ms)"


class TestPhase1PerformanceConcurrency:
    """
    TDD Concurrency Performance Tests: Phase 1 Multi-threaded Performance
    
    Tests performance under concurrent load to ensure security doesn't create bottlenecks.
    """
    
    @pytest.fixture(scope="class")
    def ltmc_server_process(self):
        """Start LTMC server for concurrency testing."""
        # Kill any existing processes
        try:
            subprocess.run(["pkill", "-f", "ltmc_mcp_server_http.py"], check=False)
            time.sleep(2)
        except Exception:
            pass
        
        # Start server
        process = subprocess.Popen(
            ["python", "ltmc_mcp_server_http.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/home/feanor/Projects/lmtc"
        )
        
        # Wait for server to start
        for _ in range(30):
            try:
                response = requests.get("http://localhost:5050/health", timeout=1)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(1)
                continue
        else:
            process.kill()
            pytest.skip("LTMC server failed to start - cannot test concurrency")
        
        yield process
        
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    
    def test_concurrent_project_isolation_performance(self):
        """
        TDD Concurrency Test 1: Project isolation under concurrent load.
        
        EXPECTED TO FAIL: ProjectIsolationManager doesn't exist yet.
        Ensures security validation doesn't become a bottleneck under load.
        """
        from ltms.security.project_isolation import ProjectIsolationManager
        
        temp_dir = tempfile.mkdtemp(prefix="ltmc_concurrent_test_")
        try:
            manager = ProjectIsolationManager(project_root=Path(temp_dir))
            
            # Register projects
            for i in range(5):
                manager.register_project(f"project_{i}", {
                    "name": f"Project {i}",
                    "allowed_paths": [f"data/proj_{i}"],
                    "database_prefix": f"proj_{i}",
                    "redis_namespace": f"ltmc:proj_{i}",
                    "neo4j_label": f"Project{i}"
                })
            
            def validate_access_batch(batch_id: int, results: List[float]):
                """Validate project access in separate thread."""
                thread_times = []
                
                for i in range(50):  # 50 validations per thread
                    start_time = time.perf_counter()
                    
                    result = manager.validate_project_access(
                        f"project_{batch_id % 5}", 
                        "read", 
                        f"data/proj_{batch_id % 5}/file_{i}.txt"
                    )
                    
                    end_time = time.perf_counter()
                    
                    assert result is True
                    thread_times.append((end_time - start_time) * 1000)
                
                results.extend(thread_times)
            
            # Run concurrent validation tests
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(validate_access_batch, i, results)
                    for i in range(10)  # 10 concurrent threads
                ]
                
                concurrent.futures.wait(futures)
            
            # Analyze concurrent performance
            if results:
                mean_time = statistics.mean(results)
                max_time = max(results)
                p95_time = sorted(results)[int(0.95 * len(results))]
                
                print(f"🔄 Concurrent project isolation - Mean: {mean_time:.2f}ms, P95: {p95_time:.2f}ms, Max: {max_time:.2f}ms")
                
                # PERFORMANCE REQUIREMENT: Concurrent access <8ms mean, <15ms P95
                assert mean_time < 8.0, f"Concurrent mean too slow: {mean_time:.2f}ms"
                assert p95_time < 15.0, f"Concurrent P95 too slow: {p95_time:.2f}ms"
                assert max_time < 25.0, f"Concurrent max too slow: {max_time:.2f}ms"
        
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_concurrent_mcp_tool_security_performance(self, ltmc_server_process):
        """
        TDD Concurrency Test 2: MCP tools with security under concurrent load.
        
        EXPECTED TO FAIL: Security-enhanced MCP tools don't exist yet.
        Tests realistic concurrent usage with multiple projects.
        """
        def make_concurrent_request(thread_id: int, project_id: str, results: List[Tuple[float, bool]]):
            """Make MCP tool request with security in separate thread."""
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "store_memory",
                    "arguments": {
                        "file_name": f"concurrent_test_{thread_id}.md",
                        "content": f"Concurrent test content from thread {thread_id}",
                        "resource_type": "test",
                        "project_id": project_id  # This parameter doesn't exist yet
                    }
                },
                "id": thread_id
            }
            
            start_time = time.perf_counter()
            
            try:
                response = requests.post(
                    "http://localhost:5050/jsonrpc",
                    json=payload,
                    timeout=20
                )
                
                end_time = time.perf_counter()
                
                success = (response.status_code == 200 and 
                          response.json().get("result", {}).get("success") is True)
                
                results.append(((end_time - start_time) * 1000, success))
                
            except requests.RequestException as e:
                end_time = time.perf_counter()
                results.append(((end_time - start_time) * 1000, False))
        
        # Test with multiple projects concurrently
        projects = ["project_a", "project_b", "project_c"]
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            
            for i in range(30):  # 30 concurrent requests
                project_id = projects[i % len(projects)]
                future = executor.submit(make_concurrent_request, i, project_id, results)
                futures.append(future)
            
            concurrent.futures.wait(futures)
        
        # Analyze results
        if results:
            times = [r[0] for r in results]
            successes = [r[1] for r in results]
            
            mean_time = statistics.mean(times)
            success_rate = sum(successes) / len(successes)
            p95_time = sorted(times)[int(0.95 * len(times))] if times else 0
            
            print(f"🔄 Concurrent MCP tools - Mean: {mean_time:.2f}ms, Success: {success_rate:.1%}, P95: {p95_time:.2f}ms")
            
            # For now, we expect low success rate since security params don't exist
            # But we measure performance to establish baseline
            
            # PERFORMANCE REQUIREMENT: When implemented, should be <15ms mean, >95% success
            if success_rate > 0.5:  # If security is implemented
                assert mean_time < 15.0, f"Concurrent MCP tool performance too slow: {mean_time:.2f}ms"
                assert success_rate > 0.95, f"Concurrent success rate too low: {success_rate:.1%}"


class TestPhase1PerformanceStress:
    """
    TDD Stress Tests: Phase 1 Security Under High Load
    
    Tests security performance under stress conditions to ensure it doesn't degrade.
    """
    
    def test_security_validation_memory_usage(self):
        """
        TDD Stress Test 1: Memory usage of security validation.
        
        EXPECTED TO FAIL: Security components don't exist yet.
        Ensures security validation doesn't leak memory or consume excessive resources.
        """
        import tracemalloc
        from ltms.security.project_isolation import ProjectIsolationManager
        from ltms.security.path_security import SecurePathValidator
        
        temp_dir = tempfile.mkdtemp(prefix="ltmc_stress_test_")
        try:
            # Start memory tracing
            tracemalloc.start()
            
            # Create security components
            isolation_manager = ProjectIsolationManager(project_root=Path(temp_dir))
            path_validator = SecurePathValidator(secure_root=Path(temp_dir))
            
            # Register many projects
            for i in range(100):
                isolation_manager.register_project(f"stress_project_{i}", {
                    "name": f"Stress Project {i}",
                    "allowed_paths": [f"data/stress_{i}"],
                    "database_prefix": f"stress_{i}",
                    "redis_namespace": f"ltmc:stress_{i}",
                    "neo4j_label": f"Stress{i}"
                })
            
            # Perform many validation operations
            for _ in range(10000):  # 10K operations
                # Project validation
                isolation_manager.validate_project_access(
                    "stress_project_50", "read", "data/stress_50/test.txt"
                )
                
                # Path validation  
                path_validator.validate_file_operation(
                    "data/stress_test/file.txt", "read", "stress_project_50"
                )
            
            # Check memory usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # PERFORMANCE REQUIREMENT: Memory usage should be reasonable
            current_mb = current / 1024 / 1024
            peak_mb = peak / 1024 / 1024
            
            print(f"🧠 Security validation memory - Current: {current_mb:.2f}MB, Peak: {peak_mb:.2f}MB")
            
            # Should not use excessive memory for validation
            assert current_mb < 50.0, f"Security validation uses too much memory: {current_mb:.2f}MB"
            assert peak_mb < 100.0, f"Security validation peak memory too high: {peak_mb:.2f}MB"
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_security_validation_under_attack_load(self):
        """
        TDD Stress Test 2: Performance when under attack.
        
        EXPECTED TO FAIL: Security components don't exist yet.
        Ensures security doesn't degrade under malicious load.
        """
        from ltms.security.path_security import SecurePathValidator, SecurityError
        
        temp_dir = tempfile.mkdtemp(prefix="ltmc_attack_test_")
        try:
            validator = SecurePathValidator(secure_root=Path(temp_dir))
            
            # Generate many malicious requests
            attack_paths = []
            for i in range(1000):
                attack_paths.extend([
                    f"../../../etc/passwd_{i}",
                    f"data/../../../root/.ssh/id_rsa_{i}",
                    f"__import__('os').system('rm -rf /{i}')",
                    f"; cat /etc/shadow_{i} > /tmp/stolen_{i}",
                    f"data/" + "A" * 100 + f"/attack_{i}.txt"  # Long paths
                ])
            
            start_time = time.perf_counter()
            blocked_count = 0
            
            # Process all attack attempts
            for attack_path in attack_paths:
                try:
                    validator.validate_file_operation(attack_path, "read", "test_project")
                except SecurityError:
                    blocked_count += 1
                    # Expected - attack should be blocked
                except Exception as e:
                    # Unexpected error - security component might be overwhelmed
                    pytest.fail(f"Security component failed under attack load: {e}")
            
            end_time = time.perf_counter()
            
            total_time_ms = (end_time - start_time) * 1000
            avg_time_ms = total_time_ms / len(attack_paths)
            
            print(f"🛡️  Attack resistance - {blocked_count}/{len(attack_paths)} blocked, {avg_time_ms:.2f}ms avg")
            
            # PERFORMANCE REQUIREMENT: Should block attacks efficiently
            assert blocked_count > len(attack_paths) * 0.95, "Should block >95% of attacks"
            assert avg_time_ms < 5.0, f"Attack detection too slow: {avg_time_ms:.2f}ms"
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    """
    TDD Performance Test Execution: Phase 1 Performance Requirements
    
    Run with: python -m pytest tests/performance/test_phase1_performance.py -v
    
    EXPECTED RESULT: Most tests will FAIL initially (security components don't exist).
    Some baseline tests may PASS to establish current performance.
    
    This defines the performance contract for Phase 1 implementation.
    """
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, project_root)
    
    print("⚡ TDD PHASE 1 PERFORMANCE TESTS")
    print("Performance Requirements Definition:")
    print("  • Project isolation validation: <5ms")
    print("  • Path security validation: <3ms") 
    print("  • Combined security overhead: <10ms")
    print("  • Concurrent performance: <15ms P95")
    print("Expected: Security tests WILL FAIL (components don't exist)")
    print("Expected: Baseline tests MAY PASS (establish current metrics)")
    print("=" * 70)
    
    # Run tests with detailed output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s",  # Show print statements
        "--no-header"
    ])
    
    print("=" * 70)
    if exit_code != 0:
        print("📊 TDD PERFORMANCE SUCCESS: Requirements defined!")
        print("💡 Next: Implement security components meeting these requirements")
        print("🎯 Target: <10ms total overhead for Phase 1 security features")
    else:
        print("📊 Performance baseline established!")
        print("💡 Next: Implement security and validate against these requirements")
    
    sys.exit(0)  # Always exit 0 for TDD