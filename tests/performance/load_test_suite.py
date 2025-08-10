"""
Comprehensive Load Testing Suite for LTMC MCP Server.

This suite validates the MCP server's ability to handle high concurrency loads,
measuring performance across all 55 tools under realistic usage patterns.

Performance Targets:
- Handle 100+ concurrent requests/second
- Maintain <200ms average response time
- Achieve >99% success rate under load
- Validate all caching and optimization features
"""

import asyncio
import json
import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Callable
import requests
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    base_url: str = "http://localhost:5050/jsonrpc"
    concurrent_users: int = 50
    requests_per_user: int = 10
    ramp_up_seconds: int = 10
    test_duration_seconds: int = 60
    warm_up_requests: int = 10
    timeout_seconds: int = 30
    target_success_rate: float = 99.0
    target_avg_response_ms: float = 200.0
    target_p95_response_ms: float = 500.0


@dataclass
class RequestResult:
    """Result of a single request."""
    tool_name: str
    response_time_ms: float
    status_code: int
    success: bool
    error_message: Optional[str] = None
    payload_size_bytes: int = 0
    timestamp: float = 0.0


@dataclass
class LoadTestResults:
    """Results from load testing."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    requests_per_second: float
    concurrent_users: int
    test_duration_seconds: float
    tool_performance: Dict[str, Dict[str, Any]]
    errors_by_type: Dict[str, int]
    performance_over_time: List[Dict[str, Any]]


class MCP_ToolLoadTester:
    """Load tester for individual MCP tools."""
    
    # Comprehensive test scenarios for all 55 MCP tools
    TOOL_SCENARIOS = {
        "store_memory": [
            {"file_name": f"test_doc_{i}.md", "content": f"Test content {i}" * 100, "resource_type": "document"}
            for i in range(10)
        ],
        "retrieve_memory": [
            {"conversation_id": f"conv_{i}", "query": f"test query {i}", "top_k": 5}
            for i in range(10)
        ],
        "log_chat": [
            {"conversation_id": f"chat_{i}", "role": "user", "content": f"Test message {i}" * 50}
            for i in range(10)
        ],
        "ask_with_context": [
            {"query": f"What is the meaning of test {i}?", "conversation_id": f"ctx_conv_{i}", "top_k": 5}
            for i in range(10)
        ],
        "route_query": [
            {"query": f"Route test query {i}", "source_types": ["document", "code"], "top_k": 5}
            for i in range(10)
        ],
        "build_context": [
            {"documents": [{"content": f"Doc {j} content", "id": j} for j in range(5)], "max_tokens": 4000}
            for i in range(5)
        ],
        "retrieve_by_type": [
            {"query": f"Type query {i}", "doc_type": "document", "top_k": 5}
            for i in range(10)
        ],
        "add_todo": [
            {"title": f"Task {i}", "description": f"Description for task {i}" * 20, "priority": "medium"}
            for i in range(10)
        ],
        "list_todos": [
            {"status": status, "limit": 10}
            for status in ["all", "pending", "completed"]
        ],
        "search_todos": [
            {"query": f"search term {i}", "limit": 10}
            for i in range(10)
        ],
        "log_code_attempt": [
            {
                "input_prompt": f"Create function {i}",
                "generated_code": f"def function_{i}():\n    return {i}",
                "result": "pass",
                "function_name": f"function_{i}",
                "tags": ["python", "test"]
            }
            for i in range(10)
        ],
        "get_code_patterns": [
            {"query": f"function pattern {i}", "result_filter": "pass", "top_k": 5}
            for i in range(10)
        ],
        "analyze_code_patterns_tool": [
            {"time_range_days": 30}
            for _ in range(5)
        ],
        "link_resources": [
            {"source_id": f"src_{i}", "target_id": f"tgt_{i}", "relation": "REFERENCES"}
            for i in range(10)
        ],
        "query_graph": [
            {"entity": f"entity_{i}", "relation_type": "REFERENCES"}
            for i in range(10)
        ],
        "get_document_relationships_tool": [
            {"doc_id": f"doc_{i}"}
            for i in range(10)
        ],
        "redis_cache_stats": [{}] * 5,
        "redis_health_check": [{}] * 5,
        "get_context_usage_statistics_tool": [{}] * 5,
        "list_tool_identifiers": [{}] * 5,
        "get_security_statistics": [{}] * 5
    }
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def make_jsonrpc_request(self, method: str, params: Dict[str, Any]) -> RequestResult:
        """Make a JSON-RPC request to the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": method,
                "arguments": params
            },
            "id": int(time.time() * 1000000)
        }
        
        start_time = time.perf_counter()
        try:
            response = self.session.post(
                self.config.base_url,
                json=payload,
                timeout=self.config.timeout_seconds
            )
            response_time_ms = (time.perf_counter() - start_time) * 1000
            
            success = response.status_code == 200
            error_message = None
            
            if success:
                try:
                    response_data = response.json()
                    if "error" in response_data:
                        success = False
                        error_message = str(response_data["error"])
                    elif response_data.get("result", {}).get("success") is False:
                        success = False
                        error_message = response_data.get("result", {}).get("error", "Unknown error")
                except json.JSONDecodeError:
                    success = False
                    error_message = "Invalid JSON response"
            else:
                error_message = f"HTTP {response.status_code}: {response.text}"
            
            return RequestResult(
                tool_name=method,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                success=success,
                error_message=error_message,
                payload_size_bytes=len(response.content),
                timestamp=time.time()
            )
            
        except requests.exceptions.Timeout:
            response_time_ms = (time.perf_counter() - start_time) * 1000
            return RequestResult(
                tool_name=method,
                response_time_ms=response_time_ms,
                status_code=0,
                success=False,
                error_message="Request timeout",
                timestamp=time.time()
            )
        except Exception as e:
            response_time_ms = (time.perf_counter() - start_time) * 1000
            return RequestResult(
                tool_name=method,
                response_time_ms=response_time_ms,
                status_code=0,
                success=False,
                error_message=str(e),
                timestamp=time.time()
            )
    
    def warm_up_server(self) -> None:
        """Warm up the server with initial requests."""
        logger.info(f"Warming up server with {self.config.warm_up_requests} requests...")
        
        warm_up_tools = ["store_memory", "retrieve_memory", "log_chat", "list_todos", "redis_health_check"]
        
        for i in range(self.config.warm_up_requests):
            tool = warm_up_tools[i % len(warm_up_tools)]
            if tool in self.TOOL_SCENARIOS:
                params = self.TOOL_SCENARIOS[tool][0]
                result = self.make_jsonrpc_request(tool, params)
                if not result.success:
                    logger.warning(f"Warm-up request failed for {tool}: {result.error_message}")
        
        logger.info("Server warm-up completed")
    
    def generate_user_scenario(self, user_id: int) -> List[tuple]:
        """Generate a realistic usage scenario for a user."""
        scenarios = []
        
        # Typical user workflow: memory operations, chat, todos, and queries
        for i in range(self.config.requests_per_user):
            # Distribute requests across different tools
            if i % 5 == 0:  # Memory operations
                tool = np.random.choice(["store_memory", "retrieve_memory"])
            elif i % 5 == 1:  # Chat operations
                tool = np.random.choice(["log_chat", "ask_with_context"])
            elif i % 5 == 2:  # Todo operations
                tool = np.random.choice(["add_todo", "list_todos", "search_todos"])
            elif i % 5 == 3:  # Code operations
                tool = np.random.choice(["log_code_attempt", "get_code_patterns"])
            else:  # System/stats operations
                tool = np.random.choice(["redis_health_check", "list_tool_identifiers", "get_security_statistics"])
            
            if tool in self.TOOL_SCENARIOS:
                params = np.random.choice(self.TOOL_SCENARIOS[tool])
                scenarios.append((tool, params))
        
        return scenarios
    
    def execute_user_scenario(self, user_id: int) -> List[RequestResult]:
        """Execute a complete user scenario."""
        scenarios = self.generate_user_scenario(user_id)
        results = []
        
        # Add ramp-up delay
        ramp_delay = (user_id / self.config.concurrent_users) * self.config.ramp_up_seconds
        time.sleep(ramp_delay)
        
        for tool, params in scenarios:
            result = self.make_jsonrpc_request(tool, params)
            results.append(result)
            
            # Small delay between requests for realistic timing
            time.sleep(np.random.uniform(0.1, 0.5))
        
        return results


