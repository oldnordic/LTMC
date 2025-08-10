"""
Advanced Markdown Tools - MCP Tools for Phase 3 Component 3.

This module provides MCP tools for enhanced markdown generation with:

1. Professional Template Management: Create, update, and manage documentation templates
2. Advanced Content Generation: Generate documentation with intelligent templates
3. Documentation Maintenance: Automated maintenance and consistency checks
4. Version Control Operations: Git integration for documentation versioning
5. Cross-Reference Management: Smart linking and reference resolution

Performance Requirements:
- Template operations: <10ms per operation
- Content generation: <15ms per document
- Maintenance operations: <20ms per operation
- Version control operations: <25ms per operation

Integration Points:
- Advanced Markdown Generator Service
- Version Control Integration
- Documentation Maintainer
- Template Engine
- Security Integration: Project isolation and validation
"""

import asyncio
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ltms.services.advanced_markdown_generator import (
    AdvancedMarkdownGenerator,
    DocumentationContext,
    TemplateType,
    TemplateMetadata,
    get_advanced_markdown_generator
)
from ltms.models.blueprint_schemas import CodeStructure
from ltms.tools.blueprint_tools import CodeAnalyzer
from ltms.security.project_isolation import ProjectIsolationManager
from ltms.security.path_security import SecurePathValidator

logger = logging.getLogger(__name__)


class AdvancedMarkdownToolsError(Exception):
    """Base exception for advanced markdown tools."""
    pass


async def generate_advanced_documentation(
    file_path: str,
    project_id: str,
    template_type: str = "api_docs",
    output_path: str = None,
    variables: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate advanced documentation using intelligent templates.
    
    Args:
        file_path: Path to Python file to document
        project_id: Project identifier for security isolation
        template_type: Type of template to use (api_docs, readme, user_guide, etc.)
        output_path: Optional output path for generated documentation
        variables: Optional template variables
        
    Returns:
        Dict with generation results and metadata
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not file_path or not project_id:
            raise AdvancedMarkdownToolsError("file_path and project_id are required")
        
        # Security validation
        isolation_manager = ProjectIsolationManager("/home/feanor/Projects/lmtc")
        path_validator = SecurePathValidator("/home/feanor/Projects/lmtc")
        
        if not isolation_manager.validate_project_access(project_id, "read", file_path):
            raise AdvancedMarkdownToolsError(f"Project access denied: {project_id}")
        
        if not path_validator.validate_path(file_path, project_id):
            raise AdvancedMarkdownToolsError(f"Invalid file path: {file_path}")
        
        # Validate file exists
        if not Path(file_path).exists():
            raise AdvancedMarkdownToolsError(f"File not found: {file_path}")
        
        # Convert template type string to enum
        try:
            template_enum = TemplateType[template_type.upper().replace('-', '_')]
        except KeyError:
            template_enum = TemplateType.API_DOCUMENTATION
        
        # Analyze code structure
        code_analyzer = CodeAnalyzer()
        code_structure = code_analyzer.analyze_file(file_path, project_id)
        
        # Create documentation context
        context = DocumentationContext(
            project_id=project_id,
            file_path=file_path,
            code_structure=code_structure,
            template_type=template_enum,
            variables=variables or {},
            version_info={
                "generator_version": "1.0.0",
                "generation_method": "advanced_template"
            }
        )
        
        # Get advanced generator
        generator = await get_advanced_markdown_generator()
        
        # Generate documentation
        result = await generator.generate_documentation(context, template_enum)
        
        # Save to output path if specified
        output_file_path = None
        if output_path:
            output_file_path = Path(output_path)
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            output_file_path.write_text(result.content)
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": result.success,
            "content": result.content,
            "metadata": {
                **result.metadata,
                "template_type": template_type,
                "code_nodes_analyzed": len(code_structure.nodes),
                "code_relationships_analyzed": len(code_structure.relationships),
                "output_file_path": str(output_file_path) if output_file_path else None,
                "total_time_ms": total_time_ms,
                "generation_time_ms": result.generation_time_ms,
                "cross_references_resolved": result.cross_references_resolved
            },
            "warnings": result.warnings,
            "error_message": result.error_message
        }
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Advanced documentation generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


