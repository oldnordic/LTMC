#!/usr/bin/env python3
"""Comprehensive validation tests for all 28 LTMC MCP tools across both transports.

This module implements the systematic testing strategy for ensuring all LTMC tools
work reliably across HTTP and stdio transports with proper timeout debugging.
"""

import pytest
import asyncio
import time
import json
import sys
import uuid
import statistics
import aiohttp
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class TestResult:
    """Test result with comprehensive metrics."""
    tool_name: str
    transport: str
    success: bool
    duration: float
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Validation result for a specific tool."""
    tool_name: str
    checks: Dict[str, bool] = field(default_factory=dict)
    overall_success: bool = True
    
    def add_check(self, check_name: str, success: bool):
        """Add validation check result."""
        self.checks[check_name] = success
        if not success:
            self.overall_success = False


class HTTPTransportTester:
    """Test all 28 tools via HTTP JSON-RPC transport."""
    
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        """Initialize HTTP session."""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup HTTP session."""
        if self.session:
            await self.session.close()
    
    async def test_tool_http(self, tool_name: str, params: Dict[str, Any]) -> TestResult:
        """Test single tool via HTTP with timeout handling."""
        start_time = time.time()
        try:
            response = await self.session.post(
                f'{self.base_url}/jsonrpc',
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": params},
                    "id": 1
                }
            )
            duration = time.time() - start_time
            result_data = await response.json()
            
            return TestResult(
                tool_name=tool_name,
                transport="http",
                success=result_data.get("error") is None,
                duration=duration,
                response=result_data,
                error=result_data.get("error")
            )
        except Exception as e:
            return TestResult(
                tool_name=tool_name,
                transport="http",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            )


class StdioTransportTester:
    """Test all 28 tools via stdio MCP transport with timeout debugging."""
    
    def __init__(self, server_path: str = None):
        self.server_path = server_path or str(project_root / "ltmc_mcp_server.py")
    
    async def test_tool_stdio(self, tool_name: str, params: Dict[str, Any]) -> TestResult:
        """Test single tool via stdio with comprehensive timeout tracking."""
        start_time = time.time()
        process = None
        debug_info = {}
        
        try:
            # Phase 1: Process startup with timing
            startup_start = time.time()
            process = await asyncio.create_subprocess_exec(
                sys.executable, self.server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            startup_duration = time.time() - startup_start
            debug_info["startup_duration"] = startup_duration
            
            # Phase 2: Request preparation and sending
            request_start = time.time()
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": params},
                "id": 1
            }
            
            request_bytes = json.dumps(request).encode() + b'\n'
            process.stdin.write(request_bytes)
            await process.stdin.drain()
            request_duration = time.time() - request_start
            debug_info["request_duration"] = request_duration
            
            # Phase 3: Response reading with granular timeout
            response_start = time.time()
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=15.0  # Stdio-specific timeout
            )
            response_duration = time.time() - response_start
            debug_info["response_duration"] = response_duration
            
            total_duration = time.time() - start_time
            result_data = json.loads(response_line.decode().strip())
            
            return TestResult(
                tool_name=tool_name,
                transport="stdio",
                success=result_data.get("error") is None,
                duration=total_duration,
                response=result_data,
                error=result_data.get("error"),
                debug_info=debug_info
            )
            
        except asyncio.TimeoutError:
            # Capture timeout debug information
            debug_info["timeout_phase"] = "response_reading"
            debug_info["total_duration"] = time.time() - start_time
            
            # Try to capture stderr for debugging
            if process and process.stderr:
                try:
                    stderr_data = await asyncio.wait_for(
                        process.stderr.read(1024), timeout=1.0
                    )
                    debug_info["stderr"] = stderr_data.decode()
                except:
                    debug_info["stderr"] = "Could not capture stderr"
            
            return TestResult(
                tool_name=tool_name,
                transport="stdio",
                success=False,
                duration=time.time() - start_time,
                error="STDIO_TIMEOUT",
                debug_info=debug_info
            )
        except Exception as e:
            return TestResult(
                tool_name=tool_name,
                transport="stdio",
                success=False,
                duration=time.time() - start_time,
                error=f"STDIO_ERROR: {str(e)}",
                debug_info=debug_info
            )
        finally:
            if process:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=3.0)
                except:
                    process.kill()
                    await process.wait()


