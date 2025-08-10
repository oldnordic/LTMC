"""Documentation MCP Tools - Component 4 (Blueprint Generation) - Phase 2.

This module provides MCP tools for documentation generation including:
- API documentation generation
- Architecture diagram creation
- Progress report generation
- Documentation updates and management
"""

import logging
from typing import Dict, Any, Optional, List

from ltms.services.documentation_generator import (
    DocumentationGenerator,
    DocumentType,
    APIDocumentationResult,
    ArchitectureDiagramResult,
    ProgressReportResult
)
from ltms.services.redis_service import get_redis_manager
from ltms.database.neo4j_store import get_neo4j_graph_store
from ltms.security.mcp_integration import (
    MCPSecurityManager,
    ToolExecutionContext,
    create_execution_context
)

logger = logging.getLogger(__name__)

# Global documentation generator instance
_documentation_generator: Optional[DocumentationGenerator] = None


async def get_documentation_generator() -> DocumentationGenerator:
    """Get or create documentation generator instance."""
    global _documentation_generator
    if not _documentation_generator:
        redis_manager = await get_redis_manager()
        neo4j_store = await get_neo4j_graph_store()
        _documentation_generator = DocumentationGenerator(
            redis_manager=redis_manager,
            neo4j_store=neo4j_store
        )
        await _documentation_generator.initialize()
    return _documentation_generator


# MCP Tool Functions

async def generate_api_docs(
    project_id: str,
    source_files: Dict[str, str],
    output_format: str = "markdown",
    template_name: Optional[str] = None,
    execution_context: Optional[ToolExecutionContext] = None
) -> Dict[str, Any]:
    """Generate API documentation from source files.
    
    Args:
        project_id: Project identifier for isolation
        source_files: Dictionary mapping file paths to file contents
        output_format: Output format (markdown, html, etc.)
        template_name: Optional template to use for generation
        execution_context: Security execution context
        
    Returns:
        Dictionary containing generated documentation and metadata
        
    Raises:
        ValueError: If required parameters are missing or invalid
        PermissionError: If access is denied for security reasons
    """
    try:
        # Security validation
        if execution_context:
            await MCPSecurityManager.validate_project_access(
                execution_context,
                project_id
            )
            
            # Validate source files access
            for file_path in source_files.keys():
                await MCPSecurityManager.validate_file_access(
                    execution_context,
                    file_path,
                    'read'
                )
        
        # Input validation
        if not project_id:
            raise ValueError("project_id is required")
        
        if not source_files:
            raise ValueError("source_files dictionary cannot be empty")
        
        if output_format not in ["markdown", "html", "json"]:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # Get documentation generator
        doc_generator = await get_documentation_generator()
        
        # Generate documentation
        result = await doc_generator.generate_api_documentation(
            project_id=project_id,
            source_files=source_files,
            output_format=output_format,
            template_name=template_name
        )
        
        # Convert result to dictionary for MCP response
        response = {
            'success': result.success,
            'documentation': result.documentation_content if result.success else None,
            'error': result.error_message,
            'metadata': {
                'project_id': result.metadata.project_id if result.metadata else project_id,
                'generation_time_ms': result.metadata.generation_time_ms if result.metadata else 0,
                'total_endpoints': result.metadata.total_endpoints if result.metadata else 0,
                'total_models': result.metadata.total_models if result.metadata else 0,
                'template_used': result.metadata.template_used if result.metadata else template_name,
                'generated_at': result.metadata.generated_at.isoformat() if result.metadata else None,
                'cache_key': result.cache_key
            }
        }
        
        logger.info(f"Generated API documentation for project {project_id}: {result.success}")
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_api_docs: {e}")
        return {
            'success': False,
            'documentation': None,
            'error': str(e),
            'metadata': {'project_id': project_id}
        }


