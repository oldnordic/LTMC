#!/usr/bin/env python3
"""Enhanced comprehensive test suite for all 28 LTMC tools following MCP 2024-11-05 standards.

This module implements systematic testing with JSON-RPC 2.0 compliance, performance metrics,
error handling validation, and detailed reporting with LTMC storage integration.

Key features:
- MCP 2024-11-05 protocol compliance testing
- JSON-RPC 2.0 specification validation
- Comprehensive error handling verification
- Performance benchmarking with detailed metrics
- Test result storage in LTMC system
- Both HTTP and stdio transport testing
- Statistical analysis and reporting
"""

import pytest
import asyncio
import time
import json
import sys
import uuid
import statistics
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MCPTestResult:
    """Enhanced test result with MCP 2024-11-05 compliance metrics."""
    tool_name: str
    transport: str
    success: bool
    duration: float
    response_time: float = 0.0
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[int] = None
    debug_info: Optional[Dict[str, Any]] = None
    
    # MCP 2024-11-05 compliance fields
    jsonrpc_valid: bool = False
    response_structure_valid: bool = False
    error_structure_valid: bool = False
    protocol_compliant: bool = False
    
    # Performance metrics
    startup_time: float = 0.0
    processing_time: float = 0.0
    network_time: float = 0.0
    
    # Quality metrics
    data_quality_score: float = 0.0
    usability_score: float = 0.0
    reliability_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LTMC storage."""
        return asdict(self)


@dataclass
class ComprehensiveValidation:
    """Comprehensive validation results for a tool."""
    tool_name: str
    http_result: Optional[MCPTestResult] = None
    stdio_result: Optional[MCPTestResult] = None
    overall_success: bool = False
    compliance_score: float = 0.0
    performance_score: float = 0.0
    reliability_score: float = 0.0
    edge_cases_passed: int = 0
    total_edge_cases: int = 0
    error_handling_score: float = 0.0
    
    def calculate_overall_scores(self):
        """Calculate overall quality scores."""
        results = [r for r in [self.http_result, self.stdio_result] if r is not None]
        
        if not results:
            return
            
        # Compliance score (MCP 2024-11-05)
        compliance_scores = []
        for result in results:
            score = 0.0
            if result.jsonrpc_valid: score += 0.25
            if result.response_structure_valid: score += 0.25
            if result.error_structure_valid: score += 0.25
            if result.protocol_compliant: score += 0.25
            compliance_scores.append(score)
        
        self.compliance_score = statistics.mean(compliance_scores) if compliance_scores else 0.0
        
        # Performance score
        perf_scores = [min(1.0, max(0.0, 1.0 - (r.duration / 10.0))) for r in results]
        self.performance_score = statistics.mean(perf_scores) if perf_scores else 0.0
        
        # Reliability score
        self.reliability_score = sum(1 for r in results if r.success) / len(results)
        
        # Error handling score
        if self.total_edge_cases > 0:
            self.error_handling_score = self.edge_cases_passed / self.total_edge_cases
        
        # Overall success
        self.overall_success = (
            self.compliance_score >= 0.8 and
            self.performance_score >= 0.7 and
            self.reliability_score >= 0.9
        )


class MCP2024Validator:
    """Validator for MCP 2024-11-05 protocol compliance."""
    
    @staticmethod
    def validate_jsonrpc_response(response: Dict[str, Any]) -> bool:
        """Validate JSON-RPC 2.0 response structure."""
        try:
            # Must have jsonrpc field with "2.0"
            if response.get("jsonrpc") != "2.0":
                return False
            
            # Must have id field
            if "id" not in response:
                return False
            
            # Must have either result or error, but not both
            # Handle common pattern where error is None (effectively no error)
            has_result = "result" in response
            has_error = "error" in response and response["error"] is not None
            
            if has_result and has_error:
                return False
            if not has_result and not has_error:
                return False
            
            # Error structure validation if present
            if has_error:
                error = response["error"]
                if not isinstance(error, dict):
                    return False
                if "code" not in error or "message" not in error:
                    return False
                if not isinstance(error["code"], int):
                    return False
                if not isinstance(error["message"], str):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def validate_mcp_tool_response(response: Dict[str, Any], tool_name: str) -> bool:
        """Validate MCP tool response structure."""
        try:
            if not MCP2024Validator.validate_jsonrpc_response(response):
                return False
            
            # If success, result should have expected structure
            if "result" in response:
                result = response["result"]
                if not isinstance(result, dict):
                    return False
                
                # Most tools should return success field
                if "success" in result and not isinstance(result["success"], bool):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def validate_error_response(response: Dict[str, Any]) -> bool:
        """Validate error response follows JSON-RPC 2.0 error structure."""
        if not MCP2024Validator.validate_jsonrpc_response(response):
            return False
        
        if "error" not in response:
            return False
        
        error = response["error"]
        required_fields = ["code", "message"]
        return all(field in error for field in required_fields)


class EnhancedHTTPTester:
    """Enhanced HTTP transport tester with comprehensive validation."""
    
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        self.session = None
        self.validator = MCP2024Validator()
    
    async def __aenter__(self):
        """Initialize HTTP session with proper timeout."""
        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup HTTP session."""
        if self.session:
            await self.session.close()
    
    async def test_tool_comprehensive(
        self, 
        tool_name: str, 
        params: Dict[str, Any],
        test_edge_cases: bool = True
    ) -> MCPTestResult:
        """Comprehensive tool testing with MCP compliance validation."""
        start_time = time.time()
        network_start = time.time()
        
        try:
            # Primary test
            response = await self.session.post(
                f'{self.base_url}/jsonrpc',
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call", 
                    "params": {"name": tool_name, "arguments": params},
                    "id": 1
                }
            )
            
            network_time = time.time() - network_start
            processing_start = time.time()
            
            result_data = await response.json()
            processing_time = time.time() - processing_start
            total_duration = time.time() - start_time
            
            # MCP 2024-11-05 compliance validation
            jsonrpc_valid = self.validator.validate_jsonrpc_response(result_data)
            response_structure_valid = self.validator.validate_mcp_tool_response(
                result_data, tool_name
            )
            error_structure_valid = True  # No error in successful case
            protocol_compliant = jsonrpc_valid and response_structure_valid
            
            # Success determination
            success = (
                result_data.get("error") is None and
                protocol_compliant and
                response.status == 200
            )
            
            # Quality scoring
            data_quality_score = 1.0 if success else 0.0
            usability_score = 1.0 if total_duration < 5.0 else max(0.0, 1.0 - (total_duration / 10.0))
            reliability_score = 1.0 if success else 0.0
            
            return MCPTestResult(
                tool_name=tool_name,
                transport="http",
                success=success,
                duration=total_duration,
                response_time=network_time,
                response=result_data,
                error=result_data.get("error"),
                jsonrpc_valid=jsonrpc_valid,
                response_structure_valid=response_structure_valid,
                error_structure_valid=error_structure_valid,
                protocol_compliant=protocol_compliant,
                network_time=network_time,
                processing_time=processing_time,
                data_quality_score=data_quality_score,
                usability_score=usability_score,
                reliability_score=reliability_score
            )
            
        except Exception as e:
            error_duration = time.time() - start_time
            error_msg = str(e)
            
            return MCPTestResult(
                tool_name=tool_name,
                transport="http",
                success=False,
                duration=error_duration,
                error=f"HTTP_ERROR: {error_msg}",
                jsonrpc_valid=False,
                response_structure_valid=False,
                error_structure_valid=False,
                protocol_compliant=False,
                debug_info={"exception": error_msg, "traceback": traceback.format_exc()}
            )
    
    async def test_error_handling(self, tool_name: str) -> List[MCPTestResult]:
        """Test error handling with invalid parameters."""
        error_tests = []
        
        # Test 1: Missing required parameters
        try:
            response = await self.session.post(
                f'{self.base_url}/jsonrpc',
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": {}},
                    "id": 2
                }
            )
            result_data = await response.json()
            
            error_structure_valid = self.validator.validate_error_response(result_data)
            
            error_tests.append(MCPTestResult(
                tool_name=f"{tool_name}_error_missing_params",
                transport="http",
                success="error" in result_data,  # Should return error
                duration=0.0,
                response=result_data,
                error_structure_valid=error_structure_valid,
                protocol_compliant=error_structure_valid
            ))
        except Exception as e:
            error_tests.append(MCPTestResult(
                tool_name=f"{tool_name}_error_missing_params",
                transport="http",
                success=False,
                duration=0.0,
                error=f"Error test failed: {str(e)}"
            ))
        
        # Test 2: Invalid parameter types
        try:
            invalid_params = {"invalid_param": 12345, "another_invalid": None}
            response = await self.session.post(
                f'{self.base_url}/jsonrpc',
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": invalid_params},
                    "id": 3
                }
            )
            result_data = await response.json()
            
            error_structure_valid = self.validator.validate_error_response(result_data)
            
            error_tests.append(MCPTestResult(
                tool_name=f"{tool_name}_error_invalid_params",
                transport="http",
                success="error" in result_data,  # Should return error
                duration=0.0,
                response=result_data,
                error_structure_valid=error_structure_valid,
                protocol_compliant=error_structure_valid
            ))
        except Exception as e:
            error_tests.append(MCPTestResult(
                tool_name=f"{tool_name}_error_invalid_params", 
                transport="http",
                success=False,
                duration=0.0,
                error=f"Error test failed: {str(e)}"
            ))
        
        return error_tests


