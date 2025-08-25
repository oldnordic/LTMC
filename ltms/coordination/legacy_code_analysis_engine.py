"""
Legacy Code Analysis Engine
Legacy code analysis and LTMC tools integration.

Extracted from legacy_code_analyzer.py for smart modularization (300-line limit compliance).
Handles analyze_legacy_code and pattern analysis with comprehensive LTMC tools integration.

Components:
- LegacyCodeAnalysisEngine: Analysis engine with pattern_action, unix_action, memory_action, graph_action
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any

# Import coordination models
from .agent_coordination_models import AgentStatus
from .agent_state_models import StateTransition

# Import LTMC tools - MANDATORY
from ltms.tools.consolidated import (
    pattern_action,     # Tool 5 - Code analysis - MANDATORY
    unix_action,        # Tool 4 - Unix utilities - MANDATORY
    memory_action,      # Tool 1 - Memory operations - MANDATORY
    graph_action        # Tool 8 - Knowledge graph - MANDATORY
)


class LegacyCodeAnalysisEngine:
    """
    Legacy code analysis engine with comprehensive LTMC integration.
    
    Handles analysis operations and LTMC tools integration:
    - Legacy code scanning with pattern_action
    - File structure analysis with unix_action
    - Analysis storage with memory_action
    - Knowledge graph relationships with graph_action
    - State management integration
    - Analysis result processing
    
    Uses MANDATORY LTMC tools:
    - pattern_action (Tool 5): Function and class extraction from codebase
    - unix_action (Tool 4): File structure and tree analysis
    - memory_action (Tool 1): Analysis result storage and persistence
    - graph_action (Tool 8): Knowledge graph relationship creation
    """
    
    def __init__(self, coordinator, state_manager):
        """
        Initialize legacy code analysis engine.
        
        Args:
            coordinator: LTMC agent coordinator for task and conversation context
            state_manager: Agent state manager for state transitions
        """
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.agent_id = "legacy_code_analyzer"
        
        # Analysis results storage
        self.legacy_decorators = []
        self.functional_tools = []
        self.analysis_report = {}
    
    def analyze_legacy_code(self) -> Dict[str, Any]:
        """
        Perform comprehensive legacy code analysis using LTMC tools.
        
        Executes complete analysis workflow:
        - Transitions agent to active state
        - Extracts functions and classes with pattern_action
        - Analyzes file structure with unix_action
        - Processes legacy decorators and maps functional tools
        - Stores analysis in LTMC memory with memory_action
        - Creates knowledge graph relationships with graph_action
        - Transitions to waiting state for next agent
        
        Uses ALL MANDATORY LTMC tools for comprehensive analysis:
        - pattern_action for code structure extraction
        - unix_action for file system analysis
        - memory_action for persistent storage
        - graph_action for relationship mapping
        
        Returns:
            Dict[str, Any]: Analysis results with legacy tools, functional mappings, and recommendations
        """
        try:
            # Transition to active state
            self.state_manager.transition_agent_state(
                self.agent_id,
                AgentStatus.ACTIVE,
                StateTransition.ACTIVATE,
                {"state_updates": {"current_task": "legacy_code_analysis"}}
            )
            
            # Use pattern_action (Tool 5) to extract functions from MCP server - MANDATORY
            mcp_server_file = "/home/feanor/Projects/ltmc/ltms/mcp_server.py"
            
            functions_result = pattern_action(
                action="extract_functions",
                file_path=mcp_server_file,
                conversation_id=self.coordinator.conversation_id,
                role="system"
            )
            
            # Use pattern_action to extract classes - MANDATORY
            classes_result = pattern_action(
                action="extract_classes", 
                file_path=mcp_server_file,
                conversation_id=self.coordinator.conversation_id,
                role="system"
            )
            
            # Use unix_action (Tool 4) to get file structure - MANDATORY
            tree_result = unix_action(
                action="tree",
                path="/home/feanor/Projects/ltmc/ltms",
                max_depth=3,
                conversation_id=self.coordinator.conversation_id,
                role="system"
            )
            
            # Process analysis results
            self._process_legacy_decorators(functions_result.get('functions', []))
            self._map_functional_tools()
            self._create_analysis_report()
            
            # Store comprehensive analysis in LTMC memory (Tool 1) - MANDATORY
            analysis_document = {
                "agent_id": self.agent_id,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "legacy_decorators": self.legacy_decorators,
                "functional_tools": self.functional_tools,
                "analysis_report": self.analysis_report,
                "file_structure": tree_result,
                "coordination_task": self.coordinator.task_id
            }
            
            memory_result = memory_action(
                action="store",
                file_name=f"legacy_analysis_{self.coordinator.task_id}_{int(time.time())}.json",
                content=json.dumps(analysis_document, indent=2),
                tags=["legacy_analysis", self.agent_id, "code_analysis", self.coordinator.task_id],
                conversation_id=self.coordinator.conversation_id,
                role="system"
            )
            
            # Create knowledge graph relationships (Tool 8) - MANDATORY
            if self.legacy_decorators:
                graph_action(
                    action="link",
                    source_entity=f"legacy_analyzer_{self.coordinator.task_id}",
                    target_entity="legacy_mcp_tools",
                    relationship="discovered_legacy_tools",
                    properties={
                        "total_legacy_tools": len(self.legacy_decorators),
                        "analysis_time": analysis_document["analysis_timestamp"]
                    }
                )
            
            # Update agent state to completed analysis
            self.state_manager.transition_agent_state(
                self.agent_id,
                AgentStatus.WAITING,
                StateTransition.PAUSE,
                {"state_updates": {"current_task": "analysis_completed", "awaiting": "safety_validation"}}
            )
            
            return {
                "success": True,
                "legacy_decorators": self.legacy_decorators,
                "functional_tools": self.functional_tools,
                "analysis_report": self.analysis_report,
                "memory_storage": memory_result,
                "next_agent": "safety_validator"
            }
            
        except Exception as e:
            # Log error and transition to error state
            error_msg = f"Legacy code analysis failed: {e}"
            print(f"❌ {error_msg}")
            
            self.state_manager.transition_agent_state(
                self.agent_id,
                AgentStatus.ERROR,
                StateTransition.FAIL,
                {"state_updates": {"error": error_msg}}
            )
            
            return {
                "success": False,
                "error": error_msg,
                "legacy_decorators": [],
                "functional_tools": [],
                "analysis_report": {}
            }
    
    def _process_legacy_decorators(self, functions: List[Dict[str, Any]]) -> None:
        """
        Process extracted functions to identify legacy @mcp.tool decorators.
        
        Analyzes function list from pattern_action to identify functions with
        legacy @mcp.tool decorators and stores them for removal recommendations.
        
        Args:
            functions: List of function dictionaries from pattern extraction
        """
        for function in functions:
            if '@mcp.tool' in function.get('decorators', []):
                self.legacy_decorators.append({
                    'name': function['name'],
                    'file': function.get('file', 'unknown'),
                    'line': function.get('line', 0),
                    'decorators': function['decorators'],
                    'signature': function.get('signature', ''),
                    'identified_by': self.agent_id
                })
    
    def _map_functional_tools(self) -> None:
        """
        Map legacy tools to functional consolidated tools.
        
        Creates mapping of all consolidated tools that serve as functional
        replacements for legacy @mcp.tool decorated functions.
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
    
    def _create_analysis_report(self) -> None:
        """
        Create comprehensive analysis report.
        
        Generates complete analysis report with legacy decorator counts,
        functional tool mappings, removal recommendations, and metadata
        for coordination workflow.
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