async def create_documentation_template(
    template_name: str,
    template_content: str,
    template_type: str,
    project_id: str,
    author: str = "LTMC System",
    description: str = None,
    version: str = "1.0.0",
    tags: List[str] = None
) -> Dict[str, Any]:
    """
    Create custom documentation template.
    
    Args:
        template_name: Name for the template file
        template_content: Jinja2 template content
        template_type: Type of template (api_docs, readme, etc.)
        project_id: Project identifier for security isolation
        author: Template author
        description: Template description
        version: Template version
        tags: Optional template tags
        
    Returns:
        Dict with template creation results
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not all([template_name, template_content, template_type, project_id]):
            raise AdvancedMarkdownToolsError("template_name, template_content, template_type, and project_id are required")
        
        # Security validation
        isolation_manager = ProjectIsolationManager()
        if not isolation_manager.validate_project_access(project_id, "write", template_name):
            raise AdvancedMarkdownToolsError(f"Project access denied: {project_id}")
        
        # Convert template type
        try:
            template_enum = TemplateType[template_type.upper().replace('-', '_')]
        except KeyError:
            raise AdvancedMarkdownToolsError(f"Invalid template type: {template_type}")
        
        # Create template metadata
        metadata = TemplateMetadata(
            template_id=f"{project_id}_{template_name}",
            template_type=template_enum,
            version=version,
            author=author,
            description=description or f"Custom {template_type} template",
            tags=tags or []
        )
        
        # Get generator and create template
        generator = await get_advanced_markdown_generator()
        
        creation_result = await generator.template_engine.create_template(
            template_name,
            template_content,
            metadata
        )
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        if creation_result["success"]:
            return {
                "success": True,
                "template_name": template_name,
                "template_type": template_type,
                "project_id": project_id,
                "template_path": creation_result["template_path"],
                "metadata_path": creation_result["metadata_path"],
                "creation_time_ms": total_time_ms
            }
        else:
            return {
                "success": False,
                "error": creation_result["error"],
                "creation_time_ms": total_time_ms
            }
    
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Template creation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "creation_time_ms": total_time_ms
        }


async def maintain_documentation_integrity(
    project_id: str,
    fix_broken_links: bool = False,
    update_index: bool = True,
    validate_cross_references: bool = True
) -> Dict[str, Any]:
    """
    Perform comprehensive documentation maintenance.
    
    Args:
        project_id: Project identifier for security isolation
        fix_broken_links: Whether to attempt fixing broken links
        update_index: Whether to update documentation index
        validate_cross_references: Whether to validate cross-references
        
    Returns:
        Dict with maintenance results and statistics
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not project_id:
            raise AdvancedMarkdownToolsError("project_id is required")
        
        # Security validation
        isolation_manager = ProjectIsolationManager()
        if not isolation_manager.validate_project_access(project_id, "read", "docs"):
            raise AdvancedMarkdownToolsError(f"Project access denied: {project_id}")
        
        # Get generator and perform maintenance
        generator = await get_advanced_markdown_generator()
        
        maintenance_result = await generator.maintain_documentation(project_id)
        
        # Additional validation if requested
        additional_checks = {}
        
        if validate_cross_references:
            link_validation = await generator.maintainer.validate_documentation_links(project_id)
            additional_checks["link_validation"] = link_validation
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": maintenance_result["success"],
            "project_id": project_id,
            "maintenance_tasks": maintenance_result["maintenance_tasks"],
            "warnings": maintenance_result.get("warnings", []),
            "additional_checks": additional_checks,
            "total_time_ms": total_time_ms,
            "maintenance_time_ms": maintenance_result.get("maintenance_time_ms", 0)
        }
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Documentation maintenance failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