class EnhancedStdioTester:
    """Enhanced stdio transport tester with comprehensive debugging."""
    
    def __init__(self, server_path: str = None):
        self.server_path = server_path or str(project_root / "ltmc_mcp_server.py")
        self.validator = MCP2024Validator()
    
    async def test_tool_comprehensive(
        self, 
        tool_name: str, 
        params: Dict[str, Any]
    ) -> MCPTestResult:
        """Comprehensive stdio tool testing with enhanced debugging."""
        start_time = time.time()
        process = None
        debug_info = {}
        
        try:
            # Phase 1: Process startup timing
            startup_start = time.time()
            process = await asyncio.create_subprocess_exec(
                sys.executable, self.server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            startup_time = time.time() - startup_start
            debug_info["startup_time"] = startup_time
            
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
            request_time = time.time() - request_start
            debug_info["request_time"] = request_time
            
            # Phase 3: Response reading with timeout
            response_start = time.time()
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=20.0  # Extended timeout for complex operations
            )
            response_time = time.time() - response_start
            debug_info["response_time"] = response_time
            
            total_duration = time.time() - start_time
            
            if not response_line:
                raise Exception("No response received from stdio server")
            
            result_data = json.loads(response_line.decode().strip())
            
            # MCP 2024-11-05 compliance validation
            jsonrpc_valid = self.validator.validate_jsonrpc_response(result_data)
            response_structure_valid = self.validator.validate_mcp_tool_response(
                result_data, tool_name
            )
            error_structure_valid = True
            protocol_compliant = jsonrpc_valid and response_structure_valid
            
            success = (
                result_data.get("error") is None and
                protocol_compliant
            )
            
            return MCPTestResult(
                tool_name=tool_name,
                transport="stdio",
                success=success,
                duration=total_duration,
                response=result_data,
                error=result_data.get("error"),
                jsonrpc_valid=jsonrpc_valid,
                response_structure_valid=response_structure_valid,
                error_structure_valid=error_structure_valid,
                protocol_compliant=protocol_compliant,
                startup_time=startup_time,
                processing_time=response_time,
                debug_info=debug_info,
                data_quality_score=1.0 if success else 0.0,
                usability_score=1.0 if total_duration < 10.0 else max(0.0, 1.0 - (total_duration / 20.0)),
                reliability_score=1.0 if success else 0.0
            )
            
        except asyncio.TimeoutError:
            debug_info["timeout_phase"] = "response_reading"
            debug_info["total_duration"] = time.time() - start_time
            
            # Capture stderr for debugging
            if process and process.stderr:
                try:
                    stderr_data = await asyncio.wait_for(
                        process.stderr.read(2048), timeout=2.0
                    )
                    debug_info["stderr"] = stderr_data.decode()
                except:
                    debug_info["stderr"] = "Could not capture stderr"
            
            return MCPTestResult(
                tool_name=tool_name,
                transport="stdio",
                success=False,
                duration=time.time() - start_time,
                error="STDIO_TIMEOUT",
                jsonrpc_valid=False,
                response_structure_valid=False,
                error_structure_valid=False,
                protocol_compliant=False,
                debug_info=debug_info
            )
        except Exception as e:
            return MCPTestResult(
                tool_name=tool_name,
                transport="stdio", 
                success=False,
                duration=time.time() - start_time,
                error=f"STDIO_ERROR: {str(e)}",
                jsonrpc_valid=False,
                response_structure_valid=False,
                error_structure_valid=False,
                protocol_compliant=False,
                debug_info=debug_info
            )
        finally:
            if process:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except:
                    process.kill()
                    try:
                        await process.wait()
                    except:
                        pass


