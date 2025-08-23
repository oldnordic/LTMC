"""
Consolidated Advanced Tools - FastMCP Implementation
===================================================

1 unified advanced tool for all advanced operations.

Consolidated Tool:
- advanced_manage - Unified tool for all advanced operations
  * get_context_usage_statistics - Get comprehensive context usage statistics
  * advanced_context_search - Perform advanced context search with filters
  * analyze_system_performance - Analyze overall system performance
  * get_usage_analytics - Get detailed usage analytics
  * export_statistics - Export statistics in various formats
  * generate_reports - Generate comprehensive system reports
"""

from typing import Dict, Any

# Official MCP SDK import
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...services.database_service import DatabaseService
from ...services.faiss_service import FAISSService
from ...utils.logging_utils import get_tool_logger


def register_consolidated_advanced_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register consolidated advanced tools with FastMCP server."""
    logger = get_tool_logger('advanced.consolidated')
    logger.info("Registering consolidated advanced tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    faiss_service = FAISSService(settings, database_service=db_service)
    
    @mcp.tool()
    async def advanced_manage(
        operation: str,
        query: str = None,
        filters: Dict[str, Any] = None,
        top_k: int = 10,
        format: str = "json",
        report_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Unified advanced management tool.
        
        Args:
            operation: Operation to perform ("get_context_usage_statistics", "advanced_context_search", "analyze_system_performance", "get_usage_analytics", "export_statistics", "generate_reports")
            query: Search query for context search operations
            filters: Optional filters dict for context search (conversation_id, date_range, agent_name, etc.)
            top_k: Maximum number of results to return (for search operations)
            format: Output format for export operations (json, csv, xml)
            report_type: Type of report to generate (comprehensive, summary, performance, usage)
            
        Returns:
            Dict with operation results and metadata
        """
        logger.debug("Advanced operation: {}".format(operation))
        
        try:
            if operation == "get_context_usage_statistics":
                # Get comprehensive context usage statistics
                logger.debug("Getting context usage statistics")
                
                # Get basic chat statistics
                chat_history = await db_service.get_chat_history("all_conversations", limit=1000)
                
                if not chat_history:
                    return {
                        "success": True,
                        "operation": "get_context_usage_statistics",
                        "statistics": {
                            "total_conversations": 0,
                            "total_messages": 0,
                            "message": "No conversation data available"
                        }
                    }
                
                # Analyze conversation patterns
                total_messages = len(chat_history)
                user_messages = sum(1 for msg in chat_history if msg.get('role') == 'user')
                assistant_messages = sum(1 for msg in chat_history if msg.get('role') == 'assistant')
                
                # Get unique conversation IDs
                conversation_ids = set(msg.get('conversation_id', 'unknown') for msg in chat_history)
                total_conversations = len(conversation_ids)
                
                # Analyze message lengths
                message_lengths = [len(msg.get('content', '')) for msg in chat_history]
                avg_message_length = sum(message_lengths) / len(message_lengths) if message_lengths else 0
                
                # Count agent usage if available
                agent_usage = {}
                for msg in chat_history:
                    agent = msg.get('agent_name', 'unknown')
                    agent_usage[agent] = agent_usage.get(agent, 0) + 1
                
                # Top agents by usage
                top_agents = sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)[:5]
                
                # Recent activity (last 50 messages)
                recent_messages = chat_history[:50] if len(chat_history) >= 50 else chat_history
                recent_user_messages = sum(1 for msg in recent_messages if msg.get('role') == 'user')
                recent_activity_rate = len(recent_messages) / min(len(chat_history), 50) if chat_history else 0
                
                logger.info("Generated context usage statistics: {} messages, {} conversations".format(total_messages, total_conversations))
                
                return {
                    "success": True,
                    "operation": "get_context_usage_statistics",
                    "statistics": {
                        "total_conversations": total_conversations,
                        "total_messages": total_messages,
                        "user_messages": user_messages,
                        "assistant_messages": assistant_messages,
                        "average_message_length": round(avg_message_length, 2),
                        "top_agents": top_agents,
                        "recent_activity": {
                            "recent_messages": len(recent_messages),
                            "recent_user_messages": recent_user_messages,
                            "activity_rate": round(recent_activity_rate, 3)
                        }
                    }
                }
                
            elif operation == "advanced_context_search":
                if not query:
                    return {"success": False, "error": "query required for advanced_context_search operation"}
                
                # Perform advanced context search with filters
                logger.debug("Performing advanced context search: {}".format(query))
                
                # Apply filters if provided
                search_filters = filters or {}
                
                # Perform semantic search
                search_results = await faiss_service.search_semantic(
                    query=query,
                    limit=top_k,
                    filters=search_filters
                )
                
                if search_results:
                    logger.info("Advanced context search found {} results".format(len(search_results)))
                    return {
                        "success": True,
                        "operation": "advanced_context_search",
                        "query": query,
                        "filters": search_filters,
                        "results": search_results,
                        "count": len(search_results),
                        "message": "Advanced context search completed successfully"
                    }
                else:
                    return {
                        "success": True,
                        "operation": "advanced_context_search",
                        "query": query,
                        "filters": search_filters,
                        "results": [],
                        "count": 0,
                        "message": "No results found for advanced context search"
                    }
                
            elif operation == "analyze_system_performance":
                # Analyze overall system performance
                logger.debug("Analyzing system performance")
                
                # Get basic performance metrics
                try:
                    # Database performance
                    db_stats = await db_service.get_database_stats()
                    
                    # FAISS performance
                    faiss_stats = await faiss_service.get_performance_stats()
                    
                    # Overall system health
                    system_health = {
                        "database": db_stats.get("status", "unknown"),
                        "faiss": faiss_stats.get("status", "unknown"),
                        "timestamp": "now"
                    }
                    
                    logger.info("System performance analysis completed")
                    return {
                        "success": True,
                        "operation": "analyze_system_performance",
                        "system_health": system_health,
                        "database_stats": db_stats,
                        "faiss_stats": faiss_stats,
                        "message": "System performance analysis completed successfully"
                    }
                except Exception as e:
                    logger.error("Error analyzing system performance: {}".format(e))
                    return {
                        "success": False,
                        "error": "System performance analysis failed: {}".format(str(e))
                    }
                
            elif operation == "get_usage_analytics":
                # Get detailed usage analytics
                logger.debug("Getting usage analytics")
                
                # Get various usage metrics
                try:
                    # Chat usage
                    chat_stats = await db_service.get_chat_statistics()
                    
                    # Memory usage
                    memory_stats = await db_service.get_memory_statistics()
                    
                    # Tool usage patterns
                    tool_stats = await db_service.get_tool_usage_statistics()
                    
                    logger.info("Usage analytics retrieved successfully")
                    return {
                        "success": True,
                        "operation": "get_usage_analytics",
                        "chat_statistics": chat_stats,
                        "memory_statistics": memory_stats,
                        "tool_statistics": tool_stats,
                        "message": "Usage analytics retrieved successfully"
                    }
                except Exception as e:
                    logger.error("Error getting usage analytics: {}".format(e))
                    return {
                        "success": False,
                        "error": "Usage analytics retrieval failed: {}".format(str(e))
                    }
                
            elif operation == "export_statistics":
                # Export statistics in various formats
                logger.debug("Exporting statistics in format: {}".format(format))
                
                # Get basic statistics
                try:
                    basic_stats = await db_service.get_basic_statistics()
                    
                    # Format based on requested format
                    if format.lower() == "json":
                        export_data = basic_stats
                    elif format.lower() == "csv":
                        # Convert to CSV format (simplified)
                        export_data = "format,value\n"
                        for key, value in basic_stats.items():
                            export_data += "{},{}\n".format(key, value)
                    else:
                        export_data = basic_stats
                    
                    logger.info("Statistics exported in {} format".format(format))
                    return {
                        "success": True,
                        "operation": "export_statistics",
                        "format": format,
                        "data": export_data,
                        "message": "Statistics exported successfully"
                    }
                except Exception as e:
                    logger.error("Error exporting statistics: {}".format(e))
                    return {
                        "success": False,
                        "error": "Statistics export failed: {}".format(str(e))
                    }
                
            elif operation == "generate_reports":
                # Generate comprehensive system reports
                logger.debug("Generating {} report".format(report_type))
                
                try:
                    if report_type == "comprehensive":
                        # Generate comprehensive report
                        report_data = await db_service.generate_comprehensive_report()
                    elif report_type == "summary":
                        # Generate summary report
                        report_data = await db_service.generate_summary_report()
                    elif report_type == "performance":
                        # Generate performance report
                        report_data = await db_service.generate_performance_report()
                    elif report_type == "usage":
                        # Generate usage report
                        report_data = await db_service.generate_usage_report()
                    else:
                        return {
                            "success": False,
                            "error": "Unknown report type: {}. Valid types: comprehensive, summary, performance, usage".format(report_type)
                        }
                    
                    logger.info("Generated {} report successfully".format(report_type))
                    return {
                        "success": True,
                        "operation": "generate_reports",
                        "report_type": report_type,
                        "report_data": report_data,
                        "message": "Report generated successfully"
                    }
                except Exception as e:
                    logger.error("Error generating report: {}".format(e))
                    return {
                        "success": False,
                        "error": "Report generation failed: {}".format(str(e))
                    }
                
            else:
                return {
                    "success": False,
                    "error": "Unknown operation: {}. Valid operations: get_context_usage_statistics, advanced_context_search, analyze_system_performance, get_usage_analytics, export_statistics, generate_reports".format(operation)
                }
                
        except Exception as e:
            logger.error("Error in advanced operation '{}': {}".format(operation, e))
            return {
                "success": False,
                "error": "Advanced operation failed: {}".format(str(e))
            }
    
    logger.info("✅ Consolidated advanced tools registered successfully")
    logger.info("📊 Tool consolidation: 6 individual tools → 1 unified tool")
    logger.info("🔧 All functionality preserved through operation parameter")
