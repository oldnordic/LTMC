"""
Advanced Markdown Generation Service - Phase 3 Component 3.

This service implements enhanced markdown generation with:

1. Professional Template System: Industry-standard markdown templates for various documentation types
2. Dynamic Content Generation: Intelligent content assembly based on code analysis
3. Maintenance Tools: Automated documentation updates and consistency maintenance  
4. Version Control Integration: Git-aware documentation versioning and change tracking
5. Cross-Reference Management: Smart linking between documentation sections

Performance Requirements:
- Template rendering: <10ms per template
- Content generation: <15ms per document
- Version control operations: <20ms per operation
- Cross-reference resolution: <5ms per link

Integration Points:
- Phase 2 DocumentationGenerator: Enhanced template capabilities
- Phase 3 Component 1: Neo4j Blueprint integration for structure-aware documentation
- Phase 3 Component 2: Documentation synchronization for real-time updates
- Phase 1 Security: Project isolation and template validation
"""

import asyncio
import time
import json
import hashlib
import logging
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from jinja2 import Environment, FileSystemLoader, Template, TemplateError
import yaml
import markdown
from markdown.extensions import toc, tables, codehilite, fenced_code

# Import supporting components
from ltms.models.blueprint_schemas import (
    BlueprintNode,
    FunctionNode,
    ClassNode, 
    ModuleNode,
    BlueprintRelationship,
    CodeStructure,
    ConsistencyLevel
)