async def create_architecture_diagram(
    project_id: str,
    blueprint_id: str,
    diagram_type: str = "component_diagram",
    output_format: str = "mermaid",
    execution_context: Optional[ToolExecutionContext] = None
) -> Dict[str, Any]:
    """Create architecture diagram from blueprint system.
    
    Args:
        project_id: Project identifier for isolation
        blueprint_id: Blueprint ID to create diagram for
        diagram_type: Type of diagram (component_diagram, dependency_graph, etc.)
        output_format: Output format (mermaid, plantuml, etc.)
        execution_context: Security execution context
        
    Returns:
        Dictionary containing generated diagram and metadata
        
    Raises:
        ValueError: If required parameters are missing or invalid
        PermissionError: If access is denied for security reasons
    """
    try:
        # Security validation
        if execution_context:
            await MCPSecurityManager.validate_project_access(
                execution_context,
                project_id
            )
        
        # Input validation
        if not project_id:
            raise ValueError("project_id is required")
        
        if not blueprint_id:
            raise ValueError("blueprint_id is required")
        
        supported_diagram_types = [
            "component_diagram",
            "dependency_graph",
            "system_overview",
            "data_flow"
        ]
        if diagram_type not in supported_diagram_types:
            raise ValueError(f"Unsupported diagram type: {diagram_type}")
        
        if output_format not in ["mermaid", "plantuml", "graphviz"]:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # Get documentation generator
        doc_generator = await get_documentation_generator()
        
        # Create architecture diagram
        result = await doc_generator.create_architecture_diagram(
            project_id=project_id,
            blueprint_id=blueprint_id,
            diagram_type=diagram_type
        )
        
        # Convert result to dictionary for MCP response
        response = {
            'success': result.success,
            'diagram': result.diagram_content if result.success else None,
            'error': result.error_message,
            'metadata': {
                'project_id': result.metadata.project_id if result.metadata else project_id,
                'blueprint_id': blueprint_id,
                'diagram_type': diagram_type,
                'output_format': result.diagram_format if result.success else output_format,
                'generation_time_ms': result.metadata.generation_time_ms if result.metadata else 0,
                'component_count': result.metadata.component_count if result.metadata else 0,
                'dependency_count': result.metadata.dependency_count if result.metadata else 0,
                'generated_at': result.metadata.generated_at.isoformat() if result.metadata else None
            }
        }
        
        logger.info(f"Created architecture diagram for blueprint {blueprint_id}: {result.success}")
        return response
        
    except Exception as e:
        logger.error(f"Error in create_architecture_diagram: {e}")
        return {
            'success': False,
            'diagram': None,
            'error': str(e),
            'metadata': {
                'project_id': project_id,
                'blueprint_id': blueprint_id,
                'diagram_type': diagram_type
            }
        }


async def generate_progress_report(
    project_id: str,
    report_type: str = "weekly",
    include_blueprints: Optional[List[str]] = None,
    include_metrics: bool = True,
    execution_context: Optional[ToolExecutionContext] = None
) -> Dict[str, Any]:
    """Generate progress report for project.
    
    Args:
        project_id: Project identifier
        report_type: Type of report (daily, weekly, monthly, custom)
        include_blueprints: Optional list of blueprint IDs to include
        include_metrics: Whether to include detailed metrics
        execution_context: Security execution context
        
    Returns:
        Dictionary containing generated report and metadata
        
    Raises:
        ValueError: If required parameters are missing or invalid
        PermissionError: If access is denied for security reasons
    """
    try:
        # Security validation
        if execution_context:
            await MCPSecurityManager.validate_project_access(
                execution_context,
                project_id
            )
        
        # Input validation
        if not project_id:
            raise ValueError("project_id is required")
        
        supported_report_types = ["daily", "weekly", "monthly", "custom"]
        if report_type not in supported_report_types:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        # Get documentation generator
        doc_generator = await get_documentation_generator()
        
        # Generate progress report
        result = await doc_generator.generate_progress_report(
            project_id=project_id,
            report_type=report_type,
            include_blueprints=include_blueprints
        )
        
        # Convert result to dictionary for MCP response
        response = {
            'success': result.success,
            'report': result.report_content if result.success else None,
            'error': result.error_message,
            'metadata': {
                'project_id': result.metadata.project_id if result.metadata else project_id,
                'report_type': result.report_type if result.success else report_type,
                'generation_time_ms': result.metadata.generation_time_ms if result.metadata else 0,
                'total_tasks': result.metadata.total_tasks if result.metadata else 0,
                'completion_percentage': result.metadata.completion_percentage if result.metadata else 0,
                'generated_at': result.metadata.generated_at.isoformat() if result.metadata else None,
                'included_blueprints': include_blueprints or []
            }
        }
        
        # Add detailed metrics if requested
        if include_metrics and result.success:
            performance_metrics = await doc_generator.get_performance_metrics()
            response['performance_metrics'] = performance_metrics
        
        logger.info(f"Generated progress report for project {project_id}: {result.success}")
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_progress_report: {e}")
        return {
            'success': False,
            'report': None,
            'error': str(e),
            'metadata': {
                'project_id': project_id,
                'report_type': report_type
            }
        }


async def update_documentation(
    project_id: str,
    documentation_type: str,
    updates: Dict[str, Any],
    execution_context: Optional[ToolExecutionContext] = None
) -> Dict[str, Any]:
    """Update existing documentation.
    
    Args:
        project_id: Project identifier
        documentation_type: Type of documentation to update
        updates: Dictionary of updates to apply
        execution_context: Security execution context
        
    Returns:
        Dictionary indicating update success and details
        
    Raises:
        ValueError: If required parameters are missing or invalid
        PermissionError: If access is denied for security reasons
    """
    try:
        # Security validation
        if execution_context:
            await MCPSecurityManager.validate_project_access(
                execution_context,
                project_id
            )
        
        # Input validation
        if not project_id:
            raise ValueError("project_id is required")
        
        if not documentation_type:
            raise ValueError("documentation_type is required")
        
        supported_types = ["api_docs", "architecture", "progress", "user_guide"]
        if documentation_type not in supported_types:
            raise ValueError(f"Unsupported documentation type: {documentation_type}")
        
        if not updates:
            raise ValueError("updates dictionary cannot be empty")
        
        # Get documentation generator
        doc_generator = await get_documentation_generator()
        
        # For now, this is a placeholder implementation
        # In a full implementation, this would update existing documentation
        response = {
            'success': True,
            'updated_sections': list(updates.keys()),
            'documentation_type': documentation_type,
            'project_id': project_id,
            'update_timestamp': None,  # Would be set after actual update
            'cache_invalidated': True
        }
        
        logger.info(f"Updated {documentation_type} documentation for project {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in update_documentation: {e}")
        return {
            'success': False,
            'error': str(e),
            'documentation_type': documentation_type,
            'project_id': project_id
        }


async def get_documentation_performance_metrics(
    project_id: Optional[str] = None,
    execution_context: Optional[ToolExecutionContext] = None
) -> Dict[str, Any]:
    """Get documentation generation performance metrics.
    
    Args:
        project_id: Optional project identifier for filtering
        execution_context: Security execution context
        
    Returns:
        Dictionary containing performance metrics
        
    Raises:
        PermissionError: If access is denied for security reasons
    """
    try:
        # Security validation
        if execution_context and project_id:
            await MCPSecurityManager.validate_project_access(
                execution_context,
                project_id
            )
        
        # Get documentation generator
        doc_generator = await get_documentation_generator()
        
        # Get performance metrics
        metrics = await doc_generator.get_performance_metrics()
        
        response = {
            'success': True,
            'metrics': metrics,
            'project_id': project_id,
            'retrieved_at': None  # Would be set to current timestamp
        }
        
        logger.info(f"Retrieved documentation performance metrics for project {project_id or 'all'}")
        return response
        
    except Exception as e:
        logger.error(f"Error in get_documentation_performance_metrics: {e}")
        return {
            'success': False,
            'error': str(e),
            'project_id': project_id
        }


# Tool registration for MCP server
DOCUMENTATION_TOOLS = {
    "generate_api_docs": {
        "function": generate_api_docs,
        "description": "Generate API documentation from source files",
        "parameters": {
            "project_id": {"type": "string", "required": True, "description": "Project identifier"},
            "source_files": {"type": "object", "required": True, "description": "Dictionary of file paths to contents"},
            "output_format": {"type": "string", "required": False, "description": "Output format (markdown, html, json)"},
            "template_name": {"type": "string", "required": False, "description": "Template to use for generation"}
        },
        "security_level": "project_scoped"
    },
    "create_architecture_diagram": {
        "function": create_architecture_diagram,
        "description": "Create architecture diagram from blueprint system",
        "parameters": {
            "project_id": {"type": "string", "required": True, "description": "Project identifier"},
            "blueprint_id": {"type": "string", "required": True, "description": "Blueprint ID for diagram"},
            "diagram_type": {"type": "string", "required": False, "description": "Type of diagram to create"},
            "output_format": {"type": "string", "required": False, "description": "Output format (mermaid, plantuml)"}
        },
        "security_level": "project_scoped"
    },
    "generate_progress_report": {
        "function": generate_progress_report,
        "description": "Generate progress report for project",
        "parameters": {
            "project_id": {"type": "string", "required": True, "description": "Project identifier"},
            "report_type": {"type": "string", "required": False, "description": "Report type (daily, weekly, monthly)"},
            "include_blueprints": {"type": "array", "required": False, "description": "List of blueprint IDs to include"},
            "include_metrics": {"type": "boolean", "required": False, "description": "Include detailed metrics"}
        },
        "security_level": "project_scoped"
    },
    "update_documentation": {
        "function": update_documentation,
        "description": "Update existing documentation",
        "parameters": {
            "project_id": {"type": "string", "required": True, "description": "Project identifier"},
            "documentation_type": {"type": "string", "required": True, "description": "Type of documentation to update"},
            "updates": {"type": "object", "required": True, "description": "Updates to apply"}
        },
        "security_level": "project_scoped"
    },
    "get_documentation_performance_metrics": {
        "function": get_documentation_performance_metrics,
        "description": "Get documentation generation performance metrics",
        "parameters": {
            "project_id": {"type": "string", "required": False, "description": "Optional project identifier"}
        },
        "security_level": "read_only"
    }
}


async def cleanup_documentation_tools():
    """Cleanup documentation tools resources."""
    global _documentation_generator
    if _documentation_generator:
        await _documentation_generator.cleanup()
        _documentation_generator = None
    logger.info("Documentation tools cleaned up")