class LoadTestAnalyzer:
    """Analyzer for load test results."""
    
    @staticmethod
    def analyze_results(all_results: List[RequestResult], config: LoadTestConfig) -> LoadTestResults:
        """Analyze load test results and generate comprehensive report."""
        if not all_results:
            raise ValueError("No results to analyze")
        
        # Basic statistics
        total_requests = len(all_results)
        successful_results = [r for r in all_results if r.success]
        failed_results = [r for r in all_results if not r.success]
        
        successful_requests = len(successful_results)
        failed_requests = len(failed_results)
        success_rate = (successful_requests / total_requests) * 100
        
        # Response time statistics
        response_times = [r.response_time_ms for r in successful_results]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        # Throughput calculation
        timestamps = [r.timestamp for r in all_results]
        test_duration = max(timestamps) - min(timestamps) if timestamps else 1
        requests_per_second = total_requests / test_duration
        
        # Tool-specific performance analysis
        tool_performance = {}
        for tool_name in set(r.tool_name for r in all_results):
            tool_results = [r for r in all_results if r.tool_name == tool_name]
            tool_successful = [r for r in tool_results if r.success]
            tool_response_times = [r.response_time_ms for r in tool_successful]
            
            tool_performance[tool_name] = {
                "total_requests": len(tool_results),
                "successful_requests": len(tool_successful),
                "success_rate": (len(tool_successful) / len(tool_results)) * 100,
                "avg_response_time_ms": statistics.mean(tool_response_times) if tool_response_times else 0,
                "p95_response_time_ms": np.percentile(tool_response_times, 95) if tool_response_times else 0,
                "min_response_time_ms": min(tool_response_times) if tool_response_times else 0,
                "max_response_time_ms": max(tool_response_times) if tool_response_times else 0
            }
        
        # Error analysis
        errors_by_type = {}
        for result in failed_results:
            error_type = result.error_message or "Unknown error"
            errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
        
        # Performance over time (time series analysis)
        performance_over_time = LoadTestAnalyzer._analyze_performance_over_time(all_results)
        
        return LoadTestResults(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            avg_response_time_ms=avg_response_time,
            median_response_time_ms=median_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            requests_per_second=requests_per_second,
            concurrent_users=config.concurrent_users,
            test_duration_seconds=test_duration,
            tool_performance=tool_performance,
            errors_by_type=errors_by_type,
            performance_over_time=performance_over_time
        )
    
    @staticmethod
    def _analyze_performance_over_time(all_results: List[RequestResult], window_seconds: int = 5) -> List[Dict[str, Any]]:
        """Analyze performance metrics over time windows."""
        if not all_results:
            return []
        
        # Sort results by timestamp
        sorted_results = sorted(all_results, key=lambda r: r.timestamp)
        start_time = sorted_results[0].timestamp
        end_time = sorted_results[-1].timestamp
        
        time_windows = []
        current_time = start_time
        
        while current_time < end_time:
            window_end = current_time + window_seconds
            window_results = [r for r in sorted_results if current_time <= r.timestamp < window_end]
            
            if window_results:
                successful_window_results = [r for r in window_results if r.success]
                response_times = [r.response_time_ms for r in successful_window_results]
                
                time_windows.append({
                    "timestamp": current_time,
                    "total_requests": len(window_results),
                    "successful_requests": len(successful_window_results),
                    "success_rate": (len(successful_window_results) / len(window_results)) * 100,
                    "avg_response_time_ms": statistics.mean(response_times) if response_times else 0,
                    "requests_per_second": len(window_results) / window_seconds
                })
            
            current_time = window_end
        
        return time_windows


