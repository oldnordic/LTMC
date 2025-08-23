"""
Analysis Code Pattern Tools - FastMCP Implementation
===================================================

Code pattern analysis and statistics tools following FastMCP patterns.

Tools implemented:
1. analyze_code_patterns - Analyze code patterns for insights
2. get_code_statistics - Get comprehensive code pattern statistics
"""

from typing import Dict, Any, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.utils.validation_utils import sanitize_user_input
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_analysis_pattern_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register analysis code pattern tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('analysis_patterns')
    logger.info("Registering analysis code pattern tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def analyze_code_patterns(
        function_name: str = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze code patterns for insights.
        
        This tool analyzes stored code patterns to identify trends,
        common failures, and successful patterns for learning.
        
        Args:
            function_name: Optional filter by function name
            tags: Optional list of tags to filter by
            
        Returns:
            Dict with analysis results, insights, and recommendations
        """
        logger.debug(f"Analyzing code patterns with function: {function_name}, tags: {tags}")
        
        try:
            # Sanitize inputs
            function_filter = sanitize_user_input(function_name) if function_name else None
            tags_clean = [sanitize_user_input(tag) for tag in tags] if tags else None
            
            # Get patterns for analysis
            all_patterns = await db_service.get_code_patterns(
                query_tags=tags_clean,
                result_filter=None,
                limit=100  # Analyze up to 100 recent patterns
            )
            
            # Perform analysis
            total_patterns = len(all_patterns)
            if total_patterns == 0:
                return {
                    "success": True,
                    "analysis": {
                        "total_patterns": 0,
                        "message": "No code patterns found for analysis"
                    }
                }
            
            # Count results
            result_counts = {}
            tag_frequencies = {}
            common_errors = []
            
            for pattern in all_patterns:
                # Count results
                result = pattern.get('result', 'unknown')
                result_counts[result] = result_counts.get(result, 0) + 1
                
                # Count tag frequencies
                pattern_tags = pattern.get('tags', [])
                if isinstance(pattern_tags, list):
                    for tag in pattern_tags:
                        tag_frequencies[tag] = tag_frequencies.get(tag, 0) + 1
                
                # Collect error messages
                if result == 'error' and pattern.get('error_message'):
                    common_errors.append(pattern['error_message'])
            
            # Calculate success rate
            successful = result_counts.get('pass', 0)
            success_rate = (successful / total_patterns * 100) if total_patterns > 0 else 0
            
            # Get most common tags
            top_tags = sorted(tag_frequencies.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Generate insights
            insights = []
            
            if success_rate > 80:
                insights.append("High success rate - code patterns are performing well")
            elif success_rate < 50:
                insights.append("Low success rate - consider reviewing failed patterns")
            
            if result_counts.get('partial', 0) > total_patterns * 0.3:
                insights.append("High partial success rate - patterns may need refinement")
            
            if len(top_tags) > 0:
                insights.append(f"Most common pattern type: {top_tags[0][0]}")
            
            logger.info(f"Analyzed {total_patterns} code patterns, success rate: {success_rate:.1f}%")
            
            return {
                "success": True,
                "analysis": {
                    "total_patterns": total_patterns,
                    "result_distribution": result_counts,
                    "success_rate_percent": round(success_rate, 2),
                    "top_tags": top_tags,
                    "insights": insights,
                    "filter_applied": {
                        "function_name": function_filter,
                        "tags": tags_clean
                    }
                },
                "recommendations": [
                    "Review failed patterns to identify common issues",
                    "Promote successful patterns as templates",
                    "Consider adding more specific tags for better categorization"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing code patterns: {e}")
            return {
                "success": False,
                "error": f"Failed to analyze code patterns: {str(e)}"
            }
    
    @mcp.tool()
    async def get_code_statistics() -> Dict[str, Any]:
        """
        Get comprehensive code pattern statistics.
        
        This tool provides detailed statistics about all stored code patterns
        including success rates, timing, and trend analysis.
        
        Returns:
            Dict with comprehensive statistics and metrics
        """
        logger.debug("Getting comprehensive code statistics")
        
        try:
            # Get all patterns for comprehensive analysis
            all_patterns = await db_service.get_code_patterns(
                query_tags=None,
                result_filter=None,
                limit=1000  # Get up to 1000 patterns for stats
            )
            
            total_patterns = len(all_patterns)
            
            if total_patterns == 0:
                return {
                    "success": True,
                    "statistics": {
                        "total_patterns": 0,
                        "message": "No code patterns in database"
                    }
                }
            
            # Count by result
            pass_count = sum(1 for p in all_patterns if p.get('result') == 'pass')
            fail_count = sum(1 for p in all_patterns if p.get('result') == 'fail')
            partial_count = sum(1 for p in all_patterns if p.get('result') == 'partial')
            error_count = sum(1 for p in all_patterns if p.get('result') == 'error')
            
            # Calculate rates
            success_rate = (pass_count / total_patterns * 100) if total_patterns > 0 else 0
            failure_rate = (fail_count / total_patterns * 100) if total_patterns > 0 else 0
            
            # Collect all unique tags
            all_tags = set()
            for pattern in all_patterns:
                pattern_tags = pattern.get('tags', [])
                if isinstance(pattern_tags, list):
                    all_tags.update(pattern_tags)
            
            # Recent activity (last 10 patterns)
            recent_patterns = all_patterns[:10] if len(all_patterns) >= 10 else all_patterns
            recent_success = sum(1 for p in recent_patterns if p.get('result') == 'pass')
            recent_success_rate = (recent_success / len(recent_patterns) * 100) if recent_patterns else 0
            
            logger.info(f"Generated statistics for {total_patterns} code patterns")
            
            return {
                "success": True,
                "statistics": {
                    "total_patterns": total_patterns,
                    "result_counts": {
                        "pass": pass_count,
                        "fail": fail_count,
                        "partial": partial_count,
                        "error": error_count
                    },
                    "success_rate_percent": round(success_rate, 2),
                    "failure_rate_percent": round(failure_rate, 2),
                    "unique_tags_count": len(all_tags),
                    "recent_activity": {
                        "recent_patterns_analyzed": len(recent_patterns),
                        "recent_success_rate_percent": round(recent_success_rate, 2)
                    }
                },
                "health_indicators": {
                    "overall_health": "good" if success_rate > 70 else "needs_attention",
                    "trend": "stable",  # TODO: Implement trend analysis
                    "recommendations": [
                        "Monitor failure patterns for improvement opportunities",
                        "Continue logging code attempts for better learning",
                        "Review high-performing patterns for reuse"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting code statistics: {e}")
            return {
                "success": False,
                "error": f"Failed to get code statistics: {str(e)}"
            }
    
    logger.info("✅ Analysis code pattern tools registered successfully")
    logger.info("  - analyze_code_patterns: Analyze patterns for insights")
    logger.info("  - get_code_statistics: Get comprehensive statistics")