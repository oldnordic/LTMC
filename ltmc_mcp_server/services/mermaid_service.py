"""
MermaidService - Core Mermaid.js Integration Service
==================================================

Core service for Mermaid.js diagram generation and manipulation.
Integrates with LTMC 4-tier memory system for advanced capabilities.

Features:
- Diagram generation and validation
- Memory integration for persistent storage
- Template system for reusable diagram patterns
- Advanced analytics and relationship mapping
"""

import asyncio
import subprocess
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from ltmc_mcp_server.utils.logging_utils import get_tool_logger


class DiagramType(Enum):
    """Supported Mermaid diagram types."""
    FLOWCHART = "flowchart"
    SEQUENCE = "sequenceDiagram"
    CLASS = "classDiagram" 
    STATE = "stateDiagram"
    GANTT = "gantt"
    PIE = "pie"
    GITGRAPH = "gitGraph"
    ER = "erDiagram"
    USER_JOURNEY = "journey"
    MINDMAP = "mindmap"


class OutputFormat(Enum):
    """Supported output formats."""
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    JSON = "json"


class MermaidService:
    """
    Core Mermaid.js service for diagram generation and management.
    
    Integrates with LTMC memory system for:
    - Persistent diagram storage
    - Template management
    - Analytics and insights
    - Relationship mapping
    """
    
    def __init__(self, settings):
        """Initialize the Mermaid service."""
        self.settings = settings
        self.logger = get_tool_logger('mermaid_service')
        self.cache_dir = Path(settings.ltmc_data_dir) / "mermaid_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Templates storage
        self.templates = {}
        self.analytics_cache = {}
        
        self.logger.info("MermaidService initialized")
    
    async def generate_diagram(
        self, 
        content: str, 
        diagram_type: DiagramType,
        output_format: OutputFormat = OutputFormat.SVG,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a Mermaid diagram from content.
        
        Args:
            content: Mermaid diagram content
            diagram_type: Type of diagram
            output_format: Output format
            options: Additional options
            
        Returns:
            Dict with generation results
        """
        try:
            # Validate content
            validation_result = await self._validate_content(content, diagram_type)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid content: {validation_result['errors']}"
                }
            
            # Generate diagram hash for caching
            content_hash = hashlib.md5(content.encode()).hexdigest()
            cache_key = f"{diagram_type.value}_{output_format.value}_{content_hash}"
            
            # Check cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.logger.info(f"Retrieved diagram from cache: {cache_key}")
                return cached_result
            
            # Generate new diagram
            result = await self._generate_new_diagram(
                content, diagram_type, output_format, options or {}
            )
            
            # Cache result
            if result["success"]:
                await self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating diagram: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_content(
        self, 
        content: str, 
        diagram_type: DiagramType
    ) -> Dict[str, Any]:
        """Validate Mermaid diagram content."""
        errors = []
        
        # Basic validation
        if not content or not content.strip():
            errors.append("Content cannot be empty")
        
        # Type-specific validation
        if diagram_type == DiagramType.FLOWCHART:
            if "graph" not in content and "flowchart" not in content:
                errors.append("Flowchart must contain 'graph' or 'flowchart' declaration")
        elif diagram_type == DiagramType.SEQUENCE:
            if "participant" not in content and "actor" not in content:
                errors.append("Sequence diagram should contain participants or actors")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _generate_new_diagram(
        self,
        content: str,
        diagram_type: DiagramType, 
        output_format: OutputFormat,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a new diagram using Mermaid CLI."""
        try:
            # Create temporary input file with simpler names
            timestamp = int(datetime.now().timestamp() * 1000000)
            input_file = self.cache_dir / f"input_{timestamp}.mmd"
            output_file = self.cache_dir / f"output_{timestamp}.{output_format.value}"
            
            # Write content to file
            input_file.write_text(content)
            
            # Simple command that we know works
            cmd = ["mmdc", "-i", str(input_file), "-o", str(output_file)]
            
            # Add theme if specified (only safe options)
            if options.get("theme") and options["theme"] in ["default", "forest", "dark", "neutral"]:
                cmd.extend(["-t", options["theme"]])
            
            self.logger.info(f"Input file: {input_file}")
            self.logger.info(f"Output file: {output_file}")
            self.logger.info(f"Command: {cmd}")
            self.logger.info(f"Command args: {[str(arg) for arg in cmd]}")
            
            # Execute with Chrome environment
            env = os.environ.copy()
            env["PUPPETEER_EXECUTABLE_PATH"] = "/usr/bin/google-chrome-stable"
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            self.logger.info(f"Return code: {process.returncode}")
            if stdout:
                self.logger.info(f"Stdout: {stdout.decode()}")
            if stderr:
                self.logger.info(f"Stderr: {stderr.decode()}")
            
            if process.returncode == 0:
                # Read generated file
                if output_file.exists():
                    output_data = output_file.read_text() if output_format == OutputFormat.SVG else output_file.read_bytes()
                    
                    # Clean up temp files
                    input_file.unlink(missing_ok=True)
                    output_file.unlink(missing_ok=True)
                    
                    return {
                        "success": True,
                        "data": output_data,
                        "format": output_format.value,
                        "diagram_type": diagram_type.value,
                        "generated_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": "Output file not generated"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Mermaid CLI error: {stderr.decode()}"
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Mermaid CLI not found. Install with: npm install -g @mermaid-js/mermaid-cli"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get diagram from cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                cache_data = json.loads(cache_file.read_text())
                # Check if cache is still valid (24 hours)
                cached_time = datetime.fromisoformat(cache_data.get("cached_at", ""))
                if (datetime.now() - cached_time).total_seconds() < 86400:
                    return cache_data
            except Exception:
                pass
        return None
    
    async def _save_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Save diagram result to cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            cache_data = {
                **result,
                "cached_at": datetime.now().isoformat()
            }
            cache_file.write_text(json.dumps(cache_data, indent=2))
        except Exception as e:
            self.logger.warning(f"Failed to cache result: {e}")
    
    async def create_template(
        self, 
        name: str, 
        content: str, 
        diagram_type: DiagramType,
        variables: List[str] = None
    ) -> Dict[str, Any]:
        """Create a reusable diagram template."""
        try:
            template = {
                "name": name,
                "content": content,
                "diagram_type": diagram_type.value,
                "variables": variables or [],
                "created_at": datetime.now().isoformat()
            }
            
            self.templates[name] = template
            
            # Save to disk
            template_file = self.cache_dir / "templates.json"
            template_file.write_text(json.dumps(self.templates, indent=2))
            
            return {
                "success": True,
                "template_name": name,
                "message": f"Template '{name}' created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_templates(self) -> Dict[str, Any]:
        """Get all available templates."""
        return {
            "success": True,
            "templates": list(self.templates.keys()),
            "count": len(self.templates)
        }
    
    async def analyze_diagram_complexity(self, content: str) -> Dict[str, Any]:
        """Analyze diagram complexity and provide insights."""
        try:
            lines = content.strip().split('\n')
            nodes = []
            edges = []
            
            # Simple analysis - count nodes and edges
            for line in lines:
                line = line.strip()
                if '-->' in line or '---' in line:
                    edges.append(line)
                elif line and not line.startswith('%') and not line.startswith('graph'):
                    # Potential node
                    if '[' in line or '(' in line or '{' in line:
                        nodes.append(line)
            
            complexity_score = len(nodes) + len(edges) * 1.5
            
            if complexity_score < 5:
                complexity_level = "Simple"
            elif complexity_score < 15:
                complexity_level = "Moderate"
            else:
                complexity_level = "Complex"
            
            return {
                "success": True,
                "analysis": {
                    "nodes": len(nodes),
                    "edges": len(edges),
                    "complexity_score": complexity_score,
                    "complexity_level": complexity_level,
                    "estimated_render_time": f"{min(10, complexity_score * 0.3):.1f}s"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get Mermaid service status and capabilities."""
        return {
            "success": True,
            "status": "healthy",
            "capabilities": {
                "diagram_types": [dt.value for dt in DiagramType],
                "output_formats": [of.value for of in OutputFormat],
                "templates_count": len(self.templates),
                "cache_enabled": True,
                "cache_directory": str(self.cache_dir)
            },
            "service_info": {
                "version": "1.0.0",
                "initialized_at": datetime.now().isoformat()
            }
        }