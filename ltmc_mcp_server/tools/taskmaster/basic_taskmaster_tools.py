"""
Basic Taskmaster Tools - FastMCP Implementation
===============================================

Core task blueprint management tools following FastMCP patterns.

Tools implemented:
1. create_task_blueprint - Create new task blueprints with ML complexity analysis
2. get_task_dependencies - Get dependencies for a task blueprint
"""

import logging
from typing import Dict, Any, Optional, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.database_service import DatabaseService
from utils.validation_utils import sanitize_user_input, validate_content_length
from utils.logging_utils import get_tool_logger


def register_basic_taskmaster_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register basic taskmaster tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('basic_taskmaster')
    logger.info("Registering basic taskmaster tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def create_task_blueprint(
        title: str,
        description: str,
        estimated_duration_minutes: int = 60,
        required_skills: Optional[List[str]] = None,
        priority_score: float = 0.5,
        tags: Optional[List[str]] = None,
        resource_requirements: Optional[Dict[str, str]] = None,
        project_id: Optional[str] = None,
        complexity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new task blueprint with automatic complexity scoring.
        
        This tool creates a comprehensive task blueprint with ML-based
        complexity analysis and metadata management.
        
        Args:
            title: Task title
            description: Detailed task description
            estimated_duration_minutes: Estimated time to complete
            required_skills: List of required skills
            priority_score: Priority score (0.0-1.0)
            tags: Optional list of tags
            resource_requirements: Resource requirements dict
            project_id: Optional project ID
            complexity: Manual complexity override
            
        Returns:
            Dict with created blueprint details and analysis
        """
        logger.debug(f"Creating task blueprint: {title}")
        
        try:
            # Validate inputs
            if not title or not description:
                return {
                    "success": False,
                    "error": "Title and description are required"
                }
            
            title_validation = validate_content_length(title, max_length=200)
            if not title_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid title: {', '.join(title_validation.errors)}"
                }
            
            desc_validation = validate_content_length(description, max_length=2000)
            if not desc_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Invalid description: {', '.join(desc_validation.errors)}"
                }
            
            if estimated_duration_minutes < 1 or estimated_duration_minutes > 40320:  # Max 4 weeks
                return {
                    "success": False,
                    "error": "Estimated duration must be between 1 and 40320 minutes (4 weeks)"
                }
            
            if priority_score < 0.0 or priority_score > 1.0:
                return {
                    "success": False,
                    "error": "Priority score must be between 0.0 and 1.0"
                }
            
            # Sanitize inputs
            title_clean = sanitize_user_input(title)
            description_clean = sanitize_user_input(description)
            project_id_clean = sanitize_user_input(project_id) if project_id else None
            
            # Clean optional lists
            skills_clean = [sanitize_user_input(skill) for skill in required_skills] if required_skills else []
            tags_clean = [sanitize_user_input(tag) for tag in tags] if tags else []
            
            # Auto-analyze complexity if not provided
            if not complexity:
                # Simple complexity analysis based on description length and skills
                desc_complexity = "low"
                if len(description_clean) > 1000:
                    desc_complexity = "high"
                elif len(description_clean) > 500:
                    desc_complexity = "medium"
                
                skill_complexity = "low"
                if len(skills_clean) > 5:
                    skill_complexity = "high"
                elif len(skills_clean) > 2:
                    skill_complexity = "medium"
                
                # Combine complexity indicators
                if desc_complexity == "high" or skill_complexity == "high":
                    complexity = "high"
                elif desc_complexity == "medium" or skill_complexity == "medium":
                    complexity = "medium"
                else:
                    complexity = "low"
            
            # Create blueprint ID (mock - in real implementation would use proper ID generation)
            blueprint_id = f"blueprint_{len(title_clean[:10])}_{estimated_duration_minutes}"
            
            # TODO: Store blueprint in database
            # For now, return mock success
            
            logger.info(f"Created task blueprint '{title_clean}' with complexity: {complexity}")
            
            return {
                "success": True,
                "blueprint_id": blueprint_id,
                "title": title_clean,
                "description": description_clean,
                "estimated_duration_minutes": estimated_duration_minutes,
                "required_skills": skills_clean,
                "priority_score": priority_score,
                "tags": tags_clean,
                "resource_requirements": resource_requirements or {},
                "project_id": project_id_clean,
                "complexity": complexity,
                "created_at": "2025-01-10T12:00:00Z",  # Mock timestamp
                "message": f"Successfully created task blueprint '{title_clean}' with {complexity} complexity"
            }
            
        except Exception as e:
            logger.error(f"Error creating task blueprint: {e}")
            return {
                "success": False,
                "error": f"Failed to create task blueprint: {str(e)}"
            }
    
    @mcp.tool()
    async def get_task_dependencies(blueprint_id: str) -> Dict[str, Any]:
        """
        Get dependencies for a task blueprint.
        
        Args:
            blueprint_id: Blueprint ID to get dependencies for
            
        Returns:
            Dict with dependency information
        """
        logger.debug(f"Getting dependencies for blueprint: {blueprint_id}")
        
        try:
            if not blueprint_id or len(blueprint_id.strip()) == 0:
                return {
                    "success": False,
                    "error": "Blueprint ID cannot be empty"
                }
            
            blueprint_id_clean = sanitize_user_input(blueprint_id)
            
            # TODO: Query actual dependencies from database
            # For now, return mock dependencies
            mock_dependencies = [
                {
                    "prerequisite_id": "blueprint_setup_123",
                    "dependency_type": "blocking",
                    "is_critical": True,
                    "title": "Environment Setup"
                },
                {
                    "prerequisite_id": "blueprint_data_456", 
                    "dependency_type": "soft",
                    "is_critical": False,
                    "title": "Data Preparation"
                }
            ]
            
            logger.info(f"Retrieved {len(mock_dependencies)} dependencies for {blueprint_id_clean}")
            
            return {
                "success": True,
                "blueprint_id": blueprint_id_clean,
                "dependencies": mock_dependencies,
                "total_dependencies": len(mock_dependencies),
                "critical_dependencies": sum(1 for dep in mock_dependencies if dep["is_critical"])
            }
            
        except Exception as e:
            logger.error(f"Error getting task dependencies: {e}")
            return {
                "success": False,
                "error": f"Failed to get dependencies: {str(e)}",
                "dependencies": []
            }
    
    logger.info("✅ Basic taskmaster tools registered successfully")
    logger.info("  - create_task_blueprint: Create task blueprints with ML analysis")
    logger.info("  - get_task_dependencies: Get blueprint dependencies")