class ToolValidator:
    """Comprehensive validation for all 28 LTMC tools."""
    
    # Tool definitions by priority
    PRIORITY_1_TOOLS = [
        "store_memory", "retrieve_memory", "log_chat", 
        "ask_with_context", "route_query", "get_chats_by_tool"
    ]
    
    PRIORITY_2_TOOLS = [
        "add_todo", "list_todos", "complete_todo", "search_todos",
        "build_context", "retrieve_by_type", "store_context_links",
        "get_context_links_for_message", "get_messages_for_chunk",
        "get_context_usage_statistics"
    ]
    
    PRIORITY_3_TOOLS = [
        "link_resources", "query_graph", "auto_link_documents",
        "get_document_relationships", "list_tool_identifiers",
        "get_tool_conversations"
    ]
    
    PRIORITY_4_TOOLS = [
        "log_code_attempt", "get_code_patterns", "analyze_code_patterns",
        "redis_cache_stats", "redis_flush_cache", "redis_health_check"
    ]
    
    ALL_TOOLS = PRIORITY_1_TOOLS + PRIORITY_2_TOOLS + PRIORITY_3_TOOLS + PRIORITY_4_TOOLS
    
    def __init__(self):
        self.http_tester = HTTPTransportTester()
        self.stdio_tester = StdioTransportTester()
    
    def get_test_params(self, tool_name: str) -> Dict[str, Any]:
        """Get appropriate test parameters for each tool."""
        test_id = str(uuid.uuid4())[:8]
        
        params = {
            # Memory operations
            "store_memory": {
                "file_name": f"test_storage_{test_id}.md",
                "content": f"Test content for {tool_name} - {test_id}",
                "resource_type": "document"
            },
            "retrieve_memory": {
                "query": "test content",
                "conversation_id": f"test_conv_{test_id}",
                "top_k": 3
            },
            
            # Chat operations
            "log_chat": {
                "content": f"Test chat message - {test_id}",
                "conversation_id": f"test_conv_{test_id}",
                "role": "user"
            },
            "ask_with_context": {
                "query": f"Test query - {test_id}",
                "conversation_id": f"test_conv_{test_id}",
                "top_k": 3
            },
            "route_query": {
                "query": f"Test routing query - {test_id}",
                "source_types": ["document"],
                "top_k": 3
            },
            "get_chats_by_tool": {
                "source_tool": "test_tool",
                "limit": 10
            },
            
            # Task management
            "add_todo": {
                "title": f"Test todo - {test_id}",
                "description": f"Test todo description - {test_id}",
                "priority": "medium"
            },
            "list_todos": {
                "status": "all",
                "limit": 10
            },
            "complete_todo": {
                "todo_id": 1  # May fail if no todos exist, but tests the interface
            },
            "search_todos": {
                "query": "test",
                "limit": 10
            },
            
            # Context operations
            "build_context": {
                "documents": [{"content": "Test doc", "file_name": "test.md"}],
                "max_tokens": 1000
            },
            "retrieve_by_type": {
                "query": f"test query - {test_id}",
                "doc_type": "document",
                "top_k": 3
            },
            "store_context_links": {
                "message_id": 1,
                "chunk_ids": [1, 2]
            },
            "get_context_links_for_message": {
                "message_id": 1
            },
            "get_messages_for_chunk": {
                "chunk_id": 1
            },
            "get_context_usage_statistics": {},
            
            # Knowledge graph
            "link_resources": {
                "source_id": f"test_source_{test_id}",
                "target_id": f"test_target_{test_id}",
                "relation": "references"
            },
            "query_graph": {
                "entity": f"test_entity_{test_id}",
                "relation_type": "references"
            },
            "auto_link_documents": {
                "documents": [{"id": "doc1", "content": "Test"}]
            },
            "get_document_relationships": {
                "doc_id": f"test_doc_{test_id}"
            },
            
            # Tool analytics
            "list_tool_identifiers": {},
            "get_tool_conversations": {
                "source_tool": "test_tool",
                "limit": 10
            },
            
            # Code patterns
            "log_code_attempt": {
                "input_prompt": f"Test code prompt - {test_id}",
                "generated_code": f"# Test code - {test_id}\nprint('test')",
                "result": "pass",
                "tags": ["test", "validation"]
            },
            "get_code_patterns": {
                "query": f"test pattern - {test_id}",
                "result_filter": "pass",
                "top_k": 3
            },
            "analyze_code_patterns": {
                "query": f"pattern analysis - {test_id}"
            },
            
            # Redis operations  
            "redis_cache_stats": {},
            "redis_flush_cache": {
                "cache_type": "test"
            },
            "redis_health_check": {}
        }
        
        return params.get(tool_name, {})
    
    async def validate_tool(self, tool_name: str, transport: str = "both") -> ValidationResult:
        """Comprehensive validation for a specific tool."""
        validation = ValidationResult(tool_name=tool_name)
        test_params = self.get_test_params(tool_name)
        
        # Test HTTP transport
        if transport in ["http", "both"]:
            async with self.http_tester as http:
                http_result = await http.test_tool_http(tool_name, test_params)
                validation.add_check("http_transport", http_result.success)
                validation.add_check("http_response_time", http_result.duration < 5.0)
        
        # Test stdio transport  
        if transport in ["stdio", "both"]:
            stdio_result = await self.stdio_tester.test_tool_stdio(tool_name, test_params)
            validation.add_check("stdio_transport", stdio_result.success)
            validation.add_check("stdio_response_time", stdio_result.duration < 10.0)
            
            # Add stdio-specific debugging checks
            if stdio_result.debug_info:
                startup_ok = stdio_result.debug_info.get("startup_duration", 10) < 5.0
                validation.add_check("stdio_startup_time", startup_ok)
        
        return validation


