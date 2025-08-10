"""Documentation Generator Service - Component 4 (Blueprint Generation) - Phase 2.

This service provides intelligent documentation generation capabilities including:
- API documentation from code analysis
- Architecture diagram creation
- Progress report generation
- Integration with Neo4j blueprint system
"""

import asyncio
import logging
import ast
import json
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from ltms.services.redis_service import RedisConnectionManager
from ltms.database.neo4j_store import Neo4jGraphStore
from ltms.models.task_blueprint import TaskBlueprint
# Import will be handled inline to avoid circular dependencies

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of documents that can be generated."""
    API_DOCUMENTATION = "api_documentation"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    PROGRESS_REPORT = "progress_report"
    USER_GUIDE = "user_guide"


@dataclass
class DocumentationMetadata:
    """Metadata for generated documentation."""
    project_id: str
    document_type: DocumentType
    generated_at: datetime
    generation_time_ms: float
    template_used: Optional[str] = None
    total_endpoints: int = 0
    total_models: int = 0
    component_count: int = 0
    dependency_count: int = 0
    total_tasks: int = 0
    completion_percentage: float = 0.0
    source_files_count: int = 0
    lines_of_code: int = 0
    diagram_type: Optional[str] = None


@dataclass
class APIDocumentationResult:
    """Result of API documentation generation."""
    success: bool
    documentation_content: str = ""
    metadata: DocumentationMetadata = None
    error_message: Optional[str] = None
    cache_key: Optional[str] = None


@dataclass
class ArchitectureDiagramResult:
    """Result of architecture diagram creation."""
    success: bool
    diagram_content: str = ""
    metadata: DocumentationMetadata = None
    error_message: Optional[str] = None
    diagram_format: str = "mermaid"


@dataclass
class ProgressReportResult:
    """Result of progress report generation."""
    success: bool
    report_content: str = ""
    metadata: DocumentationMetadata = None
    error_message: Optional[str] = None
    report_type: str = "weekly"


class CodeAnalyzer:
    """Analyzes Python source code for documentation generation."""
    
    @staticmethod
    def analyze_python_file(content: str, filename: str) -> Dict[str, Any]:
        """Analyze a Python file and extract documentation information."""
        try:
            tree = ast.parse(content)
            
            endpoints = []
            models = []
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'docstring': ast.get_docstring(node),
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list],
                        'line_number': node.lineno
                    }
                    
                    # Check if it's an API endpoint
                    if any(dec in str(func_info['decorators']) for dec in ['router.get', 'router.post', 'router.put', 'router.delete']):
                        endpoints.append(func_info)
                    else:
                        functions.append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'docstring': ast.get_docstring(node),
                        'bases': [base.id if hasattr(base, 'id') else str(base) for base in node.bases],
                        'line_number': node.lineno,
                        'methods': []
                    }
                    
                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info['methods'].append({
                                'name': item.name,
                                'docstring': ast.get_docstring(item),
                                'args': [arg.arg for arg in item.args.args if arg.arg != 'self']
                            })
                    
                    # Check if it's a data model
                    if any(base in ['BaseModel', 'Model'] for base in class_info['bases']):
                        models.append(class_info)
                    else:
                        classes.append(class_info)
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            imports.append(f"{node.module}.{alias.name}")
            
            return {
                'filename': filename,
                'endpoints': endpoints,
                'models': models,
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'lines_of_code': len(content.splitlines())
            }
            
        except SyntaxError as e:
            logger.warning(f"Syntax error analyzing {filename}: {e}")
            return {
                'filename': filename,
                'error': f"Syntax error: {e}",
                'lines_of_code': len(content.splitlines()) if content else 0
            }
        except Exception as e:
            logger.error(f"Error analyzing {filename}: {e}")
            return {
                'filename': filename,
                'error': str(e),
                'lines_of_code': len(content.splitlines()) if content else 0
            }


class DocumentationGenerator:
    """Main documentation generation service."""
    
    def __init__(
        self,
        redis_manager: RedisConnectionManager,
        neo4j_store: Neo4jGraphStore,
        cache_ttl: int = 3600  # 1 hour cache
    ):
        """Initialize documentation generator.
        
        Args:
            redis_manager: Redis connection manager
            neo4j_store: Neo4j graph database store
            cache_ttl: Cache time-to-live in seconds
        """
        self.redis_manager = redis_manager
        self.neo4j_store = neo4j_store
        self.cache_ttl = cache_ttl
        self.initialized = False
        
        # Performance metrics
        self._performance_metrics = {
            DocumentType.API_DOCUMENTATION.value: {
                'total_generations': 0,
                'total_time_ms': 0.0,
                'avg_generation_time_ms': 0.0
            },
            DocumentType.ARCHITECTURE_DIAGRAM.value: {
                'total_generations': 0,
                'total_time_ms': 0.0,
                'avg_generation_time_ms': 0.0
            },
            DocumentType.PROGRESS_REPORT.value: {
                'total_generations': 0,
                'total_time_ms': 0.0,
                'avg_generation_time_ms': 0.0
            }
        }
        
        # Code analyzer
        self.code_analyzer = CodeAnalyzer()
        
        # Template cache
        self._template_cache: Dict[str, str] = {}
    
    async def initialize(self) -> bool:
        """Initialize the documentation generator.
        
        Returns:
            True if initialized successfully
        """
        try:
            if self.initialized:
                return True
            
            # Verify Redis connection
            if not await self.redis_manager.ping():
                logger.error("Redis connection failed during documentation generator initialization")
                return False
            
            # Load templates
            await self._load_templates()
            
            self.initialized = True
            logger.info("Documentation generator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize documentation generator: {e}")
            return False
    
    async def generate_api_documentation(
        self,
        project_id: str,
        source_files: Dict[str, str],
        output_format: str = "markdown",
        template_name: Optional[str] = None
    ) -> APIDocumentationResult:
        """Generate API documentation from source files.
        
        Args:
            project_id: Project identifier for isolation
            source_files: Dictionary of filename -> file content
            output_format: Output format (markdown, html, etc.)
            template_name: Optional template to use
            
        Returns:
            APIDocumentationResult with generated content
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Ensure project isolation (inline to avoid circular imports)
            if not project_id:
                raise ValueError("Project ID required for isolation")
            
            # Generate cache key
            cache_key = self._generate_cache_key(
                "api_docs",
                project_id,
                source_files,
                output_format,
                template_name
            )
            
            # Check cache first
            cached_result = await self._get_cached_result(cache_key, DocumentType.API_DOCUMENTATION)
            if cached_result:
                return cached_result
            
            # Analyze source files
            analysis_results = []
            total_endpoints = 0
            total_models = 0
            total_lines = 0
            
            for filename, content in source_files.items():
                if not content.strip():
                    continue
                    
                analysis = self.code_analyzer.analyze_python_file(content, filename)
                
                # Check for parsing errors
                if 'error' in analysis:
                    return APIDocumentationResult(
                        success=False,
                        error_message=f"Error parsing {filename}: {analysis['error']}"
                    )
                
                analysis_results.append(analysis)
                total_endpoints += len(analysis.get('endpoints', []))
                total_models += len(analysis.get('models', []))
                total_lines += analysis.get('lines_of_code', 0)
            
            # Generate documentation content
            template = await self._get_template(template_name or "api_template")
            documentation_content = await self._generate_api_content(
                analysis_results,
                template,
                output_format
            )
            
            # Create metadata
            end_time = asyncio.get_event_loop().time()
            generation_time_ms = (end_time - start_time) * 1000
            
            metadata = DocumentationMetadata(
                project_id=project_id,
                document_type=DocumentType.API_DOCUMENTATION,
                generated_at=datetime.utcnow(),
                generation_time_ms=generation_time_ms,
                template_used=template_name or "api_template",
                total_endpoints=total_endpoints,
                total_models=total_models,
                source_files_count=len(source_files),
                lines_of_code=total_lines
            )
            
            result = APIDocumentationResult(
                success=True,
                documentation_content=documentation_content,
                metadata=metadata,
                cache_key=cache_key
            )
            
            # Cache result
            await self._cache_result(cache_key, result, DocumentType.API_DOCUMENTATION)
            
            # Update metrics
            await self._update_performance_metrics(DocumentType.API_DOCUMENTATION, generation_time_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating API documentation: {e}")
            return APIDocumentationResult(
                success=False,
                error_message=str(e)
            )
    
    async def create_architecture_diagram(
        self,
        project_id: str,
        blueprint_id: str,
        diagram_type: str = "component_diagram"
    ) -> ArchitectureDiagramResult:
        """Create architecture diagram from blueprint system.
        
        Args:
            project_id: Project identifier for isolation
            blueprint_id: Blueprint to create diagram for
            diagram_type: Type of diagram to create
            
        Returns:
            ArchitectureDiagramResult with diagram content
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Ensure project isolation (inline to avoid circular imports)
            if not project_id:
                raise ValueError("Project ID required for isolation")
            
            # Get blueprint from Neo4j
            blueprint_data = await self._get_blueprint_from_neo4j(blueprint_id)
            if not blueprint_data:
                return ArchitectureDiagramResult(
                    success=False,
                    error_message=f"Blueprint {blueprint_id} not found"
                )
            
            # Get related blueprints and dependencies
            related_data = await self._get_blueprint_relationships(blueprint_id)
            
            # Generate diagram content
            diagram_content = await self._generate_diagram_content(
                blueprint_data,
                related_data,
                diagram_type
            )
            
            # Create metadata
            end_time = asyncio.get_event_loop().time()
            generation_time_ms = (end_time - start_time) * 1000
            
            metadata = DocumentationMetadata(
                project_id=project_id,
                document_type=DocumentType.ARCHITECTURE_DIAGRAM,
                generated_at=datetime.utcnow(),
                generation_time_ms=generation_time_ms,
                component_count=len(related_data.get('components', [blueprint_data])),
                dependency_count=len(related_data.get('dependencies', [])),
                diagram_type=diagram_type
            )
            
            result = ArchitectureDiagramResult(
                success=True,
                diagram_content=diagram_content,
                metadata=metadata,
                diagram_format="mermaid"
            )
            
            # Update metrics
            await self._update_performance_metrics(DocumentType.ARCHITECTURE_DIAGRAM, generation_time_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating architecture diagram: {e}")
            return ArchitectureDiagramResult(
                success=False,
                error_message=str(e)
            )
    
    async def generate_progress_report(
        self,
        project_id: str,
        report_type: str = "weekly",
        include_blueprints: Optional[List[str]] = None
    ) -> ProgressReportResult:
        """Generate progress report for project.
        
        Args:
            project_id: Project identifier
            report_type: Type of report (daily, weekly, monthly)
            include_blueprints: Optional list of blueprint IDs to include
            
        Returns:
            ProgressReportResult with report content
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Ensure project isolation (inline to avoid circular imports)
            if not project_id:
                raise ValueError("Project ID required for isolation")
            
            # Get project blueprints and progress
            blueprints_data = await self._get_project_blueprints(project_id, include_blueprints)
            
            if not blueprints_data:
                return ProgressReportResult(
                    success=False,
                    error_message=f"No blueprints found for project {project_id}"
                )
            
            # Calculate progress metrics
            progress_metrics = await self._calculate_progress_metrics(blueprints_data)
            
            # Generate report content
            report_content = await self._generate_progress_content(
                blueprints_data,
                progress_metrics,
                report_type
            )
            
            # Create metadata
            end_time = asyncio.get_event_loop().time()
            generation_time_ms = (end_time - start_time) * 1000
            
            metadata = DocumentationMetadata(
                project_id=project_id,
                document_type=DocumentType.PROGRESS_REPORT,
                generated_at=datetime.utcnow(),
                generation_time_ms=generation_time_ms,
                total_tasks=len(blueprints_data),
                completion_percentage=progress_metrics['overall_completion']
            )
            
            result = ProgressReportResult(
                success=True,
                report_content=report_content,
                metadata=metadata,
                report_type=report_type
            )
            
            # Update metrics
            await self._update_performance_metrics(DocumentType.PROGRESS_REPORT, generation_time_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            return ProgressReportResult(
                success=False,
                error_message=str(e)
            )
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for documentation generation.
        
        Returns:
            Dictionary of performance metrics
        """
        return dict(self._performance_metrics)
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            self._template_cache.clear()
            self.initialized = False
            logger.info("Documentation generator cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Private helper methods
    
    async def _load_templates(self):
        """Load documentation templates."""
        try:
            # Default API template
            self._template_cache["api_template"] = """# API Documentation

Generated on: {generated_at}
Project: {project_id}

## Overview
This document provides comprehensive API documentation for the project.

## Endpoints

{endpoints_section}

## Models

{models_section}

## Additional Information
- Total Endpoints: {total_endpoints}
- Total Models: {total_models}
- Lines of Code: {lines_of_code}
"""
            
            # Architecture template
            self._template_cache["architecture_template"] = """# System Architecture

Project: {project_id}
Generated: {generated_at}

## Architecture Overview
{architecture_overview}

## Component Diagram
```mermaid
{diagram_content}
```

## Dependencies
{dependencies_section}
"""
            
            logger.debug("Templates loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
    
    async def _get_template(self, template_name: str) -> str:
        """Get template by name."""
        return self._template_cache.get(template_name, self._template_cache.get("api_template", ""))
    
    def _generate_cache_key(
        self,
        doc_type: str,
        project_id: str,
        source_files: Dict[str, str],
        output_format: str,
        template_name: Optional[str]
    ) -> str:
        """Generate cache key for documentation."""
        content_hash = hashlib.md5(
            json.dumps(source_files, sort_keys=True).encode()
        ).hexdigest()
        
        key_parts = [doc_type, project_id, content_hash, output_format]
        if template_name:
            key_parts.append(template_name)
        
        return f"doc_cache:{'_'.join(key_parts)}"
    
    async def _get_cached_result(
        self,
        cache_key: str,
        doc_type: DocumentType
    ) -> Optional[APIDocumentationResult]:
        """Get cached documentation result."""
        try:
            cached_data = await self.redis_manager.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                
                # Reconstruct result based on type
                if doc_type == DocumentType.API_DOCUMENTATION:
                    metadata = DocumentationMetadata(**data['metadata'])
                    return APIDocumentationResult(
                        success=data['success'],
                        documentation_content=data['content'],
                        metadata=metadata,
                        cache_key=cache_key
                    )
                # Add other types as needed
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting cached result: {e}")
            return None
    
    async def _cache_result(
        self,
        cache_key: str,
        result: Any,
        doc_type: DocumentType
    ):
        """Cache documentation result."""
        try:
            cache_data = {
                'success': result.success,
                'content': getattr(result, 'documentation_content', getattr(result, 'diagram_content', getattr(result, 'report_content', ''))),
                'metadata': result.metadata.__dict__ if result.metadata else {}
            }
            
            await self.redis_manager.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
        except Exception as e:
            logger.warning(f"Error caching result: {e}")
    
    async def _generate_api_content(
        self,
        analysis_results: List[Dict[str, Any]],
        template: str,
        output_format: str
    ) -> str:
        """Generate API documentation content."""
        try:
            # Build endpoints section
            endpoints_section = "### Endpoints\n\n"
            for analysis in analysis_results:
                for endpoint in analysis.get('endpoints', []):
                    endpoints_section += f"#### {endpoint['name']}\n"
                    if endpoint.get('docstring'):
                        endpoints_section += f"{endpoint['docstring']}\n\n"
                    endpoints_section += f"**Arguments:** {', '.join(endpoint.get('args', []))}\n\n"
            
            # Build models section
            models_section = "### Data Models\n\n"
            for analysis in analysis_results:
                for model in analysis.get('models', []):
                    models_section += f"#### {model['name']}\n"
                    if model.get('docstring'):
                        models_section += f"{model['docstring']}\n\n"
                    
                    # Add methods if any
                    if model.get('methods'):
                        models_section += "**Methods:**\n"
                        for method in model['methods']:
                            models_section += f"- {method['name']}({', '.join(method.get('args', []))})\n"
                        models_section += "\n"
            
            # Calculate totals
            total_endpoints = sum(len(a.get('endpoints', [])) for a in analysis_results)
            total_models = sum(len(a.get('models', [])) for a in analysis_results)
            total_lines = sum(a.get('lines_of_code', 0) for a in analysis_results)
            
            # Format template
            content = template.format(
                generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                project_id="Generated Documentation",
                endpoints_section=endpoints_section,
                models_section=models_section,
                total_endpoints=total_endpoints,
                total_models=total_models,
                lines_of_code=total_lines
            )
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating API content: {e}")
            return f"Error generating content: {e}"
    
    async def _get_blueprint_from_neo4j(self, blueprint_id: str) -> Optional[Dict[str, Any]]:
        """Get blueprint data from Neo4j."""
        try:
            # Simulate Neo4j query - in real implementation, use actual Neo4j queries
            # For testing, return mock data
            return {
                'blueprint_id': blueprint_id,
                'name': 'Test API Implementation',
                'description': 'Mock blueprint for testing',
                'required_skills': ['python', 'fastapi'],
                'estimated_hours': 8.0
            }
        except Exception as e:
            logger.error(f"Error getting blueprint from Neo4j: {e}")
            return None
    
    async def _get_blueprint_relationships(self, blueprint_id: str) -> Dict[str, Any]:
        """Get blueprint relationships from Neo4j."""
        try:
            # Mock relationships for testing
            return {
                'components': [
                    {'id': blueprint_id, 'name': 'Main Component'}
                ],
                'dependencies': []
            }
        except Exception as e:
            logger.error(f"Error getting blueprint relationships: {e}")
            return {'components': [], 'dependencies': []}
    
    async def _generate_diagram_content(
        self,
        blueprint_data: Dict[str, Any],
        related_data: Dict[str, Any],
        diagram_type: str
    ) -> str:
        """Generate diagram content in Mermaid format."""
        try:
            diagram_content = "graph TD\n"
            
            # Add main component
            main_id = blueprint_data['blueprint_id']
            main_name = blueprint_data.get('name', 'Unknown')
            diagram_content += f"    {main_id}[{main_name}]\n"
            
            # Add related components
            for component in related_data.get('components', []):
                if component['id'] != main_id:
                    diagram_content += f"    {component['id']}[{component['name']}]\n"
            
            # Add dependencies
            for dep in related_data.get('dependencies', []):
                diagram_content += f"    {dep['from']} --> {dep['to']}\n"
            
            return diagram_content
            
        except Exception as e:
            logger.error(f"Error generating diagram content: {e}")
            return f"graph TD\n    ERROR[Error generating diagram: {e}]"
    
    async def _get_project_blueprints(
        self,
        project_id: str,
        include_blueprints: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get blueprints for project."""
        try:
            # Mock blueprints for testing
            blueprints = [
                {
                    'blueprint_id': 'test_blueprint_001',
                    'name': 'Test API Implementation',
                    'status': 'in_progress',
                    'completion_percentage': 65.0
                }
            ]
            
            if include_blueprints:
                blueprints = [b for b in blueprints if b['blueprint_id'] in include_blueprints]
            
            return blueprints
            
        except Exception as e:
            logger.error(f"Error getting project blueprints: {e}")
            return []
    
    async def _calculate_progress_metrics(self, blueprints_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate progress metrics."""
        if not blueprints_data:
            return {'overall_completion': 0.0, 'total_tasks': 0}
        
        total_completion = sum(bp.get('completion_percentage', 0) for bp in blueprints_data)
        average_completion = total_completion / len(blueprints_data)
        
        return {
            'overall_completion': average_completion,
            'total_tasks': len(blueprints_data),
            'completed_tasks': len([bp for bp in blueprints_data if bp.get('completion_percentage', 0) >= 100]),
            'in_progress_tasks': len([bp for bp in blueprints_data if 0 < bp.get('completion_percentage', 0) < 100]),
            'pending_tasks': len([bp for bp in blueprints_data if bp.get('completion_percentage', 0) == 0])
        }
    
    async def _generate_progress_content(
        self,
        blueprints_data: List[Dict[str, Any]],
        progress_metrics: Dict[str, Any],
        report_type: str
    ) -> str:
        """Generate progress report content."""
        try:
            content = f"# Progress Report ({report_type.title()})\n\n"
            content += f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            
            content += "## Summary\n\n"
            content += f"- **Total Tasks:** {progress_metrics['total_tasks']}\n"
            content += f"- **Overall Completion:** {progress_metrics['overall_completion']:.1f}%\n"
            content += f"- **Completed Tasks:** {progress_metrics['completed_tasks']}\n"
            content += f"- **In Progress:** {progress_metrics['in_progress_tasks']}\n"
            content += f"- **Pending:** {progress_metrics['pending_tasks']}\n\n"
            
            content += "## Task Details\n\n"
            for blueprint in blueprints_data:
                content += f"### {blueprint['name']}\n"
                content += f"- **Status:** {blueprint.get('status', 'unknown')}\n"
                content += f"- **Completion:** {blueprint.get('completion_percentage', 0):.1f}%\n\n"
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating progress content: {e}")
            return f"Error generating progress report: {e}"
    
    async def _update_performance_metrics(self, doc_type: DocumentType, generation_time_ms: float):
        """Update performance metrics."""
        try:
            metrics = self._performance_metrics[doc_type.value]
            metrics['total_generations'] += 1
            metrics['total_time_ms'] += generation_time_ms
            metrics['avg_generation_time_ms'] = metrics['total_time_ms'] / metrics['total_generations']
            
        except Exception as e:
            logger.warning(f"Error updating performance metrics: {e}")