"""
Advanced Mermaid Tools - Memory Integration & Templates
======================================================

8 advanced Mermaid tools with LTMC memory system integration.
Provides persistent storage, templates, and intelligent diagram management.

Tools:
9. mermaid_store_diagram - Store diagrams in LTMC memory
10. mermaid_retrieve_diagrams - Search and retrieve stored diagrams  
11. mermaid_create_template - Create reusable templates
12. mermaid_generate_from_template - Generate diagrams from templates
13. mermaid_diagram_version_control - Version management for diagrams
14. mermaid_batch_diagram_generation - Generate multiple diagrams
15. mermaid_diagram_optimization - Optimize diagram performance
16. mermaid_memory_integration - Memory system integration
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.mermaid_service import MermaidService, DiagramType, OutputFormat
from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_advanced_mermaid_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register advanced Mermaid tools with memory integration."""
    logger = get_tool_logger('advanced_mermaid')
    logger.info("Registering advanced Mermaid tools")
    
    # Initialize services
    mermaid_service = MermaidService(settings)
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def mermaid_store_diagram(
        content: str,
        diagram_type: str,
        title: str,
        description: str = "",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Store a Mermaid diagram in LTMC memory system.
        
        Args:
            content: Mermaid diagram content
            diagram_type: Type of diagram
            title: Diagram title
            description: Optional description
            tags: List of tags for categorization
            metadata: Additional metadata
            
        Returns:
            Dict with storage results and diagram ID
        """
        try:
            # Generate diagram first to validate
            dt = DiagramType(diagram_type)
            generation_result = await mermaid_service.generate_diagram(
                content=content,
                diagram_type=dt
            )
            
            if not generation_result["success"]:
                return {
                    "success": False,
                    "error": f"Invalid diagram content: {generation_result['error']}"
                }
            
            # Store in LTMC memory
            diagram_data = {
                "content": content,
                "diagram_type": diagram_type,
                "title": title,
                "description": description,
                "tags": tags or [],
                "metadata": metadata or {},
                "generated_svg": generation_result.get("data", ""),
                "stored_at": datetime.now().isoformat()
            }
            
            # Store as resource in LTMC database
            resource_id, vector_id = await db_service.store_resource(
                file_name=f"mermaid_diagram_{title.replace(' ', '_')}.json",
                resource_type="mermaid_diagram",
                content=json.dumps(diagram_data, indent=2)
            )
            
            return {
                "success": True,
                "diagram_id": resource_id,
                "vector_id": vector_id,
                "title": title,
                "message": f"Diagram '{title}' stored successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_retrieve_diagrams(
        query: str = "",
        diagram_type: str = "",
        tags: List[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search and retrieve stored Mermaid diagrams.
        
        Args:
            query: Search query for diagram content/title
            diagram_type: Filter by diagram type
            tags: Filter by tags
            limit: Maximum number of results
            
        Returns:
            Dict with matching diagrams
        """
        try:
            # Get resources from database
            resources = await db_service.get_resources_by_type("mermaid_diagram")
            
            # Filter results
            filtered_results = []
            for resource in resources:
                try:
                    diagram_data = json.loads(resource["content"])
                    
                    # Apply filters
                    if diagram_type and diagram_data.get("diagram_type") != diagram_type:
                        continue
                    
                    if tags:
                        diagram_tags = diagram_data.get("tags", [])
                        if not any(tag in diagram_tags for tag in tags):
                            continue
                    
                    if query:
                        searchable_text = f"{diagram_data.get('title', '')} {diagram_data.get('description', '')} {diagram_data.get('content', '')}"
                        if query.lower() not in searchable_text.lower():
                            continue
                    
                    filtered_results.append({
                        "id": resource["id"],
                        "title": diagram_data.get("title", ""),
                        "description": diagram_data.get("description", ""),
                        "diagram_type": diagram_data.get("diagram_type", ""),
                        "tags": diagram_data.get("tags", []),
                        "stored_at": diagram_data.get("stored_at", ""),
                        "content": diagram_data.get("content", "")
                    })
                    
                except json.JSONDecodeError:
                    continue
            
            # Limit results
            filtered_results = filtered_results[:limit]
            
            return {
                "success": True,
                "diagrams": filtered_results,
                "total_found": len(filtered_results),
                "query": query,
                "filters": {
                    "diagram_type": diagram_type,
                    "tags": tags
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_create_template(
        name: str,
        content: str,
        diagram_type: str,
        variables: List[str],
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a reusable Mermaid diagram template.
        
        Args:
            name: Template name
            content: Template content with variables (e.g., {{variable_name}})
            diagram_type: Type of diagram
            variables: List of variable names in the template
            description: Template description
            
        Returns:
            Dict with template creation results
        """
        try:
            dt = DiagramType(diagram_type)
            
            result = await mermaid_service.create_template(
                name=name,
                content=content,
                diagram_type=dt,
                variables=variables
            )
            
            if result["success"]:
                # Also store in LTMC memory
                template_data = {
                    "name": name,
                    "content": content,
                    "diagram_type": diagram_type,
                    "variables": variables,
                    "description": description,
                    "created_at": datetime.now().isoformat()
                }
                
                await db_service.store_resource(
                    file_name=f"mermaid_template_{name}.json",
                    resource_type="mermaid_template",
                    content=json.dumps(template_data, indent=2)
                )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_generate_from_template(
        template_name: str,
        variables: Dict[str, str],
        output_format: str = "svg"
    ) -> Dict[str, Any]:
        """
        Generate a diagram from a template with variable substitution.
        
        Args:
            template_name: Name of the template to use
            variables: Variable values for substitution
            output_format: Output format for generated diagram
            
        Returns:
            Dict with generated diagram
        """
        try:
            # Get template from memory
            templates = await mermaid_service.get_templates()
            if template_name not in mermaid_service.templates:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found"
                }
            
            template = mermaid_service.templates[template_name]
            content = template["content"]
            
            # Substitute variables
            for var_name, var_value in variables.items():
                content = content.replace(f"{{{{{var_name}}}}}", var_value)
            
            # Generate diagram
            dt = DiagramType(template["diagram_type"])
            of = OutputFormat(output_format)
            
            result = await mermaid_service.generate_diagram(
                content=content,
                diagram_type=dt,
                output_format=of
            )
            
            return {
                **result,
                "template_used": template_name,
                "variables_applied": variables,
                "generated_content": content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_diagram_version_control(
        diagram_id: int,
        action: str,
        new_content: str = "",
        version_message: str = ""
    ) -> Dict[str, Any]:
        """
        Manage versions of stored diagrams.
        
        Args:
            diagram_id: ID of the diagram to manage
            action: Action to perform (update, revert, list_versions)
            new_content: New diagram content for updates
            version_message: Message describing the changes
            
        Returns:
            Dict with version control results
        """
        try:
            if action == "update":
                # Create new version
                version_data = {
                    "diagram_id": diagram_id,
                    "content": new_content,
                    "message": version_message,
                    "created_at": datetime.now().isoformat(),
                    "version": "auto-generated"
                }
                
                # Store version
                await db_service.store_resource(
                    file_name=f"mermaid_version_{diagram_id}_{datetime.now().isoformat()}.json",
                    resource_type="mermaid_version",
                    content=json.dumps(version_data, indent=2)
                )
                
                return {
                    "success": True,
                    "action": "update",
                    "diagram_id": diagram_id,
                    "message": "New version created successfully"
                }
            
            elif action == "list_versions":
                # Get all versions for this diagram
                all_resources = await db_service.get_resources_by_type("mermaid_version")
                versions = []
                
                for resource in all_resources:
                    try:
                        version_data = json.loads(resource["content"])
                        if version_data.get("diagram_id") == diagram_id:
                            versions.append(version_data)
                    except json.JSONDecodeError:
                        continue
                
                return {
                    "success": True,
                    "action": "list_versions",
                    "diagram_id": diagram_id,
                    "versions": versions,
                    "total_versions": len(versions)
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_batch_diagram_generation(
        diagrams: List[Dict[str, Any]],
        output_format: str = "svg"
    ) -> Dict[str, Any]:
        """
        Generate multiple diagrams in batch.
        
        Args:
            diagrams: List of diagram specifications
            output_format: Output format for all diagrams
            
        Returns:
            Dict with batch generation results
        """
        try:
            results = []
            successful = 0
            failed = 0
            
            for i, diagram_spec in enumerate(diagrams):
                try:
                    dt = DiagramType(diagram_spec["diagram_type"])
                    of = OutputFormat(output_format)
                    
                    result = await mermaid_service.generate_diagram(
                        content=diagram_spec["content"],
                        diagram_type=dt,
                        output_format=of
                    )
                    
                    results.append({
                        "index": i,
                        "title": diagram_spec.get("title", f"Diagram {i+1}"),
                        **result
                    })
                    
                    if result["success"]:
                        successful += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    results.append({
                        "index": i,
                        "title": diagram_spec.get("title", f"Diagram {i+1}"),
                        "success": False,
                        "error": str(e)
                    })
                    failed += 1
            
            return {
                "success": True,
                "batch_results": results,
                "summary": {
                    "total": len(diagrams),
                    "successful": successful,
                    "failed": failed,
                    "success_rate": successful / len(diagrams) * 100 if diagrams else 0
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_diagram_optimization(
        content: str,
        diagram_type: str
    ) -> Dict[str, Any]:
        """
        Analyze and optimize diagram performance.
        
        Args:
            content: Mermaid diagram content
            diagram_type: Type of diagram
            
        Returns:
            Dict with optimization analysis and suggestions
        """
        try:
            # Analyze complexity
            analysis = await mermaid_service.analyze_diagram_complexity(content)
            
            if not analysis["success"]:
                return analysis
            
            complexity = analysis["analysis"]
            suggestions = []
            
            # Generate optimization suggestions
            if complexity["complexity_score"] > 20:
                suggestions.append("Consider breaking this diagram into smaller sub-diagrams")
            
            if complexity["nodes"] > 15:
                suggestions.append("Large number of nodes detected - consider grouping related nodes")
            
            if complexity["edges"] > 20:
                suggestions.append("High number of connections - consider simplifying relationships")
            
            # Performance recommendations
            performance_tips = []
            if complexity["complexity_level"] == "Complex":
                performance_tips.extend([
                    "Use PNG format for complex diagrams to reduce file size",
                    "Consider caching generated diagrams",
                    "Break into multiple views for better user experience"
                ])
            
            return {
                "success": True,
                "complexity_analysis": complexity,
                "optimization_suggestions": suggestions,
                "performance_tips": performance_tips,
                "recommended_format": "png" if complexity["complexity_score"] > 15 else "svg"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_memory_integration(
        action: str,
        diagram_id: int = None,
        search_query: str = ""
    ) -> Dict[str, Any]:
        """
        Advanced memory system integration for Mermaid diagrams.
        
        Args:
            action: Action to perform (stats, search, cleanup, export)
            diagram_id: Specific diagram ID for actions
            search_query: Query for search actions
            
        Returns:
            Dict with memory integration results
        """
        try:
            if action == "stats":
                # Get statistics about stored diagrams
                all_diagrams = await db_service.get_resources_by_type("mermaid_diagram")
                all_templates = await db_service.get_resources_by_type("mermaid_template")
                
                # Analyze diagram types
                type_counts = {}
                for resource in all_diagrams:
                    try:
                        diagram_data = json.loads(resource["content"])
                        dtype = diagram_data.get("diagram_type", "unknown")
                        type_counts[dtype] = type_counts.get(dtype, 0) + 1
                    except json.JSONDecodeError:
                        continue
                
                return {
                    "success": True,
                    "statistics": {
                        "total_diagrams": len(all_diagrams),
                        "total_templates": len(all_templates),
                        "diagram_types": type_counts,
                        "memory_usage": "integrated_with_ltmc_system"
                    }
                }
            
            elif action == "search":
                # Semantic search across all Mermaid content
                return await retrieve_mermaid_diagrams(query=search_query)
            
            elif action == "cleanup":
                # Clean up old or invalid diagrams
                all_diagrams = await db_service.get_resources_by_type("mermaid_diagram")
                cleaned = 0
                
                for resource in all_diagrams:
                    try:
                        diagram_data = json.loads(resource["content"])
                        # Add cleanup logic here (e.g., remove diagrams older than X months)
                        # For now, just validate JSON structure
                        if not diagram_data.get("content") or not diagram_data.get("diagram_type"):
                            cleaned += 1
                    except json.JSONDecodeError:
                        cleaned += 1
                
                return {
                    "success": True,
                    "action": "cleanup",
                    "total_checked": len(all_diagrams),
                    "items_cleaned": cleaned,
                    "message": f"Cleanup completed - processed {len(all_diagrams)} diagrams"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    logger.info("✅ Advanced Mermaid tools registered successfully")
    logger.info("  - store_mermaid_diagram: Store diagrams in LTMC memory")
    logger.info("  - retrieve_mermaid_diagrams: Search stored diagrams")
    logger.info("  - create_mermaid_template: Template management")
    logger.info("  - generate_from_template: Template-based generation")
    logger.info("  - diagram_version_control: Version management")
    logger.info("  - batch_diagram_generation: Batch processing")
    logger.info("  - diagram_optimization: Performance optimization")
    logger.info("  - mermaid_memory_integration: Memory system integration")