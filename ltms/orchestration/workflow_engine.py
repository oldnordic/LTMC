"""Workflow Engine - Component 5 (Advanced Task Orchestration) - Phase 2.

This module provides advanced workflow execution capabilities including:
- Sequential and parallel step execution
- Error recovery and retry mechanisms
- State management for complex workflows
- Performance optimization and concurrency control
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum

from ltms.services.redis_service import RedisConnectionManager

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Workflow execution states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RetryPolicy:
    """Retry policy for workflow steps."""
    max_retries: int = 0
    delay_seconds: float = 5.0
    exponential_backoff: bool = False
    max_delay_seconds: float = 300.0


@dataclass
class StepResult:
    """Result of a workflow step execution."""
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    retry_count: int = 0


@dataclass 
class WorkflowStep:
    """Individual step in a workflow."""
    step_id: str
    name: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_policy: Optional[RetryPolicy] = None
    condition: Optional[str] = None  # Conditional execution expression


@dataclass
class ParallelExecutionGroup:
    """Group of steps that can execute in parallel."""
    group_id: str
    steps: List[WorkflowStep]
    max_concurrent: int = 10
    fail_fast: bool = True  # Stop on first failure


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    workflow_id: str
    name: str
    description: str
    steps: List[Union[WorkflowStep, ParallelExecutionGroup]]
    timeout_seconds: int = 3600
    max_parallel_executions: int = 5
    retry_policy: Optional[RetryPolicy] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Runtime execution state of a workflow."""
    execution_id: str
    workflow_id: str
    state: WorkflowState
    started_at: datetime
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    project_id: Optional[str] = None


@dataclass
class WorkflowResult:
    """Final result of workflow execution."""
    success: bool
    workflow_execution: WorkflowExecution
    error_message: Optional[str] = None
    total_execution_time_seconds: float = 0.0


