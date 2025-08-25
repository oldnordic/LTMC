"""
Legacy Code Processing Utilities
Helper methods and data processing functionality.

Extracted from legacy_code_analyzer.py for smart modularization (300-line limit compliance).
Handles _process_legacy_decorators, _map_functional_tools, _create_analysis_report.

Components:
- LegacyCodeProcessingUtilities: Data processing utilities for legacy code analysis
"""

from datetime import datetime, timezone
from typing import Dict, List, Any


class LegacyCodeProcessingUtilities:
    """
    Legacy code analyzer processing utilities.
    
    Handles data processing operations for legacy code analysis:
    - Legacy decorator identification and processing
    - Functional tool mapping to consolidated tools
    - Analysis report creation with recommendations
    - Data validation and structure management
    - Processing workflow coordination
    
    Pure processing utilities without LTMC tool dependencies.
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize legacy code processing utilities.
        
        Args:
            agent_id: Agent identifier for processing attribution
        """
        self.agent_id = agent_id
        
        # Processing results storage
        self.legacy_decorators = []
        self.functional_tools = []
        self.analysis_report = {}
    
    def process_legacy_decorators(self, functions: List[Dict[str, Any]]) -> None:
        """
        Process extracted functions to identify legacy @mcp.tool decorators.
        
        Analyzes function list from pattern extraction to identify functions with
        legacy @mcp.tool decorators. Creates detailed decorator records with
        file location, signature, and identification metadata.
        
        Handles edge cases:
        - Missing decorator fields
        - None values
        - Missing file/line information
        - Partial decorator matches
        
        Args:
            functions: List of function dictionaries from pattern extraction
        """
        for function in functions:
            # Handle missing or None decorators field
            decorators = function.get('decorators')
            if not decorators:
                continue
            
            # Check for exact @mcp.tool match
            if '@mcp.tool' in decorators:
                self.legacy_decorators.append({
                    'name': function['name'],
                    'file': function.get('file', 'unknown'),
                    'line': function.get('line', 0),
                    'decorators': decorators,
                    'signature': function.get('signature', ''),
                    'identified_by': self.agent_id
                })
    
    def map_functional_tools(self) -> None:
        """
        Map legacy tools to functional consolidated tools.
        
        Creates comprehensive mapping of all consolidated tools that serve as
        functional replacements for legacy @mcp.tool decorated functions.
        
        Maps all 11 consolidated LTMC tools:
        - memory_action, todo_action, chat_action, unix_action
        - pattern_action, blueprint_action, cache_action, graph_action
        - documentation_action, sync_action, config_action
        """
        consolidated_tools = [
            'memory_action', 'todo_action', 'chat_action', 'unix_action',
            'pattern_action', 'blueprint_action', 'cache_action', 'graph_action',
            'documentation_action', 'sync_action', 'config_action'
        ]
        
        for tool_name in consolidated_tools:
            self.functional_tools.append({
                'name': tool_name,
                'file': 'ltms/tools/consolidated.py',
                'type': 'functional_replacement',
                'status': 'active'
            })
    
    def create_analysis_report(self) -> None:
        """
        Create comprehensive analysis report.
        
        Generates complete analysis report with:
        - Legacy decorator and functional tool counts
        - Specific removal recommendations for each legacy decorator
        - Analysis metadata including agent ID and timestamp
        - Structured format for communication to next agent
        
        Report structure compatible with coordination workflow and
        communication module requirements.
        """
        self.analysis_report = {
            "total_legacy_decorators": len(self.legacy_decorators),
            "total_functional_tools": len(self.functional_tools),
            "removal_recommendations": [
                f"Remove {decorator['name']} from {decorator['file']}:{decorator['line']}"
                for decorator in self.legacy_decorators
            ],
            "analysis_agent": self.agent_id,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }