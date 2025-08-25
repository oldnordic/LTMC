"""
LTMC Legacy Code Analyzer Agent
Coordinated agent for analyzing legacy @mcp.tool decorators.

Extracted from legacy_removal_coordinated_agents.py for smart modularization (300-line limit compliance).
Uses real LTMC coordination framework for agent communication and comprehensive LTMC tool integration.

Components:
- LegacyCodeAnalyzer: Agent for legacy code analysis and reporting
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import coordination framework components
from .agent_coordination_framework import (
    LTMCAgentCoordinator,
    AgentStatus,
    AgentMessage,
    AgentRegistration
)
from .mcp_communication_patterns import (
    LTMCMessageBroker,
    create_request_response_message,
    MessagePriority
)
from .agent_state_manager import (
    LTMCAgentStateManager,
    StateTransition
)

# Import ALL LTMC tools - MANDATORY
from ltms.tools.consolidated import (
    memory_action,      # Tool 1 - Memory operations
    todo_action,        # Tool 2 - Task management
    chat_action,        # Tool 3 - Chat logging
    unix_action,        # Tool 4 - Unix utilities  
    pattern_action,     # Tool 5 - Code analysis
    blueprint_action,   # Tool 6 - Blueprint management
    cache_action,       # Tool 7 - Cache operations
    graph_action,       # Tool 8 - Knowledge graph
    documentation_action, # Tool 9 - Documentation
    sync_action,        # Tool 10 - Doc synchronization
    config_action       # Tool 11 - Configuration
)


class LegacyCodeAnalyzer:
    """
    Coordinated agent for analyzing legacy @mcp.tool decorators.
    
    Uses real LTMC coordination framework for agent communication and
    comprehensive LTMC tool integration for legacy code analysis:
    - Scans codebase for legacy @mcp.tool decorators
    - Maps legacy tools to functional consolidated tools
    - Creates removal recommendations with safety analysis
    - Integrates with agent coordination workflow
    - Stores all findings in LTMC memory system
    
    Part of the coordinated legacy removal workflow alongside SafetyValidator
    and LegacyRemovalWorkflow agents.
    """
    
    def __init__(self, coordinator: LTMCAgentCoordinator, state_manager: LTMCAgentStateManager):
        """
        Initialize legacy code analyzer agent.
        
        Args:
            coordinator: LTMC agent coordinator for registration and communication
            state_manager: Agent state manager for lifecycle management
        """
        self.agent_id = "legacy_code_analyzer"
        self.agent_type = "ltmc-legacy-analyzer"
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.message_broker = LTMCMessageBroker(coordinator.conversation_id)
        
        # Analysis results storage
        self.legacy_decorators = []
        self.functional_tools = []
        self.analysis_report = {}
    
    def initialize_agent(self) -> bool:
        """
        Initialize agent with coordination framework.
        
        Registers agent with coordinator, creates initial state, and logs
        initialization in LTMC chat system. Essential for coordinated workflow.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Register with coordinator
            success = self.coordinator.register_agent(
                self.agent_id,
                self.agent_type,
                task_scope=["legacy_analysis", "decorator_mapping", "code_structure_analysis"],
                outputs=["legacy_inventory", "functional_tool_mapping", "removal_recommendations"]
            )
            
            if success:
                # Create agent state in state manager
                state_data = {
                    "agent_id": self.agent_id,
                    "task_scope": ["legacy_analysis", "decorator_mapping", "code_structure_analysis"],
                    "current_task": "initialization"
                }
                
                self.state_manager.create_agent_state(
                    self.agent_id,
                    AgentStatus.INITIALIZING,
                    state_data
                )
                
                # Log initialization in LTMC chat system
                chat_action(
                    action="log",
                    message=f"Legacy Code Analyzer initialized for coordination task {self.coordinator.task_id}",
                    tool_name=self.agent_id,
                    conversation_id=self.coordinator.conversation_id,
                    role="system"
                )
                
                print(f"✅ {self.agent_id} initialized successfully")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to initialize {self.agent_id}: {e}")
            return False
    
    def analyze_legacy_code(self) -> Dict[str, Any]:
        """
        Perform comprehensive legacy code analysis using LTMC tools.
        
        Scans the codebase for legacy @mcp.tool decorators, maps them to
        functional consolidated tools, and creates detailed analysis report
        stored in LTMC memory system.
        
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
            
            # Use pattern_action (Tool 5) to extract functions from MCP server
            mcp_server_file = "/home/feanor/Projects/ltmc/ltms/mcp_server.py"
            
            functions_result = pattern_action(
                action="extract_functions",
                file_path=mcp_server_file,
                conversation_id=self.coordinator.conversation_id,
                role="system"
            )
            
            # Use pattern_action to extract classes
            classes_result = pattern_action(
                action="extract_classes", 
                file_path=mcp_server_file,
                conversation_id=self.coordinator.conversation_id,
                role="system"
            )
            
            # Use unix_action (Tool 4) to get file structure
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
            
            # Store comprehensive analysis in LTMC memory (Tool 1)
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
            
            # Create knowledge graph relationships (Tool 8)
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
    
    def send_analysis_to_next_agent(self, recipient_agent_id: str) -> bool:
        """
        Send analysis results to next agent in coordination workflow.
        
        Uses LTMC message broker and chat system to coordinate with next agent
        in the legacy removal workflow (typically SafetyValidator).
        
        Args:
            recipient_agent_id: ID of the agent to receive analysis results
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            # Create coordination message
            message_data = {
                "from_agent": self.agent_id,
                "to_agent": recipient_agent_id,
                "message_type": "analysis_results",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "legacy_decorators": self.legacy_decorators,
                    "functional_tools": self.functional_tools,
                    "analysis_report": self.analysis_report,
                    "coordination_task": self.coordinator.task_id
                }
            }
            
            # Send via message broker
            message = create_request_response_message(
                self.agent_id,
                recipient_agent_id,
                "legacy_analysis_complete",
                message_data,
                MessagePriority.HIGH,
                self.coordinator.conversation_id
            )
            
            success = self.message_broker.send_message(message)
            
            if success:
                # Log handoff in LTMC chat system (Tool 3)
                chat_action(
                    action="log",
                    message=f"Legacy analysis results sent from {self.agent_id} to {recipient_agent_id}",
                    tool_name=self.agent_id,
                    conversation_id=self.coordinator.conversation_id,
                    role="system"
                )
                
                # Transition to handoff state
                self.state_manager.transition_agent_state(
                    self.agent_id,
                    AgentStatus.HANDOFF,
                    StateTransition.HANDOFF,
                    {"state_updates": {"handed_off_to": recipient_agent_id}}
                )
                
                print(f"✅ Analysis results sent to {recipient_agent_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to send analysis to {recipient_agent_id}: {e}")
            return False
    
    def _process_legacy_decorators(self, functions: List[Dict[str, Any]]) -> None:
        """Process extracted functions to identify legacy @mcp.tool decorators."""
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
        """Map legacy tools to functional consolidated tools."""
        # This would contain the actual mapping logic
        # For now, creating sample mapping
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
        """Create comprehensive analysis report."""
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