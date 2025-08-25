"""
Workflow Phase Executor - Early Phases (1-3)
Phase execution for initialization, analysis, and validation.

Extracted from workflow_phase_executor.py for 300-line limit compliance.
Handles Phases 1-3 with LTMC tools integration.

Components:
- WorkflowPhaseExecutorEarly: Phases 1-3 execution with todo, chat, graph tools
"""

from datetime import datetime, timezone
from typing import Dict, Any

# Import LTMC tools - MANDATORY
from ltms.tools.consolidated import (
    todo_action,            # Tool 2 - Task management - MANDATORY
    chat_action,            # Tool 3 - Chat logging - MANDATORY
    graph_action            # Tool 8 - Knowledge graph - MANDATORY
)


class WorkflowPhaseExecutorEarly:
    """
    Early phase execution with comprehensive LTMC integration.
    
    Handles early phase execution operations:
    - Phase 1: Agent initialization and workflow setup
    - Phase 2: Legacy code analysis with handoff coordination  
    - Phase 3: Safety validation and risk assessment
    
    Uses MANDATORY LTMC tools:
    - todo_action (Tool 2): Workflow and task tracking
    - chat_action (Tool 3): Phase completion logging
    - graph_action (Tool 8): Knowledge graph relationship creation
    """
    
    def __init__(self, coordinator, state_manager, workflow_orchestrator, 
                 analyzer, validator, workflow_id: str, conversation_id: str):
        """
        Initialize early phase executor.
        
        Args:
            coordinator: LTMC agent coordinator for coordination operations
            state_manager: Agent state manager for state transitions
            workflow_orchestrator: Workflow orchestrator for advanced coordination
            analyzer: LegacyCodeAnalyzer agent for analysis operations
            validator: SafetyValidator agent for validation operations
            workflow_id: Unique workflow identifier
            conversation_id: Conversation context identifier
        """
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.workflow_orchestrator = workflow_orchestrator
        self.analyzer = analyzer
        self.validator = validator
        self.workflow_id = workflow_id
        self.conversation_id = conversation_id
    
    def execute_phase_1_agent_initialization(self) -> Dict[str, Any]:
        """
        Execute Phase 1: Agent Initialization and Workflow Setup.
        
        Uses MANDATORY LTMC tools for initialization tracking:
        - todo_action for workflow task creation
        - chat_action for phase completion logging
        
        Returns:
            Dict[str, Any]: Phase 1 execution results
        """
        try:
            print("\\n📋 Phase 1: Agent Initialization and Workflow Setup")
            
            # Create workflow tracking task using todo_action (Tool 2) - MANDATORY
            workflow_task = todo_action(
                action="add",
                content=f"Execute coordinated legacy removal workflow {self.workflow_id}",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            # Initialize all coordinated agents
            analyzer_init = self.analyzer.initialize_agent()
            validator_init = self.validator.initialize_agent()
            
            if not (analyzer_init and validator_init):
                raise Exception("Agent initialization failed - coordination cannot proceed")
            
            # Log phase completion using chat_action (Tool 3) - MANDATORY
            chat_action(
                action="log",
                message=f"Phase 1 Complete: All agents initialized for workflow {self.workflow_id}",
                tool_name="workflow_orchestrator",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            print("✅ All agents initialized successfully")
            
            return {
                "success": True,
                "phase": 1,
                "agents_initialized": 2,
                "workflow_task": workflow_task
            }
            
        except Exception as e:
            return {
                "success": False,
                "phase": 1,
                "error": f"Phase 1 failed: Agent initialization failed - coordination cannot proceed"
            }
    
    def execute_phase_2_legacy_analysis(self) -> Dict[str, Any]:
        """
        Execute Phase 2: Legacy Code Analysis.
        
        Performs analysis and coordinated handoff between agents.
        
        Returns:
            Dict[str, Any]: Phase 2 execution results with analysis data
        """
        try:
            print("\\n📋 Phase 2: Legacy Code Analysis")
            
            analysis_result = self.analyzer.analyze_legacy_code()
            if not analysis_result.get('success'):
                raise Exception(f"Legacy analysis failed: {analysis_result.get('error', 'Unknown analysis error')}")
            
            # Execute coordinated agent handoff
            handoff_success = self.coordinator.coordinate_agent_handoff(
                self.analyzer.agent_id,
                self.validator.agent_id,
                {
                    "analysis_results": analysis_result,
                    "handoff_type": "analysis_to_validation",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            if not handoff_success:
                raise Exception("Agent handoff coordination failed")
            
            # Send analysis results to validator agent
            message_sent = self.analyzer.send_analysis_to_next_agent("safety_validator")
            if not message_sent:
                raise Exception("Failed to send analysis results to validator agent")
            
            print("✅ Analysis complete and successfully handed off to validator")
            
            return {
                "success": True,
                "phase": 2,
                "analysis_results": analysis_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "phase": 2,
                "error": str(e)
            }
    
    def execute_phase_3_safety_validation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Phase 3: Safety Validation and Risk Assessment.
        
        Uses MANDATORY LTMC tools for validation tracking:
        - graph_action for knowledge graph relationship creation
        
        Args:
            analysis_result: Results from Phase 2 analysis
            
        Returns:
            Dict[str, Any]: Phase 3 execution results with validation data
        """
        try:
            print("\\n📋 Phase 3: Safety Validation and Risk Assessment")
            
            validation_result = self.validator.validate_removal_safety(analysis_result)
            if not validation_result.get('success'):
                raise Exception(f"Safety validation failed: {validation_result.get('error', 'Unknown validation error')}")
            
            # Create knowledge graph relationships using graph_action (Tool 8) - MANDATORY
            graph_action(
                action="link",
                source_entity=f"workflow_{self.workflow_id}",
                target_entity="legacy_removal_validation",
                relationship="completed_validation",
                properties={
                    "safety_score": validation_result.get('validation_report', {}).get('safety_score', 0),
                    "validation_timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            print("✅ Safety validation completed with comprehensive risk assessment")
            
            return {
                "success": True,
                "phase": 3,
                "validation_results": validation_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "phase": 3,
                "error": str(e)
            }