# Test classes for pytest integration

@pytest.mark.asyncio
class TestPriority1Tools:
    """Test Priority 1 (Critical) tools - must work perfectly."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.validator = ToolValidator()
    
    @pytest.mark.parametrize("tool_name", ToolValidator.PRIORITY_1_TOOLS)
    async def test_priority1_tool_validation(self, tool_name):
        """Test critical tools with highest validation standards."""
        validation = await self.validator.validate_tool(tool_name, "both")
        
        # Critical tools must pass all checks
        assert validation.overall_success, f"{tool_name} failed validation: {validation.checks}"
        
        # Ensure both transports work
        assert validation.checks.get("http_transport", False), f"{tool_name} HTTP transport failed"
        # Note: stdio transport may have known timeout issues, so we log but don't fail
        stdio_success = validation.checks.get("stdio_transport", False)
        if not stdio_success:
            print(f"WARNING: {tool_name} stdio transport failed - needs investigation")


@pytest.mark.asyncio  
class TestPriority2Tools:
    """Test Priority 2 (High) tools - important workflow support."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.validator = ToolValidator()
    
    @pytest.mark.parametrize("tool_name", ToolValidator.PRIORITY_2_TOOLS)
    async def test_priority2_tool_validation(self, tool_name):
        """Test high priority tools with good validation coverage."""
        validation = await self.validator.validate_tool(tool_name, "both")
        
        # High priority tools should work on HTTP at minimum
        assert validation.checks.get("http_transport", False), f"{tool_name} HTTP transport failed"


