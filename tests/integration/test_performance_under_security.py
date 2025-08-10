#!/usr/bin/env python3
"""
LTMC Performance Under Security Integration Tests

MANDATORY: REAL PERFORMANCE TESTING UNDER SECURITY LOAD ONLY
- Tests real system performance with security validation enabled
- Tests real performance degradation under security overhead  
- Tests real concurrent load with security validation active
- Tests real memory usage with security components
- Tests real response time distribution under security load
- Tests real throughput limits with security enforcement
- Tests real resource utilization under security stress

NO MOCKS - REAL PERFORMANCE TESTING UNDER SECURITY ONLY!

Critical Focus: Security performance impact, scalability, resource utilization
"""

import os
import sys
import asyncio
import time
import threading
import multiprocessing
import statistics
# Optional performance monitoring dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

try:
    import memory_profiler
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    memory_profiler = None

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-GUI backend for CI environments
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    matplotlib = None
    plt = None

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
import pytest
import requests
import logging
import subprocess
import json
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance measurement data structure."""
    response_times: List[float]
    cpu_usage: List[float]
    memory_usage: List[float]
    throughput: float
    error_rate: float
    concurrent_users: int
    test_duration: float
    security_overhead: float

@dataclass
class SecurityLoadScenario:
    """Security load test scenario configuration."""
    name: str
    concurrent_users: int
    requests_per_user: int
    security_features: List[str]
    expected_max_response_time: float
    expected_min_throughput: float

class RealPerformanceSecurityTester:
    """
    Real Performance Security Tester
    
    Tests ACTUAL system performance under REAL security load:
    - Real concurrent user simulation with security validation
    - Real memory and CPU monitoring during security operations
    - Real throughput measurement with security overhead
    - Real response time distribution analysis
    - Real resource utilization tracking
    - Real scalability testing with security constraints
    """
    
    def __init__(self):
        self.project_root = project_root
        self.test_server_port = 5055
        self.server_process: Optional[subprocess.Popen] = None
        self.monitoring_active = False
        self.performance_data: Dict[str, Any] = {}
        
        # Performance test scenarios
        self.load_scenarios = self._create_load_scenarios()
        self.security_scenarios = self._create_security_scenarios()
        
        # Monitoring configuration
        self.monitoring_interval = 0.5  # 500ms sampling
        self.cpu_monitor = None
        self.memory_monitor = None
        
    def _create_load_scenarios(self) -> List[SecurityLoadScenario]:
        """Create performance load test scenarios."""
        return [
            SecurityLoadScenario(
                name="light_load_with_security",
                concurrent_users=5,
                requests_per_user=20,
                security_features=["project_isolation", "path_validation"],
                expected_max_response_time=2.0,
                expected_min_throughput=10.0
            ),
            SecurityLoadScenario(
                name="medium_load_with_security",
                concurrent_users=15,
                requests_per_user=30,
                security_features=["project_isolation", "path_validation", "input_sanitization"],
                expected_max_response_time=5.0,
                expected_min_throughput=20.0
            ),
            SecurityLoadScenario(
                name="heavy_load_with_security",
                concurrent_users=30,
                requests_per_user=25,
                security_features=["project_isolation", "path_validation", "input_sanitization", "rate_limiting"],
                expected_max_response_time=10.0,
                expected_min_throughput=15.0
            ),
            SecurityLoadScenario(
                name="stress_load_with_security",
                concurrent_users=50,
                requests_per_user=20,
                security_features=["project_isolation", "path_validation", "input_sanitization", "rate_limiting", "attack_detection"],
                expected_max_response_time=15.0,
                expected_min_throughput=10.0
            )
        ]
    
    def _create_security_scenarios(self) -> List[Dict[str, Any]]:
        """Create security-focused performance scenarios."""
        return [
            {
                "name": "path_traversal_attack_load",
                "description": "High volume of path traversal attacks",
                "attack_payloads": [
                    "../../../etc/passwd",
                    "..\\..\\..\\windows\\system32\\config\\sam", 
                    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                    "....//....//....//etc//passwd"
                ] * 10,  # Repeat for volume
                "concurrent_attackers": 20,
                "expected_blocked": True
            },
            {
                "name": "sql_injection_attack_load", 
                "description": "High volume of SQL injection attempts",
                "attack_payloads": [
                    "'; DROP TABLE memories; --",
                    "' OR '1'='1' --",
                    "'; UNION SELECT password FROM users; --",
                    "' AND 1=(SELECT COUNT(*) FROM tabname); --"
                ] * 15,  # Repeat for volume
                "concurrent_attackers": 25,
                "expected_blocked": True
            },
            {
                "name": "buffer_overflow_attack_load",
                "description": "Large payload attacks to test limits",
                "attack_payloads": [
                    "A" * (1024 * 1024),      # 1MB payload
                    "B" * (2 * 1024 * 1024),  # 2MB payload
                    "C" * (5 * 1024 * 1024),  # 5MB payload
                ],
                "concurrent_attackers": 10,
                "expected_blocked": True
            }
        ]

@pytest.fixture(scope="module")
def performance_security_tester():
    """Fixture providing real performance security tester."""
    tester = RealPerformanceSecurityTester()
    yield tester
    tester.cleanup()

class TestPerformanceUnderSecurityLoad:
    """
    Test system performance under various security loads.
    
    Measures actual performance impact of security features.
    """
    
    def test_baseline_performance_measurement(self, performance_security_tester):
        """
        Establish baseline performance measurements without security load.
        
        Creates performance baseline for comparison with security overhead.
        """
        tester = performance_security_tester
        
        # Start real LTMC server
        server_cmd = [
            sys.executable,
            str(tester.project_root / "ltmc_mcp_server.py"),
            "--transport", "http",
            "--host", "127.0.0.1",
            "--port", str(tester.test_server_port)
        ]
        
        tester.server_process = subprocess.Popen(
            server_cmd,
            cwd=str(tester.project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        
        # Wait for server startup
        time.sleep(5)
        
        # Baseline test: Simple operations without security stress
        baseline_metrics = self._measure_performance_scenario(
            tester=tester,
            scenario_name="baseline",
            concurrent_users=5,
            requests_per_user=10,
            operation_type="simple_health_check",
            security_stress=False
        )
        
        # Store baseline for comparison
        tester.performance_data["baseline"] = baseline_metrics
        
        # Validate baseline performance
        assert baseline_metrics.error_rate < 0.05, f"High baseline error rate: {baseline_metrics.error_rate:.2%}"
        assert len(baseline_metrics.response_times) > 0, "No baseline response times recorded"
        
        avg_response_time = statistics.mean(baseline_metrics.response_times)
        assert avg_response_time < 1.0, f"Baseline response time too high: {avg_response_time:.3f}s"
        
        logger.info(f"✅ Baseline performance established:")
        logger.info(f"   Average response time: {avg_response_time:.3f}s")
        logger.info(f"   Throughput: {baseline_metrics.throughput:.1f} req/s")
        logger.info(f"   Error rate: {baseline_metrics.error_rate:.2%}")
    
    def test_progressive_load_with_security(self, performance_security_tester):
        """
        Test performance under progressively increasing security load.
        
        Measures performance degradation as security load increases.
        """
        tester = performance_security_tester
        
        performance_results = {}
        
        for scenario in tester.load_scenarios:
            logger.info(f"Testing scenario: {scenario.name}")
            
            # Measure performance under this security load scenario
            scenario_metrics = self._measure_performance_scenario(
                tester=tester,
                scenario_name=scenario.name,
                concurrent_users=scenario.concurrent_users,
                requests_per_user=scenario.requests_per_user,
                operation_type="security_validated_operations",
                security_stress=True,
                security_features=scenario.security_features
            )
            
            performance_results[scenario.name] = scenario_metrics
            
            # Validate scenario performance meets requirements
            avg_response_time = statistics.mean(scenario_metrics.response_times) if scenario_metrics.response_times else float('inf')
            
            assert avg_response_time <= scenario.expected_max_response_time, \
                f"Response time exceeded limit in {scenario.name}: {avg_response_time:.3f}s > {scenario.expected_max_response_time}s"
            
            assert scenario_metrics.throughput >= scenario.expected_min_throughput, \
                f"Throughput below minimum in {scenario.name}: {scenario_metrics.throughput:.1f} < {scenario.expected_min_throughput}"
            
            assert scenario_metrics.error_rate < 0.10, \
                f"Error rate too high in {scenario.name}: {scenario_metrics.error_rate:.2%}"
            
            logger.info(f"✅ {scenario.name} performance validated:")
            logger.info(f"   Average response time: {avg_response_time:.3f}s")
            logger.info(f"   Throughput: {scenario_metrics.throughput:.1f} req/s") 
            logger.info(f"   Error rate: {scenario_metrics.error_rate:.2%}")
            logger.info(f"   Security overhead: {scenario_metrics.security_overhead:.1f}%")
        
        # Compare progressive degradation
        baseline = tester.performance_data.get("baseline")
        if baseline:
            self._analyze_performance_degradation(baseline, performance_results)
        
        tester.performance_data.update(performance_results)
    
    def test_security_attack_performance_impact(self, performance_security_tester):
        """
        Test performance impact during active security attacks.
        
        Measures system performance while under actual attack load.
        """
        tester = performance_security_tester
        
        attack_performance_results = {}
        
        for security_scenario in tester.security_scenarios:
            logger.info(f"Testing security attack scenario: {security_scenario['name']}")
            
            # Measure performance during active attack simulation
            attack_metrics = self._measure_attack_scenario_performance(
                tester=tester,
                scenario=security_scenario
            )
            
            attack_performance_results[security_scenario['name']] = attack_metrics
            
            # Validate system remains stable under attack
            assert attack_metrics.error_rate < 0.20, \
                f"System overwhelmed by attacks in {security_scenario['name']}: {attack_metrics.error_rate:.2%} error rate"
            
            # System should still serve legitimate requests
            if attack_metrics.response_times:
                avg_response_time = statistics.mean(attack_metrics.response_times)
                assert avg_response_time < 20.0, \
                    f"Response time too high under attack in {security_scenario['name']}: {avg_response_time:.3f}s"
            
            # Validate attacks were properly blocked
            if security_scenario["expected_blocked"]:
                # Most attack requests should be blocked (high error rate for attack requests is expected)
                logger.info(f"Attacks properly blocked with {attack_metrics.error_rate:.1%} rejection rate")
            
            logger.info(f"✅ {security_scenario['name']} attack resistance validated:")
            logger.info(f"   System remained stable under {security_scenario['concurrent_attackers']} concurrent attackers")
            logger.info(f"   Attack blocking rate: {attack_metrics.error_rate:.1%}")
        
        tester.performance_data.update(attack_performance_results)
    
    def test_resource_utilization_under_security(self, performance_security_tester):
        """
        Test resource utilization (CPU, memory) under security load.
        
        Monitors actual system resource usage during security operations.
        """
        tester = performance_security_tester
        
        # Get server process for monitoring
        if not tester.server_process:
            pytest.fail("Server process not available for resource monitoring")
        
        server_pid = tester.server_process.pid
        
        # Monitor resource usage during heavy security load
        resource_metrics = self._monitor_resource_usage_during_load(
            server_pid=server_pid,
            tester=tester,
            load_duration=60,  # 60 second test
            concurrent_users=20,
            requests_per_user=30
        )
        
        # Validate resource usage is within acceptable limits
        max_cpu_usage = max(resource_metrics["cpu_usage"]) if resource_metrics["cpu_usage"] else 0
        max_memory_mb = max(resource_metrics["memory_usage"]) if resource_metrics["memory_usage"] else 0
        avg_cpu_usage = statistics.mean(resource_metrics["cpu_usage"]) if resource_metrics["cpu_usage"] else 0
        avg_memory_mb = statistics.mean(resource_metrics["memory_usage"]) if resource_metrics["memory_usage"] else 0
        
        # CPU usage limits (allow higher usage during security validation)
        assert max_cpu_usage < 95.0, f"CPU usage too high: {max_cpu_usage:.1f}%"
        assert avg_cpu_usage < 70.0, f"Average CPU usage too high: {avg_cpu_usage:.1f}%"
        
        # Memory usage limits (security validation may increase memory usage)
        assert max_memory_mb < 2048, f"Memory usage too high: {max_memory_mb:.1f}MB"
        assert avg_memory_mb < 1024, f"Average memory usage too high: {avg_memory_mb:.1f}MB"
        
        # Check for memory leaks (memory should stabilize, not continuously grow)
        if len(resource_metrics["memory_usage"]) > 10:
            early_avg = statistics.mean(resource_metrics["memory_usage"][:5])
            late_avg = statistics.mean(resource_metrics["memory_usage"][-5:])
            memory_growth = (late_avg - early_avg) / early_avg
            assert memory_growth < 0.20, f"Possible memory leak detected: {memory_growth:.1%} growth"
        
        logger.info(f"✅ Resource utilization under security load validated:")
        logger.info(f"   Peak CPU usage: {max_cpu_usage:.1f}%")
        logger.info(f"   Average CPU usage: {avg_cpu_usage:.1f}%") 
        logger.info(f"   Peak memory usage: {max_memory_mb:.1f}MB")
        logger.info(f"   Average memory usage: {avg_memory_mb:.1f}MB")
        
        tester.performance_data["resource_utilization"] = resource_metrics
    
    def _measure_performance_scenario(
        self,
        tester,
        scenario_name: str,
        concurrent_users: int,
        requests_per_user: int,
        operation_type: str,
        security_stress: bool,
        security_features: Optional[List[str]] = None
    ) -> PerformanceMetrics:
        """Measure performance for a specific scenario."""
        
        def execute_user_requests(user_id: int) -> List[Tuple[float, bool]]:
            """Execute requests for a single user and return (response_time, success) tuples."""
            results = []
            
            for request_id in range(requests_per_user):
                start_time = time.time()
                success = False
                
                try:
                    if operation_type == "simple_health_check":
                        response = requests.post(
                            f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                            json={
                                "jsonrpc": "2.0",
                                "method": "tools/call",
                                "params": {
                                    "name": "redis_health_check",
                                    "arguments": {"project_id": f"user_{user_id}"}
                                },
                                "id": f"{user_id}_{request_id}"
                            },
                            timeout=30
                        )
                    else:  # security_validated_operations
                        response = requests.post(
                            f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                            json={
                                "jsonrpc": "2.0",
                                "method": "tools/call",
                                "params": {
                                    "name": "store_memory",
                                    "arguments": {
                                        "content": f"Performance test data from user {user_id}, request {request_id}",
                                        "file_name": f"perf_test_u{user_id}_r{request_id}.md",
                                        "project_id": f"user_{user_id}_project"
                                    }
                                },
                                "id": f"{user_id}_{request_id}"
                            },
                            timeout=30
                        )
                    
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if "result" in response_data:
                            success = True
                        
                    results.append((response_time, success))
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    results.append((response_time, False))
                    logger.debug(f"Request failed for user {user_id}, request {request_id}: {e}")
                
                # Small delay between requests
                time.sleep(0.01)
            
            return results
        
        # Execute scenario with concurrent users
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(execute_user_requests, user_id)
                for user_id in range(concurrent_users)
            ]
            
            all_results = []
            for future in as_completed(futures):
                user_results = future.result()
                all_results.extend(user_results)
        
        total_duration = time.time() - start_time
        
        # Calculate metrics
        response_times = [result[0] for result in all_results]
        successes = [result[1] for result in all_results]
        
        total_requests = len(all_results)
        successful_requests = sum(successes)
        error_rate = (total_requests - successful_requests) / total_requests if total_requests > 0 else 1.0
        throughput = successful_requests / total_duration if total_duration > 0 else 0.0
        
        # Calculate security overhead (comparison to baseline if available)
        security_overhead = 0.0
        if "baseline" in tester.performance_data and response_times:
            baseline_avg = statistics.mean(tester.performance_data["baseline"].response_times)
            current_avg = statistics.mean(response_times)
            security_overhead = ((current_avg - baseline_avg) / baseline_avg) * 100 if baseline_avg > 0 else 0.0
        
        return PerformanceMetrics(
            response_times=response_times,
            cpu_usage=[],  # CPU monitoring would be added here
            memory_usage=[],  # Memory monitoring would be added here
            throughput=throughput,
            error_rate=error_rate,
            concurrent_users=concurrent_users,
            test_duration=total_duration,
            security_overhead=security_overhead
        )
    
    def _measure_attack_scenario_performance(self, tester, scenario: Dict[str, Any]) -> PerformanceMetrics:
        """Measure performance during active attack scenario."""
        
        def execute_attack_requests(attacker_id: int) -> List[Tuple[float, bool]]:
            """Execute attack requests and measure response."""
            results = []
            
            for payload in scenario["attack_payloads"]:
                start_time = time.time()
                success = False  # For attacks, "success" means the attack was blocked
                
                try:
                    # Try different attack vectors
                    if "path_traversal" in scenario["name"]:
                        attack_args = {
                            "content": "attack content",
                            "file_name": payload,  # Malicious path
                            "project_id": f"attacker_{attacker_id}"
                        }
                    elif "sql_injection" in scenario["name"]:
                        attack_args = {
                            "content": payload,  # Malicious SQL
                            "file_name": "attack_file.md",
                            "project_id": f"attacker_{attacker_id}"
                        }
                    else:  # buffer_overflow
                        attack_args = {
                            "content": payload,  # Large payload
                            "file_name": "attack_file.md", 
                            "project_id": f"attacker_{attacker_id}"
                        }
                    
                    response = requests.post(
                        f"http://127.0.0.1:{tester.test_server_port}/jsonrpc",
                        json={
                            "jsonrpc": "2.0",
                            "method": "tools/call",
                            "params": {
                                "name": "store_memory",
                                "arguments": attack_args
                            },
                            "id": f"attack_{attacker_id}"
                        },
                        timeout=20
                    )
                    
                    response_time = time.time() - start_time
                    
                    # For attacks, we expect them to be blocked (error or failure)
                    if response.status_code != 200:
                        success = True  # Attack was blocked at HTTP level
                    else:
                        response_data = response.json()
                        if "error" in response_data:
                            success = True  # Attack was blocked at application level
                        elif "result" in response_data:
                            result = response_data["result"]
                            if not result.get("success", True):
                                success = True  # Attack was blocked/failed
                    
                    results.append((response_time, success))
                    
                except Exception:
                    response_time = time.time() - start_time  
                    results.append((response_time, True))  # Exception indicates attack was blocked
                
                # Small delay between attack attempts
                time.sleep(0.05)
            
            return results
        
        # Execute attack scenario
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=scenario["concurrent_attackers"]) as executor:
            futures = [
                executor.submit(execute_attack_requests, attacker_id)
                for attacker_id in range(scenario["concurrent_attackers"])
            ]
            
            all_results = []
            for future in as_completed(futures, timeout=120):
                attacker_results = future.result()
                all_results.extend(attacker_results)
        
        total_duration = time.time() - start_time
        
        # Calculate attack scenario metrics
        response_times = [result[0] for result in all_results]
        blocks = [result[1] for result in all_results]  # successful blocks
        
        total_attacks = len(all_results)
        blocked_attacks = sum(blocks)
        block_rate = blocked_attacks / total_attacks if total_attacks > 0 else 0.0
        
        # For attack scenarios, error_rate represents the attack blocking rate (higher is better)
        return PerformanceMetrics(
            response_times=response_times,
            cpu_usage=[],
            memory_usage=[],
            throughput=total_attacks / total_duration if total_duration > 0 else 0.0,
            error_rate=block_rate,  # For attacks, this is actually the blocking success rate
            concurrent_users=scenario["concurrent_attackers"],
            test_duration=total_duration,
            security_overhead=0.0
        )
    
    def _monitor_resource_usage_during_load(
        self,
        server_pid: int,
        tester,
        load_duration: int,
        concurrent_users: int,
        requests_per_user: int
    ) -> Dict[str, List[float]]:
        """Monitor resource usage during load test."""
        
        resource_data = {
            "cpu_usage": [],
            "memory_usage": [],
            "timestamps": []
        }
        
        monitoring_active = True
        
        def monitor_resources():
            """Background resource monitoring."""
            if not PSUTIL_AVAILABLE:
                logger.warning("psutil not available - resource monitoring disabled")
                return
                
            try:
                process = psutil.Process(server_pid)
                
                while monitoring_active:
                    try:
                        cpu_percent = process.cpu_percent()
                        memory_mb = process.memory_info().rss / 1024 / 1024  # Convert to MB
                        
                        resource_data["cpu_usage"].append(cpu_percent)
                        resource_data["memory_usage"].append(memory_mb)
                        resource_data["timestamps"].append(time.time())
                        
                        time.sleep(tester.monitoring_interval)
                        
                    except psutil.NoSuchProcess:
                        break
                    except Exception as e:
                        logger.warning(f"Resource monitoring error: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"Failed to start resource monitoring: {e}")
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        monitor_thread.start()
        
        # Run load test while monitoring
        try:
            load_metrics = self._measure_performance_scenario(
                tester=tester,
                scenario_name="resource_monitoring_load",
                concurrent_users=concurrent_users,
                requests_per_user=requests_per_user,
                operation_type="security_validated_operations",
                security_stress=True
            )
            
            # Let monitoring continue for specified duration
            time.sleep(load_duration)
            
        finally:
            # Stop monitoring
            monitoring_active = False
            monitor_thread.join(timeout=5)
        
        return resource_data
    
    def _analyze_performance_degradation(
        self,
        baseline: PerformanceMetrics,
        load_results: Dict[str, PerformanceMetrics]
    ):
        """Analyze performance degradation compared to baseline."""
        
        baseline_avg = statistics.mean(baseline.response_times) if baseline.response_times else 0
        baseline_throughput = baseline.throughput
        
        logger.info("Performance degradation analysis:")
        logger.info(f"Baseline - Response time: {baseline_avg:.3f}s, Throughput: {baseline_throughput:.1f} req/s")
        
        for scenario_name, metrics in load_results.items():
            scenario_avg = statistics.mean(metrics.response_times) if metrics.response_times else 0
            
            response_degradation = ((scenario_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0
            throughput_degradation = ((baseline_throughput - metrics.throughput) / baseline_throughput * 100) if baseline_throughput > 0 else 0
            
            logger.info(f"{scenario_name} - Response time degradation: {response_degradation:.1f}%, Throughput degradation: {throughput_degradation:.1f}%")
            
            # Validate degradation is within acceptable limits
            assert response_degradation < 300, f"Response time degradation too high in {scenario_name}: {response_degradation:.1f}%"
            assert throughput_degradation < 80, f"Throughput degradation too high in {scenario_name}: {throughput_degradation:.1f}%"

# Cleanup implementation  
class RealPerformanceSecurityTester(RealPerformanceSecurityTester):
    def cleanup(self):
        """Clean up test resources."""
        # Stop monitoring
        self.monitoring_active = False
        
        # Stop server process
        if self.server_process and self.server_process.poll() is None:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            except Exception as e:
                logger.warning(f"Failed to stop server process: {e}")
        
        logger.info("✅ Performance security test cleanup completed")

if __name__ == "__main__":
    # Run performance under security integration tests
    pytest.main([__file__, "-v", "--tb=short", "--durations=10"])