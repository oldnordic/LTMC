#!/usr/bin/env python3
"""Advanced stdio timeout debugging framework for LTMC MCP server.

This module provides comprehensive debugging tools for diagnosing and fixing
stdio transport timeout issues across all 28 LTMC tools.
"""

import asyncio
import json
import sys
import time
import psutil
import cProfile
import pstats
import io
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import traceback
import threading


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class TimeoutDiagnosis:
    """Comprehensive timeout diagnosis for stdio transport."""
    tool_name: str
    startup_time: float = 0.0
    db_connection_time: float = 0.0  
    execution_time: float = 0.0
    serialization_time: float = 0.0
    cleanup_time: float = 0.0
    total_time: float = 0.0
    memory_usage: int = 0
    cpu_usage: float = 0.0
    file_descriptors: int = 0
    timeout_phase: Optional[str] = None
    error_details: Optional[str] = None
    stderr_output: Optional[str] = None
    performance_profile: Optional[Dict[str, Any]] = None


@dataclass
class ResourceUsage:
    """System resource usage during tool execution."""
    tool_name: str
    duration: float
    memory_delta: int
    cpu_usage: float
    file_descriptors: int
    peak_memory: int
    io_operations: Dict[str, int] = field(default_factory=dict)


@dataclass 
class PerformanceProfile:
    """Performance profiling results for stdio tool execution."""
    tool_name: str
    total_time: float
    function_stats: Dict[str, Dict[str, Any]]
    bottlenecks: List[Dict[str, Any]]
    call_graph: Optional[str] = None