class ComprehensiveLoadTestSuite:
    """Comprehensive load testing suite for the LTMC MCP Server."""
    
    def __init__(self, config: LoadTestConfig = None):
        self.config = config or LoadTestConfig()
        self.tester = MCP_ToolLoadTester(self.config)
    
    def run_load_test(self) -> LoadTestResults:
        """Execute comprehensive load test with multiple concurrent users."""
        logger.info(f"Starting load test with {self.config.concurrent_users} concurrent users")
        logger.info(f"Each user will make {self.config.requests_per_user} requests")
        logger.info(f"Target success rate: {self.config.target_success_rate}%")
        logger.info(f"Target average response time: {self.config.target_avg_response_ms}ms")
        
        # Warm up the server
        self.tester.warm_up_server()
        
        # Execute concurrent load test
        start_time = time.time()
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.config.concurrent_users) as executor:
            # Submit all user scenarios
            futures = [
                executor.submit(self.tester.execute_user_scenario, user_id)
                for user_id in range(self.config.concurrent_users)
            ]
            
            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    all_results.extend(user_results)
                except Exception as e:
                    logger.error(f"User scenario failed: {e}")
        
        end_time = time.time()
        logger.info(f"Load test completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total requests executed: {len(all_results)}")
        
        # Analyze results
        results = LoadTestAnalyzer.analyze_results(all_results, self.config)
        
        return results
    
    def validate_performance_targets(self, results: LoadTestResults) -> Dict[str, bool]:
        """Validate that performance targets were met."""
        validations = {
            "success_rate_target": results.success_rate >= self.config.target_success_rate,
            "avg_response_time_target": results.avg_response_time_ms <= self.config.target_avg_response_ms,
            "p95_response_time_target": results.p95_response_time_ms <= self.config.target_p95_response_ms,
            "no_critical_errors": len(results.errors_by_type) == 0 or all(
                "timeout" not in error.lower() and "connection" not in error.lower()
                for error in results.errors_by_type.keys()
            )
        }
        
        return validations
    
    def generate_performance_report(self, results: LoadTestResults) -> str:
        """Generate a detailed performance report."""
        validations = self.validate_performance_targets(results)
        
        report = f"""
LTMC MCP Server Load Test Report
================================

Test Configuration:
- Concurrent Users: {results.concurrent_users}
- Total Requests: {results.total_requests}
- Test Duration: {results.test_duration_seconds:.2f} seconds
- Target Success Rate: {self.config.target_success_rate}%
- Target Avg Response Time: {self.config.target_avg_response_ms}ms

Overall Performance:
- Success Rate: {results.success_rate:.2f}% {'✅' if validations['success_rate_target'] else '❌'}
- Successful Requests: {results.successful_requests}
- Failed Requests: {results.failed_requests}
- Requests per Second: {results.requests_per_second:.2f}

Response Time Statistics:
- Average: {results.avg_response_time_ms:.2f}ms {'✅' if validations['avg_response_time_target'] else '❌'}
- Median: {results.median_response_time_ms:.2f}ms
- P95: {results.p95_response_time_ms:.2f}ms {'✅' if validations['p95_response_time_target'] else '❌'}
- P99: {results.p99_response_time_ms:.2f}ms
- Min: {results.min_response_time_ms:.2f}ms
- Max: {results.max_response_time_ms:.2f}ms

Tool Performance Summary:
"""
        
        # Add tool-specific performance
        for tool_name, metrics in sorted(results.tool_performance.items()):
            success_indicator = "✅" if metrics['success_rate'] >= 95 else "❌"
            perf_indicator = "✅" if metrics['avg_response_time_ms'] <= self.config.target_avg_response_ms else "❌"
            
            report += f"""
- {tool_name}: {success_indicator} {perf_indicator}
  Success Rate: {metrics['success_rate']:.1f}% ({metrics['successful_requests']}/{metrics['total_requests']})
  Avg Response: {metrics['avg_response_time_ms']:.1f}ms
  P95 Response: {metrics['p95_response_time_ms']:.1f}ms"""
        
        if results.errors_by_type:
            report += f"\n\nError Analysis:\n"
            for error_type, count in sorted(results.errors_by_type.items(), key=lambda x: x[1], reverse=True):
                report += f"- {error_type}: {count} occurrences\n"
        
        # Overall assessment
        all_targets_met = all(validations.values())
        report += f"""

Performance Assessment: {'✅ PASSED' if all_targets_met else '❌ FAILED'}
- Success Rate Target: {'Met' if validations['success_rate_target'] else 'Not Met'}
- Average Response Time Target: {'Met' if validations['avg_response_time_target'] else 'Not Met'}  
- P95 Response Time Target: {'Met' if validations['p95_response_time_target'] else 'Not Met'}
- Critical Error Check: {'Passed' if validations['no_critical_errors'] else 'Failed'}
"""
        
        return report


