"""Advanced Task Orchestration - Component 5 (Phase 2).

This package provides advanced orchestration capabilities including:
- WorkflowEngine for complex step-based execution
- TaskCoordinator for multi-task coordination with dependencies
- Error recovery and retry mechanisms
- State management and progress monitoring
"""

from .workflow_engine import (
    WorkflowEngine,
    WorkflowState,
    WorkflowStep,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowResult,
    StepResult,
    RetryPolicy,
    ParallelExecutionGroup
)

from .task_coordinator import (
    TaskCoordinator,
    CoordinationTask,
    TaskDependency,
    ExecutionContext,
    TaskStatus,
    TaskProgress,
    CoordinationResult
)

__all__ = [
    # WorkflowEngine classes
    "WorkflowEngine",
    "WorkflowState",
    "WorkflowStep",
    "WorkflowDefinition", 
    "WorkflowExecution",
    "WorkflowResult",
    "StepResult",
    "RetryPolicy",
    "ParallelExecutionGroup",
    
    # TaskCoordinator classes
    "TaskCoordinator",
    "CoordinationTask",
    "TaskDependency",
    "ExecutionContext",
    "TaskStatus",
    "TaskProgress",
    "CoordinationResult"
]