from ltms.services.documentation_generator import DocumentationGenerator
from ltms.services.documentation_sync_service import DocumentationSyncManager
from ltms.tools.blueprint_tools import CodeAnalyzer
from ltms.security.project_isolation import ProjectIsolationManager
from ltms.security.path_security import SecurePathValidator

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Types of documentation templates."""
    API_DOCUMENTATION = "api_docs"
    ARCHITECTURE_OVERVIEW = "architecture"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "dev_guide"
    README = "readme"
    CHANGELOG = "changelog"
    CONTRIBUTING = "contributing"
    CODE_REFERENCE = "code_reference"
    DEPLOYMENT_GUIDE = "deployment"
    TROUBLESHOOTING = "troubleshooting"


class ContentType(Enum):
    """Types of content within templates."""
    HEADER = "header"
    SECTION = "section"
    CODE_BLOCK = "code_block"
    TABLE = "table"
    LIST = "list"
    DIAGRAM = "diagram"
    CROSS_REFERENCE = "cross_reference"
    METADATA = "metadata"


class VersionControlOperation(Enum):
    """Version control operations for documentation."""
    COMMIT = "commit"
    TAG = "tag"
    BRANCH = "branch"
    MERGE = "merge"
    DIFF = "diff"
    LOG = "log"


@dataclass
class TemplateMetadata:
    """Metadata for documentation templates."""
    template_id: str
    template_type: TemplateType
    version: str
    author: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    output_format: str = "markdown"
    supported_languages: List[str] = field(default_factory=lambda: ["python"])


@dataclass
class DocumentationContext:
    """Context for documentation generation."""
    project_id: str
    file_path: str
    code_structure: CodeStructure
    template_type: TemplateType
    generation_timestamp: datetime = field(default_factory=datetime.now)
    variables: Dict[str, Any] = field(default_factory=dict)
    cross_references: List[Dict[str, str]] = field(default_factory=list)
    version_info: Dict[str, str] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Results of documentation generation."""
    success: bool
    content: str
    metadata: Dict[str, Any]
    generation_time_ms: float
    template_used: str
    cross_references_resolved: int = 0
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class AdvancedTemplateEngine:
    """Advanced Jinja2-based template engine with enhanced features."""
    
    def __init__(self, templates_directory: str = None):
        """
        Initialize advanced template engine.
        
        Args:
            templates_directory: Directory containing templates
        """
        self.templates_dir = Path(templates_directory) if templates_directory else self._create_default_templates_dir()
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self._register_custom_filters()
        
        # Template cache
        self._template_cache = {}
        self._template_metadata = {}
    
    def _create_default_templates_dir(self) -> Path:
        """Create default templates directory."""
        return Path(__file__).parent / "templates" / "markdown"
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters for documentation generation."""
        
        def format_function_signature(func_node: FunctionNode) -> str:
            """Format function signature for documentation."""
            if not isinstance(func_node, FunctionNode):
                return str(func_node)
            
            params = []
            for param in func_node.parameters or []:
                if isinstance(param, dict):
                    param_name = param.get("name", "")
                    param_type = param.get("type", "")
                    if param_type:
                        params.append(f"{param_name}: {param_type}")
                    else:
                        params.append(param_name)
                else:
                    params.append(str(param))
            
            signature = f"{'async ' if func_node.is_async else ''}{func_node.name}({', '.join(params)})"
            if func_node.return_type:
                signature += f" -> {func_node.return_type}"
            
            return signature
        
        def format_class_hierarchy(class_node: ClassNode) -> str:
            """Format class hierarchy for documentation."""
            if not isinstance(class_node, ClassNode):
                return str(class_node)
            
            if class_node.base_classes:
                return f"{class_node.name}({', '.join(class_node.base_classes)})"
            return class_node.name
        
        def format_code_block(code: str, language: str = "python") -> str:
            """Format code block for markdown."""
            return f"```{language}\n{code}\n```"
        
        def create_anchor_link(text: str) -> str:
            """Create anchor link from text."""
            return text.lower().replace(" ", "-").replace("_", "-")
        
        def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
            """Format timestamp for documentation."""
            return timestamp.strftime(format_str)
        
        # Register all filters with the environment
        self.env.filters['format_function_signature'] = format_function_signature
        self.env.filters['format_class_hierarchy'] = format_class_hierarchy
        self.env.filters['format_code_block'] = format_code_block
        self.env.filters['create_anchor_link'] = create_anchor_link
        self.env.filters['format_timestamp'] = format_timestamp
    
    async def render_template(
        self,
        template_name: str,
        context: DocumentationContext
    ) -> Dict[str, Any]:
        """
        Render template with provided context.
        
        Args:
            template_name: Name of template to render
            context: Documentation context with variables
            
        Returns:
            Dict with rendering results
        """
        start_time = time.perf_counter()
        
        try:
            # Load template
            template = self._get_template(template_name)
            if not template:
                raise TemplateError(f"Template not found: {template_name}")
            
            # Prepare rendering variables
            render_vars = {
                "project_id": context.project_id,
                "file_path": context.file_path,
                "code_structure": context.code_structure,
                "generation_timestamp": context.generation_timestamp,
                "version_info": context.version_info,
                **context.variables
            }
            
            # Render template
            rendered_content = await asyncio.to_thread(
                template.render,
                **render_vars
            )
            
            end_time = time.perf_counter()
            render_time_ms = (end_time - start_time) * 1000
            
            return {
                "success": True,
                "content": rendered_content,
                "render_time_ms": render_time_ms,
                "template_name": template_name,
                "variables_count": len(render_vars)
            }
            
        except Exception as e:
            end_time = time.perf_counter()
            render_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Template rendering failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "render_time_ms": render_time_ms
            }
    
    def _get_template(self, template_name: str) -> Optional[Template]:
        """Get template from cache or load from file."""
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        
        try:
            template = self.env.get_template(template_name)
            self._template_cache[template_name] = template
            return template
        except:
            return None
    
    async def create_template(
        self,
        template_name: str,
        content: str,
        metadata: TemplateMetadata
    ) -> Dict[str, Any]:
        """
        Create new template with metadata.
        
        Args:
            template_name: Name for the template
            content: Template content (Jinja2)
            metadata: Template metadata
            
        Returns:
            Dict with creation results
        """
        try:
            template_path = self.templates_dir / template_name
            
            # Write template content
            template_path.write_text(content)
            
            # Store metadata
            metadata_path = self.templates_dir / f"{template_name}.meta.yaml"
            metadata_dict = {
                "template_id": metadata.template_id,
                "template_type": metadata.template_type.value,
                "version": metadata.version,
                "author": metadata.author,
                "description": metadata.description,
                "created_at": metadata.created_at.isoformat(),
                "updated_at": metadata.updated_at.isoformat(),
                "tags": metadata.tags,
                "requirements": metadata.requirements,
                "output_format": metadata.output_format,
                "supported_languages": metadata.supported_languages
            }
            
            with open(metadata_path, 'w') as f:
                yaml.dump(metadata_dict, f, default_flow_style=False)
            
            # Clear cache to reload
            self._template_cache.pop(template_name, None)
            
            return {
                "success": True,
                "template_name": template_name,
                "template_path": str(template_path),
                "metadata_path": str(metadata_path)
            }
            
        except Exception as e:
            logger.error(f"Template creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class DocumentationMaintainer:
    """Automated documentation maintenance and update system."""
    
    def __init__(self, project_root: str = None):
        """
        Initialize documentation maintainer.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.docs_directory = self.project_root / "docs"
        self.docs_directory.mkdir(parents=True, exist_ok=True)
        
        self._maintenance_history = {}
        self._update_queue = asyncio.Queue()
    
    async def update_documentation_index(self, project_id: str) -> Dict[str, Any]:
        """
        Update documentation index with cross-references.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dict with index update results
        """
        start_time = time.perf_counter()
        
        try:
            # Scan documentation directory
            doc_files = list(self.docs_directory.rglob("*.md"))
            
            # Build index structure
            index_data = {
                "project_id": project_id,
                "generated_at": datetime.now().isoformat(),
                "documentation_files": [],
                "cross_references": [],
                "categories": {}
            }
            
            # Process each documentation file
            for doc_file in doc_files:
                file_info = await self._analyze_documentation_file(doc_file)
                index_data["documentation_files"].append(file_info)
                
                # Extract cross-references
                cross_refs = self._extract_cross_references(file_info["content"])
                index_data["cross_references"].extend(cross_refs)
            
            # Generate index file
            index_path = self.docs_directory / "README.md"
            index_content = self._generate_index_content(index_data)
            
            index_path.write_text(index_content)
            
            end_time = time.perf_counter()
            update_time_ms = (end_time - start_time) * 1000
            
            return {
                "success": True,
                "project_id": project_id,
                "files_indexed": len(doc_files),
                "cross_references_found": len(index_data["cross_references"]),
                "index_path": str(index_path),
                "update_time_ms": update_time_ms
            }
            
        except Exception as e:
            end_time = time.perf_counter()
            update_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Documentation index update failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "update_time_ms": update_time_ms
            }
    
    async def validate_documentation_links(self, project_id: str) -> Dict[str, Any]:
        """
        Validate all documentation links and cross-references.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dict with link validation results
        """
        try:
            doc_files = list(self.docs_directory.rglob("*.md"))
            broken_links = []
            valid_links = []
            
            for doc_file in doc_files:
                content = doc_file.read_text()
                links = self._extract_markdown_links(content)
                
                for link in links:
                    if self._validate_link(link, doc_file):
                        valid_links.append({
                            "file": str(doc_file.relative_to(self.docs_directory)),
                            "link": link,
                            "type": "valid"
                        })
                    else:
                        broken_links.append({
                            "file": str(doc_file.relative_to(self.docs_directory)),
                            "link": link,
                            "type": "broken"
                        })
            
            return {
                "success": True,
                "project_id": project_id,
                "total_links_checked": len(valid_links) + len(broken_links),
                "valid_links": len(valid_links),
                "broken_links": len(broken_links),
                "broken_link_details": broken_links[:10]  # Limit output
            }
            
        except Exception as e:
            logger.error(f"Link validation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_documentation_file(self, doc_file: Path) -> Dict[str, Any]:
        """Analyze a documentation file for metadata."""
        try:
            content = doc_file.read_text()
            
            # Extract basic info
            file_info = {
                "path": str(doc_file.relative_to(self.docs_directory)),
                "size_bytes": len(content),
                "line_count": len(content.splitlines()),
                "content": content[:1000]  # First 1000 chars for analysis
            }
            
            # Extract headers
            headers = []
            for line in content.splitlines():
                if line.strip().startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    header_text = line.strip('#').strip()
                    headers.append({"level": level, "text": header_text})
            
            file_info["headers"] = headers
            return file_info
            
        except Exception as e:
            logger.error(f"File analysis failed for {doc_file}: {e}")
            return {"path": str(doc_file), "error": str(e)}
    
    def _extract_cross_references(self, content: str) -> List[Dict[str, str]]:
        """Extract cross-references from content."""
        # Simplified cross-reference extraction
        # Would use regex patterns to find [text](links) and [[internal links]]
        cross_refs = []
        
        import re
        
        # Markdown links [text](url)
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for text, url in markdown_links:
            cross_refs.append({
                "type": "markdown_link",
                "text": text,
                "target": url
            })
        
        # Internal links [[page]]
        internal_links = re.findall(r'\[\[([^\]]+)\]\]', content)
        for link in internal_links:
            cross_refs.append({
                "type": "internal_link", 
                "text": link,
                "target": link
            })
        
        return cross_refs
    
    def _extract_markdown_links(self, content: str) -> List[str]:
        """Extract markdown links from content."""
        import re
        links = re.findall(r'\]\(([^)]+)\)', content)
        return links
    
    def _validate_link(self, link: str, source_file: Path) -> bool:
        """Validate a single link."""
        try:
            # Handle relative links
            if link.startswith(('http://', 'https://')):
                return True  # Skip external link validation for now
            
            # Handle relative file links
            if link.startswith('./') or link.startswith('../') or not link.startswith('/'):
                target_path = source_file.parent / link
                return target_path.exists()
            
            # Handle absolute links within docs
            target_path = self.docs_directory / link.lstrip('/')
            return target_path.exists()
            
        except Exception:
            return False
    
    def _generate_index_content(self, index_data: Dict[str, Any]) -> str:
        """Generate content for documentation index."""
        content = f"""# Documentation Index

Project ID: {index_data['project_id']}
Generated: {index_data['generated_at']}

## Documentation Files

"""
        
        for file_info in index_data['documentation_files']:
            content += f"- [{file_info['path']}]({file_info['path']})\n"
            
            # Add headers if available
            if 'headers' in file_info:
                for header in file_info['headers'][:3]:  # Show first 3 headers
                    indent = "  " * (header['level'] - 1)
                    content += f"{indent}- {header['text']}\n"
        
        content += f"""
## Statistics

- Total files: {len(index_data['documentation_files'])}
- Cross-references: {len(index_data['cross_references'])}

---
*Auto-generated by LTMC Advanced Markdown Generator*
"""
        
        return content


class VersionControlIntegration:
    """Git integration for documentation versioning and change tracking."""
    
    def __init__(self, repository_path: str = None):
        """
        Initialize version control integration.
        
        Args:
            repository_path: Path to Git repository
        """
        self.repo_path = Path(repository_path) if repository_path else Path.cwd()
        self._git_available = self._check_git_availability()
    
    def _check_git_availability(self) -> bool:
        """Check if git is available and repository exists."""
        try:
            result = subprocess.run(
                ["git", "status"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    async def commit_documentation_changes(
        self,
        file_paths: List[str],
        commit_message: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Commit documentation changes to Git.
        
        Args:
            file_paths: List of file paths to commit
            commit_message: Commit message
            project_id: Project identifier
            
        Returns:
            Dict with commit results
        """
        start_time = time.perf_counter()
        
        try:
            if not self._git_available:
                return {
                    "success": False,
                    "error": "Git not available or not in a repository"
                }
            
            # Stage files
            for file_path in file_paths:
                await asyncio.to_thread(
                    self._run_git_command,
                    ["add", file_path]
                )
            
            # Create commit
            full_message = f"{commit_message}\n\nProject: {project_id}\nGenerated by: LTMC Advanced Markdown Generator"
            
            result = await asyncio.to_thread(
                self._run_git_command,
                ["commit", "-m", full_message]
            )
            
            end_time = time.perf_counter()
            commit_time_ms = (end_time - start_time) * 1000
            
            if result["success"]:
                return {
                    "success": True,
                    "project_id": project_id,
                    "files_committed": file_paths,
                    "commit_message": commit_message,
                    "commit_time_ms": commit_time_ms,
                    "git_output": result["output"]
                }
            else:
                return {
                    "success": False,
                    "error": result["error"],
                    "commit_time_ms": commit_time_ms
                }
            
        except Exception as e:
            end_time = time.perf_counter()
            commit_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Git commit failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "commit_time_ms": commit_time_ms
            }
    
    async def create_documentation_tag(
        self,
        tag_name: str,
        project_id: str,
        message: str = None
    ) -> Dict[str, Any]:
        """
        Create Git tag for documentation version.
        
        Args:
            tag_name: Name for the tag
            project_id: Project identifier  
            message: Optional tag message
            
        Returns:
            Dict with tag creation results
        """
        try:
            if not self._git_available:
                return {
                    "success": False,
                    "error": "Git not available"
                }
            
            tag_message = message or f"Documentation version {tag_name} for project {project_id}"
            
            result = await asyncio.to_thread(
                self._run_git_command,
                ["tag", "-a", tag_name, "-m", tag_message]
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "tag_name": tag_name,
                    "project_id": project_id,
                    "message": tag_message
                }
            else:
                return {
                    "success": False,
                    "error": result["error"]
                }
                
        except Exception as e:
            logger.error(f"Git tag creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_documentation_changelog(
        self,
        project_id: str,
        since_date: str = None
    ) -> Dict[str, Any]:
        """
        Generate changelog for documentation changes.
        
        Args:
            project_id: Project identifier
            since_date: Optional date filter (YYYY-MM-DD)
            
        Returns:
            Dict with changelog data
        """
        try:
            if not self._git_available:
                return {
                    "success": False,
                    "error": "Git not available"
                }
            
            # Build git log command
            cmd = ["log", "--oneline", "--grep=Advanced Markdown Generator"]
            if since_date:
                cmd.extend([f"--since={since_date}"])
            
            result = await asyncio.to_thread(
                self._run_git_command,
                cmd
            )
            
            if result["success"]:
                commits = []
                for line in result["output"].splitlines():
                    if line.strip():
                        commits.append({
                            "hash": line.split()[0],
                            "message": " ".join(line.split()[1:])
                        })
                
                return {
                    "success": True,
                    "project_id": project_id,
                    "commits": commits,
                    "total_commits": len(commits)
                }
            else:
                return {
                    "success": False,
                    "error": result["error"]
                }
                
        except Exception as e:
            logger.error(f"Changelog generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """Run git command and return results."""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }


class AdvancedMarkdownGenerator:
    """Main service for advanced markdown generation and maintenance."""
    
    def __init__(
        self,
        templates_directory: str = None,
        project_root: str = None
    ):
        """
        Initialize advanced markdown generator.
        
        Args:
            templates_directory: Directory containing templates
            project_root: Root directory of the project
        """
        self.template_engine = AdvancedTemplateEngine(templates_directory)
        self.maintainer = DocumentationMaintainer(project_root)
        self.version_control = VersionControlIntegration(project_root)
        
        # Initialize default templates
        asyncio.create_task(self._initialize_default_templates())
    
    async def generate_documentation(
        self,
        context: DocumentationContext,
        template_type: TemplateType = None
    ) -> GenerationResult:
        """
        Generate documentation using advanced templates.
        
        Args:
            context: Documentation context
            template_type: Type of template to use
            
        Returns:
            GenerationResult with generated content
        """
        start_time = time.perf_counter()
        
        try:
            # Determine template
            template_type = template_type or context.template_type
            template_name = self._get_template_name(template_type)
            
            # Render template
            render_result = await self.template_engine.render_template(
                template_name,
                context
            )
            
            if not render_result["success"]:
                raise Exception(f"Template rendering failed: {render_result.get('error')}")
            
            # Process cross-references
            content = render_result["content"]
            cross_refs_resolved = self._resolve_cross_references(content, context)
            content = cross_refs_resolved["content"]
            
            end_time = time.perf_counter()
            generation_time_ms = (end_time - start_time) * 1000
            
            return GenerationResult(
                success=True,
                content=content,
                metadata={
                    "template_used": template_name,
                    "project_id": context.project_id,
                    "generation_timestamp": context.generation_timestamp.isoformat(),
                    "file_path": context.file_path
                },
                generation_time_ms=generation_time_ms,
                template_used=template_name,
                cross_references_resolved=cross_refs_resolved["count"]
            )
            
        except Exception as e:
            end_time = time.perf_counter()
            generation_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Documentation generation failed: {e}")
            return GenerationResult(
                success=False,
                content="",
                metadata={},
                generation_time_ms=generation_time_ms,
                template_used="",
                error_message=str(e)
            )
    
    async def maintain_documentation(self, project_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive documentation maintenance.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dict with maintenance results
        """
        start_time = time.perf_counter()
        
        try:
            results = {
                "project_id": project_id,
                "maintenance_tasks": [],
                "warnings": []
            }
            
            # Update documentation index
            index_result = await self.maintainer.update_documentation_index(project_id)
            results["maintenance_tasks"].append({
                "task": "update_index",
                "success": index_result["success"],
                "details": index_result
            })
            
            # Validate links
            link_result = await self.maintainer.validate_documentation_links(project_id)
            results["maintenance_tasks"].append({
                "task": "validate_links",
                "success": link_result["success"], 
                "details": link_result
            })
            
            if link_result.get("broken_links", 0) > 0:
                results["warnings"].append(f"Found {link_result['broken_links']} broken links")
            
            end_time = time.perf_counter()
            maintenance_time_ms = (end_time - start_time) * 1000
            
            results["success"] = all(task["success"] for task in results["maintenance_tasks"])
            results["maintenance_time_ms"] = maintenance_time_ms
            
            return results
            
        except Exception as e:
            end_time = time.perf_counter()
            maintenance_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Documentation maintenance failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "maintenance_time_ms": maintenance_time_ms
            }
    
    async def version_control_commit(
        self,
        file_paths: List[str],
        project_id: str,
        commit_message: str = None
    ) -> Dict[str, Any]:
        """
        Commit documentation changes to version control.
        
        Args:
            file_paths: List of documentation files to commit
            project_id: Project identifier
            commit_message: Optional commit message
            
        Returns:
            Dict with version control results
        """
        try:
            message = commit_message or f"Update documentation for project {project_id}"
            
            commit_result = await self.version_control.commit_documentation_changes(
                file_paths,
                message,
                project_id
            )
            
            return commit_result
            
        except Exception as e:
            logger.error(f"Version control commit failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_template_name(self, template_type: TemplateType) -> str:
        """Get template file name for template type."""
        template_mapping = {
            TemplateType.API_DOCUMENTATION: "api_docs.md.j2",
            TemplateType.ARCHITECTURE_OVERVIEW: "architecture.md.j2",
            TemplateType.USER_GUIDE: "user_guide.md.j2",
            TemplateType.DEVELOPER_GUIDE: "dev_guide.md.j2",
            TemplateType.README: "readme.md.j2",
            TemplateType.CHANGELOG: "changelog.md.j2",
            TemplateType.CONTRIBUTING: "contributing.md.j2",
            TemplateType.CODE_REFERENCE: "code_reference.md.j2",
            TemplateType.DEPLOYMENT_GUIDE: "deployment.md.j2",
            TemplateType.TROUBLESHOOTING: "troubleshooting.md.j2"
        }
        
        return template_mapping.get(template_type, "default.md.j2")
    
    def _resolve_cross_references(self, content: str, context: DocumentationContext) -> Dict[str, Any]:
        """Resolve cross-references in generated content."""
        # Simplified cross-reference resolution
        # In production, would implement sophisticated link resolution
        
        resolved_count = 0
        
        # Replace template placeholders with actual values
        if "{{project_id}}" in content:
            content = content.replace("{{project_id}}", context.project_id)
            resolved_count += 1
        
        if "{{file_path}}" in content:
            content = content.replace("{{file_path}}", context.file_path)
            resolved_count += 1
        
        return {
            "content": content,
            "count": resolved_count
        }
    
    async def _initialize_default_templates(self):
        """Initialize default documentation templates."""
        try:
            # Create basic API documentation template
            api_template = """# API Documentation

## Project: {{ project_id }}

Generated: {{ generation_timestamp | format_timestamp }}
Source File: {{ file_path }}

## Functions

{% for node in code_structure.nodes %}
{% if node.node_type.value == 'function' %}
### {{ node.name }}

```python
{{ node | format_function_signature }}
```

{{ node.docstring or 'No documentation available.' }}

{% if node.parameters %}
**Parameters:**
{% for param in node.parameters %}
- `{{ param.name }}` ({{ param.type or 'Any' }}): {{ param.description or 'No description' }}
{% endfor %}
{% endif %}

{% if node.return_type %}
**Returns:** {{ node.return_type }}
{% endif %}

---
{% endif %}
{% endfor %}

## Classes

{% for node in code_structure.nodes %}
{% if node.node_type.value == 'class' %}
### {{ node | format_class_hierarchy }}

{{ node.docstring or 'No documentation available.' }}

{% if node.methods %}
**Methods:**
{% for method in node.methods %}
- `{{ method }}`
{% endfor %}
{% endif %}

---
{% endif %}
{% endfor %}
"""
            
            api_metadata = TemplateMetadata(
                template_id="default_api_docs",
                template_type=TemplateType.API_DOCUMENTATION,
                version="1.0.0",
                author="LTMC Advanced Markdown Generator",
                description="Standard API documentation template"
            )
            
            await self.template_engine.create_template(
                "api_docs.md.j2",
                api_template,
                api_metadata
            )
            
            # Create README template
            readme_template = """# {{ project_id | title }}

Generated: {{ generation_timestamp | format_timestamp }}

## Overview

This project contains Python code with the following structure:

## Code Structure

- **Functions:** {{ code_structure.nodes | selectattr('node_type.value', 'equalto', 'function') | list | length }}
- **Classes:** {{ code_structure.nodes | selectattr('node_type.value', 'equalto', 'class') | list | length }}
- **Modules:** {{ code_structure.nodes | selectattr('node_type.value', 'equalto', 'module') | list | length }}

## Quick Start

```python
# Example usage
from {{ file_path.split('/')[-1].replace('.py', '') }} import *
```

## Documentation

- [API Documentation](api_docs.md)
- [Architecture Overview](architecture.md)

---
*Generated by LTMC Advanced Markdown Generator*
"""
            
            readme_metadata = TemplateMetadata(
                template_id="default_readme",
                template_type=TemplateType.README,
                version="1.0.0", 
                author="LTMC Advanced Markdown Generator",
                description="Standard README template"
            )
            
            await self.template_engine.create_template(
                "readme.md.j2",
                readme_template,
                readme_metadata
            )
            
            logger.info("Default templates initialized successfully")
            
        except Exception as e:
            logger.error(f"Default template initialization failed: {e}")


# Global instance management
_advanced_generator: Optional[AdvancedMarkdownGenerator] = None


async def get_advanced_markdown_generator() -> AdvancedMarkdownGenerator:
    """Get or create advanced markdown generator instance."""
    global _advanced_generator
    if not _advanced_generator:
        _advanced_generator = AdvancedMarkdownGenerator()
    return _advanced_generator