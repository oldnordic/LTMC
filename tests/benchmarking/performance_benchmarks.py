#!/usr/bin/env python3
"""Performance benchmarking framework for LTMC MCP tools.

This module provides comprehensive performance testing and benchmarking
capabilities for all 28 LTMC tools across both HTTP and stdio transports.
"""

import asyncio
import time
import statistics
import json
import sys
import uuid
import aiohttp
import psutil
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import concurrent.futures
import threading


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class BenchmarkResult:
    """Single benchmark test result."""
    tool_name: str
    transport: str
    success: bool
    duration: float
    memory_usage: int = 0
    cpu_usage: float = 0.0
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass 
class ThroughputResult:
    """Throughput benchmark results."""
    tool_name: str
    transport: str
    duration: float
    total_requests: int
    success_count: int
    error_count: int
    requests_per_second: float
    success_rate: float
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    response_times: List[float] = field(default_factory=list)


@dataclass
class LoadTestResult:
    """Load testing results."""
    test_name: str
    concurrent_users: int
    duration: float
    successful_sessions: int
    failed_sessions: int
    success_rate: float
    avg_session_duration: float
    p95_session_duration: float
    total_requests: int
    requests_per_second: float
    errors: List[str] = field(default_factory=list)


@dataclass
class StabilityResult:
    """Long-running stability test results."""
    test_duration: float
    total_samples: int
    success_count: int
    error_count: int
    success_rate: float
    avg_response_time: float
    memory_leak_detected: bool
    performance_degradation: bool
    resource_samples: List[Dict[str, Any]] = field(default_factory=list)


