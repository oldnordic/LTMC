#!/usr/bin/env python3
"""
Comprehensive MCP 2024-11-05 Testing Suite Runner

This script orchestrates systematic testing of all 28 LTMC tools with:
- MCP 2024-11-05 protocol compliance validation
- JSON-RPC 2.0 specification verification
- Performance benchmarking and analysis
- Error handling and edge case testing
- Detailed reporting with LTMC integration
- Statistical analysis and trend tracking
"""

import asyncio
import json
import sys
import time
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.comprehensive.test_mcp_2024_11_05_compliance import (
    ComprehensiveToolValidator, 
    ComprehensiveValidation,
    MCPTestResult
)


class MCPTestOrchestrator:
    """Orchestrates comprehensive MCP testing across all tools and transports."""
    
    def __init__(self):
        self.validator = ComprehensiveToolValidator()
        self.test_results = {}
        self.session_id = f"mcp_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def run_full_test_suite(
        self, 
        transports: List[str] = ["http", "stdio"],
        include_performance_tests: bool = True,
        include_error_tests: bool = True,
        store_in_ltmc: bool = True
    ) -> Dict[str, Any]:
        """Run complete test suite with comprehensive validation."""
        
        print("🚀 Starting Comprehensive MCP 2024-11-05 Test Suite")
        print("=" * 80)
        print(f"Session ID: {self.session_id}")
        print(f"Testing {len(self.validator.ALL_TOOLS)} tools across {len(transports)} transports")
        print(f"Options: Performance={include_performance_tests}, Errors={include_error_tests}, LTMC={store_in_ltmc}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Phase 1: Basic functionality tests
        await self._run_basic_functionality_tests(transports)
        
        # Phase 2: Performance tests
        if include_performance_tests:
            await self._run_performance_tests(transports)
        
        # Phase 3: Error handling tests
        if include_error_tests:
            await self._run_error_handling_tests()
        
        # Phase 4: Analysis and reporting
        test_summary = await self._analyze_results()
        
        # Phase 5: Store in LTMC
        if store_in_ltmc:
            await self._store_comprehensive_results(test_summary)
        
        total_duration = time.time() - start_time
        test_summary["test_duration"] = total_duration
        
        await self._generate_final_report(test_summary)
        
        return test_summary
    
    async def _run_basic_functionality_tests(self, transports: List[str]):
        """Run basic functionality tests for all tools."""
        print("\n📋 Phase 1: Basic Functionality Testing")
        print("-" * 50)
        
        categories = [
            ("Memory", self.validator.MEMORY_TOOLS),
            ("Chat", self.validator.CHAT_TOOLS),
            ("Task", self.validator.TASK_TOOLS),
            ("Context", self.validator.CONTEXT_TOOLS),
            ("Graph", self.validator.GRAPH_TOOLS),
            ("Analytics", self.validator.ANALYTICS_TOOLS),
            ("Code", self.validator.CODE_TOOLS),
            ("Redis", self.validator.REDIS_TOOLS)
        ]
        
        for category_name, tools in categories:
            print(f"\n  📂 {category_name} Tools ({len(tools)} tools)")
            
            for tool_name in tools:
                print(f"    🔧 Testing {tool_name}...", end=" ", flush=True)
                
                validation = await self.validator.validate_tool_comprehensive(
                    tool_name, transports
                )
                self.test_results[tool_name] = validation
                
                # Status output
                status = "✅" if validation.overall_success else "⚠️ " if any(
                    r.success for r in [validation.http_result, validation.stdio_result] if r
                ) else "❌"
                print(f"{status}")
    
    async def _run_performance_tests(self, transports: List[str]):
        """Run performance benchmarking tests."""
        print("\n⚡ Phase 2: Performance Benchmarking")
        print("-" * 50)
        
        # Test critical tools under performance conditions
        critical_tools = [
            "store_memory", "retrieve_memory", "log_chat", 
            "ask_with_context", "add_todo", "redis_health_check"
        ]
        
        performance_results = {}
        
        for tool_name in critical_tools:
            print(f"  📊 Benchmarking {tool_name}...", end=" ", flush=True)
            
            # Run multiple iterations for statistical analysis
            iterations = 5
            durations = []
            
            for i in range(iterations):
                validation = await self.validator.validate_tool_comprehensive(
                    tool_name, ["http"]  # Use HTTP for consistent performance testing
                )
                
                if validation.http_result:
                    durations.append(validation.http_result.duration)
            
            if durations:
                avg_duration = statistics.mean(durations)
                std_dev = statistics.stdev(durations) if len(durations) > 1 else 0
                min_duration = min(durations)
                max_duration = max(durations)
                
                performance_results[tool_name] = {
                    "average_duration": avg_duration,
                    "std_deviation": std_dev,
                    "min_duration": min_duration,
                    "max_duration": max_duration,
                    "iterations": iterations,
                    "performance_score": min(1.0, max(0.0, 1.0 - (avg_duration / 5.0)))
                }
                
                print(f"Avg: {avg_duration:.2f}s (±{std_dev:.2f}s)")
            else:
                print("Failed")
                performance_results[tool_name] = {"error": "No successful runs"}
        
        self.test_results["performance_benchmarks"] = performance_results
    
    async def _run_error_handling_tests(self):
        """Run comprehensive error handling tests."""
        print("\n🛡️  Phase 3: Error Handling Validation")
        print("-" * 50)
        
        # Test error scenarios for critical tools
        error_test_tools = [
            "store_memory", "retrieve_memory", "log_chat", 
            "add_todo", "link_resources", "log_code_attempt"
        ]
        
        error_results = {}
        
        async with self.validator.http_tester as http:
            for tool_name in error_test_tools:
                print(f"  🔍 Error testing {tool_name}...", end=" ", flush=True)
                
                error_tests = await http.test_error_handling(tool_name)
                success_count = sum(1 for test in error_tests if test.success)
                
                error_results[tool_name] = {
                    "total_error_tests": len(error_tests),
                    "successful_error_handling": success_count,
                    "error_handling_rate": success_count / len(error_tests) if error_tests else 0,
                    "test_details": [test.to_dict() for test in error_tests]
                }
                
                print(f"{success_count}/{len(error_tests)} passed")
        
        self.test_results["error_handling"] = error_results
    
    async def _analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and generate summary statistics."""
        print("\n📈 Phase 4: Results Analysis")
        print("-" * 50)
        
        # Basic statistics
        total_tools = len([k for k in self.test_results.keys() if isinstance(self.test_results[k], ComprehensiveValidation)])
        http_successes = sum(1 for v in self.test_results.values() 
                           if isinstance(v, ComprehensiveValidation) and v.http_result and v.http_result.success)
        stdio_successes = sum(1 for v in self.test_results.values() 
                            if isinstance(v, ComprehensiveValidation) and v.stdio_result and v.stdio_result.success)
        
        # Compliance analysis
        compliance_scores = []
        performance_scores = []
        reliability_scores = []
        
        for key, validation in self.test_results.items():
            if isinstance(validation, ComprehensiveValidation):
                compliance_scores.append(validation.compliance_score)
                performance_scores.append(validation.performance_score)
                reliability_scores.append(validation.reliability_score)
        
        # Category-wise analysis
        category_stats = {}
        categories = [
            ("memory", self.validator.MEMORY_TOOLS),
            ("chat", self.validator.CHAT_TOOLS),
            ("task", self.validator.TASK_TOOLS),
            ("context", self.validator.CONTEXT_TOOLS),
            ("graph", self.validator.GRAPH_TOOLS),
            ("analytics", self.validator.ANALYTICS_TOOLS),
            ("code", self.validator.CODE_TOOLS),
            ("redis", self.validator.REDIS_TOOLS)
        ]
        
        for cat_name, tools in categories:
            cat_results = [self.test_results[tool] for tool in tools if tool in self.test_results]
            cat_http_success = sum(1 for v in cat_results if v.http_result and v.http_result.success)
            cat_stdio_success = sum(1 for v in cat_results if v.stdio_result and v.stdio_result.success)
            
            category_stats[cat_name] = {
                "total_tools": len(tools),
                "http_success_rate": cat_http_success / len(tools) if tools else 0,
                "stdio_success_rate": cat_stdio_success / len(tools) if tools else 0,
                "tools": tools
            }
        
        # Performance analysis
        performance_summary = {}
        if "performance_benchmarks" in self.test_results:
            perf_data = self.test_results["performance_benchmarks"]
            avg_durations = [data.get("average_duration", 0) for data in perf_data.values() if isinstance(data, dict) and "average_duration" in data]
            
            performance_summary = {
                "tools_benchmarked": len(perf_data),
                "average_response_time": statistics.mean(avg_durations) if avg_durations else 0,
                "fastest_tool": min(perf_data.items(), key=lambda x: x[1].get("average_duration", float('inf')) if isinstance(x[1], dict) else float('inf'))[0] if perf_data else None,
                "slowest_tool": max(perf_data.items(), key=lambda x: x[1].get("average_duration", 0) if isinstance(x[1], dict) else 0)[0] if perf_data else None
            }
        
        # Error handling analysis
        error_summary = {}
        if "error_handling" in self.test_results:
            error_data = self.test_results["error_handling"]
            error_rates = [data["error_handling_rate"] for data in error_data.values()]
            
            error_summary = {
                "tools_tested": len(error_data),
                "average_error_handling_rate": statistics.mean(error_rates) if error_rates else 0,
                "best_error_handler": max(error_data.items(), key=lambda x: x[1]["error_handling_rate"])[0] if error_data else None
            }
        
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "basic_stats": {
                "total_tools": total_tools,
                "http_success_rate": http_successes / total_tools if total_tools > 0 else 0,
                "stdio_success_rate": stdio_successes / total_tools if total_tools > 0 else 0,
                "overall_success_rate": max(http_successes, stdio_successes) / total_tools if total_tools > 0 else 0
            },
            "compliance_analysis": {
                "average_compliance_score": statistics.mean(compliance_scores) if compliance_scores else 0,
                "average_performance_score": statistics.mean(performance_scores) if performance_scores else 0,
                "average_reliability_score": statistics.mean(reliability_scores) if reliability_scores else 0,
                "mcp_2024_11_05_compliant_tools": sum(1 for score in compliance_scores if score >= 0.8),
                "total_tested": len(compliance_scores)
            },
            "category_analysis": category_stats,
            "performance_analysis": performance_summary,
            "error_handling_analysis": error_summary
        }
        
        print(f"  ✅ Analysis complete - {total_tools} tools analyzed")
        return summary
    
    async def _store_comprehensive_results(self, summary: Dict[str, Any]):
        """Store comprehensive results in LTMC system."""
        print("\n💾 Phase 5: Storing Results in LTMC")
        print("-" * 50)
        
        try:
            # Store test results
            storage_success = await self.validator.store_results_in_ltmc(
                {k: v for k, v in self.test_results.items() if isinstance(v, ComprehensiveValidation)}
            )
            
            if storage_success:
                print("  ✅ Test results stored successfully")
            else:
                print("  ❌ Failed to store test results")
            
            # Store summary analysis
            import aiohttp
            async with aiohttp.ClientSession() as session:
                summary_response = await session.post(
                    "http://localhost:5050/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "store_memory",
                            "arguments": {
                                "file_name": f"mcp_test_summary_{self.session_id}.json",
                                "content": json.dumps(summary, indent=2),
                                "resource_type": "test_summary"
                            }
                        },
                        "id": 1
                    }
                )
                
                # Log the testing session
                session_response = await session.post(
                    "http://localhost:5050/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "log_chat",
                            "arguments": {
                                "content": f"Comprehensive MCP 2024-11-05 testing session completed. Session ID: {self.session_id}. Results: {summary['basic_stats']['total_tools']} tools tested, {summary['basic_stats']['http_success_rate']*100:.1f}% HTTP success rate, {summary['compliance_analysis']['average_compliance_score']:.2f} average compliance score.",
                                "conversation_id": f"mcp_testing_{self.session_id}",
                                "role": "system"
                            }
                        },
                        "id": 2
                    }
                )
                
                print("  ✅ Summary and session logged successfully")
                
        except Exception as e:
            print(f"  ❌ Error storing results: {e}")
    
    async def _generate_final_report(self, summary: Dict[str, Any]):
        """Generate and display final comprehensive report."""
        print("\n" + "=" * 80)
        print("🏆 COMPREHENSIVE MCP 2024-11-05 TEST RESULTS")
        print("=" * 80)
        
        basic = summary["basic_stats"]
        compliance = summary["compliance_analysis"]
        
        print(f"📊 Overall Statistics:")
        print(f"   • Session ID: {summary['session_id']}")
        print(f"   • Test Duration: {summary.get('test_duration', 0):.1f} seconds")
        print(f"   • Total Tools Tested: {basic['total_tools']}")
        print(f"   • HTTP Success Rate: {basic['http_success_rate']*100:.1f}%")
        print(f"   • Stdio Success Rate: {basic['stdio_success_rate']*100:.1f}%")
        print(f"   • Overall Success Rate: {basic['overall_success_rate']*100:.1f}%")
        
        print(f"\n🎯 MCP 2024-11-05 Compliance:")
        print(f"   • Average Compliance Score: {compliance['average_compliance_score']:.2f}/1.00")
        print(f"   • Average Performance Score: {compliance['average_performance_score']:.2f}/1.00")
        print(f"   • Average Reliability Score: {compliance['average_reliability_score']:.2f}/1.00")
        print(f"   • Compliant Tools (≥0.8): {compliance['mcp_2024_11_05_compliant_tools']}/{compliance['total_tested']}")
        
        # Category breakdown
        print(f"\n📂 Category Analysis:")
        for category, stats in summary["category_analysis"].items():
            print(f"   • {category.capitalize()}: HTTP {stats['http_success_rate']*100:.0f}%, Stdio {stats['stdio_success_rate']*100:.0f}% ({stats['total_tools']} tools)")
        
        # Performance insights
        if summary.get("performance_analysis") and summary["performance_analysis"].get("tools_benchmarked", 0) > 0:
            perf = summary["performance_analysis"]
            print(f"\n⚡ Performance Insights:")
            print(f"   • Average Response Time: {perf['average_response_time']:.2f}s")
            print(f"   • Fastest Tool: {perf.get('fastest_tool', 'N/A')}")
            print(f"   • Slowest Tool: {perf.get('slowest_tool', 'N/A')}")
        
        # Error handling insights
        if summary.get("error_handling_analysis") and summary["error_handling_analysis"].get("tools_tested", 0) > 0:
            error = summary["error_handling_analysis"]
            print(f"\n🛡️  Error Handling:")
            print(f"   • Average Error Handling Rate: {error['average_error_handling_rate']*100:.1f}%")
            print(f"   • Best Error Handler: {error.get('best_error_handler', 'N/A')}")
        
        # Final assessment
        print(f"\n🎖️  Final Assessment:")
        if (basic['http_success_rate'] >= 0.95 and 
            compliance['average_compliance_score'] >= 0.8 and
            compliance['average_reliability_score'] >= 0.9):
            print("   🏆 EXCELLENT - System is production-ready with full MCP 2024-11-05 compliance!")
            assessment = "excellent"
        elif (basic['http_success_rate'] >= 0.9 and 
              compliance['average_compliance_score'] >= 0.7):
            print("   ✅ GOOD - System is largely compliant with minor areas for improvement")
            assessment = "good"
        elif basic['http_success_rate'] >= 0.8:
            print("   ⚠️  ACCEPTABLE - System functions but needs compliance improvements")
            assessment = "acceptable"
        else:
            print("   ❌ NEEDS WORK - Significant issues requiring immediate attention")
            assessment = "needs_work"
        
        summary["final_assessment"] = assessment
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if basic['stdio_success_rate'] < 0.8:
            print("   • Investigate stdio transport timeout issues")
        if compliance['average_compliance_score'] < 0.8:
            print("   • Improve JSON-RPC 2.0 response structure compliance")
        if compliance['average_performance_score'] < 0.7:
            print("   • Optimize response times for better performance")
        if basic['http_success_rate'] >= 0.95:
            print("   • HTTP transport is excellent - consider it as primary")
        
        print("\n🚀 Testing Complete!")
        print("=" * 80)


async def main():
    """Main entry point for comprehensive testing."""
    parser = argparse.ArgumentParser(
        description="Comprehensive MCP 2024-11-05 Testing Suite"
    )
    parser.add_argument(
        "--transports", 
        nargs="+", 
        default=["http", "stdio"],
        choices=["http", "stdio"],
        help="Transport types to test (default: both)"
    )
    parser.add_argument(
        "--no-performance", 
        action="store_true",
        help="Skip performance benchmarking tests"
    )
    parser.add_argument(
        "--no-error-tests", 
        action="store_true",
        help="Skip error handling tests"
    )
    parser.add_argument(
        "--no-ltmc-storage", 
        action="store_true",
        help="Skip storing results in LTMC"
    )
    parser.add_argument(
        "--quick", 
        action="store_true",
        help="Quick test mode (HTTP only, no performance or error tests)"
    )
    
    args = parser.parse_args()
    
    if args.quick:
        transports = ["http"]
        include_performance = False
        include_error_tests = False
    else:
        transports = args.transports
        include_performance = not args.no_performance
        include_error_tests = not args.no_error_tests
    
    include_ltmc = not args.no_ltmc_storage
    
    orchestrator = MCPTestOrchestrator()
    
    try:
        summary = await orchestrator.run_full_test_suite(
            transports=transports,
            include_performance_tests=include_performance,
            include_error_tests=include_error_tests,
            store_in_ltmc=include_ltmc
        )
        
        # Save summary to file
        summary_file = f"mcp_test_results_{orchestrator.session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {summary_file}")
        
        # Exit code based on results
        if summary["final_assessment"] in ["excellent", "good"]:
            return 0
        elif summary["final_assessment"] == "acceptable":
            return 1
        else:
            return 2
            
    except Exception as e:
        print(f"❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)