async def commit_documentation_changes(
    file_paths: List[str],
    project_id: str,
    commit_message: str = None,
    create_tag: bool = False,
    tag_name: str = None
) -> Dict[str, Any]:
    """
    Commit documentation changes to version control.
    
    Args:
        file_paths: List of documentation files to commit
        project_id: Project identifier for security isolation
        commit_message: Optional commit message
        create_tag: Whether to create a Git tag
        tag_name: Name for Git tag (if create_tag is True)
        
    Returns:
        Dict with version control operation results
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not file_paths or not project_id:
            raise AdvancedMarkdownToolsError("file_paths and project_id are required")
        
        # Security validation
        isolation_manager = ProjectIsolationManager("/home/feanor/Projects/lmtc")
        path_validator = SecurePathValidator("/home/feanor/Projects/lmtc")
        
        if not isolation_manager.validate_project_access(project_id, "write", "git"):
            raise AdvancedMarkdownToolsError(f"Project access denied: {project_id}")
        
        # Validate all file paths
        for file_path in file_paths:
            if not path_validator.validate_path(file_path, project_id):
                raise AdvancedMarkdownToolsError(f"Invalid file path: {file_path}")
        
        # Get generator
        generator = await get_advanced_markdown_generator()
        
        # Commit changes
        commit_result = await generator.version_control_commit(
            file_paths,
            project_id,
            commit_message
        )
        
        # Create tag if requested
        tag_result = None
        if create_tag and commit_result["success"]:
            tag_name = tag_name or f"docs-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            tag_result = await generator.version_control.create_documentation_tag(
                tag_name,
                project_id
            )
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        response = {
            "success": commit_result["success"],
            "project_id": project_id,
            "files_committed": file_paths,
            "commit_result": commit_result,
            "total_time_ms": total_time_ms
        }
        
        if tag_result:
            response["tag_result"] = tag_result
        
        return response
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Documentation commit failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


async def generate_documentation_changelog(
    project_id: str,
    since_date: str = None,
    output_format: str = "markdown",
    include_stats: bool = True
) -> Dict[str, Any]:
    """
    Generate changelog for documentation changes.
    
    Args:
        project_id: Project identifier for security isolation
        since_date: Optional date filter (YYYY-MM-DD)
        output_format: Output format (markdown, json, yaml)
        include_stats: Whether to include statistics
        
    Returns:
        Dict with generated changelog content
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not project_id:
            raise AdvancedMarkdownToolsError("project_id is required")
        
        # Security validation
        isolation_manager = ProjectIsolationManager()
        if not isolation_manager.validate_project_access(project_id, "write", "git"):
            raise AdvancedMarkdownToolsError(f"Project access denied: {project_id}")
        
        # Get generator
        generator = await get_advanced_markdown_generator()
        
        # Generate changelog
        changelog_result = await generator.version_control.get_documentation_changelog(
            project_id,
            since_date
        )
        
        # Format output based on requested format
        if changelog_result["success"]:
            changelog_content = ""
            
            if output_format.lower() == "markdown":
                changelog_content = f"# Documentation Changelog\n\nProject: {project_id}\n"
                if since_date:
                    changelog_content += f"Since: {since_date}\n"
                changelog_content += f"Generated: {datetime.now().isoformat()}\n\n"
                
                for commit in changelog_result["commits"]:
                    changelog_content += f"- `{commit['hash']}` {commit['message']}\n"
                
                if include_stats:
                    changelog_content += f"\n## Statistics\n\nTotal commits: {changelog_result['total_commits']}\n"
            
            elif output_format.lower() == "json":
                changelog_content = json.dumps(changelog_result, indent=2)
            
            elif output_format.lower() == "yaml":
                import yaml
                changelog_content = yaml.dump(changelog_result, default_flow_style=False)
            
            else:
                changelog_content = str(changelog_result)
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": changelog_result["success"],
            "project_id": project_id,
            "changelog_content": changelog_content,
            "commits": changelog_result.get("commits", []),
            "total_commits": changelog_result.get("total_commits", 0),
            "output_format": output_format,
            "total_time_ms": total_time_ms,
            "error": changelog_result.get("error")
        }
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Changelog generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


