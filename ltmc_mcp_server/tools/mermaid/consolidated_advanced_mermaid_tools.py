"""
Consolidated Advanced Mermaid Tools - Unified Memory Integration & Templates
===========================================================================

Consolidated tool combining all 8 advanced Mermaid tools:
- store_diagram: Store diagrams in LTMC memory
- retrieve_diagrams: Search and retrieve stored diagrams
- create_template: Create reusable templates
- generate_from_template: Generate diagrams from templates
- diagram_version_control: Version management for diagrams
- batch_diagram_generation: Generate multiple diagrams
- diagram_optimization: Optimize diagram performance
- memory_integration: Memory system integration

All functionality preserved through operation parameter.
"""

import json
from typing import Dict, Any, List
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.mermaid_service import MermaidService, DiagramType
from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_consolidated_advanced_mermaid_tools(
    mcp: FastMCP, settings: LTMCSettings
) -> None:
    """Register consolidated advanced Mermaid tools with memory integration."""
    logger = get_tool_logger('consolidated_advanced_mermaid')
    logger.info("Registering consolidated advanced Mermaid tools")
    
    # Initialize services
    mermaid_service = MermaidService(settings)
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def mermaid_advanced_manage(
        operation: str,
        content: str = None,
        diagram_type: str = None,
        title: str = None,
        description: str = "",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        query: str = "",
        limit: int = 10,
        template_name: str = None,
        template_data: Dict[str, Any] = None,
        version_notes: str = None,
        batch_content: List[str] = None,
        optimization_target: str = None
    ) -> Dict[str, Any]:
        """
        Unified tool for all advanced Mermaid operations.
        
        Args:
            operation: Operation to perform (store_diagram, retrieve_diagrams, 
                       create_template, generate_from_template, diagram_version_control,
                       batch_diagram_generation, diagram_optimization, memory_integration)
            content: Mermaid diagram content
            diagram_type: Type of diagram
            title: Diagram title
            description: Optional description
            tags: List of tags for categorization
            metadata: Additional metadata
            query: Search query for diagram content/title
            limit: Maximum number of results
            template_name: Name for template operations
            template_data: Template data for generation
            version_notes: Notes for version control
            batch_content: List of diagram contents for batch operations
            optimization_target: Target for optimization operations
            
        Returns:
            Dict with operation results
        """
        
        if operation == "store_diagram":
            return await _store_diagram(
                content, diagram_type, title, description, tags, metadata
            )
        elif operation == "retrieve_diagrams":
            return await _retrieve_diagrams(query, diagram_type, tags, limit)
        elif operation == "create_template":
            return await _create_template(
                template_name, content, diagram_type, description, tags
            )
        elif operation == "generate_from_template":
            return await _generate_from_template(
                template_name, template_data, diagram_type
            )
        elif operation == "diagram_version_control":
            return await _diagram_version_control(
                content, diagram_type, title, version_notes
            )
        elif operation == "batch_diagram_generation":
            return await _batch_diagram_generation(
                batch_content, diagram_type, title
            )
        elif operation == "diagram_optimization":
            return await _diagram_optimization(
                content, diagram_type, optimization_target
            )
        elif operation == "memory_integration":
            return await _memory_integration(content, diagram_type, title)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Valid operations: store_diagram, retrieve_diagrams, create_template, generate_from_template, diagram_version_control, batch_diagram_generation, diagram_optimization, memory_integration"
            }
    
    async def _store_diagram(
        content: str,
        diagram_type: str,
        title: str,
        description: str = "",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Store a Mermaid diagram in LTMC memory system."""
        try:
            if not content or not diagram_type or not title:
                return {
                    "success": False,
                    "error": "Content, diagram_type, and title are required"
                }
            
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
    
    async def _retrieve_diagrams(
        query: str = "",
        diagram_type: str = "",
        tags: List[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search and retrieve stored Mermaid diagrams."""
        try:
            # Get resources from database
            resources = await db_service.get_resources_by_type("mermaid_diagram")
            
            # Filter results
            filtered_results = []
            for resource in resources[:limit]:
                try:
                    diagram_data = json.loads(resource["content"])
                    
                    # Apply filters
                    title_match = query.lower() in diagram_data["title"].lower()
                    content_match = query.lower() in diagram_data["content"].lower()
                    if query and not title_match and not content_match:
                        continue
                    
                    if diagram_type and diagram_data["diagram_type"] != diagram_type:
                        continue
                    
                    if tags and not any(tag in diagram_data.get("tags", []) for tag in tags):
                        continue
                    
                    filtered_results.append({
                        "id": resource["id"],
                        "title": diagram_data["title"],
                        "diagram_type": diagram_data["diagram_type"],
                        "description": diagram_data.get("description", ""),
                        "tags": diagram_data.get("tags", []),
                        "stored_at": diagram_data.get("stored_at", ""),
                        "metadata": diagram_data.get("metadata", {})
                    })
                    
                except json.JSONDecodeError:
                    continue
            
            return {
                "success": True,
                "diagrams": filtered_results,
                "total_found": len(filtered_results),
                "query": query,
                "filters_applied": {
                    "diagram_type": diagram_type,
                    "tags": tags,
                    "limit": limit
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_template(
        template_name: str,
        content: str,
        diagram_type: str,
        description: str = "",
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Create a reusable Mermaid diagram template."""
        try:
            if not template_name or not content or not diagram_type:
                return {
                    "success": False,
                    "error": "Template name, content, and diagram_type are required"
                }
            
            # Validate diagram content
            dt = DiagramType(diagram_type)
            validation_result = await mermaid_service.generate_diagram(
                content=content,
                diagram_type=dt
            )
            
            if not validation_result["success"]:
                return {
                    "success": False,
                    "error": f"Invalid diagram content: {validation_result['error']}"
                }
            
            # Create template data
            template_data = {
                "name": template_name,
                "content": content,
                "diagram_type": diagram_type,
                "description": description,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            # Store template
            resource_id, vector_id = await db_service.store_resource(
                file_name=f"mermaid_template_{template_name.replace(' ', '_')}.json",
                resource_type="mermaid_template",
                content=json.dumps(template_data, indent=2)
            )
            
            return {
                "success": True,
                "template_id": resource_id,
                "template_name": template_name,
                "message": f"Template '{template_name}' created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_from_template(
        template_name: str,
        template_data: Dict[str, Any],
        diagram_type: str
    ) -> Dict[str, Any]:
        """Generate a diagram from a stored template."""
        try:
            if not template_name:
                return {
                    "success": False,
                    "error": "Template name is required"
                }
            
            # Retrieve template
            resources = await db_service.get_resources_by_type("mermaid_template")
            template = None
            
            for resource in resources:
                try:
                    data = json.loads(resource["content"])
                    if data["name"] == template_name:
                        template = data
                        break
                except json.JSONDecodeError:
                    continue
            
            if not template:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found"
                }
            
            # Apply template data if provided
            content = template["content"]
            if template_data:
                for key, value in template_data.items():
                    content = content.replace(f"{{{{{key}}}}}", str(value))
            
            # Generate diagram
            dt = DiagramType(diagram_type or template["diagram_type"])
            generation_result = await mermaid_service.generate_diagram(
                content=content,
                diagram_type=dt
            )
            
            if not generation_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to generate diagram: {generation_result['error']}"
                }
            
            # Update template usage count
            template["usage_count"] += 1
            await db_service.update_resource(
                resource_id=resource["id"],
                content=json.dumps(template, indent=2)
            )
            
            return {
                "success": True,
                "diagram": {
                    "content": content,
                    "diagram_type": dt.value,
                    "svg": generation_result.get("data", ""),
                    "generated_from_template": template_name
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _diagram_version_control(
        content: str,
        diagram_type: str,
        title: str,
        version_notes: str = None
    ) -> Dict[str, Any]:
        """Manage versions of Mermaid diagrams."""
        try:
            if not content or not diagram_type or not title:
                return {
                    "success": False,
                    "error": "Content, diagram_type, and title are required"
                }
            
            # Generate version ID
            version_id = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create version data
            version_data = {
                "version_id": version_id,
                "title": title,
                "content": content,
                "diagram_type": diagram_type,
                "version_notes": version_notes or "New version",
                "created_at": datetime.now().isoformat(),
                "previous_versions": []
            }
            
            # Store version
            resource_id, vector_id = await db_service.store_resource(
                file_name=f"mermaid_version_{version_id}.json",
                resource_type="mermaid_version",
                content=json.dumps(version_data, indent=2)
            )
            
            return {
                "success": True,
                "version_id": version_id,
                "resource_id": resource_id,
                "message": f"Version '{version_id}' created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _batch_diagram_generation(
        batch_content: List[str],
        diagram_type: str,
        title: str
    ) -> Dict[str, Any]:
        """Generate multiple diagrams in batch."""
        try:
            if not batch_content or not diagram_type or not title:
                return {
                    "success": False,
                    "error": "Batch content, diagram_type, and title are required"
                }
            
            results = []
            dt = DiagramType(diagram_type)
            
            for i, content in enumerate(batch_content):
                try:
                    generation_result = await mermaid_service.generate_diagram(
                        content=content,
                        diagram_type=dt
                    )
                    
                    if generation_result["success"]:
                        results.append({
                            "index": i,
                            "success": True,
                            "svg": generation_result.get("data", ""),
                            "content": content
                        })
                    else:
                        results.append({
                            "index": i,
                            "success": False,
                            "error": generation_result.get("error", "Unknown error")
                        })
                        
                except Exception as e:
                    results.append({
                        "index": i,
                        "success": False,
                        "error": str(e)
                    })
            
            success_count = sum(1 for r in results if r["success"])
            
            return {
                "success": True,
                "batch_results": results,
                "total_processed": len(batch_content),
                "successful": success_count,
                "failed": len(batch_content) - success_count,
                "title": title
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _diagram_optimization(
        content: str,
        diagram_type: str,
        optimization_target: str = None
    ) -> Dict[str, Any]:
        """Optimize Mermaid diagram performance and readability."""
        try:
            if not content or not diagram_type:
                return {
                    "success": False,
                    "error": "Content and diagram_type are required"
                }
            
            optimization_target = optimization_target or "performance"
            optimizations = []
            
            if optimization_target == "performance":
                # Count nodes and edges
                lines = content.split('\n')
                node_count = sum(1 for line in lines if '[' in line and ']' in line)
                edge_count = sum(1 for line in lines if '-->' in line or '---' in line)
                
                if node_count > 20:
                    optimizations.append({
                        "type": "reduce_nodes",
                        "description": f"Diagram has {node_count} nodes, consider breaking into smaller diagrams",
                        "impact": "Improves rendering performance"
                    })
                
                if edge_count > 30:
                    optimizations.append({
                        "type": "reduce_edges",
                        "description": f"Diagram has {edge_count} edges, consider simplifying relationships",
                        "impact": "Improves readability and performance"
                    })
            
            elif optimization_target == "readability":
                # Check for long labels
                long_labels = [line for line in lines if len(line.strip()) > 50]
                if long_labels:
                    optimizations.append({
                        "type": "shorten_labels",
                        "description": f"Found {len(long_labels)} lines with long labels",
                        "impact": "Improves visual clarity"
                    })
            
            # Generate optimized version if possible
            dt = DiagramType(diagram_type)
            generation_result = await mermaid_service.generate_diagram(
                content=content,
                diagram_type=dt
            )
            
            return {
                "success": True,
                "optimizations": optimizations,
                "original_content": content,
                "optimized_svg": generation_result.get("data", ""),
                "target": optimization_target
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _memory_integration(
        content: str,
        diagram_type: str,
        title: str
    ) -> Dict[str, Any]:
        """Integrate diagram with LTMC memory system."""
        try:
            if not content or not diagram_type or not title:
                return {
                    "success": False,
                    "error": "Content, diagram_type, and title are required"
                }
            
            # Store in memory system
            memory_result = await _store_diagram(
                content, diagram_type, title, "", [], {}
            )
            
            if not memory_result["success"]:
                return memory_result
            
            # Create memory associations
            memory_data = {
                "diagram_id": memory_result["diagram_id"],
                "title": title,
                "diagram_type": diagram_type,
                "integrated_at": datetime.now().isoformat(),
                "associations": [],
                "search_index": content.lower().split()
            }
            
            # Store memory integration data
            await db_service.store_resource(
                file_name=f"mermaid_memory_{title.replace(' ', '_')}.json",
                resource_type="mermaid_memory_integration",
                content=json.dumps(memory_data, indent=2)
            )
            
            return {
                "success": True,
                "memory_integration": {
                    "diagram_id": memory_result["diagram_id"],
                    "title": title,
                    "integrated_at": memory_data["integrated_at"],
                    "search_index_size": len(memory_data["search_index"])
                },
                "message": f"Diagram '{title}' integrated with memory system"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