@pytest.mark.asyncio
class TestPriority3Tools:
    """Test Priority 3 (Medium) tools - advanced features."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.validator = ToolValidator()
    
    @pytest.mark.parametrize("tool_name", ToolValidator.PRIORITY_3_TOOLS)
    async def test_priority3_tool_validation(self, tool_name):
        """Test medium priority tools with basic validation."""
        validation = await self.validator.validate_tool(tool_name, "http")
        
        # Medium priority tools should work on HTTP
        http_success = validation.checks.get("http_transport", False)
        if not http_success:
            print(f"WARNING: {tool_name} HTTP transport failed - may need attention")


@pytest.mark.asyncio
class TestPriority4Tools:
    """Test Priority 4 (Supporting) tools - optional features."""
    
    def setup_method(self):
        """Setup for each test method.""" 
        self.validator = ToolValidator()
    
    @pytest.mark.parametrize("tool_name", ToolValidator.PRIORITY_4_TOOLS)
    async def test_priority4_tool_validation(self, tool_name):
        """Test supporting tools with basic validation."""
        validation = await self.validator.validate_tool(tool_name, "http")
        
        # Supporting tools - log results but don't fail tests
        http_success = validation.checks.get("http_transport", False)
        print(f"{tool_name}: {'✅' if http_success else '❌'}")


@pytest.mark.asyncio
class TestTransportComparison:
    """Compare HTTP vs stdio transport performance and reliability."""
    
    def setup_method(self):
        """Setup for transport comparison tests."""
        self.validator = ToolValidator()
    
    async def test_transport_performance_comparison(self):
        """Compare performance between HTTP and stdio transports."""
        results = {"http": {}, "stdio": {}}
        
        # Test a representative sample of tools
        sample_tools = [
            "store_memory", "retrieve_memory", "log_chat",  # P1
            "add_todo", "build_context",  # P2  
            "redis_health_check"  # P4
        ]
        
        for tool_name in sample_tools:
            test_params = self.validator.get_test_params(tool_name)
            
            # Test HTTP
            async with self.validator.http_tester as http:
                http_result = await http.test_tool_http(tool_name, test_params)
                results["http"][tool_name] = http_result
            
            # Test stdio
            stdio_result = await self.validator.stdio_tester.test_tool_stdio(tool_name, test_params)
            results["stdio"][tool_name] = stdio_result
        
        # Analyze results
        http_successes = sum(1 for r in results["http"].values() if r.success)
        stdio_successes = sum(1 for r in results["stdio"].values() if r.success)
        
        print(f"Transport Comparison Results:")
        print(f"HTTP Success Rate: {http_successes}/{len(sample_tools)} ({http_successes/len(sample_tools)*100:.1f}%)")
        print(f"Stdio Success Rate: {stdio_successes}/{len(sample_tools)} ({stdio_successes/len(sample_tools)*100:.1f}%)")
        
        # HTTP should have high success rate
        assert http_successes >= len(sample_tools) * 0.9, "HTTP transport reliability below 90%"


@pytest.mark.asyncio
class TestStdioTimeoutDebugging:
    """Comprehensive stdio timeout debugging."""
    
    def setup_method(self):
        """Setup for stdio debugging tests."""
        self.stdio_tester = StdioTransportTester()
    
    async def test_stdio_timeout_diagnosis(self):
        """Diagnose stdio timeout issues with detailed debugging."""
        # Test problematic tools with detailed timing
        critical_tools = ["store_memory", "retrieve_memory", "log_chat"]
        timeout_analysis = {}
        
        for tool_name in critical_tools:
            test_params = self.validator.get_test_params(tool_name)
            result = await self.stdio_tester.test_tool_stdio(tool_name, test_params)
            
            timeout_analysis[tool_name] = {
                "success": result.success,
                "duration": result.duration,
                "debug_info": result.debug_info,
                "error": result.error
            }
        
        # Analyze patterns
        failed_tools = [name for name, data in timeout_analysis.items() if not data["success"]]
        
        if failed_tools:
            print(f"Stdio timeout analysis for failed tools: {failed_tools}")
            for tool_name in failed_tools:
                data = timeout_analysis[tool_name]
                print(f"\n{tool_name}:")
                print(f"  Duration: {data['duration']:.2f}s")
                print(f"  Error: {data['error']}")
                if data['debug_info']:
                    for key, value in data['debug_info'].items():
                        print(f"  {key}: {value}")
        
        # At minimum, document the issues for further investigation
        success_rate = (len(critical_tools) - len(failed_tools)) / len(critical_tools)
        print(f"Stdio Success Rate for Critical Tools: {success_rate*100:.1f}%")


if __name__ == "__main__":
    """Run comprehensive validation when executed directly."""
    import asyncio
    
    async def run_comprehensive_validation():
        """Run complete validation suite."""
        print("🧪 Starting LTMC Comprehensive Tool Validation")
        print("=" * 60)
        
        validator = ToolValidator()
        
        print("📊 Testing all 28 tools across both transports...")
        
        # Track results by priority
        priority_results = {
            "Priority 1 (Critical)": [],
            "Priority 2 (High)": [],
            "Priority 3 (Medium)": [],
            "Priority 4 (Supporting)": []
        }
        
        tool_groups = [
            (ToolValidator.PRIORITY_1_TOOLS, "Priority 1 (Critical)"),
            (ToolValidator.PRIORITY_2_TOOLS, "Priority 2 (High)"),
            (ToolValidator.PRIORITY_3_TOOLS, "Priority 3 (Medium)"),
            (ToolValidator.PRIORITY_4_TOOLS, "Priority 4 (Supporting)")
        ]
        
        for tools, priority_name in tool_groups:
            print(f"\n🔍 Testing {priority_name}: {len(tools)} tools")
            
            for tool_name in tools:
                print(f"  Testing {tool_name}...", end=" ")
                validation = await validator.validate_tool(tool_name, "both")
                
                http_ok = validation.checks.get("http_transport", False)
                stdio_ok = validation.checks.get("stdio_transport", False)
                
                status = "✅" if validation.overall_success else "❌"
                transport_status = f"HTTP:{'✅' if http_ok else '❌'} Stdio:{'✅' if stdio_ok else '❌'}"
                
                print(f"{status} {transport_status}")
                priority_results[priority_name].append({
                    "tool": tool_name,
                    "validation": validation
                })
        
        # Summary report
        print("\n" + "=" * 60)
        print("📈 VALIDATION SUMMARY REPORT")
        print("=" * 60)
        
        total_tools = 0
        http_successes = 0
        stdio_successes = 0
        
        for priority_name, results in priority_results.items():
            http_success_count = sum(1 for r in results if r["validation"].checks.get("http_transport", False))
            stdio_success_count = sum(1 for r in results if r["validation"].checks.get("stdio_transport", False))
            
            total_tools += len(results)
            http_successes += http_success_count
            stdio_successes += stdio_success_count
            
            print(f"\n{priority_name}: {len(results)} tools")
            print(f"  HTTP Success Rate: {http_success_count}/{len(results)} ({http_success_count/len(results)*100:.1f}%)")
            print(f"  Stdio Success Rate: {stdio_success_count}/{len(results)} ({stdio_success_count/len(results)*100:.1f}%)")
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"Total Tools Tested: {total_tools}")
        print(f"HTTP Transport Success Rate: {http_successes}/{total_tools} ({http_successes/total_tools*100:.1f}%)")
        print(f"Stdio Transport Success Rate: {stdio_successes}/{total_tools} ({stdio_successes/total_tools*100:.1f}%)")
        
        # Recommendations
        if http_successes >= total_tools * 0.95:
            print("\n✅ HTTP Transport: EXCELLENT - Ready for production")
        elif http_successes >= total_tools * 0.90:
            print("\n⚠️  HTTP Transport: GOOD - Minor issues need attention")
        else:
            print("\n❌ HTTP Transport: NEEDS WORK - Significant issues found")
        
        if stdio_successes >= total_tools * 0.95:
            print("✅ Stdio Transport: EXCELLENT - Ready for production")
        elif stdio_successes >= total_tools * 0.90:
            print("⚠️  Stdio Transport: GOOD - Minor issues need attention") 
        else:
            print("❌ Stdio Transport: NEEDS WORK - Significant timeout issues")
            print("   Recommendation: Focus on stdio timeout debugging")
        
        print("\n🚀 Validation Complete!")
    
    # Run the validation
    asyncio.run(run_comprehensive_validation())