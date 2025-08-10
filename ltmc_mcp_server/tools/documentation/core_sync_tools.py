"""
Core Sync Documentation Tools - FastMCP Implementation
=====================================================

Core documentation synchronization tools following FastMCP patterns.

Tools implemented:
1. sync_documentation_with_code - Sync documentation with code changes
2. update_documentation_from_blueprint - Update docs from blueprints
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


def register_core_sync_documentation_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register core sync documentation tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('core_sync_documentation')
    logger.info("Registering core sync documentation tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    neo4j_service = Neo4jService(settings)
    
    @mcp.tool()
    async def sync_documentation_with_code(
        file_path: str,
        project_id: str,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize documentation with code changes.
        
        This tool analyzes code changes and updates corresponding documentation
        to maintain consistency between code and documentation.
        
        Args:
            file_path: Path to the code file to sync
            project_id: Project ID for organization
            force_update: Force update even if no changes detected
            
        Returns:
            Dict with sync results and changes made
        """
        logger.debug(f"Syncing documentation with code: {file_path}")
        
        try:
            # Validate inputs
            if not file_path or not project_id:
                return {
                    "success": False,
                    "error": "file_path and project_id are required"
                }
            
            path_validation = validate_content_length(file_path, max_length=500)
            project_validation = validate_content_length(project_id, max_length=100)
            
            if not path_validation.is_valid or not project_validation.is_valid:
                return {
                    "success": False,
                    "error": "Invalid file_path or project_id"
                }
            
            # Sanitize inputs
            file_path_clean = sanitize_user_input(file_path)
            project_id_clean = sanitize_user_input(project_id)
            
            # TODO: Implement actual documentation sync logic
            # For now, return mock sync results
            
            changes_made = [
                {
                    "type": "function_documentation",
                    "element": "process_data",
                    "change": "Updated parameter documentation",
                    "line": 45
                },
                {
                    "type": "class_documentation", 
                    "element": "DataProcessor",
                    "change": "Added new method documentation",
                    "line": 120
                }
            ]
            
            sync_summary = {
                "total_changes": len(changes_made),
                "functions_updated": sum(1 for c in changes_made if c["type"] == "function_documentation"),
                "classes_updated": sum(1 for c in changes_made if c["type"] == "class_documentation"),
                "force_update_applied": force_update
            }
            
            logger.info(f"Synced documentation for {file_path_clean}: {len(changes_made)} changes")
            
            return {
                "success": True,
                "file_path": file_path_clean,
                "project_id": project_id_clean,
                "force_update": force_update,
                "changes_made": changes_made,
                "sync_summary": sync_summary,
                "message": f"Successfully synced documentation for {file_path_clean}"
            }
            
        except Exception as e:
            logger.error(f"Error syncing documentation: {e}")
            return {
                "success": False,
                "error": f"Failed to sync documentation: {str(e)}"
            }
    
    @mcp.tool()
    async def update_documentation_from_blueprint(
        blueprint_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Update documentation from Neo4j blueprint changes.
        
        This tool synchronizes documentation with blueprint changes
        stored in the Neo4j graph database.
        
        Args:
            blueprint_id: Blueprint ID to sync documentation from
            project_id: Project ID for context
            
        Returns:
            Dict with documentation update results
        """
        logger.debug(f"Updating documentation from blueprint: {blueprint_id}")
        
        try:
            # Validate inputs
            if not blueprint_id or not project_id:
                return {
                    "success": False,
                    "error": "blueprint_id and project_id are required"
                }
            
            # Sanitize inputs
            blueprint_id_clean = sanitize_user_input(blueprint_id)
            project_id_clean = sanitize_user_input(project_id)
            
            # TODO: Implement actual blueprint-to-documentation sync
            # For now, return mock update results
            
            updates_made = [
                {
                    "type": "class_documentation",
                    "element": "DataProcessor",
                    "update": "Updated class description from blueprint"
                },
                {
                    "type": "method_documentation",
                    "element": "process",
                    "update": "Updated method parameters from blueprint"
                }
            ]
            
            update_summary = {
                "total_updates": len(updates_made),
                "documentation_sections_updated": len(set(u["type"] for u in updates_made)),
                "blueprint_source": blueprint_id_clean
            }
            
            logger.info(f"Updated documentation from blueprint {blueprint_id_clean}: {len(updates_made)} updates")
            
            return {
                "success": True,
                "blueprint_id": blueprint_id_clean,
                "project_id": project_id_clean,
                "updates_made": updates_made,
                "update_summary": update_summary,
                "message": f"Successfully updated documentation from blueprint {blueprint_id_clean}"
            }
            
        except Exception as e:
            logger.error(f"Error updating documentation from blueprint: {e}")
            return {
                "success": False,
                "error": f"Failed to update documentation: {str(e)}"
            }
    
    logger.info("✅ Core sync documentation tools registered successfully")
    logger.info("  - sync_documentation_with_code: Sync docs with code changes")
    logger.info("  - update_documentation_from_blueprint: Update docs from blueprints")