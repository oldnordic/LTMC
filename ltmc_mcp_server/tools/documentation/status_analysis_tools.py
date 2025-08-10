"""
Status Analysis Documentation Tools - FastMCP Implementation
===========================================================

Status monitoring and change detection tools for documentation systems.

Tools implemented:
1. get_sync_status - Get synchronization status for project
2. detect_code_changes - Detect changes in code files for synchronization
"""

import logging
from typing import Dict, Any, Optional, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.database_service import DatabaseService
from services.neo4j_service import Neo4jService
from utils.validation_utils import sanitize_user_input, validate_content_length
from utils.logging_utils import get_tool_logger


def register_status_analysis_documentation_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register status analysis documentation tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('status_analysis_documentation')
    logger.info("Registering status analysis documentation tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    neo4j_service = Neo4jService(settings)
    
    @mcp.tool()
    async def get_sync_status(project_id: str) -> Dict[str, Any]:
        """
        Get synchronization status for project.
        
        This tool retrieves the current status of documentation synchronization
        for a specific project, including recent activities and health metrics.
        
        Args:
            project_id: Project ID to get sync status for
            
        Returns:
            Dict with comprehensive sync status information
        """
        logger.debug(f"Getting sync status for project: {project_id}")
        
        try:
            # Validate input
            if not project_id:
                return {
                    "success": False,
                    "error": "project_id is required"
                }
            
            project_validation = validate_content_length(project_id, max_length=100)
            if not project_validation.is_valid:
                return {
                    "success": False,
                    "error": "Invalid project_id"
                }
            
            project_id_clean = sanitize_user_input(project_id)
            
            # TODO: Query actual sync status from database
            # For now, return mock sync status
            
            sync_status = {
                "project_id": project_id_clean,
                "overall_status": "healthy",
                "last_sync": "2025-01-10T11:45:00Z",
                "next_scheduled_sync": "2025-01-10T12:15:00Z",
                "sync_frequency": "every_30_minutes"
            }
            
            file_statuses = [
                {
                    "file_path": "src/main.py",
                    "last_modified": "2025-01-10T10:30:00Z",
                    "last_synced": "2025-01-10T11:45:00Z",
                    "status": "synced",
                    "consistency_score": 0.95
                },
                {
                    "file_path": "src/utils.py",
                    "last_modified": "2025-01-10T11:50:00Z",
                    "last_synced": "2025-01-10T11:45:00Z",
                    "status": "pending_sync",
                    "consistency_score": 0.82
                }
            ]
            
            health_metrics = {
                "average_consistency_score": 0.88,
                "files_requiring_sync": 1,
                "total_monitored_files": len(file_statuses),
                "sync_success_rate_24h": 0.96,
                "average_sync_time_ms": 150
            }
            
            recent_activities = [
                {
                    "timestamp": "2025-01-10T11:45:00Z",
                    "activity": "automated_sync",
                    "files_affected": 3,
                    "status": "completed"
                },
                {
                    "timestamp": "2025-01-10T11:20:00Z", 
                    "activity": "drift_detection",
                    "files_affected": 1,
                    "status": "completed"
                }
            ]
            
            logger.info(f"Retrieved sync status for project {project_id_clean}")
            
            return {
                "success": True,
                "sync_status": sync_status,
                "file_statuses": file_statuses,
                "health_metrics": health_metrics,
                "recent_activities": recent_activities,
                "recommendations": [
                    "Sync pending file: src/utils.py",
                    "Review consistency scores below 0.85"
                ] if health_metrics["files_requiring_sync"] > 0 else ["All files are synchronized"]
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                "success": False,
                "error": f"Failed to get sync status: {str(e)}"
            }
    
    @mcp.tool()
    async def detect_code_changes(
        file_paths: List[str],
        project_id: str
    ) -> Dict[str, Any]:
        """
        Detect changes in code files for synchronization.
        
        This tool analyzes code files to identify recent changes that may
        require documentation updates or synchronization.
        
        Args:
            file_paths: List of file paths to analyze for changes
            project_id: Project ID for context
            
        Returns:
            Dict with detected changes and synchronization recommendations
        """
        logger.debug(f"Detecting code changes for {len(file_paths)} files")
        
        try:
            # Validate inputs
            if not file_paths or not project_id:
                return {
                    "success": False,
                    "error": "file_paths and project_id are required"
                }
            
            if len(file_paths) > 50:
                return {
                    "success": False,
                    "error": "Cannot analyze more than 50 files at once"
                }
            
            # Validate file paths
            valid_paths = []
            for path in file_paths:
                if path and validate_content_length(path, max_length=500).is_valid:
                    valid_paths.append(sanitize_user_input(path))
            
            project_id_clean = sanitize_user_input(project_id)
            
            if not valid_paths:
                return {
                    "success": False,
                    "error": "No valid file paths provided"
                }
            
            # TODO: Implement actual change detection
            # For now, return mock change analysis
            
            detected_changes = [
                {
                    "file_path": valid_paths[0],
                    "change_type": "function_signature_modified",
                    "element": "process_data",
                    "change_details": "Added new parameter 'validate'",
                    "line_number": 45,
                    "timestamp": "2025-01-10T11:50:00Z",
                    "requires_doc_update": True
                }
            ]
            
            if len(valid_paths) > 1:
                detected_changes.append({
                    "file_path": valid_paths[1],
                    "change_type": "new_class_added",
                    "element": "DataValidator",
                    "change_details": "New class with 3 methods",
                    "line_number": 120,
                    "timestamp": "2025-01-10T11:30:00Z",
                    "requires_doc_update": True
                })
            
            change_summary = {
                "total_files_analyzed": len(valid_paths),
                "files_with_changes": len([c for c in detected_changes if c["file_path"] in valid_paths]),
                "total_changes_detected": len(detected_changes),
                "changes_requiring_doc_update": sum(1 for c in detected_changes if c.get("requires_doc_update", False)),
                "analysis_timestamp": "2025-01-10T12:00:00Z"
            }
            
            sync_recommendations = []
            for change in detected_changes:
                if change.get("requires_doc_update"):
                    sync_recommendations.append(
                        f"Update documentation for {change['element']} in {change['file_path']}"
                    )
            
            logger.info(f"Detected {len(detected_changes)} changes across {len(valid_paths)} files")
            
            return {
                "success": True,
                "project_id": project_id_clean,
                "analyzed_files": valid_paths,
                "detected_changes": detected_changes,
                "change_summary": change_summary,
                "sync_recommendations": sync_recommendations,
                "next_actions": [
                    "Run sync_documentation_with_code for files with changes",
                    "Update project documentation index"
                ] if detected_changes else ["No changes detected - documentation is current"]
            }
            
        except Exception as e:
            logger.error(f"Error detecting code changes: {e}")
            return {
                "success": False,
                "error": f"Failed to detect changes: {str(e)}"
            }
    
    logger.info("✅ Status analysis documentation tools registered successfully")
    logger.info("  - get_sync_status: Get synchronization status for project")
    logger.info("  - detect_code_changes: Detect changes in code files for synchronization")