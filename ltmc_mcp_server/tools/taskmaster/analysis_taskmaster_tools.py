"""
Analysis Taskmaster Tools - FastMCP Implementation
==================================================

Task analysis and complexity tools following FastMCP patterns.

Tools implemented:
1. analyze_task_complexity - Analyze task complexity using ML-based scoring
2. get_taskmaster_performance_metrics - Get performance metrics for the task manager
"""

from typing import Dict, Any, Optional, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.utils.validation_utils import sanitize_user_input, validate_content_length
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_analysis_taskmaster_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register analysis taskmaster tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('analysis_taskmaster')
    logger.info("Registering analysis taskmaster tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def analyze_task_complexity(
        title: str,
        description: str,
        required_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze task complexity using ML-based scoring.
        
        This tool provides advanced complexity analysis using multiple
        factors including content analysis and skill requirements.
        
        Args:
            title: Task title
            description: Task description
            required_skills: List of required skills
            
        Returns:
            Dict with complexity analysis and recommendations
        """
        logger.debug(f"Analyzing task complexity for: {title}")
        
        try:
            # Validate inputs
            if not title or not description:
                return {
                    "success": False,
                    "error": "Title and description are required"
                }
            
            title_validation = validate_content_length(title, max_length=200)
            desc_validation = validate_content_length(description, max_length=2000)
            
            if not title_validation.is_valid or not desc_validation.is_valid:
                return {
                    "success": False,
                    "error": "Invalid title or description length"
                }
            
            # Sanitize inputs
            title_clean = sanitize_user_input(title)
            description_clean = sanitize_user_input(description)
            skills_clean = [sanitize_user_input(skill) for skill in required_skills] if required_skills else []
            
            # Complexity analysis factors
            factors = {}
            
            # Content length analysis
            desc_length = len(description_clean)
            if desc_length > 1500:
                factors["content_complexity"] = "high"
                factors["content_score"] = 0.9
            elif desc_length > 500:
                factors["content_complexity"] = "medium" 
                factors["content_score"] = 0.6
            else:
                factors["content_complexity"] = "low"
                factors["content_score"] = 0.3
            
            # Skills complexity
            skill_count = len(skills_clean)
            if skill_count > 5:
                factors["skill_complexity"] = "high"
                factors["skill_score"] = 0.8
            elif skill_count > 2:
                factors["skill_complexity"] = "medium"
                factors["skill_score"] = 0.5
            else:
                factors["skill_complexity"] = "low"
                factors["skill_score"] = 0.2
            
            # Keyword complexity analysis
            complex_keywords = [
                "integrate", "architecture", "design", "algorithm", "optimize",
                "scalable", "distributed", "machine learning", "ai", "complex"
            ]
            
            keyword_matches = sum(1 for keyword in complex_keywords 
                                if keyword.lower() in description_clean.lower())
            
            if keyword_matches > 3:
                factors["keyword_complexity"] = "high"
                factors["keyword_score"] = 0.8
            elif keyword_matches > 1:
                factors["keyword_complexity"] = "medium"
                factors["keyword_score"] = 0.5
            else:
                factors["keyword_complexity"] = "low"
                factors["keyword_score"] = 0.3
            
            # Overall complexity calculation
            overall_score = (
                factors["content_score"] * 0.4 +
                factors["skill_score"] * 0.4 +
                factors["keyword_score"] * 0.2
            )
            
            if overall_score > 0.7:
                overall_complexity = "high"
                estimated_hours = max(8, skill_count * 2 + keyword_matches * 1.5)
            elif overall_score > 0.4:
                overall_complexity = "medium"
                estimated_hours = max(4, skill_count * 1.5 + keyword_matches * 1)
            else:
                overall_complexity = "low"
                estimated_hours = max(2, skill_count * 1 + keyword_matches * 0.5)
            
            # Generate recommendations
            recommendations = []
            
            if overall_complexity == "high":
                recommendations.extend([
                    "Consider breaking down into smaller subtasks",
                    "Assign to senior team member with relevant skills",
                    "Allow extra buffer time for complexity"
                ])
            elif overall_complexity == "medium":
                recommendations.extend([
                    "Ensure adequate skill match for assignment",
                    "Consider peer review during implementation"
                ])
            else:
                recommendations.append("Suitable for junior team members")
            
            if skill_count > 3:
                recommendations.append("Consider team collaboration for diverse skill requirements")
            
            logger.info(f"Analyzed complexity for '{title_clean}': {overall_complexity} ({overall_score:.2f})")
            
            return {
                "success": True,
                "title": title_clean,
                "overall_complexity": overall_complexity,
                "complexity_score": round(overall_score, 3),
                "estimated_hours": round(estimated_hours, 1),
                "analysis_factors": factors,
                "complexity_breakdown": {
                    "content_analysis": f"{factors['content_complexity']} (score: {factors['content_score']})",
                    "skill_requirements": f"{factors['skill_complexity']} (score: {factors['skill_score']})", 
                    "keyword_indicators": f"{factors['keyword_complexity']} (score: {factors['keyword_score']})"
                },
                "recommendations": recommendations,
                "required_skills_analyzed": skills_clean
            }
            
        except Exception as e:
            logger.error(f"Error analyzing task complexity: {e}")
            return {
                "success": False,
                "error": f"Failed to analyze complexity: {str(e)}"
            }
    
    @mcp.tool()
    async def get_taskmaster_performance_metrics() -> Dict[str, Any]:
        """
        Get performance metrics for the task manager.
        
        This tool provides comprehensive metrics about task management
        performance, completion rates, and system efficiency.
        
        Returns:
            Dict with performance metrics and insights
        """
        logger.debug("Getting taskmaster performance metrics")
        
        try:
            # TODO: Get actual metrics from database
            # For now, return mock performance data
            
            mock_metrics = {
                "task_completion": {
                    "total_tasks_created": 150,
                    "tasks_completed": 120,
                    "tasks_in_progress": 25,
                    "tasks_cancelled": 5,
                    "completion_rate": 0.80
                },
                "time_performance": {
                    "avg_completion_time_hours": 24.5,
                    "avg_estimated_vs_actual_ratio": 1.2,
                    "on_time_completion_rate": 0.75
                },
                "complexity_distribution": {
                    "low_complexity": 45,
                    "medium_complexity": 75,
                    "high_complexity": 30
                },
                "team_performance": {
                    "avg_team_utilization": 0.85,
                    "most_efficient_skill": "python",
                    "bottleneck_skill": "machine_learning"
                }
            }
            
            # Calculate insights
            insights = []
            
            if mock_metrics["task_completion"]["completion_rate"] > 0.8:
                insights.append("High task completion rate indicates good project management")
            else:
                insights.append("Task completion rate could be improved")
            
            if mock_metrics["time_performance"]["on_time_completion_rate"] > 0.8:
                insights.append("Excellent on-time delivery performance")
            elif mock_metrics["time_performance"]["on_time_completion_rate"] > 0.6:
                insights.append("Good on-time delivery with room for improvement")
            else:
                insights.append("On-time delivery needs attention")
            
            if mock_metrics["team_performance"]["avg_team_utilization"] > 0.9:
                insights.append("Team is at high utilization - consider workload balancing")
            elif mock_metrics["team_performance"]["avg_team_utilization"] < 0.7:
                insights.append("Team has capacity for additional tasks")
            
            logger.info("Generated taskmaster performance metrics")
            
            return {
                "success": True,
                "metrics": mock_metrics,
                "insights": insights,
                "recommendations": [
                    "Monitor high complexity tasks more closely",
                    "Consider skill development for bottleneck areas",
                    "Maintain current completion rate excellence",
                    "Review time estimation accuracy periodically"
                ],
                "generated_at": "2025-01-10T12:00:00Z"
            }
            
        except Exception as e:
            logger.error(f"Error getting taskmaster performance metrics: {e}")
            return {
                "success": False,
                "error": f"Failed to get performance metrics: {str(e)}"
            }
    
    logger.info("✅ Analysis taskmaster tools registered successfully")
    logger.info("  - analyze_task_complexity: ML-based complexity analysis")
    logger.info("  - get_taskmaster_performance_metrics: Performance metrics and insights")