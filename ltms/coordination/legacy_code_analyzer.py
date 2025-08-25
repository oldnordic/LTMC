"""
LTMC Legacy Code Analyzer Agent - INTEGRATED VERSION
Coordinated agent for analyzing legacy @mcp.tool decorators.

Smart modularization completed (300-line limit compliance).
Uses 4 focused modules with ALL LTMC tools integration maintained.

Components:
- LegacyCodeInitialization: Agent initialization with chat_action logging
- LegacyCodeAnalysisEngine: Analysis with pattern_action, unix_action, memory_action, graph_action
- LegacyCodeCommunication: Communication with chat_action logging
- LegacyCodeProcessingUtilities: Data processing utilities

Maintains ALL LTMC tools integration: chat_action, pattern_action, unix_action, 
memory_action, graph_action
"""

from typing import Dict, List, Any, Optional

# Import coordination framework components
from .agent_coordination_core import LTMCAgentCoordinator
from .agent_state_manager import LTMCAgentStateManager

# Import modularized components - ALL 4 modules
from .legacy_code_initialization import LegacyCodeInitialization
from .legacy_code_analysis_engine import LegacyCodeAnalysisEngine
from .legacy_code_communication import LegacyCodeCommunication
from .legacy_code_processing_utilities import LegacyCodeProcessingUtilities


class LegacyCodeAnalyzer:
    """
    Modularized coordinated agent for analyzing legacy @mcp.tool decorators.
    
    Integrates 4 focused modules for complete legacy code analysis:
    - LegacyCodeInitialization: Agent setup with LTMC chat logging
    - LegacyCodeAnalysisEngine: Analysis with LTMC pattern/unix/memory/graph tools
    - LegacyCodeCommunication: Handoff with LTMC chat logging
    - LegacyCodeProcessingUtilities: Data processing for analysis workflow
    
    Maintains 100% LTMC tools integration across all modules with real functionality.
    
    Part of the coordinated legacy removal workflow alongside SafetyValidator
    and LegacyRemovalWorkflow agents.
    """
    
    def __init__(self, coordinator: LTMCAgentCoordinator, state_manager: LTMCAgentStateManager):
        """
        Initialize modularized legacy code analyzer agent.
        
        Args:
            coordinator: LTMC agent coordinator for registration and communication
            state_manager: Agent state manager for lifecycle management
        """
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.agent_id = "legacy_code_analyzer"
        
        # Initialize modular components
        self.initialization = LegacyCodeInitialization(coordinator, state_manager)
        self.analysis_engine = LegacyCodeAnalysisEngine(coordinator, state_manager)
        self.processing_utilities = LegacyCodeProcessingUtilities(self.agent_id)
        
        # Communication module initialized after analysis (requires analysis data)
        self.communication = None
    
    def initialize_agent(self) -> bool:
        """
        Initialize agent using initialization module.
        
        Delegates to LegacyCodeInitialization for complete agent setup with
        LTMC chat_action logging integration.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        return self.initialization.initialize_agent()
    
    def analyze_legacy_code(self) -> Dict[str, Any]:
        """
        Perform comprehensive legacy code analysis using analysis engine.
        
        Delegates to LegacyCodeAnalysisEngine for complete analysis workflow with
        ALL LTMC tools integration (pattern_action, unix_action, memory_action, graph_action).
        
        Integrates processing utilities for data processing and result preparation.
        
        Returns:
            Dict[str, Any]: Analysis results with legacy tools, functional mappings, and recommendations
        """
        # Perform analysis using analysis engine
        analysis_result = self.analysis_engine.analyze_legacy_code()
        
        if analysis_result['success']:
            # Initialize communication module with analysis results
            self.communication = LegacyCodeCommunication(
                self.coordinator,
                self.state_manager,
                self.initialization.message_broker,
                analysis_result['legacy_decorators'],
                analysis_result['functional_tools'],
                analysis_result['analysis_report']
            )
        
        return analysis_result
    
    def send_analysis_to_next_agent(self, recipient_agent_id: str) -> bool:
        """
        Send analysis results to next agent using communication module.
        
        Delegates to LegacyCodeCommunication for message coordination with
        LTMC chat_action logging integration.
        
        Args:
            recipient_agent_id: ID of the agent to receive analysis results
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.communication:
            print("❌ Communication module not initialized. Run analyze_legacy_code first.")
            return False
        
        return self.communication.send_analysis_to_next_agent(recipient_agent_id)
    
    # Expose processing utilities for compatibility
    def _process_legacy_decorators(self, functions: List[Dict[str, Any]]) -> None:
        """Process legacy decorators using processing utilities module."""
        self.processing_utilities.process_legacy_decorators(functions)
    
    def _map_functional_tools(self) -> None:
        """Map functional tools using processing utilities module."""
        self.processing_utilities.map_functional_tools()
    
    def _create_analysis_report(self) -> None:
        """Create analysis report using processing utilities module."""
        self.processing_utilities.create_analysis_report()
    
    # Expose properties for compatibility
    @property
    def legacy_decorators(self) -> List[Dict[str, Any]]:
        """Get legacy decorators from analysis engine."""
        return getattr(self.analysis_engine, 'legacy_decorators', [])
    
    @property
    def functional_tools(self) -> List[Dict[str, Any]]:
        """Get functional tools from analysis engine."""
        return getattr(self.analysis_engine, 'functional_tools', [])
    
    @property
    def analysis_report(self) -> Dict[str, Any]:
        """Get analysis report from analysis engine."""
        return getattr(self.analysis_engine, 'analysis_report', {})