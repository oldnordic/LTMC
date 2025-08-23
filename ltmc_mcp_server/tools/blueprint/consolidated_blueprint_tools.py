"""
Consolidated Blueprint Tools - FastMCP Implementation
====================================================

1 unified blueprint tool for all blueprint operations.

Consolidated Tool:
- blueprint_manage - Unified tool for all blueprint operations
  * create_from_code - Create Neo4j blueprints from code analysis
  * update_structure - Update blueprint structure from code changes
  * validate_consistency - Validate blueprint-code consistency
  * query_relationships - Query Neo4j blueprint relationships
  * generate_documentation - Generate documentation from blueprints
"""

from typing import Dict, Any, List

# Official MCP SDK import
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...services.blueprint_service import BlueprintService
from ...utils.logging_utils import get_tool_logger


def register_consolidated_blueprint_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register consolidated blueprint tools with FastMCP server."""
    logger = get_tool_logger('blueprint.consolidated')
    logger.info("Registering consolidated blueprint tools")
    
    # Initialize blueprint service
    blueprint_service = BlueprintService(settings)
    
    @mcp.tool()
    async def blueprint_manage(
        operation: str,
        file_path: str = None,
        project_id: str = None,
        blueprint_id: str = None,
        entity_id: str = None,
        relationship_types: List[str] = None,
        max_depth: int = 2,
        format: str = "markdown",
        include_relationships: bool = True
    ) -> Dict[str, Any]:
        """
        Unified blueprint management tool.
        
        Args:
            operation: Operation to perform ("create_from_code", "update_structure", "validate_consistency", "query_relationships", "generate_documentation")
            file_path: Path to the code file (for create_from_code and update_structure operations)
            project_id: Project identifier (for create_from_code operation)
            blueprint_id: Blueprint ID (for update_structure, validate_consistency, and generate_documentation operations)
            entity_id: Entity ID (for query_relationships operation)
            relationship_types: List of relationship types to filter by (for query_relationships operation)
            max_depth: Maximum depth for relationship traversal (for query_relationships operation)
            format: Output format for documentation (markdown, html, json) (for generate_documentation operation)
            include_relationships: Whether to include relationship diagrams (for generate_documentation operation)
            
        Returns:
            Dict with operation results and metadata
        """
        logger.debug("Blueprint operation: {}".format(operation))
        
        try:
            if operation == "create_from_code":
                if not file_path or not project_id:
                    return {"success": False, "error": "file_path and project_id required for create_from_code operation"}
                
                # Validate inputs
                if not file_path or len(file_path.strip()) == 0:
                    return {
                        "success": False,
                        "error": "File path cannot be empty"
                    }
                
                # Create blueprint from code
                logger.debug("Creating blueprint from code: {}".format(file_path))
                result = await blueprint_service.create_blueprint_from_code(file_path, project_id)
                
                if result.get("success", False):
                    logger.info("Created blueprint from code: {}".format(file_path))
                    return {
                        "success": True,
                        "operation": "create_from_code",
                        "file_path": file_path,
                        "project_id": project_id,
                        "blueprint_id": result.get("blueprint_id"),
                        "message": "Blueprint created successfully from code"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Blueprint creation failed")
                    }
                
            elif operation == "update_structure":
                if not blueprint_id or not file_path:
                    return {"success": False, "error": "blueprint_id and file_path required for update_structure operation"}
                
                # Update blueprint structure
                logger.debug("Updating blueprint structure: {}".format(blueprint_id))
                result = await blueprint_service.update_blueprint_structure(blueprint_id, file_path)
                
                if result.get("success", False):
                    logger.info("Updated blueprint structure: {}".format(blueprint_id))
                    return {
                        "success": True,
                        "operation": "update_structure",
                        "blueprint_id": blueprint_id,
                        "file_path": file_path,
                        "message": "Blueprint structure updated successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Blueprint structure update failed")
                    }
                
            elif operation == "validate_consistency":
                if not blueprint_id or not file_path:
                    return {"success": False, "error": "blueprint_id and file_path required for validate_consistency operation"}
                
                # Validate blueprint consistency
                logger.debug("Validating blueprint consistency: {}".format(blueprint_id))
                result = await blueprint_service.validate_blueprint_consistency(blueprint_id, file_path)
                
                if result.get("success", False):
                    logger.info("Validated blueprint consistency: {}".format(blueprint_id))
                    return {
                        "success": True,
                        "operation": "validate_consistency",
                        "blueprint_id": blueprint_id,
                        "file_path": file_path,
                        "consistency_score": result.get("consistency_score"),
                        "message": "Blueprint consistency validated successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Blueprint consistency validation failed")
                    }
                
            elif operation == "query_relationships":
                if not entity_id:
                    return {"success": False, "error": "entity_id required for query_relationships operation"}
                
                # Query blueprint relationships
                logger.debug("Querying blueprint relationships: {}".format(entity_id))
                result = await blueprint_service.query_blueprint_relationships(
                    entity_id, 
                    relationship_types=relationship_types or [],
                    max_depth=max_depth
                )
                
                if result.get("success", False):
                    logger.info("Queried blueprint relationships: {}".format(entity_id))
                    return {
                        "success": True,
                        "operation": "query_relationships",
                        "entity_id": entity_id,
                        "relationships": result.get("relationships", []),
                        "message": "Blueprint relationships queried successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Blueprint relationships query failed")
                    }
                
            elif operation == "generate_documentation":
                if not blueprint_id:
                    return {"success": False, "error": "blueprint_id required for generate_documentation operation"}
                
                # Generate blueprint documentation
                logger.debug("Generating blueprint documentation: {}".format(blueprint_id))
                result = await blueprint_service.generate_blueprint_documentation(
                    blueprint_id,
                    format=format,
                    include_relationships=include_relationships
                )
                
                if result.get("success", False):
                    logger.info("Generated blueprint documentation: {}".format(blueprint_id))
                    return {
                        "success": True,
                        "operation": "generate_documentation",
                        "blueprint_id": blueprint_id,
                        "format": format,
                        "documentation": result.get("documentation"),
                        "message": "Blueprint documentation generated successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Blueprint documentation generation failed")
                    }
                
            else:
                return {
                    "success": False,
                    "error": "Unknown operation: {}. Valid operations: create_from_code, update_structure, validate_consistency, query_relationships, generate_documentation".format(operation)
                }
                
        except Exception as e:
            logger.error("Error in blueprint operation '{}': {}".format(operation, e))
            return {
                "success": False,
                "error": "Blueprint operation failed: {}".format(str(e))
            }
    
    logger.info("✅ Consolidated blueprint tools registered successfully")
    logger.info("📊 Tool consolidation: 5 individual tools → 1 unified tool")
    logger.info("🔧 All functionality preserved through operation parameter")
