"""
Basic Mermaid Tools - Consolidated Diagram Management
==================================================

1 unified Mermaid tool for all diagram operations.
Integrates with LTMC system for persistent storage and retrieval.

Consolidated Tool:
- mermaid_diagram_manage - Unified tool for all Mermaid operations
  * generate - Generate diagrams from content
  * validate - Validate diagram syntax
  * create_flowchart - Create specialized flowcharts
  * create_sequence - Create sequence diagrams
  * create_class - Create class diagrams
  * export - Export diagrams to different formats
"""

import logging
from typing import Dict, Any, List

from mcp.server.fastmcp import FastMCP
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.mermaid_service import MermaidService, DiagramType, OutputFormat
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_basic_mermaid_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register consolidated Mermaid tools with FastMCP server."""
    logger = get_tool_logger('basic_mermaid')
    logger.info("Registering consolidated Mermaid tools")
    
    # Initialize Mermaid service
    mermaid_service = MermaidService(settings)
    
    @mcp.tool()
    async def mermaid_diagram_manage(
        operation: str,
        content: str,
        diagram_type: str = None,
        output_format: str = "svg",
        theme: str = "default",
        background: str = "white"
    ) -> Dict[str, Any]:
        """
        Unified Mermaid diagram management tool.
        
        Args:
            operation: Operation to perform ("generate", "validate", "create_flowchart", "create_sequence", "create_class", "export")
            content: Mermaid diagram content/syntax
            diagram_type: Type of diagram (flowchart, sequence, class, etc.)
            output_format: Output format (svg, png, pdf) - for generate/export operations
            theme: Diagram theme (default, dark, forest, etc.) - for generate operations
            background: Background color - for generate operations
            
        Returns:
            Dict with operation results and metadata
        """
        try:
            if operation == "generate":
                if not diagram_type:
                    return {"success": False, "error": "diagram_type required for generate operation"}
                
                # Convert string parameters to enums
                dt = DiagramType(diagram_type)
                of = OutputFormat(output_format)
                
                # Generate diagram
                result = await mermaid_service.generate_diagram(
                    content=content,
                    diagram_type=dt,
                    output_format=of,
                    options={
                        "theme": theme,
                        "background": background
                    }
                )
                return result
                
            elif operation == "validate":
                if not diagram_type:
                    return {"success": False, "error": "diagram_type required for validate operation"}
                
                # Validate syntax
                validation_result = await mermaid_service.validate_syntax(content, DiagramType(diagram_type))
                return validation_result
                
            elif operation == "create_flowchart":
                # Create specialized flowchart
                result = await mermaid_service.create_flowchart(content, theme=theme, background=background)
                return result
                
            elif operation == "create_sequence":
                # Create sequence diagram
                result = await mermaid_service.create_sequence_diagram(content, theme=theme, background=background)
                return result
                
            elif operation == "create_class":
                # Create class diagram
                result = await mermaid_service.create_class_diagram(content, theme=theme, background=background)
                return result
                
            elif operation == "export":
                if not diagram_type:
                    return {"success": False, "error": "diagram_type required for export operation"}
                
                # Export diagram
                of = OutputFormat(output_format)
                result = await mermaid_service.export_diagram(content, DiagramType(diagram_type), of)
                return result
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}. Valid operations: generate, validate, create_flowchart, create_sequence, create_class, export"
                }
            
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid parameter: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    logger.info("✅ Consolidated Mermaid tools registered successfully")
    logger.info("📊 Tool consolidation: 8 individual tools → 1 unified tool")
    logger.info("🔧 All functionality preserved through operation parameter")