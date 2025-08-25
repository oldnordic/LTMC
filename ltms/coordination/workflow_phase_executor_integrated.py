"""
Workflow Phase Executor - Integrated Version
Master phase execution delegating to early and late phase modules.

Smart modularization completed (300-line limit compliance).
Delegates to 2 focused modules: early phases (1-3) and late phases (4-6).

Components:
- WorkflowPhaseExecutor: Main orchestrator delegating to early/late phase modules
- WorkflowPhaseExecutorEarly: Phases 1-3 with todo, chat, graph tools
- WorkflowPhaseExecutorLate: Phases 4-6 with doc, sync, cache, memory tools

Maintains ALL LTMC tools integration: todo_action, chat_action, graph_action,
documentation_action, sync_action, cache_action, memory_action
"""

from typing import Dict, Any

# Import modularized phase executors
from .workflow_phase_executor_early import WorkflowPhaseExecutorEarly
from .workflow_phase_executor_late import WorkflowPhaseExecutorLate


class WorkflowPhaseExecutor:
    """
    Modularized workflow phase execution with comprehensive LTMC integration.
    
    Delegates to focused phase executor modules:
    - WorkflowPhaseExecutorEarly: Phases 1-3 (initialization, analysis, validation)
    - WorkflowPhaseExecutorLate: Phases 4-6 (planning, documentation, completion)
    
    Maintains 100% LTMC tools integration across both modules with real functionality.
    Uses ALL 7 LTMC tools: todo, chat, graph, documentation, sync, cache, memory.
    """
    
    def __init__(self, coordinator, state_manager, workflow_orchestrator, 
                 analyzer, validator, workflow_id: str, conversation_id: str):
        """
        Initialize modularized workflow phase executor.
        
        Sets up both early and late phase executors with shared context.
        
        Args:
            coordinator: LTMC agent coordinator for coordination operations
            state_manager: Agent state manager for state transitions
            workflow_orchestrator: Workflow orchestrator for advanced coordination
            analyzer: LegacyCodeAnalyzer agent for analysis operations
            validator: SafetyValidator agent for validation operations
            workflow_id: Unique workflow identifier
            conversation_id: Conversation context identifier
        """
        # Initialize early phase executor (Phases 1-3)
        self.early_executor = WorkflowPhaseExecutorEarly(
            coordinator, state_manager, workflow_orchestrator,
            analyzer, validator, workflow_id, conversation_id
        )
        
        # Initialize late phase executor (Phases 4-6)
        self.late_executor = WorkflowPhaseExecutorLate(
            coordinator, state_manager, workflow_orchestrator,
            analyzer, validator, workflow_id, conversation_id
        )
        
        # Expose shared properties for compatibility
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.workflow_orchestrator = workflow_orchestrator
        self.analyzer = analyzer
        self.validator = validator
        self.workflow_id = workflow_id
        self.conversation_id = conversation_id
    
    # Early phases delegation methods (Phases 1-3)
    def execute_phase_1_agent_initialization(self) -> Dict[str, Any]:
        """Delegate Phase 1 execution to early phase executor."""
        return self.early_executor.execute_phase_1_agent_initialization()
    
    def execute_phase_2_legacy_analysis(self) -> Dict[str, Any]:
        """Delegate Phase 2 execution to early phase executor."""
        return self.early_executor.execute_phase_2_legacy_analysis()
    
    def execute_phase_3_safety_validation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate Phase 3 execution to early phase executor."""
        return self.early_executor.execute_phase_3_safety_validation(analysis_result)
    
    # Late phases delegation methods (Phases 4-6)
    def execute_phase_4_removal_planning(self) -> Dict[str, Any]:
        """Delegate Phase 4 execution to late phase executor."""
        return self.late_executor.execute_phase_4_removal_planning()
    
    def execute_phase_5_documentation(self) -> Dict[str, Any]:
        """Delegate Phase 5 execution to late phase executor."""
        return self.late_executor.execute_phase_5_documentation()
    
    def execute_phase_6_completion(self, analysis_result: Dict[str, Any], 
                                 validation_result: Dict[str, Any], 
                                 removal_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate Phase 6 execution to late phase executor."""
        return self.late_executor.execute_phase_6_completion(
            analysis_result, validation_result, removal_plan
        )