class WorkflowEngine:
    """Advanced workflow execution engine."""
    
    def __init__(
        self,
        redis_manager: RedisConnectionManager,
        max_concurrent_workflows: int = 20,
        step_timeout_default: int = 300
    ):
        """Initialize workflow engine.
        
        Args:
            redis_manager: Redis connection manager
            max_concurrent_workflows: Maximum concurrent workflow executions
            step_timeout_default: Default step timeout in seconds
        """
        self.redis_manager = redis_manager
        self.max_concurrent_workflows = max_concurrent_workflows
        self.step_timeout_default = step_timeout_default
        self.initialized = False
        
        # Workflow definitions storage
        self._workflow_definitions: Dict[str, WorkflowDefinition] = {}
        
        # Active executions
        self._active_executions: Dict[str, WorkflowExecution] = {}
        
        # Step handlers
        self._step_handlers: Dict[str, Callable] = {}
        
        # Execution semaphore for concurrency control
        self._execution_semaphore: Optional[asyncio.Semaphore] = None
    
    async def initialize(self) -> bool:
        """Initialize the workflow engine.
        
        Returns:
            True if initialized successfully
        """
        try:
            if self.initialized:
                return True
            
            # Initialize concurrency control
            self._execution_semaphore = asyncio.Semaphore(self.max_concurrent_workflows)
            
            # Verify Redis connection
            if not await self.redis_manager.ping():
                logger.error("Redis connection failed during workflow engine initialization")
                return False
            
            # Load existing workflow definitions from Redis
            await self._load_workflow_definitions()
            
            self.initialized = True
            logger.info("Workflow engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow engine: {e}")
            return False
    
    async def register_workflow_definition(self, workflow_def: WorkflowDefinition) -> bool:
        """Register a workflow definition.
        
        Args:
            workflow_def: Workflow definition to register
            
        Returns:
            True if registered successfully
        """
        try:
            # Validate workflow definition
            if not await self._validate_workflow_definition(workflow_def):
                return False
            
            # Store in memory
            self._workflow_definitions[workflow_def.workflow_id] = workflow_def
            
            # Persist to Redis
            await self._save_workflow_definition(workflow_def)
            
            logger.info(f"Registered workflow definition: {workflow_def.workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering workflow definition: {e}")
            return False
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        project_id: Optional[str] = None,
        execution_id: Optional[str] = None
    ) -> WorkflowResult:
        """Execute a workflow.
        
        Args:
            workflow_id: ID of workflow to execute
            input_data: Input data for the workflow
            project_id: Optional project identifier
            execution_id: Optional custom execution ID
            
        Returns:
            WorkflowResult with execution results
        """
        execution_id = execution_id or str(uuid.uuid4())
        
        try:
            # Get workflow definition
            workflow_def = self._workflow_definitions.get(workflow_id)
            if not workflow_def:
                return WorkflowResult(
                    success=False,
                    workflow_execution=WorkflowExecution(
                        execution_id=execution_id,
                        workflow_id=workflow_id,
                        state=WorkflowState.FAILED,
                        started_at=datetime.utcnow(),
                        input_data=input_data,
                        project_id=project_id
                    ),
                    error_message=f"Workflow definition not found: {workflow_id}"
                )
            
            # Acquire execution semaphore
            async with self._execution_semaphore:
                return await self._execute_workflow_internal(
                    workflow_def,
                    input_data,
                    project_id,
                    execution_id
                )
                
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            return WorkflowResult(
                success=False,
                workflow_execution=WorkflowExecution(
                    execution_id=execution_id,
                    workflow_id=workflow_id,
                    state=WorkflowState.FAILED,
                    started_at=datetime.utcnow(),
                    input_data=input_data,
                    project_id=project_id,
                    error_message=str(e)
                ),
                error_message=str(e)
            )
    
    async def register_step_handler(
        self,
        action_name: str,
        handler: Callable
    ) -> bool:
        """Register a handler for a workflow step action.
        
        Args:
            action_name: Name of the action
            handler: Async callable to handle the action
            
        Returns:
            True if registered successfully
        """
        try:
            self._step_handlers[action_name] = handler
            logger.debug(f"Registered step handler: {action_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering step handler {action_name}: {e}")
            return False
    
    async def get_workflow_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition by ID.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            WorkflowDefinition or None if not found
        """
        return self._workflow_definitions.get(workflow_id)
    
    async def get_active_executions(self) -> List[WorkflowExecution]:
        """Get list of currently active workflow executions.
        
        Returns:
            List of active WorkflowExecution objects
        """
        return list(self._active_executions.values())
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a workflow execution.
        
        Args:
            execution_id: Execution to cancel
            
        Returns:
            True if cancelled successfully
        """
        try:
            execution = self._active_executions.get(execution_id)
            if execution:
                execution.state = WorkflowState.CANCELLED
                execution.completed_at = datetime.utcnow()
                execution.error_message = "Execution cancelled"
                
                # Remove from active executions
                del self._active_executions[execution_id]
                
                logger.info(f"Cancelled workflow execution: {execution_id}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling execution {execution_id}: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup workflow engine resources."""
        try:
            # Cancel all active executions
            for execution_id in list(self._active_executions.keys()):
                await self.cancel_execution(execution_id)
            
            self._workflow_definitions.clear()
            self._step_handlers.clear()
            self.initialized = False
            
            logger.info("Workflow engine cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Private implementation methods
    
    async def _execute_workflow_internal(
        self,
        workflow_def: WorkflowDefinition,
        input_data: Dict[str, Any],
        project_id: Optional[str],
        execution_id: str
    ) -> WorkflowResult:
        """Internal workflow execution logic."""
        start_time = datetime.utcnow()
        
        # Create execution state
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_def.workflow_id,
            state=WorkflowState.RUNNING,
            started_at=start_time,
            input_data=input_data,
            project_id=project_id
        )
        
        # Add to active executions
        self._active_executions[execution_id] = execution
        
        try:
            # Execute workflow steps
            success = await self._execute_workflow_steps(workflow_def, execution)
            
            # Update final state
            execution.completed_at = datetime.utcnow()
            execution.state = WorkflowState.COMPLETED if success else WorkflowState.FAILED
            
            # Calculate total execution time
            total_time = (execution.completed_at - start_time).total_seconds()
            
            return WorkflowResult(
                success=success,
                workflow_execution=execution,
                error_message=execution.error_message,
                total_execution_time_seconds=total_time
            )
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            execution.state = WorkflowState.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            
            return WorkflowResult(
                success=False,
                workflow_execution=execution,
                error_message=str(e)
            )
            
        finally:
            # Remove from active executions
            if execution_id in self._active_executions:
                del self._active_executions[execution_id]
    
    async def _execute_workflow_steps(
        self,
        workflow_def: WorkflowDefinition,
        execution: WorkflowExecution
    ) -> bool:
        """Execute all steps in a workflow."""
        try:
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(workflow_def.steps)
            
            # Execute steps in dependency order
            completed_steps = set()
            
            while len(completed_steps) < len(dependency_graph):
                # Find steps ready to execute
                ready_steps = []
                
                for step_item in workflow_def.steps:
                    if isinstance(step_item, ParallelExecutionGroup):
                        # Handle parallel group
                        if step_item.group_id not in completed_steps:
                            # Check if dependencies are met
                            if self._dependencies_satisfied(step_item, completed_steps, dependency_graph):
                                ready_steps.append(step_item)
                    else:
                        # Handle individual step
                        if step_item.step_id not in completed_steps:
                            if self._dependencies_satisfied(step_item, completed_steps, dependency_graph):
                                ready_steps.append(step_item)
                
                if not ready_steps:
                    # No steps ready - check for circular dependencies
                    remaining_steps = len(dependency_graph) - len(completed_steps)
                    if remaining_steps > 0:
                        execution.error_message = "Circular dependency detected or unmet dependencies"
                        return False
                    break
                
                # Execute ready steps
                for step_item in ready_steps:
                    if isinstance(step_item, ParallelExecutionGroup):
                        success = await self._execute_parallel_group(step_item, execution)
                        if success:
                            completed_steps.add(step_item.group_id)
                        else:
                            return False
                    else:
                        success = await self._execute_single_step(step_item, execution)
                        if success:
                            completed_steps.add(step_item.step_id)
                        else:
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing workflow steps: {e}")
            execution.error_message = str(e)
            return False
    
    async def _execute_single_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> bool:
        """Execute a single workflow step."""
        step_start_time = asyncio.get_event_loop().time()
        
        try:
            execution.current_step = step.step_id
            
            # Get step handler
            handler = self._step_handlers.get(step.action)
            if not handler:
                error_msg = f"No handler registered for action: {step.action}"
                execution.step_results[step.step_id] = StepResult(
                    success=False,
                    error=error_msg
                )
                execution.error_message = error_msg
                return False
            
            # Execute with retry logic
            retry_count = 0
            max_retries = step.retry_policy.max_retries if step.retry_policy else 0
            
            while retry_count <= max_retries:
                try:
                    # Execute step with timeout
                    result = await asyncio.wait_for(
                        handler(**step.parameters, **execution.input_data),
                        timeout=step.timeout_seconds
                    )
                    
                    # Calculate execution time
                    execution_time = asyncio.get_event_loop().time() - step_start_time
                    
                    # Handle result
                    if isinstance(result, StepResult):
                        result.execution_time_seconds = execution_time
                        result.retry_count = retry_count
                        execution.step_results[step.step_id] = result
                        return result.success
                    else:
                        # Convert dict result to StepResult
                        step_result = StepResult(
                            success=True,
                            output=result if isinstance(result, dict) else {"result": result},
                            execution_time_seconds=execution_time,
                            retry_count=retry_count
                        )
                        execution.step_results[step.step_id] = step_result
                        return True
                        
                except asyncio.TimeoutError:
                    error_msg = f"Step {step.step_id} timed out after {step.timeout_seconds} seconds"
                    if retry_count >= max_retries:
                        execution.step_results[step.step_id] = StepResult(
                            success=False,
                            error=error_msg,
                            retry_count=retry_count
                        )
                        return False
                    retry_count += 1
                    
                except Exception as step_error:
                    if retry_count >= max_retries:
                        execution_time = asyncio.get_event_loop().time() - step_start_time
                        execution.step_results[step.step_id] = StepResult(
                            success=False,
                            error=str(step_error),
                            execution_time_seconds=execution_time,
                            retry_count=retry_count
                        )
                        return False
                    retry_count += 1
                    
                    # Wait before retry
                    if step.retry_policy:
                        delay = step.retry_policy.delay_seconds
                        if step.retry_policy.exponential_backoff:
                            delay = min(delay * (2 ** retry_count), step.retry_policy.max_delay_seconds)
                        await asyncio.sleep(delay)
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing step {step.step_id}: {e}")
            execution_time = asyncio.get_event_loop().time() - step_start_time
            execution.step_results[step.step_id] = StepResult(
                success=False,
                error=str(e),
                execution_time_seconds=execution_time
            )
            return False
    
    async def _execute_parallel_group(
        self,
        group: ParallelExecutionGroup,
        execution: WorkflowExecution
    ) -> bool:
        """Execute a group of steps in parallel."""
        try:
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(group.max_concurrent)
            
            async def execute_step_with_semaphore(step):
                async with semaphore:
                    return await self._execute_single_step(step, execution)
            
            # Execute all steps in parallel
            tasks = [
                execute_step_with_semaphore(step)
                for step in group.steps
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            all_successful = True
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    all_successful = False
                    step_id = group.steps[i].step_id
                    execution.step_results[step_id] = StepResult(
                        success=False,
                        error=str(result)
                    )
                    if group.fail_fast:
                        break
                elif not result:
                    all_successful = False
                    if group.fail_fast:
                        break
            
            return all_successful
            
        except Exception as e:
            logger.error(f"Error executing parallel group {group.group_id}: {e}")
            return False
    
    def _build_dependency_graph(self, steps: List[Union[WorkflowStep, ParallelExecutionGroup]]) -> Dict[str, List[str]]:
        """Build dependency graph from workflow steps."""
        graph = {}
        
        for step_item in steps:
            if isinstance(step_item, ParallelExecutionGroup):
                # For parallel groups, dependencies are handled at the group level
                graph[step_item.group_id] = []
            else:
                graph[step_item.step_id] = step_item.depends_on.copy()
        
        return graph
    
    def _dependencies_satisfied(
        self,
        step_item: Union[WorkflowStep, ParallelExecutionGroup],
        completed_steps: set,
        dependency_graph: Dict[str, List[str]]
    ) -> bool:
        """Check if step dependencies are satisfied."""
        if isinstance(step_item, ParallelExecutionGroup):
            step_id = step_item.group_id
        else:
            step_id = step_item.step_id
        
        dependencies = dependency_graph.get(step_id, [])
        return all(dep in completed_steps for dep in dependencies)
    
    async def _validate_workflow_definition(self, workflow_def: WorkflowDefinition) -> bool:
        """Validate workflow definition."""
        try:
            # Check for duplicate step IDs
            step_ids = set()
            for step_item in workflow_def.steps:
                if isinstance(step_item, ParallelExecutionGroup):
                    if step_item.group_id in step_ids:
                        logger.error(f"Duplicate step ID: {step_item.group_id}")
                        return False
                    step_ids.add(step_item.group_id)
                    
                    # Check parallel group steps
                    for sub_step in step_item.steps:
                        if sub_step.step_id in step_ids:
                            logger.error(f"Duplicate step ID: {sub_step.step_id}")
                            return False
                        step_ids.add(sub_step.step_id)
                else:
                    if step_item.step_id in step_ids:
                        logger.error(f"Duplicate step ID: {step_item.step_id}")
                        return False
                    step_ids.add(step_item.step_id)
            
            # Check for circular dependencies (simplified check)
            # In a complete implementation, would use proper topological sort
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating workflow definition: {e}")
            return False
    
    async def _save_workflow_definition(self, workflow_def: WorkflowDefinition):
        """Save workflow definition to Redis."""
        try:
            key = f"workflow_def:{workflow_def.workflow_id}"
            data = json.dumps(asdict(workflow_def), default=str)
            await self.redis_manager.set(key, data)
            
        except Exception as e:
            logger.error(f"Error saving workflow definition: {e}")
    
    async def _load_workflow_definitions(self):
        """Load workflow definitions from Redis."""
        try:
            # In a complete implementation, would load from Redis
            # For now, this is a placeholder
            pass
            
        except Exception as e:
            logger.error(f"Error loading workflow definitions: {e}")