class StdioTimeoutDebugger:
    """Comprehensive stdio timeout debugging and diagnosis."""
    
    TIMEOUT_CATEGORIES = {
        "STARTUP_TIMEOUT": "Process fails to start within 5s",
        "REQUEST_TIMEOUT": "Request write fails within 2s", 
        "PROCESSING_TIMEOUT": "Tool processing exceeds 10s",
        "RESPONSE_TIMEOUT": "Response read fails within 5s",
        "CLEANUP_TIMEOUT": "Process shutdown exceeds 3s"
    }
    
    def __init__(self, server_path: str = None, debug_mode: bool = True):
        self.server_path = server_path or str(project_root / "ltmc_mcp_server.py")
        self.debug_mode = debug_mode
        self.diagnosis_results: Dict[str, TimeoutDiagnosis] = {}
    
    async def diagnose_timeout(self, tool_name: str, params: Dict[str, Any] = None) -> TimeoutDiagnosis:
        """Comprehensive timeout diagnosis for specific tool."""
        diagnosis = TimeoutDiagnosis(tool_name=tool_name)
        
        if params is None:
            params = self._get_default_params(tool_name)
        
        print(f"🔍 Diagnosing stdio timeout for {tool_name}...")
        
        # Phase 1: Startup diagnosis
        startup_result = await self._diagnose_startup()
        diagnosis.startup_time = startup_result["duration"]
        
        # Phase 2: Full execution diagnosis with profiling
        execution_result = await self._diagnose_full_execution(tool_name, params)
        diagnosis.execution_time = execution_result["duration"] 
        diagnosis.timeout_phase = execution_result.get("timeout_phase")
        diagnosis.error_details = execution_result.get("error")
        diagnosis.stderr_output = execution_result.get("stderr")
        
        # Phase 3: Resource usage diagnosis
        resource_result = await self._diagnose_resource_usage(tool_name, params)
        diagnosis.memory_usage = resource_result.memory_delta
        diagnosis.cpu_usage = resource_result.cpu_usage
        diagnosis.file_descriptors = resource_result.file_descriptors
        
        # Phase 4: Performance profiling (if enabled)
        if self.debug_mode:
            profile_result = await self._profile_tool_execution(tool_name, params)
            if profile_result:
                diagnosis.performance_profile = profile_result.function_stats
        
        diagnosis.total_time = diagnosis.startup_time + diagnosis.execution_time
        
        # Store diagnosis for analysis
        self.diagnosis_results[tool_name] = diagnosis
        
        return diagnosis
    
    async def _diagnose_startup(self) -> Dict[str, Any]:
        """Measure and diagnose stdio server startup performance."""
        startup_times = []
        
        # Test startup multiple times to get reliable metrics
        for i in range(5):
            start_time = time.time()
            process = None
            
            try:
                process = await asyncio.create_subprocess_exec(
                    sys.executable, self.server_path,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE, 
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Wait for process to be ready (send simple request)
                request = {
                    "jsonrpc": "2.0",
                    "method": "tools/call", 
                    "params": {"name": "redis_health_check", "arguments": {}},
                    "id": 1
                }
                
                request_bytes = json.dumps(request).encode() + b'\n'
                process.stdin.write(request_bytes)
                await process.stdin.drain()
                
                # Read response to confirm startup complete
                await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
                
                startup_duration = time.time() - start_time
                startup_times.append(startup_duration)
                
            except Exception as e:
                startup_times.append(float('inf'))  # Mark failed startup
                
            finally:
                if process:
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=3.0)
                    except:
                        process.kill()
                        await process.wait()
        
        # Analyze startup times
        valid_times = [t for t in startup_times if t != float('inf')]
        
        return {
            "duration": min(valid_times) if valid_times else float('inf'),
            "avg_duration": sum(valid_times) / len(valid_times) if valid_times else float('inf'),
            "success_rate": len(valid_times) / len(startup_times),
            "attempts": len(startup_times)
        }
    
    async def _diagnose_full_execution(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose full tool execution with detailed phase timing."""
        process = None
        start_time = time.time()
        phase_timings = {}
        
        try:
            # Phase 1: Process startup
            phase_start = time.time()
            process = await asyncio.create_subprocess_exec(
                sys.executable, self.server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            phase_timings["startup"] = time.time() - phase_start
            
            # Phase 2: Request preparation and sending  
            phase_start = time.time()
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": params},
                "id": 1
            }
            
            request_bytes = json.dumps(request).encode() + b'\n'
            process.stdin.write(request_bytes)
            await process.stdin.drain()
            phase_timings["request_send"] = time.time() - phase_start
            
            # Phase 3: Response waiting with detailed timeout tracking
            phase_start = time.time()
            
            # Use longer timeout for complex operations
            timeout_seconds = self._get_tool_timeout(tool_name)
            
            try:
                response_line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=timeout_seconds
                )
                phase_timings["response_wait"] = time.time() - phase_start
                
                # Phase 4: Response parsing
                phase_start = time.time() 
                response_data = json.loads(response_line.decode().strip())
                phase_timings["response_parse"] = time.time() - phase_start
                
                return {
                    "duration": time.time() - start_time,
                    "success": response_data.get("error") is None,
                    "phase_timings": phase_timings,
                    "response": response_data
                }
                
            except asyncio.TimeoutError:
                phase_timings["response_wait"] = time.time() - phase_start
                
                # Capture stderr for timeout debugging
                stderr_data = ""
                try:
                    stderr_bytes = await asyncio.wait_for(
                        process.stderr.read(4096), timeout=1.0
                    )
                    stderr_data = stderr_bytes.decode()
                except:
                    stderr_data = "Could not capture stderr"
                
                return {
                    "duration": time.time() - start_time,
                    "success": False,
                    "timeout_phase": "response_wait",
                    "phase_timings": phase_timings,
                    "error": f"TIMEOUT after {timeout_seconds}s",
                    "stderr": stderr_data
                }
                
        except Exception as e:
            return {
                "duration": time.time() - start_time,
                "success": False,
                "error": str(e),
                "phase_timings": phase_timings,
                "exception": traceback.format_exc()
            }
            
        finally:
            if process:
                cleanup_start = time.time()
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=3.0)
                except:
                    process.kill()
                    await process.wait()
                phase_timings["cleanup"] = time.time() - cleanup_start
    
    async def _diagnose_resource_usage(self, tool_name: str, params: Dict[str, Any]) -> ResourceUsage:
        """Monitor system resources during tool execution."""
        process = None
        initial_memory = 0
        peak_memory = 0
        
        try:
            # Get initial system state
            system_process = psutil.Process()
            initial_memory = system_process.memory_info().rss
            initial_cpu = system_process.cpu_percent()
            initial_fds = len(system_process.open_files())
            
            start_time = time.time()
            
            # Start stdio server process
            process = await asyncio.create_subprocess_exec(
                sys.executable, self.server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor resources during execution
            resource_monitor = ResourceMonitor(process.pid)
            monitor_task = asyncio.create_task(resource_monitor.start_monitoring())
            
            # Execute tool
            request = {
                "jsonrpc": "2.0", 
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": params},
                "id": 1
            }
            
            request_bytes = json.dumps(request).encode() + b'\n'
            process.stdin.write(request_bytes)
            await process.stdin.drain()
            
            # Wait for response with timeout
            timeout_seconds = self._get_tool_timeout(tool_name)
            try:
                await asyncio.wait_for(process.stdout.readline(), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                pass  # Continue with resource analysis
            
            # Stop monitoring and get results
            monitor_results = await resource_monitor.stop_monitoring()
            monitor_task.cancel()
            
            duration = time.time() - start_time
            
            # Get final system state
            final_memory = system_process.memory_info().rss
            final_cpu = system_process.cpu_percent()
            final_fds = len(system_process.open_files())
            
            return ResourceUsage(
                tool_name=tool_name,
                duration=duration,
                memory_delta=final_memory - initial_memory,
                cpu_usage=final_cpu - initial_cpu,
                file_descriptors=final_fds - initial_fds,
                peak_memory=monitor_results.get("peak_memory", 0),
                io_operations=monitor_results.get("io_operations", {})
            )
            
        except Exception as e:
            return ResourceUsage(
                tool_name=tool_name,
                duration=time.time() - start_time if 'start_time' in locals() else 0.0,
                memory_delta=0,
                cpu_usage=0.0,
                file_descriptors=0,
                peak_memory=0
            )
            
        finally:
            if process:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=3.0)
                except:
                    process.kill()
                    await process.wait()
    
    async def _profile_tool_execution(self, tool_name: str, params: Dict[str, Any]) -> Optional[PerformanceProfile]:
        """Profile stdio tool execution with cProfile."""
        try:
            # Note: This is a simplified profiling approach
            # In a real scenario, we'd need to profile the server process itself
            # For now, we'll profile the client-side execution
            
            profiler = cProfile.Profile()
            profiler.enable()
            
            start_time = time.time()
            
            # Execute tool (this profiles the client side, not ideal but useful)
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
            
            try:
                await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=self._get_tool_timeout(tool_name)
                )
            except asyncio.TimeoutError:
                pass
            
            profiler.disable()
            
            # Process termination
            process.terminate()
            await process.wait()
            
            total_time = time.time() - start_time
            
            # Analyze profile results
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            
            # Extract top functions
            stats_stream = io.StringIO()
            stats.print_stats(10, file=stats_stream)
            stats_output = stats_stream.getvalue()
            
            # Parse function statistics
            function_stats = self._parse_profile_stats(stats)
            bottlenecks = self._identify_bottlenecks(function_stats)
            
            return PerformanceProfile(
                tool_name=tool_name,
                total_time=total_time,
                function_stats=function_stats,
                bottlenecks=bottlenecks,
                call_graph=stats_output
            )
            
        except Exception as e:
            if self.debug_mode:
                print(f"Profiling failed for {tool_name}: {e}")
            return None
    
    def _get_tool_timeout(self, tool_name: str) -> float:
        """Get appropriate timeout for different tool categories."""
        # Priority 1 tools - shorter timeout expected
        if tool_name in ["store_memory", "retrieve_memory", "log_chat", "redis_health_check"]:
            return 10.0
        
        # Database-heavy operations
        elif tool_name in ["query_graph", "link_resources", "analyze_code_patterns"]:
            return 20.0
            
        # Default timeout
        return 15.0
    
    def _get_default_params(self, tool_name: str) -> Dict[str, Any]:
        """Get appropriate default parameters for testing each tool."""
        import uuid
        test_id = str(uuid.uuid4())[:8]
        
        # Simplified parameter sets for timeout debugging
        params = {
            "store_memory": {
                "file_name": f"timeout_test_{test_id}.md",
                "content": "Timeout debugging test content",
                "resource_type": "document"
            },
            "retrieve_memory": {
                "query": "timeout test", 
                "conversation_id": f"timeout_test_{test_id}",
                "top_k": 3
            },
            "log_chat": {
                "content": "Timeout test chat",
                "conversation_id": f"timeout_test_{test_id}",
                "role": "user"
            },
            "redis_health_check": {},
            "list_tool_identifiers": {},
            "add_todo": {
                "title": f"Timeout test {test_id}",
                "description": "Test todo for timeout debugging",
                "priority": "low"
            }
        }
        
        return params.get(tool_name, {})
    
    def _parse_profile_stats(self, stats: pstats.Stats) -> Dict[str, Dict[str, Any]]:
        """Parse cProfile statistics into structured data.""" 
        function_stats = {}
        
        for func_info, (cc, nc, tt, ct, callers) in stats.stats.items():
            filename, line, func_name = func_info
            
            function_stats[f"{filename}:{line}({func_name})"] = {
                "call_count": cc,
                "primitive_call_count": nc, 
                "total_time": tt,
                "cumulative_time": ct,
                "time_per_call": tt / cc if cc > 0 else 0,
                "cum_time_per_call": ct / cc if cc > 0 else 0
            }
        
        return function_stats
    
    def _identify_bottlenecks(self, function_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks from function statistics.""" 
        bottlenecks = []
        
        # Sort by cumulative time to find bottlenecks
        sorted_functions = sorted(
            function_stats.items(),
            key=lambda x: x[1]["cumulative_time"],
            reverse=True
        )
        
        # Top 5 bottlenecks
        for func_name, stats in sorted_functions[:5]:
            if stats["cumulative_time"] > 0.1:  # Only significant bottlenecks
                bottlenecks.append({
                    "function": func_name,
                    "cumulative_time": stats["cumulative_time"],
                    "call_count": stats["call_count"],
                    "time_per_call": stats["cum_time_per_call"]
                })
        
        return bottlenecks
    
    def generate_diagnosis_report(self) -> str:
        """Generate comprehensive diagnosis report for all tested tools."""
        if not self.diagnosis_results:
            return "No diagnosis results available."
        
        report = ["🔍 STDIO TIMEOUT DIAGNOSIS REPORT", "=" * 60, ""]
        
        # Summary statistics
        total_tools = len(self.diagnosis_results)
        timeout_tools = [name for name, diag in self.diagnosis_results.items() 
                        if diag.timeout_phase is not None]
        
        report.extend([
            f"📊 SUMMARY:",
            f"  Total Tools Tested: {total_tools}",
            f"  Tools with Timeouts: {len(timeout_tools)}",
            f"  Timeout Rate: {len(timeout_tools)/total_tools*100:.1f}%",
            ""
        ])
        
        # Detailed analysis by tool
        report.append("🛠️  DETAILED ANALYSIS BY TOOL:")
        report.append("-" * 40)
        
        for tool_name, diagnosis in sorted(self.diagnosis_results.items()):
            status = "❌ TIMEOUT" if diagnosis.timeout_phase else "✅ SUCCESS"
            
            report.extend([
                f"\n{tool_name}: {status}",
                f"  Total Time: {diagnosis.total_time:.2f}s",
                f"  Startup Time: {diagnosis.startup_time:.2f}s",
                f"  Execution Time: {diagnosis.execution_time:.2f}s", 
                f"  Memory Usage: {diagnosis.memory_usage / 1024 / 1024:.1f} MB",
                f"  CPU Usage: {diagnosis.cpu_usage:.1f}%",
                f"  File Descriptors: {diagnosis.file_descriptors}"
            ])
            
            if diagnosis.timeout_phase:
                report.append(f"  Timeout Phase: {diagnosis.timeout_phase}")
            
            if diagnosis.error_details:
                report.append(f"  Error: {diagnosis.error_details}")
            
            if diagnosis.performance_profile:
                bottlenecks = len([f for f in diagnosis.performance_profile.values() 
                                 if f.get("cumulative_time", 0) > 0.1])
                report.append(f"  Performance Bottlenecks: {bottlenecks}")
        
        # Recommendations
        report.extend([
            "\n" + "=" * 60,
            "💡 RECOMMENDATIONS:",
            ""
        ])
        
        if timeout_tools:
            report.extend([
                "🔧 IMMEDIATE ACTIONS NEEDED:",
                "  1. Increase timeout values for failing tools:",
                f"     {', '.join(timeout_tools)}",
                "  2. Investigate startup performance bottlenecks",
                "  3. Consider connection pooling to reduce startup overhead",
                "  4. Profile server-side execution for bottleneck identification",
                ""
            ])
        else:
            report.extend([
                "✅ All tools executing successfully!",
                "🚀 Consider optimizing startup time for better performance.",
                ""
            ])
        
        # Performance optimization suggestions
        avg_startup_time = sum(d.startup_time for d in self.diagnosis_results.values()) / total_tools
        if avg_startup_time > 3.0:
            report.extend([
                "⚡ PERFORMANCE OPTIMIZATIONS:",
                f"  - Average startup time ({avg_startup_time:.2f}s) is high",
                "  - Consider implementing stdio process pooling",
                "  - Optimize database connection initialization",
                "  - Consider lazy loading of heavy dependencies",
                ""
            ])
        
        return "\n".join(report)


class ResourceMonitor:
    """Monitor system resources during process execution."""
    
    def __init__(self, pid: int):
        self.pid = pid
        self.monitoring = False
        self.resource_samples = []
        self.peak_memory = 0
    
    async def start_monitoring(self) -> None:
        """Start resource monitoring in background."""
        self.monitoring = True
        
        while self.monitoring:
            try:
                process = psutil.Process(self.pid)
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()
                
                self.resource_samples.append({
                    "timestamp": time.time(),
                    "memory_rss": memory_info.rss,
                    "memory_vms": memory_info.vms, 
                    "cpu_percent": cpu_percent
                })
                
                # Track peak memory
                if memory_info.rss > self.peak_memory:
                    self.peak_memory = memory_info.rss
                
                await asyncio.sleep(0.1)  # Sample every 100ms
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            except Exception:
                continue
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return results."""
        self.monitoring = False
        
        if not self.resource_samples:
            return {"peak_memory": 0, "io_operations": {}}
        
        return {
            "peak_memory": self.peak_memory,
            "sample_count": len(self.resource_samples),
            "avg_cpu": sum(s["cpu_percent"] for s in self.resource_samples) / len(self.resource_samples),
            "io_operations": {}  # TODO: Add I/O monitoring if needed
        }


async def run_comprehensive_stdio_debugging():
    """Run comprehensive stdio timeout debugging for all critical tools."""
    print("🔍 Starting Comprehensive Stdio Timeout Debugging")
    print("=" * 60)
    
    debugger = StdioTimeoutDebugger(debug_mode=True)
    
    # Focus on critical tools first
    critical_tools = [
        "store_memory", "retrieve_memory", "log_chat", 
        "redis_health_check", "list_tool_identifiers"
    ]
    
    print(f"🎯 Debugging {len(critical_tools)} critical tools...")
    
    # Diagnose each tool
    for tool_name in critical_tools:
        print(f"\n📊 Analyzing {tool_name}...")
        diagnosis = await debugger.diagnose_timeout(tool_name)
        
        # Quick status report
        if diagnosis.timeout_phase:
            print(f"  ❌ TIMEOUT in {diagnosis.timeout_phase} phase ({diagnosis.total_time:.2f}s)")
        else:
            print(f"  ✅ SUCCESS ({diagnosis.total_time:.2f}s)")
        
        print(f"  📈 Startup: {diagnosis.startup_time:.2f}s, "
              f"Execution: {diagnosis.execution_time:.2f}s")
    
    # Generate comprehensive report
    print("\n" + "=" * 60)
    print("📋 GENERATING COMPREHENSIVE DIAGNOSIS REPORT...")
    print("=" * 60)
    
    report = debugger.generate_diagnosis_report()
    print(report)
    
    # Save report for future reference
    report_path = project_root / "debug_reports" / f"stdio_timeout_diagnosis_{int(time.time())}.txt"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\n💾 Full report saved to: {report_path}")
    print("🎯 Use this report to guide stdio timeout fixes!")


if __name__ == "__main__":
    """Run stdio timeout debugging when executed directly."""
    asyncio.run(run_comprehensive_stdio_debugging())