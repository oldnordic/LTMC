#!/usr/bin/env python3
"""
LTMC Statistics Collector
========================

Script to collect comprehensive statistics from the running LTMC MCP server
using stdio transport to get actual tool usage, performance metrics, and system health.
"""

import json
import sys
import subprocess
import asyncio
from pathlib import Path


class LTMCStatsCollector:
    """Collect statistics from LTMC MCP server via stdio."""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.server_script = self.project_dir / "ltmc_mcp_server" / "main.py"
        
    async def call_mcp_tool(self, tool_name: str, params: dict = None) -> dict:
        """Call an LTMC MCP tool and return the result."""
        if params is None:
            params = {}
            
        # Create MCP request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }
        
        try:
            # Call the MCP server via stdio
            process = await asyncio.create_subprocess_exec(
                "python", str(self.server_script),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_dir)
            )
            
            # Send request
            request_json = json.dumps(request) + "\n"
            stdout, stderr = await process.communicate(request_json.encode())
            
            if process.returncode != 0:
                return {"error": f"Process failed: {stderr.decode()}", "success": False}
                
            # Parse response
            response = json.loads(stdout.decode().strip())
            
            if "error" in response:
                return {"error": response["error"], "success": False}
                
            return response.get("result", {})
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_all_statistics(self):
        """Collect all available statistics from LTMC."""
        print("🔍 Collecting LTMC Statistics...")
        print("=" * 50)
        
        # 1. Performance Report (unified tool)
        print("\n📊 SYSTEM PERFORMANCE REPORT")
        print("-" * 30)
        perf_report = await self.call_mcp_tool("get_performance_report")
        if perf_report.get("success", False):
            self.display_performance_report(perf_report)
        else:
            print(f"❌ Error: {perf_report.get('error', 'Unknown error')}")
        
        # 2. Context Usage Statistics (advanced tool)
        print("\n🧠 CONTEXT USAGE STATISTICS")
        print("-" * 30)
        context_stats = await self.call_mcp_tool("get_context_usage_statistics")
        if context_stats.get("success", False):
            self.display_context_statistics(context_stats)
        else:
            print(f"❌ Error: {context_stats.get('error', 'Unknown error')}")
        
        # 3. Code Pattern Statistics (pattern tool)
        print("\n💻 CODE PATTERN STATISTICS")
        print("-" * 30)
        code_stats = await self.call_mcp_tool("get_code_statistics")
        if code_stats.get("success", False):
            self.display_code_statistics(code_stats)
        else:
            print(f"❌ Error: {code_stats.get('error', 'Unknown error')}")
        
        # 4. Taskmaster Performance Metrics (taskmaster tool)
        print("\n⚡ TASKMASTER PERFORMANCE METRICS")
        print("-" * 35)
        taskmaster_stats = await self.call_mcp_tool("get_taskmaster_performance_metrics")
        if taskmaster_stats.get("success", False):
            self.display_taskmaster_statistics(taskmaster_stats)
        else:
            print(f"❌ Error: {taskmaster_stats.get('error', 'Unknown error')}")
        
        # 5. Blueprint Statistics (check if available)
        print("\n🏗️ BLUEPRINT STATISTICS")
        print("-" * 25)
        await self.get_blueprint_statistics()
        
        # 6. Redis Cache Statistics (redis tool)
        print("\n🗄️ REDIS CACHE STATISTICS")
        print("-" * 27)
        redis_stats = await self.call_mcp_tool("redis_cache_stats")
        if redis_stats.get("success", False):
            self.display_redis_statistics(redis_stats)
        else:
            print(f"❌ Error: {redis_stats.get('error', 'Unknown error')}")
    
    def display_performance_report(self, report: dict):
        """Display system performance report."""
        system = report.get("system_overview", {})
        db_status = report.get("database_status", {})
        tools = report.get("tool_statistics", {})
        perf = report.get("performance_metrics", {})
        health = report.get("health_assessment", {})
        
        print(f"✅ Status: {system.get('system_status', 'unknown')}")
        print(f"🏗️ Architecture: {system.get('architecture', 'unknown')}")
        print(f"🔧 Total Tools: {tools.get('total_tools_available', 0)}")
        print(f"📈 Health Score: {health.get('overall_health_score', 0):.2f}")
        print(f"⚡ Response Time: {perf.get('report_generation_time_ms', 0):.2f}ms")
        
        if "tool_categories" in tools:
            print("\n🛠️ Tool Categories:")
            for category, count in tools["tool_categories"].items():
                print(f"   {category}: {count} tools")
    
    def display_context_statistics(self, stats: dict):
        """Display context usage statistics."""
        usage = stats.get("context_usage", {})
        performance = stats.get("performance_metrics", {})
        
        print(f"🔍 Total Queries: {usage.get('total_queries', 0)}")
        print(f"📝 Documents Retrieved: {usage.get('documents_retrieved', 0)}")
        print(f"⚡ Avg Query Time: {performance.get('avg_query_time_ms', 0):.2f}ms")
        print(f"💾 Cache Hit Rate: {performance.get('cache_hit_rate', 0):.1%}")
    
    def display_code_statistics(self, stats: dict):
        """Display code pattern statistics."""
        patterns = stats.get("pattern_statistics", {})
        success_rate = stats.get("success_rate_percent", 0)
        
        print(f"🔢 Total Patterns: {patterns.get('total_patterns', 0)}")
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        if "result_distribution" in patterns:
            print("\n📊 Pattern Results:")
            for result, count in patterns["result_distribution"].items():
                print(f"   {result}: {count} patterns")
        
        if "top_tags" in stats:
            print("\n🏷️ Top Tags:")
            for tag, count in stats["top_tags"][:5]:
                print(f"   {tag}: {count} uses")
    
    def display_taskmaster_statistics(self, stats: dict):
        """Display taskmaster performance metrics."""
        metrics = stats.get("metrics", {})
        completion = metrics.get("task_completion", {})
        performance = metrics.get("time_performance", {})
        
        print(f"📋 Total Tasks: {completion.get('total_tasks_created', 0)}")
        print(f"✅ Completed: {completion.get('tasks_completed', 0)}")
        print(f"⏱️ In Progress: {completion.get('tasks_in_progress', 0)}")
        print(f"📈 Completion Rate: {completion.get('completion_rate', 0):.1%}")
        print(f"⚡ Avg Time: {performance.get('avg_completion_time_hours', 0):.1f}h")
    
    async def get_blueprint_statistics(self):
        """Get blueprint statistics from database or tools."""
        # Try to get blueprint count via database
        try:
            import sqlite3
            db_path = self.project_dir / "ltmc.db"
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM TaskBlueprints")
                blueprint_count = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT complexity, COUNT(*) 
                    FROM TaskBlueprints 
                    GROUP BY complexity
                """)
                complexity_dist = cursor.fetchall()
                
                print(f"📋 Total Blueprints: {blueprint_count}")
                if complexity_dist:
                    print("🎯 Complexity Distribution:")
                    for complexity, count in complexity_dist:
                        print(f"   {complexity}: {count} blueprints")
                
                conn.close()
            else:
                print("❌ Database not found")
        except Exception as e:
            print(f"❌ Error accessing blueprints: {e}")
    
    def display_redis_statistics(self, stats: dict):
        """Display Redis cache statistics."""
        cache_stats = stats.get("cache_statistics", {})
        performance = stats.get("performance_metrics", {})
        
        print(f"🔗 Status: {stats.get('status', 'unknown')}")
        print(f"💾 Memory Usage: {cache_stats.get('used_memory_human', 'unknown')}")
        print(f"🗝️ Total Keys: {cache_stats.get('total_keys', 0)}")
        print(f"📈 Hit Rate: {performance.get('hit_rate', 0):.1%}")
        print(f"⚡ Latency: {performance.get('avg_latency_ms', 0):.2f}ms")


async def main():
    """Main function to collect and display all LTMC statistics."""
    collector = LTMCStatsCollector()
    
    print("🚀 LTMC Comprehensive Statistics Report")
    print("=" * 50)
    print("Collecting data from running LTMC MCP server...")
    
    await collector.get_all_statistics()
    
    print("\n" + "=" * 50)
    print("📊 Statistics collection complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)