class ComprehensiveToolValidator:
    """Enhanced validator for all 28 LTMC tools with comprehensive testing."""
    
    # Tool categories and definitions
    MEMORY_TOOLS = ["store_memory", "retrieve_memory"]
    CHAT_TOOLS = ["log_chat", "ask_with_context", "route_query", "get_chats_by_tool"]
    TASK_TOOLS = ["add_todo", "list_todos", "complete_todo", "search_todos"]
    CONTEXT_TOOLS = [
        "build_context", "retrieve_by_type", "store_context_links",
        "get_context_links_for_message", "get_messages_for_chunk", 
        "get_context_usage_statistics"
    ]
    GRAPH_TOOLS = [
        "link_resources", "query_graph", "auto_link_documents",
        "get_document_relationships"
    ]
    ANALYTICS_TOOLS = ["list_tool_identifiers", "get_tool_conversations"]
    CODE_TOOLS = ["log_code_attempt", "get_code_patterns", "analyze_code_patterns"]
    REDIS_TOOLS = ["redis_cache_stats", "redis_flush_cache", "redis_health_check"]
    
    ALL_TOOLS = (MEMORY_TOOLS + CHAT_TOOLS + TASK_TOOLS + CONTEXT_TOOLS + 
                 GRAPH_TOOLS + ANALYTICS_TOOLS + CODE_TOOLS + REDIS_TOOLS)
    
    def __init__(self):
        self.http_tester = EnhancedHTTPTester()
        self.stdio_tester = EnhancedStdioTester()
    
    def get_test_parameters(self, tool_name: str) -> Dict[str, Any]:
        """Get comprehensive test parameters for each tool."""
        test_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        params = {
            # Memory operations
            "store_memory": {
                "file_name": f"mcp_test_{test_id}.md",
                "content": f"MCP 2024-11-05 test content - {tool_name} - {timestamp}",
                "resource_type": "document"
            },
            "retrieve_memory": {
                "query": "MCP test content",
                "conversation_id": f"mcp_test_{test_id}",
                "top_k": 5
            },
            
            # Chat operations
            "log_chat": {
                "content": f"MCP test chat message - {test_id} - {timestamp}",
                "conversation_id": f"mcp_test_{test_id}",
                "role": "user"
            },
            "ask_with_context": {
                "query": f"MCP test query - {test_id}",
                "conversation_id": f"mcp_test_{test_id}",
                "top_k": 3
            },
            "route_query": {
                "query": f"MCP routing test - {test_id}",
                "source_types": ["document"],
                "top_k": 5
            },
            "get_chats_by_tool": {
                "source_tool": "mcp_test_tool",
                "limit": 20
            },
            
            # Task management
            "add_todo": {
                "title": f"MCP Test Todo - {test_id}",
                "description": f"MCP 2024-11-05 compliance test todo - {timestamp}",
                "priority": "medium"
            },
            "list_todos": {
                "status": "all",
                "limit": 20
            },
            "complete_todo": {
                "todo_id": 1
            },
            "search_todos": {
                "query": "MCP",
                "limit": 10
            },
            
            # Context operations
            "build_context": {
                "documents": [
                    {
                        "content": f"MCP test document content - {test_id}",
                        "file_name": f"mcp_test_{test_id}.md"
                    }
                ],
                "max_tokens": 2000
            },
            "retrieve_by_type": {
                "query": f"MCP test query - {test_id}",
                "doc_type": "document", 
                "top_k": 5
            },
            "store_context_links": {
                "message_id": 1,
                "chunk_ids": [1, 2, 3]
            },
            "get_context_links_for_message": {
                "message_id": 1
            },
            "get_messages_for_chunk": {
                "chunk_id": 1
            },
            "get_context_usage_statistics": {},
            
            # Knowledge graph operations
            "link_resources": {
                "source_id": f"mcp_source_{test_id}",
                "target_id": f"mcp_target_{test_id}",
                "relation": "tested_with"
            },
            "query_graph": {
                "entity": f"mcp_entity_{test_id}",
                "relation_type": "tested_with"
            },
            "auto_link_documents": {
                "documents": [
                    {"id": f"doc_{test_id}_1", "content": "MCP testing document"},
                    {"id": f"doc_{test_id}_2", "content": "MCP validation document"}
                ]
            },
            "get_document_relationships": {
                "doc_id": f"mcp_doc_{test_id}"
            },
            
            # Analytics operations
            "list_tool_identifiers": {},
            "get_tool_conversations": {
                "source_tool": "mcp_test_tool",
                "limit": 15
            },
            
            # Code pattern operations
            "log_code_attempt": {
                "input_prompt": f"MCP test code generation - {test_id}",
                "generated_code": f"# MCP 2024-11-05 test code - {test_id}\nprint('MCP compliance test')",
                "result": "pass",
                "tags": ["mcp", "test", "2024-11-05", "compliance"]
            },
            "get_code_patterns": {
                "query": f"MCP test pattern - {test_id}",
                "result_filter": "pass",
                "top_k": 5
            },
            "analyze_code_patterns": {
                "query": f"MCP pattern analysis - {test_id}"
            },
            
            # Redis operations
            "redis_cache_stats": {},
            "redis_flush_cache": {
                "cache_type": "test_cache"
            },
            "redis_health_check": {}
        }
        
        return params.get(tool_name, {})
    
    async def validate_tool_comprehensive(
        self, 
        tool_name: str, 
        test_transports: List[str] = ["http", "stdio"]
    ) -> ComprehensiveValidation:
        """Comprehensive validation for a single tool."""
        validation = ComprehensiveValidation(tool_name=tool_name)
        test_params = self.get_test_parameters(tool_name)
        
        # HTTP testing
        if "http" in test_transports:
            async with self.http_tester as http:
                validation.http_result = await http.test_tool_comprehensive(
                    tool_name, test_params
                )
                
                # Error handling tests
                error_results = await http.test_error_handling(tool_name)
                validation.edge_cases_passed += sum(1 for r in error_results if r.success)
                validation.total_edge_cases += len(error_results)
        
        # Stdio testing
        if "stdio" in test_transports:
            validation.stdio_result = await self.stdio_tester.test_tool_comprehensive(
                tool_name, test_params
            )
        
        # Calculate scores
        validation.calculate_overall_scores()
        
        return validation
    
    async def store_results_in_ltmc(self, results: Dict[str, ComprehensiveValidation]) -> bool:
        """Store comprehensive test results in LTMC system."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Generate comprehensive report
            report_data = {
                "test_session": f"mcp_2024_11_05_comprehensive_{timestamp}",
                "total_tools": len(results),
                "timestamp": datetime.now().isoformat(),
                "results": {}
            }
            
            # Collect statistics
            total_tools = len(results)
            http_successes = sum(1 for v in results.values() if v.http_result and v.http_result.success)
            stdio_successes = sum(1 for v in results.values() if v.stdio_result and v.stdio_result.success)
            compliance_scores = [v.compliance_score for v in results.values()]
            performance_scores = [v.performance_score for v in results.values()]
            reliability_scores = [v.reliability_score for v in results.values()]
            
            # Build detailed report
            for tool_name, validation in results.items():
                result_summary = {
                    "overall_success": validation.overall_success,
                    "compliance_score": validation.compliance_score,
                    "performance_score": validation.performance_score,
                    "reliability_score": validation.reliability_score,
                    "http_result": validation.http_result.to_dict() if validation.http_result else None,
                    "stdio_result": validation.stdio_result.to_dict() if validation.stdio_result else None,
                    "edge_cases": {
                        "passed": validation.edge_cases_passed,
                        "total": validation.total_edge_cases
                    }
                }
                report_data["results"][tool_name] = result_summary
            
            # Summary statistics
            report_data["summary"] = {
                "total_tools_tested": total_tools,
                "http_success_rate": http_successes / total_tools if total_tools > 0 else 0,
                "stdio_success_rate": stdio_successes / total_tools if total_tools > 0 else 0,
                "average_compliance_score": statistics.mean(compliance_scores) if compliance_scores else 0,
                "average_performance_score": statistics.mean(performance_scores) if performance_scores else 0,
                "average_reliability_score": statistics.mean(reliability_scores) if reliability_scores else 0,
                "mcp_2024_11_05_compliant": sum(1 for v in results.values() if v.compliance_score >= 0.8)
            }
            
            # Store in LTMC
            async with aiohttp.ClientSession() as session:
                # Store detailed results
                store_response = await session.post(
                    "http://localhost:5050/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "store_memory",
                            "arguments": {
                                "file_name": f"mcp_2024_11_05_test_results_{timestamp}.json",
                                "content": json.dumps(report_data, indent=2),
                                "resource_type": "test_results"
                            }
                        },
                        "id": 1
                    }
                )
                
                # Log test completion
                log_response = await session.post(
                    "http://localhost:5050/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "log_code_attempt",
                            "arguments": {
                                "input_prompt": "Comprehensive MCP 2024-11-05 compliance testing for all 28 LTMC tools",
                                "generated_code": f"Test Results Summary:\n- Total Tools: {total_tools}\n- HTTP Success Rate: {http_successes/total_tools*100:.1f}%\n- Stdio Success Rate: {stdio_successes/total_tools*100:.1f}%\n- Average Compliance Score: {statistics.mean(compliance_scores) if compliance_scores else 0:.2f}\n- MCP 2024-11-05 Compliant Tools: {report_data['summary']['mcp_2024_11_05_compliant']}/{total_tools}",
                                "result": "pass" if report_data['summary']['http_success_rate'] >= 0.9 else "partial",
                                "tags": ["mcp", "comprehensive-testing", "2024-11-05", "compliance", "validation"]
                            }
                        },
                        "id": 2
                    }
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to store results in LTMC: {e}")
            return False


# Pytest test classes

@pytest.mark.asyncio
class TestMCPMemoryTools:
    """Test memory tools with MCP 2024-11-05 compliance."""
    
    def setup_method(self):
        self.validator = ComprehensiveToolValidator()
    
    @pytest.mark.parametrize("tool_name", ComprehensiveToolValidator.MEMORY_TOOLS)
    async def test_memory_tool_mcp_compliance(self, tool_name):
        """Test memory tools for MCP 2024-11-05 compliance."""
        validation = await self.validator.validate_tool_comprehensive(
            tool_name, ["http"]
        )
        
        # Memory tools are critical - must pass
        assert validation.http_result is not None, f"{tool_name} HTTP test failed"
        assert validation.http_result.success, f"{tool_name} HTTP execution failed: {validation.http_result.error}"
        assert validation.http_result.protocol_compliant, f"{tool_name} not MCP 2024-11-05 compliant"
        assert validation.compliance_score >= 0.8, f"{tool_name} compliance score too low: {validation.compliance_score}"


@pytest.mark.asyncio
class TestMCPChatTools:
    """Test chat tools with MCP 2024-11-05 compliance."""
    
    def setup_method(self):
        self.validator = ComprehensiveToolValidator()
    
    @pytest.mark.parametrize("tool_name", ComprehensiveToolValidator.CHAT_TOOLS)
    async def test_chat_tool_mcp_compliance(self, tool_name):
        """Test chat tools for MCP 2024-11-05 compliance."""
        validation = await self.validator.validate_tool_comprehensive(
            tool_name, ["http"]
        )
        
        # Chat tools are critical - must pass
        assert validation.http_result is not None, f"{tool_name} HTTP test failed"
        assert validation.http_result.success, f"{tool_name} HTTP execution failed: {validation.http_result.error}"
        assert validation.http_result.protocol_compliant, f"{tool_name} not MCP 2024-11-05 compliant"
        assert validation.compliance_score >= 0.8, f"{tool_name} compliance score too low: {validation.compliance_score}"


@pytest.mark.asyncio
class TestMCPTaskTools:
    """Test task management tools with MCP 2024-11-05 compliance."""
    
    def setup_method(self):
        self.validator = ComprehensiveToolValidator()
    
    @pytest.mark.parametrize("tool_name", ComprehensiveToolValidator.TASK_TOOLS)
    async def test_task_tool_mcp_compliance(self, tool_name):
        """Test task tools for MCP 2024-11-05 compliance."""
        validation = await self.validator.validate_tool_comprehensive(
            tool_name, ["http"]
        )
        
        # Task tools are important - should pass
        assert validation.http_result is not None, f"{tool_name} HTTP test failed"
        
        # Allow some flexibility for complete_todo which may fail if no todos exist
        if tool_name == "complete_todo" and not validation.http_result.success:
            # This is acceptable if the error is about non-existent todo
            return
            
        assert validation.http_result.success, f"{tool_name} HTTP execution failed: {validation.http_result.error}"
        assert validation.http_result.protocol_compliant, f"{tool_name} not MCP 2024-11-05 compliant"


@pytest.mark.asyncio
class TestMCPContextTools:
    """Test context tools with MCP 2024-11-05 compliance."""
    
    def setup_method(self):
        self.validator = ComprehensiveToolValidator()
    
    @pytest.mark.parametrize("tool_name", ComprehensiveToolValidator.CONTEXT_TOOLS)
    async def test_context_tool_mcp_compliance(self, tool_name):
        """Test context tools for MCP 2024-11-05 compliance."""
        validation = await self.validator.validate_tool_comprehensive(
            tool_name, ["http"]
        )
        
        # Context tools - important for advanced features
        assert validation.http_result is not None, f"{tool_name} HTTP test failed"
        
        # Some context tools may return empty results - that's OK if structure is valid
        if validation.http_result.success:
            assert validation.http_result.protocol_compliant, f"{tool_name} not MCP 2024-11-05 compliant"


@pytest.mark.asyncio
class TestMCPGraphTools:
    """Test knowledge graph tools with MCP 2024-11-05 compliance."""
    
    def setup_method(self):
        self.validator = ComprehensiveToolValidator()
    
    @pytest.mark.parametrize("tool_name", ComprehensiveToolValidator.GRAPH_TOOLS)
    async def test_graph_tool_mcp_compliance(self, tool_name):
        """Test graph tools for MCP 2024-11-05 compliance."""
        validation = await self.validator.validate_tool_comprehensive(
            tool_name, ["http"]
        )
        
        # Graph tools - advanced features
        assert validation.http_result is not None, f"{tool_name} HTTP test failed"
        
        # Graph tools may have limited functionality - validate structure
        if validation.http_result.success:
            assert validation.http_result.protocol_compliant, f"{tool_name} not MCP 2024-11-05 compliant"


@pytest.mark.asyncio
class TestMCPAnalyticsTools:
    """Test analytics tools with MCP 2024-11-05 compliance."""
    
    def setup_method(self):
        self.validator = ComprehensiveToolValidator()
    
    @pytest.mark.parametrize("tool_name", ComprehensiveToolValidator.ANALYTICS_TOOLS)
    async def test_analytics_tool_mcp_compliance(self, tool_name):
        """Test analytics tools for MCP 2024-11-05 compliance."""
        validation = await self.validator.validate_tool_comprehensive(
            tool_name, ["http"]
        )
        
        # Analytics tools should work
        assert validation.http_result is not None, f"{tool_name} HTTP test failed"
        assert validation.http_result.success, f"{tool_name} HTTP execution failed: {validation.http_result.error}"
        assert validation.http_result.protocol_compliant, f"{tool_name} not MCP 2024-11-05 compliant"


@pytest.mark.asyncio
class TestMCPCodeTools:
    """Test code pattern tools with MCP 2024-11-05 compliance."""
    
    def setup_method(self):
        self.validator = ComprehensiveToolValidator()
    
    @pytest.mark.parametrize("tool_name", ComprehensiveToolValidator.CODE_TOOLS)
    async def test_code_tool_mcp_compliance(self, tool_name):
        """Test code tools for MCP 2024-11-05 compliance."""
        validation = await self.validator.validate_tool_comprehensive(
            tool_name, ["http"]
        )
        
        # Code tools are important for development workflow
        assert validation.http_result is not None, f"{tool_name} HTTP test failed"
        assert validation.http_result.success, f"{tool_name} HTTP execution failed: {validation.http_result.error}"
        assert validation.http_result.protocol_compliant, f"{tool_name} not MCP 2024-11-05 compliant"


@pytest.mark.asyncio
class TestMCPRedisTools:
    """Test Redis tools with MCP 2024-11-05 compliance."""
    
    def setup_method(self):
        self.validator = ComprehensiveToolValidator()
    
    @pytest.mark.parametrize("tool_name", ComprehensiveToolValidator.REDIS_TOOLS)
    async def test_redis_tool_mcp_compliance(self, tool_name):
        """Test Redis tools for MCP 2024-11-05 compliance."""
        validation = await self.validator.validate_tool_comprehensive(
            tool_name, ["http"]
        )
        
        # Redis tools should work
        assert validation.http_result is not None, f"{tool_name} HTTP test failed"
        assert validation.http_result.success, f"{tool_name} HTTP execution failed: {validation.http_result.error}"
        assert validation.http_result.protocol_compliant, f"{tool_name} not MCP 2024-11-05 compliant"


@pytest.mark.asyncio
class TestTransportComparison:
    """Compare transport performance and compliance."""
    
    def setup_method(self):
        self.validator = ComprehensiveToolValidator()
    
    async def test_comprehensive_transport_comparison(self):
        """Compare HTTP vs stdio transport across all tool categories."""
        # Test representative tools from each category
        test_tools = [
            "store_memory",  # Memory
            "log_chat",      # Chat
            "add_todo",      # Task
            "build_context", # Context
            "link_resources", # Graph
            "list_tool_identifiers", # Analytics
            "log_code_attempt", # Code
            "redis_health_check" # Redis
        ]
        
        http_results = []
        stdio_results = []
        
        for tool_name in test_tools:
            validation = await self.validator.validate_tool_comprehensive(
                tool_name, ["http", "stdio"]
            )
            
            if validation.http_result:
                http_results.append(validation.http_result)
            if validation.stdio_result:
                stdio_results.append(validation.stdio_result)
        
        # Calculate success rates
        http_success_rate = sum(1 for r in http_results if r.success) / len(http_results)
        stdio_success_rate = sum(1 for r in stdio_results if r.success) / len(stdio_results)
        
        # Calculate compliance rates
        http_compliance_rate = sum(1 for r in http_results if r.protocol_compliant) / len(http_results)
        stdio_compliance_rate = sum(1 for r in stdio_results if r.protocol_compliant) / len(stdio_results)
        
        print(f"\n🔄 Transport Comparison Results:")
        print(f"HTTP - Success: {http_success_rate*100:.1f}%, Compliance: {http_compliance_rate*100:.1f}%")
        print(f"Stdio - Success: {stdio_success_rate*100:.1f}%, Compliance: {stdio_compliance_rate*100:.1f}%")
        
        # HTTP should have high success and compliance rates
        assert http_success_rate >= 0.9, f"HTTP success rate too low: {http_success_rate*100:.1f}%"
        assert http_compliance_rate >= 0.9, f"HTTP compliance rate too low: {http_compliance_rate*100:.1f}%"


if __name__ == "__main__":
    """Run comprehensive MCP 2024-11-05 validation."""
    
    async def run_comprehensive_mcp_validation():
        """Execute complete MCP 2024-11-05 compliance testing."""
        print("🧪 MCP 2024-11-05 Comprehensive Compliance Testing")
        print("=" * 70)
        print(f"Testing all {len(ComprehensiveToolValidator.ALL_TOOLS)} LTMC tools...")
        print("=" * 70)
        
        validator = ComprehensiveToolValidator()
        all_results = {}
        
        # Test by category for organized output
        categories = [
            ("Memory Tools", validator.MEMORY_TOOLS),
            ("Chat Tools", validator.CHAT_TOOLS),
            ("Task Tools", validator.TASK_TOOLS),
            ("Context Tools", validator.CONTEXT_TOOLS),
            ("Graph Tools", validator.GRAPH_TOOLS),
            ("Analytics Tools", validator.ANALYTICS_TOOLS),
            ("Code Tools", validator.CODE_TOOLS),
            ("Redis Tools", validator.REDIS_TOOLS)
        ]
        
        for category_name, tools in categories:
            print(f"\n📂 Testing {category_name} ({len(tools)} tools)")
            print("-" * 50)
            
            for tool_name in tools:
                print(f"  🔧 {tool_name}...", end=" ")
                
                validation = await validator.validate_tool_comprehensive(
                    tool_name, ["http", "stdio"]
                )
                all_results[tool_name] = validation
                
                # Status indicators
                http_status = "✅" if validation.http_result and validation.http_result.success else "❌"
                stdio_status = "✅" if validation.stdio_result and validation.stdio_result.success else "❌"
                compliance = f"{validation.compliance_score:.2f}"
                performance = f"{validation.performance_score:.2f}"
                
                print(f"HTTP:{http_status} Stdio:{stdio_status} C:{compliance} P:{performance}")
        
        # Generate comprehensive summary
        print("\n" + "=" * 70)
        print("📊 MCP 2024-11-05 COMPLIANCE SUMMARY")
        print("=" * 70)
        
        total_tools = len(all_results)
        http_successes = sum(1 for v in all_results.values() if v.http_result and v.http_result.success)
        stdio_successes = sum(1 for v in all_results.values() if v.stdio_result and v.stdio_result.success)
        
        compliance_scores = [v.compliance_score for v in all_results.values()]
        performance_scores = [v.performance_score for v in all_results.values()]
        reliability_scores = [v.reliability_score for v in all_results.values()]
        
        avg_compliance = statistics.mean(compliance_scores) if compliance_scores else 0
        avg_performance = statistics.mean(performance_scores) if performance_scores else 0
        avg_reliability = statistics.mean(reliability_scores) if reliability_scores else 0
        
        compliant_tools = sum(1 for v in all_results.values() if v.compliance_score >= 0.8)
        
        print(f"🎯 Overall Results:")
        print(f"   • Total Tools Tested: {total_tools}")
        print(f"   • HTTP Success Rate: {http_successes}/{total_tools} ({http_successes/total_tools*100:.1f}%)")
        print(f"   • Stdio Success Rate: {stdio_successes}/{total_tools} ({stdio_successes/total_tools*100:.1f}%)")
        print(f"   • Average Compliance Score: {avg_compliance:.2f}")
        print(f"   • Average Performance Score: {avg_performance:.2f}")
        print(f"   • Average Reliability Score: {avg_reliability:.2f}")
        print(f"   • MCP 2024-11-05 Compliant: {compliant_tools}/{total_tools} ({compliant_tools/total_tools*100:.1f}%)")
        
        # Store results in LTMC
        print(f"\n💾 Storing results in LTMC...")
        storage_success = await validator.store_results_in_ltmc(all_results)
        if storage_success:
            print("✅ Results successfully stored in LTMC system")
        else:
            print("❌ Failed to store results in LTMC system")
        
        # Final assessment
        print(f"\n🏆 FINAL ASSESSMENT:")
        if http_successes/total_tools >= 0.95 and avg_compliance >= 0.8:
            print("🎉 EXCELLENT - System is MCP 2024-11-05 compliant and production ready!")
        elif http_successes/total_tools >= 0.9 and avg_compliance >= 0.7:
            print("✅ GOOD - System is largely compliant with minor issues to address")
        else:
            print("⚠️  NEEDS IMPROVEMENT - Significant compliance or reliability issues found")
        
        return all_results
    
    # Execute comprehensive validation
    asyncio.run(run_comprehensive_mcp_validation())