class PerformanceBenchmark:
    """Comprehensive performance benchmarking for LTMC tools."""
    
    def __init__(self, http_url: str = "http://localhost:5050", server_path: str = None):
        self.http_url = http_url
        self.server_path = server_path or str(project_root / "ltmc_mcp_server.py")
        self.benchmark_results: List[BenchmarkResult] = []
    
    def get_test_params(self, tool_name: str) -> Dict[str, Any]:
        """Get optimized test parameters for benchmarking."""
        test_id = str(uuid.uuid4())[:8]
        
        # Lightweight parameters for performance testing
        params = {
            "store_memory": {
                "file_name": f"bench_{test_id}.md",
                "content": f"Benchmark content {test_id}",
                "resource_type": "document"
            },
            "retrieve_memory": {
                "query": "benchmark test",
                "conversation_id": f"bench_{test_id}",
                "top_k": 3
            },
            "log_chat": {
                "content": f"Benchmark chat {test_id}",
                "conversation_id": f"bench_{test_id}",
                "role": "user"
            },
            "redis_health_check": {},
            "list_tool_identifiers": {},
            "add_todo": {
                "title": f"Benchmark todo {test_id}",
                "description": "Benchmark test todo",
                "priority": "low"
            },
            "ask_with_context": {
                "query": f"benchmark query {test_id}",
                "conversation_id": f"bench_{test_id}",
                "top_k": 3
            }
        }
        
        return params.get(tool_name, {})
    
    async def benchmark_single_tool_http(self, tool_name: str, iterations: int = 100) -> ThroughputResult:
        """Benchmark single tool performance via HTTP transport."""
        print(f"🚀 Benchmarking {tool_name} via HTTP ({iterations} iterations)...")
        
        results = []
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(iterations):
                task = self._execute_http_request(session, tool_name)
                tasks.append(task)
            
            # Execute all requests concurrently (with some limit)
            semaphore = asyncio.Semaphore(20)  # Limit concurrent requests
            
            async def limited_request(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(*[limited_request(task) for task in tasks])
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        response_times = [r.duration for r in successful_results]
        
        return ThroughputResult(
            tool_name=tool_name,
            transport="http",
            duration=total_duration,
            total_requests=len(results),
            success_count=len(successful_results),
            error_count=len(failed_results),
            requests_per_second=len(results) / total_duration,
            success_rate=len(successful_results) / len(results) if results else 0,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            p50_response_time=statistics.median(response_times) if response_times else 0,
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
            p99_response_time=statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0,
            response_times=response_times
        )
    
    async def _execute_http_request(self, session: aiohttp.ClientSession, tool_name: str) -> BenchmarkResult:
        """Execute single HTTP request with timing."""
        start_time = time.time()
        params = self.get_test_params(tool_name)
        
        try:
            async with session.post(
                f"{self.http_url}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": params},
                    "id": 1
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                duration = time.time() - start_time
                
                return BenchmarkResult(
                    tool_name=tool_name,
                    transport="http",
                    success=result.get("error") is None,
                    duration=duration,
                    error=str(result.get("error")) if result.get("error") else None
                )
                
        except Exception as e:
            return BenchmarkResult(
                tool_name=tool_name,
                transport="http",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            )
    
    async def benchmark_single_tool_stdio(self, tool_name: str, iterations: int = 50) -> ThroughputResult:
        """Benchmark single tool performance via stdio transport."""
        print(f"🚀 Benchmarking {tool_name} via stdio ({iterations} iterations)...")
        
        results = []
        start_time = time.time()
        
        # Stdio benchmarking with sequential execution (avoiding process overhead)
        for i in range(iterations):
            result = await self._execute_stdio_request(tool_name)
            results.append(result)
            
            # Small delay to prevent overwhelming the system
            await asyncio.sleep(0.01)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        response_times = [r.duration for r in successful_results]
        
        return ThroughputResult(
            tool_name=tool_name,
            transport="stdio",
            duration=total_duration,
            total_requests=len(results),
            success_count=len(successful_results),
            error_count=len(failed_results),
            requests_per_second=len(results) / total_duration,
            success_rate=len(successful_results) / len(results) if results else 0,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            p50_response_time=statistics.median(response_times) if response_times else 0,
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
            p99_response_time=statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0,
            response_times=response_times
        )
    
    async def _execute_stdio_request(self, tool_name: str) -> BenchmarkResult:
        """Execute single stdio request with timing."""
        start_time = time.time()
        params = self.get_test_params(tool_name)
        process = None
        
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, self.server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call", 
                "params": {"name": tool_name, "arguments": params},
                "id": 1
            }
            
            request_bytes = json.dumps(request).encode() + b'\n'
            process.stdin.write(request_bytes)
            await process.stdin.drain()
            
            # Read response with timeout
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=15.0
            )
            
            duration = time.time() - start_time
            result = json.loads(response_line.decode().strip())
            
            return BenchmarkResult(
                tool_name=tool_name,
                transport="stdio",
                success=result.get("error") is None,
                duration=duration,
                error=str(result.get("error")) if result.get("error") else None
            )
            
        except asyncio.TimeoutError:
            return BenchmarkResult(
                tool_name=tool_name,
                transport="stdio", 
                success=False,
                duration=time.time() - start_time,
                error="STDIO_TIMEOUT"
            )
        except Exception as e:
            return BenchmarkResult(
                tool_name=tool_name,
                transport="stdio",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            )
        finally:
            if process:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=3.0)
                except:
                    process.kill()
                    await process.wait()
    
    async def run_load_test(self, concurrent_users: int = 25, duration_seconds: int = 60) -> LoadTestResult:
        """Run load test with concurrent user simulation."""
        print(f"⚡ Running load test: {concurrent_users} concurrent users for {duration_seconds}s...")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # Define user session workflow
        session_tools = ["store_memory", "retrieve_memory", "log_chat", "ask_with_context"]
        
        async def simulate_user_session(user_id: int) -> Dict[str, Any]:
            """Simulate realistic user session."""
            session_start = time.time()
            session_id = f"load_test_user_{user_id}"
            
            operations = []
            session_errors = []
            
            while time.time() < end_time:
                # Execute typical workflow
                for tool_name in session_tools:
                    try:
                        # Customize params for user session
                        params = self.get_test_params(tool_name)
                        if "conversation_id" in params:
                            params["conversation_id"] = session_id
                        
                        # Execute via HTTP (more reliable for load testing)
                        async with aiohttp.ClientSession() as session:
                            result = await self._execute_http_request(session, tool_name)
                            operations.append(result)
                            
                            if not result.success:
                                session_errors.append(f"{tool_name}: {result.error}")
                    
                    except Exception as e:
                        session_errors.append(f"{tool_name}: {str(e)}")
                    
                    # Brief pause between operations
                    await asyncio.sleep(0.1)
                
                # Pause between workflow cycles
                await asyncio.sleep(1.0)
            
            session_duration = time.time() - session_start
            successful_ops = sum(1 for op in operations if op.success)
            
            return {
                "user_id": user_id,
                "session_duration": session_duration,
                "total_operations": len(operations),
                "successful_operations": successful_ops,
                "success_rate": successful_ops / len(operations) if operations else 0,
                "errors": session_errors
            }
        
        # Run concurrent user sessions
        tasks = [simulate_user_session(i) for i in range(concurrent_users)]
        session_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_sessions = [r for r in session_results if not isinstance(r, Exception)]
        failed_sessions = [r for r in session_results if isinstance(r, Exception)]
        
        total_duration = time.time() - start_time
        
        # Calculate metrics
        if successful_sessions:
            total_operations = sum(s["total_operations"] for s in successful_sessions)
            session_durations = [s["session_duration"] for s in successful_sessions]
            all_errors = []
            for s in successful_sessions:
                all_errors.extend(s["errors"])
        else:
            total_operations = 0
            session_durations = [0]
            all_errors = []
        
        return LoadTestResult(
            test_name=f"load_test_{concurrent_users}_users",
            concurrent_users=concurrent_users,
            duration=total_duration,
            successful_sessions=len(successful_sessions),
            failed_sessions=len(failed_sessions),
            success_rate=len(successful_sessions) / concurrent_users,
            avg_session_duration=statistics.mean(session_durations) if session_durations else 0,
            p95_session_duration=statistics.quantiles(session_durations, n=20)[18] if len(session_durations) > 20 else 0,
            total_requests=total_operations,
            requests_per_second=total_operations / total_duration if total_duration > 0 else 0,
            errors=all_errors[:50]  # Limit error list size
        )
    
    async def run_stability_test(self, duration_hours: float = 1.0, sample_interval: int = 60) -> StabilityResult:
        """Run long-term stability test."""
        test_duration_seconds = duration_hours * 3600
        print(f"🕒 Running stability test for {duration_hours} hours...")
        
        start_time = time.time()
        end_time = start_time + test_duration_seconds
        
        samples = []
        initial_memory = psutil.virtual_memory().used
        
        # Critical tools for stability testing
        stability_tools = ["store_memory", "retrieve_memory", "log_chat", "redis_health_check"]
        
        while time.time() < end_time:
            sample_start = time.time()
            
            # Test all critical tools
            for tool_name in stability_tools:
                try:
                    async with aiohttp.ClientSession() as session:
                        result = await self._execute_http_request(session, tool_name)
                        
                        # Record sample
                        samples.append({
                            "timestamp": time.time(),
                            "tool_name": tool_name,
                            "success": result.success,
                            "duration": result.duration,
                            "memory_usage": psutil.virtual_memory().used,
                            "error": result.error
                        })
                
                except Exception as e:
                    samples.append({
                        "timestamp": time.time(),
                        "tool_name": tool_name,
                        "success": False,
                        "duration": 0.0,
                        "memory_usage": psutil.virtual_memory().used,
                        "error": str(e)
                    })
            
            # Wait for next sample interval
            sample_duration = time.time() - sample_start
            sleep_time = max(0, sample_interval - sample_duration)
            await asyncio.sleep(sleep_time)
        
        total_duration = time.time() - start_time
        
        # Analyze stability
        successful_samples = [s for s in samples if s["success"]]
        failed_samples = [s for s in samples if not s["success"]]
        
        # Memory leak detection
        memory_samples = [s["memory_usage"] for s in samples]
        memory_trend = self._calculate_memory_trend(memory_samples)
        memory_leak_detected = memory_trend > 0.1  # 10% increase indicates potential leak
        
        # Performance degradation detection
        response_times = [s["duration"] for s in successful_samples]
        performance_degradation = self._detect_performance_degradation(response_times)
        
        return StabilityResult(
            test_duration=total_duration,
            total_samples=len(samples),
            success_count=len(successful_samples),
            error_count=len(failed_samples),
            success_rate=len(successful_samples) / len(samples) if samples else 0,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            memory_leak_detected=memory_leak_detected,
            performance_degradation=performance_degradation,
            resource_samples=samples[-100:]  # Keep last 100 samples for analysis
        )
    
    def _calculate_memory_trend(self, memory_samples: List[int]) -> float:
        """Calculate memory usage trend (linear regression slope)."""
        if len(memory_samples) < 10:
            return 0.0
        
        n = len(memory_samples)
        x_values = list(range(n))
        
        # Simple linear regression
        sum_x = sum(x_values)
        sum_y = sum(memory_samples)
        sum_xy = sum(x * y for x, y in zip(x_values, memory_samples))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Normalize slope by initial memory value
        initial_memory = memory_samples[0]
        return slope / initial_memory if initial_memory > 0 else 0.0
    
    def _detect_performance_degradation(self, response_times: List[float]) -> bool:
        """Detect if performance is degrading over time."""
        if len(response_times) < 100:
            return False
        
        # Compare first quarter vs last quarter
        quarter_size = len(response_times) // 4
        first_quarter = response_times[:quarter_size]
        last_quarter = response_times[-quarter_size:]
        
        first_avg = statistics.mean(first_quarter)
        last_avg = statistics.mean(last_quarter)
        
        # Degradation if last quarter is 50% slower than first
        return last_avg > first_avg * 1.5
    
    def generate_benchmark_report(self, results: List[ThroughputResult]) -> str:
        """Generate comprehensive benchmark report."""
        report = ["🚀 LTMC PERFORMANCE BENCHMARK REPORT", "=" * 60, ""]
        
        # Summary statistics
        http_results = [r for r in results if r.transport == "http"]
        stdio_results = [r for r in results if r.transport == "stdio"]
        
        report.extend([
            f"📊 SUMMARY:",
            f"  Total Tools Benchmarked: {len(set(r.tool_name for r in results))}",
            f"  HTTP Transport Tests: {len(http_results)}",
            f"  Stdio Transport Tests: {len(stdio_results)}",
            ""
        ])
        
        # Performance comparison
        if http_results and stdio_results:
            http_avg_rps = statistics.mean(r.requests_per_second for r in http_results)
            stdio_avg_rps = statistics.mean(r.requests_per_second for r in stdio_results)
            
            report.extend([
                f"🏎️  TRANSPORT PERFORMANCE COMPARISON:",
                f"  HTTP Average RPS: {http_avg_rps:.1f}",
                f"  Stdio Average RPS: {stdio_avg_rps:.1f}",
                f"  Performance Ratio: {http_avg_rps/stdio_avg_rps:.2f}x" if stdio_avg_rps > 0 else "  Stdio failed",
                ""
            ])
        
        # Tool-by-tool analysis
        report.append("🛠️  DETAILED RESULTS BY TOOL:")
        report.append("-" * 40)
        
        tools = set(r.tool_name for r in results)
        for tool_name in sorted(tools):
            tool_results = [r for r in results if r.tool_name == tool_name]
            
            report.append(f"\n{tool_name}:")
            
            for result in tool_results:
                status = "✅" if result.success_rate > 0.95 else "⚠️" if result.success_rate > 0.8 else "❌"
                
                report.extend([
                    f"  {result.transport.upper()}: {status} {result.success_rate*100:.1f}% success",
                    f"    RPS: {result.requests_per_second:.1f}",
                    f"    Avg Response: {result.avg_response_time*1000:.0f}ms",
                    f"    P95 Response: {result.p95_response_time*1000:.0f}ms"
                ])
        
        return "\n".join(report)


