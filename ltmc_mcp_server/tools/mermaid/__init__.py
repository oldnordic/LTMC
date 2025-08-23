"""
Mermaid Tools - MCP Integration
==============================

Complete Mermaid.js integration for LTMC system with 24 specialized tools.
Provides diagram generation, memory integration, and advanced analytics.

Tool Categories:
1. Basic Tools (8) - Core diagram generation
2. Advanced Tools (8) - Memory integration & templates  
3. Analysis Tools (8) - Analytics & optimization

Total: 24 Mermaid MCP tools for comprehensive diagram capabilities.
"""

from .basic_mermaid_tools import register_basic_mermaid_tools
from .advanced_mermaid_tools import register_advanced_mermaid_tools 
from .analysis_core_mermaid_tools import register_analysis_core_mermaid_tools
from .analysis_intelligence_mermaid_tools import (
    register_analysis_intelligence_mermaid_tools
)
from .consolidated_analysis_mermaid_tools import (
    register_consolidated_analysis_mermaid_tools
)
from .consolidated_analysis_core_mermaid_tools import (
    register_consolidated_analysis_core_mermaid_tools
)
from .consolidated_advanced_mermaid_tools import (
    register_consolidated_advanced_mermaid_tools
)
from .consolidated_analysis_intelligence_mermaid_tools import (
    register_consolidated_analysis_intelligence_mermaid_tools
)

__all__ = [
    'register_basic_mermaid_tools',
    'register_advanced_mermaid_tools', 
    'register_analysis_core_mermaid_tools',
    'register_analysis_intelligence_mermaid_tools',
    'register_consolidated_analysis_mermaid_tools',
    'register_consolidated_analysis_core_mermaid_tools',
    'register_consolidated_advanced_mermaid_tools',
    'register_consolidated_analysis_intelligence_mermaid_tools'
]