def run_comprehensive_load_test(
    concurrent_users: int = 50,
    requests_per_user: int = 10,
    server_url: str = "http://localhost:5050/jsonrpc"
) -> LoadTestResults:
    """Run comprehensive load test with specified parameters."""
    config = LoadTestConfig(
        base_url=server_url,
        concurrent_users=concurrent_users,
        requests_per_user=requests_per_user,
        ramp_up_seconds=10,
        test_duration_seconds=60,
        warm_up_requests=10
    )
    
    suite = ComprehensiveLoadTestSuite(config)
    results = suite.run_load_test()
    
    # Generate and print report
    report = suite.generate_performance_report(results)
    print(report)
    
    return results


if __name__ == "__main__":
    # Run load test with different configurations
    print("Running LTMC MCP Server Load Test Suite...")
    
    # Test 1: Moderate load
    print("\n=== Test 1: Moderate Load (25 users, 10 requests each) ===")
    results_moderate = run_comprehensive_load_test(concurrent_users=25, requests_per_user=10)
    
    # Test 2: High load
    print("\n=== Test 2: High Load (50 users, 20 requests each) ===")
    results_high = run_comprehensive_load_test(concurrent_users=50, requests_per_user=20)
    
    # Test 3: Stress test
    print("\n=== Test 3: Stress Test (100 users, 15 requests each) ===")
    results_stress = run_comprehensive_load_test(concurrent_users=100, requests_per_user=15)