async def validate_template_syntax(
    template_content: str,
    template_variables: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Validate Jinja2 template syntax and test rendering.
    
    Args:
        template_content: Jinja2 template content to validate
        template_variables: Optional variables for test rendering
        
    Returns:
        Dict with validation results and any syntax errors
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not template_content:
            raise AdvancedMarkdownToolsError("template_content is required")
        
        from jinja2 import Environment, Template, TemplateError
        
        env = Environment()
        
        # Try to parse template
        try:
            template = env.from_string(template_content)
            syntax_valid = True
            syntax_errors = []
        except TemplateError as e:
            syntax_valid = False
            syntax_errors = [str(e)]
            template = None
        
        # Try test rendering if template is valid and variables provided
        render_valid = False
        render_errors = []
        rendered_content = None
        
        if syntax_valid and template and template_variables:
            try:
                rendered_content = template.render(**template_variables)
                render_valid = True
            except Exception as e:
                render_errors.append(str(e))
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": syntax_valid,
            "syntax_valid": syntax_valid,
            "syntax_errors": syntax_errors,
            "render_valid": render_valid,
            "render_errors": render_errors,
            "rendered_content": rendered_content,
            "validation_time_ms": total_time_ms
        }
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Template validation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "validation_time_ms": total_time_ms
        }


# MCP Tool Registration Functions

def get_advanced_markdown_tools() -> List[Dict[str, Any]]:
    """Get list of all advanced markdown MCP tools."""
    return [
        {
            "name": "generate_advanced_documentation",
            "description": "Generate advanced documentation using intelligent templates",
            "parameters": {
                "file_path": {"type": "string", "description": "Path to Python file to document"},
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "template_type": {"type": "string", "description": "Type of template (api_docs, readme, user_guide, etc.)", "default": "api_docs"},
                "output_path": {"type": "string", "description": "Optional output path for generated documentation"},
                "variables": {"type": "object", "description": "Optional template variables"}
            }
        },
        {
            "name": "create_documentation_template", 
            "description": "Create custom documentation template",
            "parameters": {
                "template_name": {"type": "string", "description": "Name for the template file"},
                "template_content": {"type": "string", "description": "Jinja2 template content"},
                "template_type": {"type": "string", "description": "Type of template (api_docs, readme, etc.)"},
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "author": {"type": "string", "description": "Template author", "default": "LTMC System"},
                "description": {"type": "string", "description": "Template description"},
                "version": {"type": "string", "description": "Template version", "default": "1.0.0"},
                "tags": {"type": "array", "description": "Optional template tags"}
            }
        },
        {
            "name": "maintain_documentation_integrity",
            "description": "Perform comprehensive documentation maintenance",
            "parameters": {
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "fix_broken_links": {"type": "boolean", "description": "Whether to attempt fixing broken links", "default": False},
                "update_index": {"type": "boolean", "description": "Whether to update documentation index", "default": True},
                "validate_cross_references": {"type": "boolean", "description": "Whether to validate cross-references", "default": True}
            }
        },
        {
            "name": "commit_documentation_changes",
            "description": "Commit documentation changes to version control",
            "parameters": {
                "file_paths": {"type": "array", "description": "List of documentation files to commit"},
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "commit_message": {"type": "string", "description": "Optional commit message"},
                "create_tag": {"type": "boolean", "description": "Whether to create a Git tag", "default": False},
                "tag_name": {"type": "string", "description": "Name for Git tag (if create_tag is True)"}
            }
        },
        {
            "name": "generate_documentation_changelog",
            "description": "Generate changelog for documentation changes", 
            "parameters": {
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "since_date": {"type": "string", "description": "Optional date filter (YYYY-MM-DD)"},
                "output_format": {"type": "string", "description": "Output format (markdown, json, yaml)", "default": "markdown"},
                "include_stats": {"type": "boolean", "description": "Whether to include statistics", "default": True}
            }
        },
        {
            "name": "validate_template_syntax",
            "description": "Validate Jinja2 template syntax and test rendering",
            "parameters": {
                "template_content": {"type": "string", "description": "Jinja2 template content to validate"},
                "template_variables": {"type": "object", "description": "Optional variables for test rendering"}
            }
        }
    ]


# Export functions for MCP integration
__all__ = [
    "generate_advanced_documentation",
    "create_documentation_template", 
    "maintain_documentation_integrity",
    "commit_documentation_changes",
    "generate_documentation_changelog",
    "validate_template_syntax",
    "get_advanced_markdown_tools"
]