async def run_comprehensive_benchmarks():
    """Run comprehensive performance benchmarks for LTMC."""
    print("🚀 Starting Comprehensive LTMC Performance Benchmarks")
    print("=" * 60)
    
    benchmark = PerformanceBenchmark()
    
    # Critical tools for benchmarking
    critical_tools = [
        "store_memory", "retrieve_memory", "log_chat", 
        "redis_health_check", "list_tool_identifiers", "ask_with_context"
    ]
    
    all_results = []
    
    print(f"📊 Benchmarking {len(critical_tools)} critical tools...")
    
    # HTTP Transport Benchmarks
    print("\n🌐 HTTP Transport Benchmarks:")
    for tool_name in critical_tools:
        try:
            result = await benchmark.benchmark_single_tool_http(tool_name, iterations=50)
            all_results.append(result)
            
            status = "✅" if result.success_rate > 0.95 else "⚠️" if result.success_rate > 0.8 else "❌"
            print(f"  {tool_name}: {status} {result.success_rate*100:.1f}% ({result.requests_per_second:.1f} RPS)")
            
        except Exception as e:
            print(f"  {tool_name}: ❌ Benchmark failed: {e}")
    
    # Stdio Transport Benchmarks  
    print("\n🖥️  Stdio Transport Benchmarks:")
    for tool_name in critical_tools:
        try:
            result = await benchmark.benchmark_single_tool_stdio(tool_name, iterations=20)
            all_results.append(result)
            
            status = "✅" if result.success_rate > 0.90 else "⚠️" if result.success_rate > 0.7 else "❌"
            print(f"  {tool_name}: {status} {result.success_rate*100:.1f}% ({result.requests_per_second:.1f} RPS)")
            
        except Exception as e:
            print(f"  {tool_name}: ❌ Benchmark failed: {e}")
    
    # Load Testing
    print("\n⚡ Load Testing:")
    try:
        load_result = await benchmark.run_load_test(concurrent_users=10, duration_seconds=30)
        status = "✅" if load_result.success_rate > 0.90 else "⚠️" if load_result.success_rate > 0.7 else "❌"
        print(f"  10 Users/30s: {status} {load_result.success_rate*100:.1f}% success")
        print(f"    Total Requests: {load_result.total_requests}")
        print(f"    RPS: {load_result.requests_per_second:.1f}")
        
    except Exception as e:
        print(f"  Load Test: ❌ Failed: {e}")
    
    # Generate and display comprehensive report
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE BENCHMARK REPORT")
    print("=" * 60)
    
    report = benchmark.generate_benchmark_report(all_results)
    print(report)
    
    # Save detailed results
    results_path = project_root / "benchmark_results" / f"performance_benchmark_{int(time.time())}.json"
    results_path.parent.mkdir(exist_ok=True)
    
    # Convert results to JSON-serializable format
    results_data = {
        "timestamp": time.time(),
        "throughput_results": [
            {
                "tool_name": r.tool_name,
                "transport": r.transport,
                "requests_per_second": r.requests_per_second,
                "success_rate": r.success_rate,
                "avg_response_time": r.avg_response_time,
                "p95_response_time": r.p95_response_time,
                "total_requests": r.total_requests
            }
            for r in all_results
        ]
    }
    
    with open(results_path, "w") as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_path}")
    print("🎯 Use these metrics to optimize LTMC performance!")


if __name__ == "__main__":
    """Run comprehensive benchmarks when executed directly."""
    asyncio.run(run_comprehensive_benchmarks())