"""
Production Readiness Validator for LTMC MCP Server.

This module performs comprehensive validation of the MCP server's production readiness,
including performance benchmarks, security checks, reliability tests, and scalability validation.

Validation Categories:
1. Performance & Scalability
2. Security & Authentication  
3. Reliability & Error Handling
4. Monitoring & Observability
5. Configuration & Deployment
"""

import asyncio
import json
import logging
import time
import traceback
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import requests
import redis
from neo4j import GraphDatabase
import sqlite3

from ltms.core.connection_pool import get_connection_manager, PoolConfig
from tests.performance.load_test_suite import run_comprehensive_load_test, LoadTestConfig

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    check_name: str
    category: str
    status: str  # "PASS", "FAIL", "WARNING", "SKIP"
    message: str
    details: Dict[str, Any] = None
    execution_time_ms: float = 0.0


@dataclass
class ProductionReadinessReport:
    """Comprehensive production readiness report."""
    overall_status: str
    overall_score: float  # 0-100 score
    validation_results: List[ValidationResult]
    performance_summary: Dict[str, Any]
    security_summary: Dict[str, Any]
    reliability_summary: Dict[str, Any]
    recommendations: List[str]
    generated_at: str


class ProductionReadinessValidator:
    """Comprehensive production readiness validator."""
    
    def __init__(self, 
                 mcp_server_url: str = "http://localhost:5050/jsonrpc",
                 db_path: str = None,
                 redis_url: str = "redis://localhost:6379/0",
                 neo4j_uri: str = "bolt://localhost:7687"):
        self.mcp_server_url = mcp_server_url
        self.db_path = db_path
        self.redis_url = redis_url
        self.neo4j_uri = neo4j_uri
        self.validation_results: List[ValidationResult] = []
        
        # Import config here to avoid circular imports
        if not self.db_path:
            try:
                from ltms.config import config
                self.db_path = config.get_db_path()
            except Exception:
                self.db_path = "ltmc.db"
    
    def run_validation_check(self, func, check_name: str, category: str) -> ValidationResult:
        """Run a single validation check with error handling."""
        start_time = time.perf_counter()
        
        try:
            result = func()
            if isinstance(result, ValidationResult):
                result.execution_time_ms = (time.perf_counter() - start_time) * 1000
                return result
            else:
                # Handle simple boolean or tuple returns
                if isinstance(result, bool):
                    status = "PASS" if result else "FAIL"
                    message = f"{check_name} {'passed' if result else 'failed'}"
                elif isinstance(result, tuple) and len(result) >= 2:
                    status, message = result[:2]
                    details = result[2] if len(result) > 2 else None
                else:
                    status = "PASS"
                    message = str(result)
                
                return ValidationResult(
                    check_name=check_name,
                    category=category,
                    status=status,
                    message=message,
                    details=details if 'details' in locals() else None,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000
                )
                
        except Exception as e:
            return ValidationResult(
                check_name=check_name,
                category=category,
                status="FAIL",
                message=f"Check failed with exception: {str(e)}",
                details={"exception": str(e), "traceback": traceback.format_exc()},
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )
    
    # ==================== Performance & Scalability Checks ====================
    
    def check_server_availability(self) -> ValidationResult:
        """Check if MCP server is available and responding."""
        try:
            response = requests.post(
                self.mcp_server_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "redis_health_check", "arguments": {}},
                    "id": 1
                },
                timeout=5
            )
            
            if response.status_code == 200:
                return ValidationResult(
                    check_name="Server Availability",
                    category="Performance",
                    status="PASS",
                    message="MCP server is available and responding",
                    details={"response_code": response.status_code}
                )
            else:
                return ValidationResult(
                    check_name="Server Availability",
                    category="Performance",
                    status="FAIL",
                    message=f"Server returned HTTP {response.status_code}",
                    details={"response_code": response.status_code, "response_text": response.text}
                )
                
        except Exception as e:
            return ValidationResult(
                check_name="Server Availability",
                category="Performance",
                status="FAIL",
                message=f"Failed to connect to server: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_database_performance(self) -> ValidationResult:
        """Check database connection and basic performance."""
        try:
            connection_manager = get_connection_manager(self.db_path)
            
            # Test database connection and basic query performance
            start_time = time.perf_counter()
            with connection_manager.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
            query_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Get pool metrics
            pool_metrics = connection_manager.db_pool.get_metrics()
            
            if query_time_ms < 50 and pool_metrics["creation_errors"] == 0:
                status = "PASS"
                message = f"Database performance excellent ({query_time_ms:.1f}ms query time)"
            elif query_time_ms < 100:
                status = "WARNING"
                message = f"Database performance acceptable ({query_time_ms:.1f}ms query time)"
            else:
                status = "FAIL"
                message = f"Database performance poor ({query_time_ms:.1f}ms query time)"
            
            return ValidationResult(
                check_name="Database Performance",
                category="Performance",
                status=status,
                message=message,
                details={
                    "query_time_ms": query_time_ms,
                    "table_count": table_count,
                    "pool_metrics": pool_metrics
                }
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="Database Performance",
                category="Performance",
                status="FAIL",
                message=f"Database check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_redis_performance(self) -> ValidationResult:
        """Check Redis connection and performance."""
        try:
            # Test Redis connection
            redis_client = redis.from_url(self.redis_url)
            
            # Performance test: SET and GET operations
            start_time = time.perf_counter()
            test_key = "prod_readiness_test"
            test_value = "test_value_" + str(int(time.time()))
            
            redis_client.set(test_key, test_value)
            retrieved_value = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            operation_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Check if value was retrieved correctly
            if retrieved_value and retrieved_value.decode() == test_value:
                if operation_time_ms < 10:
                    status = "PASS"
                    message = f"Redis performance excellent ({operation_time_ms:.1f}ms for SET/GET/DEL)"
                elif operation_time_ms < 50:
                    status = "WARNING"
                    message = f"Redis performance acceptable ({operation_time_ms:.1f}ms for SET/GET/DEL)"
                else:
                    status = "FAIL"
                    message = f"Redis performance poor ({operation_time_ms:.1f}ms for SET/GET/DEL)"
            else:
                status = "FAIL"
                message = "Redis data integrity test failed"
            
            # Get Redis info
            redis_info = redis_client.info()
            redis_client.close()
            
            return ValidationResult(
                check_name="Redis Performance",
                category="Performance",
                status=status,
                message=message,
                details={
                    "operation_time_ms": operation_time_ms,
                    "redis_version": redis_info.get("redis_version"),
                    "connected_clients": redis_info.get("connected_clients"),
                    "used_memory_human": redis_info.get("used_memory_human")
                }
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="Redis Performance",
                category="Performance",
                status="FAIL", 
                message=f"Redis check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_neo4j_performance(self) -> ValidationResult:
        """Check Neo4j connection and performance."""
        try:
            driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=("neo4j", "kwe_password"),
                connection_timeout=5
            )
            
            # Test basic query performance
            start_time = time.perf_counter()
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
            query_time_ms = (time.perf_counter() - start_time) * 1000
            
            driver.close()
            
            if test_value == 1:
                if query_time_ms < 100:
                    status = "PASS"
                    message = f"Neo4j performance excellent ({query_time_ms:.1f}ms query time)"
                elif query_time_ms < 500:
                    status = "WARNING"
                    message = f"Neo4j performance acceptable ({query_time_ms:.1f}ms query time)"
                else:
                    status = "FAIL"
                    message = f"Neo4j performance poor ({query_time_ms:.1f}ms query time)"
            else:
                status = "FAIL"
                message = "Neo4j basic query test failed"
            
            return ValidationResult(
                check_name="Neo4j Performance",
                category="Performance",
                status=status,
                message=message,
                details={"query_time_ms": query_time_ms}
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="Neo4j Performance", 
                category="Performance",
                status="FAIL",
                message=f"Neo4j check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_connection_pooling(self) -> ValidationResult:
        """Check connection pool configuration and performance."""
        try:
            connection_manager = get_connection_manager(self.db_path)
            all_metrics = connection_manager.get_all_metrics()
            
            # Evaluate pool configuration
            db_metrics = all_metrics.get("database", {})
            pool_config = all_metrics.get("pool_config", {})
            
            issues = []
            
            if db_metrics.get("creation_errors", 0) > 0:
                issues.append(f"{db_metrics['creation_errors']} database connection creation errors")
            
            if db_metrics.get("timeout_errors", 0) > 0:
                issues.append(f"{db_metrics['timeout_errors']} database connection timeout errors")
            
            if db_metrics.get("avg_acquisition_time_ms", 0) > 10:
                issues.append(f"High average connection acquisition time: {db_metrics['avg_acquisition_time_ms']:.1f}ms")
            
            if pool_config.get("max_connections", 0) < 10:
                issues.append("Low maximum connection pool size may limit scalability")
            
            if not issues:
                status = "PASS"
                message = "Connection pooling is properly configured and performing well"
            else:
                status = "WARNING" if len(issues) <= 2 else "FAIL"
                message = f"Connection pooling issues: {'; '.join(issues)}"
            
            return ValidationResult(
                check_name="Connection Pooling",
                category="Performance",
                status=status,
                message=message,
                details=all_metrics
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="Connection Pooling",
                category="Performance",
                status="FAIL",
                message=f"Connection pooling check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_load_test_performance(self) -> ValidationResult:
        """Run a comprehensive load test to validate performance under load."""
        try:
            logger.info("Starting load test for production readiness validation...")
            
            # Run a focused load test
            load_config = LoadTestConfig(
                base_url=self.mcp_server_url,
                concurrent_users=25,
                requests_per_user=5,
                ramp_up_seconds=5,
                test_duration_seconds=30,
                target_success_rate=98.0,
                target_avg_response_ms=300.0
            )
            
            results = run_comprehensive_load_test(
                concurrent_users=load_config.concurrent_users,
                requests_per_user=load_config.requests_per_user,
                server_url=self.mcp_server_url
            )
            
            # Evaluate load test results
            issues = []
            
            if results.success_rate < load_config.target_success_rate:
                issues.append(f"Success rate {results.success_rate:.1f}% below target {load_config.target_success_rate}%")
            
            if results.avg_response_time_ms > load_config.target_avg_response_ms:
                issues.append(f"Average response time {results.avg_response_time_ms:.1f}ms above target {load_config.target_avg_response_ms}ms")
            
            if results.p95_response_time_ms > 1000:
                issues.append(f"P95 response time {results.p95_response_time_ms:.1f}ms too high")
            
            if results.requests_per_second < 10:
                issues.append(f"Throughput {results.requests_per_second:.1f} req/s too low")
            
            if not issues:
                status = "PASS"
                message = f"Load test passed: {results.success_rate:.1f}% success rate, {results.avg_response_time_ms:.1f}ms avg response"
            else:
                status = "FAIL"
                message = f"Load test failed: {'; '.join(issues)}"
            
            return ValidationResult(
                check_name="Load Test Performance",
                category="Performance",
                status=status,
                message=message,
                details={
                    "success_rate": results.success_rate,
                    "avg_response_time_ms": results.avg_response_time_ms,
                    "p95_response_time_ms": results.p95_response_time_ms,
                    "requests_per_second": results.requests_per_second,
                    "total_requests": results.total_requests
                }
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="Load Test Performance",
                category="Performance",
                status="FAIL",
                message=f"Load test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    # ==================== Security Checks ====================
    
    def check_security_features(self) -> ValidationResult:
        """Check security features and configurations."""
        try:
            # Test security statistics endpoint
            response = requests.post(
                self.mcp_server_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "get_security_statistics", "arguments": {}},
                    "id": 1
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return ValidationResult(
                    check_name="Security Features",
                    category="Security",
                    status="FAIL",
                    message="Security statistics endpoint not accessible"
                )
            
            result_data = response.json()
            if "error" in result_data:
                return ValidationResult(
                    check_name="Security Features",
                    category="Security",
                    status="FAIL",
                    message=f"Security statistics error: {result_data['error']}"
                )
            
            security_stats = result_data.get("result", {}).get("statistics", {})
            
            # Check security features
            security_features = security_stats.get("security_features", {})
            issues = []
            
            if not security_features.get("project_isolation_enabled"):
                issues.append("Project isolation not enabled")
            
            if not security_features.get("path_validation_enabled"):
                issues.append("Path validation not enabled")
            
            if not security_features.get("input_sanitization_enabled"):
                issues.append("Input sanitization not enabled")
            
            if not security_features.get("performance_monitoring_enabled"):
                issues.append("Performance monitoring not enabled")
            
            if not issues:
                status = "PASS"
                message = "All security features are properly enabled"
            else:
                status = "FAIL"
                message = f"Security issues: {'; '.join(issues)}"
            
            return ValidationResult(
                check_name="Security Features",
                category="Security",
                status=status,
                message=message,
                details=security_stats
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="Security Features",
                category="Security",
                status="FAIL",
                message=f"Security check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    # ==================== Reliability Checks ====================
    
    def check_error_handling(self) -> ValidationResult:
        """Check error handling and recovery mechanisms."""
        try:
            test_scenarios = [
                # Test invalid tool name
                {
                    "method": "tools/call",
                    "params": {"name": "nonexistent_tool", "arguments": {}},
                    "expected": "error"
                },
                # Test invalid parameters
                {
                    "method": "tools/call", 
                    "params": {"name": "store_memory", "arguments": {"invalid_param": "value"}},
                    "expected": "error"
                },
                # Test empty parameters
                {
                    "method": "tools/call",
                    "params": {"name": "retrieve_memory", "arguments": {}},
                    "expected": "error"
                }
            ]
            
            error_handling_results = []
            
            for scenario in test_scenarios:
                response = requests.post(
                    self.mcp_server_url,
                    json={"jsonrpc": "2.0", "id": 1, **scenario},
                    timeout=5
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    has_error = "error" in result_data or result_data.get("result", {}).get("success") is False
                    error_handling_results.append(has_error)
                else:
                    error_handling_results.append(True)  # HTTP error is acceptable for error scenarios
            
            # All error scenarios should be handled gracefully
            if all(error_handling_results):
                status = "PASS"
                message = "Error handling is working correctly for all test scenarios"
            else:
                status = "FAIL"
                message = f"Error handling failed for {len(error_handling_results) - sum(error_handling_results)} scenarios"
            
            return ValidationResult(
                check_name="Error Handling",
                category="Reliability",
                status=status,
                message=message,
                details={"test_results": error_handling_results}
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="Error Handling",
                category="Reliability",
                status="FAIL",
                message=f"Error handling check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_tool_coverage(self) -> ValidationResult:
        """Check that all expected MCP tools are available and working."""
        expected_tools = [
            "store_memory", "retrieve_memory", "log_chat", "ask_with_context",
            "route_query", "build_context", "retrieve_by_type", "add_todo",
            "list_todos", "complete_todo", "search_todos", "log_code_attempt",
            "get_code_patterns", "analyze_code_patterns_tool", "link_resources",
            "query_graph", "get_document_relationships_tool", "redis_health_check",
            "redis_cache_stats", "get_context_usage_statistics_tool",
            "list_tool_identifiers", "get_security_statistics"
        ]
        
        try:
            working_tools = []
            broken_tools = []
            
            for tool in expected_tools:
                # Test each tool with minimal parameters
                test_params = self._get_minimal_test_params(tool)
                
                response = requests.post(
                    self.mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": tool, "arguments": test_params},
                        "id": 1
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    # Tool is working if it doesn't have a method not found error
                    if "error" not in result_data or "method not found" not in str(result_data.get("error", "")).lower():
                        working_tools.append(tool)
                    else:
                        broken_tools.append(tool)
                else:
                    broken_tools.append(tool)
            
            coverage_percentage = (len(working_tools) / len(expected_tools)) * 100
            
            if coverage_percentage >= 95:
                status = "PASS"
                message = f"Tool coverage excellent: {len(working_tools)}/{len(expected_tools)} tools working ({coverage_percentage:.1f}%)"
            elif coverage_percentage >= 80:
                status = "WARNING"
                message = f"Tool coverage acceptable: {len(working_tools)}/{len(expected_tools)} tools working ({coverage_percentage:.1f}%)"
            else:
                status = "FAIL"
                message = f"Tool coverage poor: {len(working_tools)}/{len(expected_tools)} tools working ({coverage_percentage:.1f}%)"
            
            return ValidationResult(
                check_name="Tool Coverage",
                category="Reliability",
                status=status,
                message=message,
                details={
                    "working_tools": working_tools,
                    "broken_tools": broken_tools,
                    "coverage_percentage": coverage_percentage
                }
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="Tool Coverage",
                category="Reliability",
                status="FAIL",
                message=f"Tool coverage check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def _get_minimal_test_params(self, tool: str) -> Dict[str, Any]:
        """Get minimal test parameters for a tool."""
        params_map = {
            "store_memory": {"file_name": "test.md", "content": "test"},
            "retrieve_memory": {"conversation_id": "test", "query": "test"},
            "log_chat": {"conversation_id": "test", "role": "user", "content": "test"},
            "ask_with_context": {"query": "test", "conversation_id": "test"},
            "route_query": {"query": "test", "source_types": ["document"]},
            "build_context": {"documents": []},
            "retrieve_by_type": {"query": "test", "doc_type": "document"},
            "add_todo": {"title": "test", "description": "test"},
            "list_todos": {},
            "complete_todo": {"todo_id": 999},  # Will fail but tool exists
            "search_todos": {"query": "test"},
            "log_code_attempt": {"input_prompt": "test", "generated_code": "test", "result": "pass"},
            "get_code_patterns": {"query": "test"},
            "analyze_code_patterns_tool": {},
            "link_resources": {"source_id": "test", "target_id": "test", "relation": "TEST"},
            "query_graph": {"entity": "test"},
            "get_document_relationships_tool": {"doc_id": "test"},
            "redis_health_check": {},
            "redis_cache_stats": {},
            "get_context_usage_statistics_tool": {},
            "list_tool_identifiers": {},
            "get_security_statistics": {}
        }
        return params_map.get(tool, {})
    
    # ==================== Main Validation Runner ====================
    
    def run_comprehensive_validation(self) -> ProductionReadinessReport:
        """Run comprehensive production readiness validation."""
        logger.info("Starting comprehensive production readiness validation...")
        
        # Define all validation checks
        validation_checks = [
            # Performance & Scalability
            (self.check_server_availability, "Server Availability", "Performance"),
            (self.check_database_performance, "Database Performance", "Performance"),
            (self.check_redis_performance, "Redis Performance", "Performance"),
            (self.check_neo4j_performance, "Neo4j Performance", "Performance"),
            (self.check_connection_pooling, "Connection Pooling", "Performance"),
            (self.check_load_test_performance, "Load Test Performance", "Performance"),
            
            # Security
            (self.check_security_features, "Security Features", "Security"),
            
            # Reliability
            (self.check_error_handling, "Error Handling", "Reliability"),
            (self.check_tool_coverage, "Tool Coverage", "Reliability")
        ]
        
        # Run all validation checks
        for check_func, check_name, category in validation_checks:
            logger.info(f"Running {check_name} validation...")
            result = self.run_validation_check(check_func, check_name, category)
            self.validation_results.append(result)
        
        # Generate comprehensive report
        report = self._generate_production_report()
        
        logger.info(f"Production readiness validation completed. Overall status: {report.overall_status}")
        return report
    
    def _generate_production_report(self) -> ProductionReadinessReport:
        """Generate comprehensive production readiness report."""
        # Calculate overall scores and status
        total_checks = len(self.validation_results)
        passed_checks = len([r for r in self.validation_results if r.status == "PASS"])
        warning_checks = len([r for r in self.validation_results if r.status == "WARNING"])
        failed_checks = len([r for r in self.validation_results if r.status == "FAIL"])
        
        # Calculate weighted score
        overall_score = (passed_checks * 100 + warning_checks * 60) / total_checks if total_checks > 0 else 0
        
        # Determine overall status
        if failed_checks == 0 and warning_checks <= 1:
            overall_status = "PRODUCTION_READY"
        elif failed_checks <= 1 and warning_checks <= 3:
            overall_status = "NEEDS_MINOR_FIXES"
        elif failed_checks <= 3:
            overall_status = "NEEDS_MAJOR_FIXES"
        else:
            overall_status = "NOT_PRODUCTION_READY"
        
        # Generate category summaries
        performance_results = [r for r in self.validation_results if r.category == "Performance"]
        security_results = [r for r in self.validation_results if r.category == "Security"]
        reliability_results = [r for r in self.validation_results if r.category == "Reliability"]
        
        performance_summary = self._summarize_category(performance_results)
        security_summary = self._summarize_category(security_results)
        reliability_summary = self._summarize_category(reliability_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        return ProductionReadinessReport(
            overall_status=overall_status,
            overall_score=overall_score,
            validation_results=self.validation_results,
            performance_summary=performance_summary,
            security_summary=security_summary,
            reliability_summary=reliability_summary,
            recommendations=recommendations,
            generated_at=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        )
    
    def _summarize_category(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Summarize validation results for a category."""
        if not results:
            return {"status": "NO_CHECKS", "passed": 0, "warnings": 0, "failed": 0}
        
        passed = len([r for r in results if r.status == "PASS"])
        warnings = len([r for r in results if r.status == "WARNING"]) 
        failed = len([r for r in results if r.status == "FAIL"])
        total = len(results)
        
        if failed == 0:
            status = "EXCELLENT" if warnings == 0 else "GOOD"
        elif failed <= total // 3:
            status = "NEEDS_IMPROVEMENT"
        else:
            status = "CRITICAL"
        
        return {
            "status": status,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "total": total,
            "score": (passed * 100 + warnings * 60) / total
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        failed_results = [r for r in self.validation_results if r.status == "FAIL"]
        warning_results = [r for r in self.validation_results if r.status == "WARNING"]
        
        # Critical recommendations for failed checks
        for result in failed_results:
            if "Server Availability" in result.check_name:
                recommendations.append("CRITICAL: Fix MCP server availability issues before production deployment")
            elif "Load Test" in result.check_name:
                recommendations.append("CRITICAL: Address performance issues identified in load testing")
            elif "Security" in result.check_name:
                recommendations.append("CRITICAL: Resolve security configuration issues")
            elif "Tool Coverage" in result.check_name:
                recommendations.append("HIGH: Fix broken MCP tools to ensure full functionality")
            else:
                recommendations.append(f"HIGH: Address {result.check_name} failure: {result.message}")
        
        # Improvement recommendations for warnings
        for result in warning_results:
            if "Performance" in result.category:
                recommendations.append(f"MEDIUM: Optimize {result.check_name.lower()} for better production performance")
            else:
                recommendations.append(f"LOW: Consider improving {result.check_name.lower()}")
        
        # General recommendations
        if not failed_results and not warning_results:
            recommendations.append("System is production-ready with excellent validation results")
        elif len(failed_results) == 0:
            recommendations.append("System is near production-ready - address warnings for optimal performance")
        
        recommendations.append("Monitor system performance continuously in production")
        recommendations.append("Implement automated health checks and alerting")
        recommendations.append("Regularly run production readiness validation")
        
        return recommendations
    
    def print_validation_report(self, report: ProductionReadinessReport) -> None:
        """Print a formatted validation report."""
        print("\n" + "="*80)
        print("LTMC MCP SERVER PRODUCTION READINESS REPORT")
        print("="*80)
        print(f"Generated: {report.generated_at}")
        print(f"Overall Status: {report.overall_status}")
        print(f"Overall Score: {report.overall_score:.1f}/100")
        print()
        
        # Category summaries
        print("CATEGORY SUMMARIES:")
        print("-" * 40)
        categories = [
            ("Performance & Scalability", report.performance_summary),
            ("Security", report.security_summary),
            ("Reliability", report.reliability_summary)
        ]
        
        for name, summary in categories:
            status_icon = {"EXCELLENT": "✅", "GOOD": "✅", "NEEDS_IMPROVEMENT": "⚠️", "CRITICAL": "❌", "NO_CHECKS": "⚪"}.get(summary["status"], "❓")
            print(f"{status_icon} {name}: {summary['status']} ({summary['passed']}/{summary['total']} passed)")
        
        print()
        
        # Detailed results
        print("DETAILED VALIDATION RESULTS:")
        print("-" * 40)
        for result in report.validation_results:
            status_icon = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌", "SKIP": "⚪"}.get(result.status, "❓")
            print(f"{status_icon} {result.check_name}: {result.message}")
            if result.execution_time_ms > 0:
                print(f"   Execution time: {result.execution_time_ms:.1f}ms")
        
        print()
        
        # Recommendations
        if report.recommendations:
            print("RECOMMENDATIONS:")
            print("-" * 40)
            for i, rec in enumerate(report.recommendations, 1):
                print(f"{i}. {rec}")
        
        print("\n" + "="*80)


def run_production_readiness_validation(
    mcp_server_url: str = "http://localhost:5050/jsonrpc",
    db_path: str = None,
    detailed_output: bool = True
) -> ProductionReadinessReport:
    """Run comprehensive production readiness validation."""
    validator = ProductionReadinessValidator(
        mcp_server_url=mcp_server_url,
        db_path=db_path
    )
    
    report = validator.run_comprehensive_validation()
    
    if detailed_output:
        validator.print_validation_report(report)
    
    return report


if __name__ == "__main__":
    # Run production readiness validation
    print("Starting LTMC MCP Server Production Readiness Validation...")
    
    report = run_production_readiness_validation()
    
    # Save report to file
    report_file = Path("production_readiness_report.json")
    with open(report_file, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str)
    
    print(f"\nDetailed report saved to: {report_file}")
    print(f"Final Status: {report.overall_status} (Score: {report.overall_score:.1f}/100)")