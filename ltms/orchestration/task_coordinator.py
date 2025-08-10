"""Task Coordinator - Component 5 (Advanced Task Orchestration) - Phase 2.

This module provides advanced task coordination capabilities including:
- Multi-step task management with dependencies
- Inter-task communication and data flow
- Progress monitoring and status updates
- Integration with WorkflowEngine for complex orchestration
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum

from ltms.services.redis_service import RedisConnectionManager
from ltms.models.task_blueprint import TaskPriority

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of coordination tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class TaskDependency:
    """Dependency between coordination tasks."""
    task_id: str
    dependency_type: str = "blocks"  # blocks, data, notification


@dataclass
class ExecutionContext:
    """Context for task coordination execution."""
    coordinator_id: str
    project_id: str
    initiated_by: str
    initiated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationTask:
    """Individual task in a coordination workflow."""
    task_id: str
    name: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[TaskDependency] = field(default_factory=list)
    estimated_duration_minutes: Optional[int] = None
    timeout_minutes: int = 60
    retry_count: int = 0
    max_retries: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TaskProgress:
    """Progress information for a coordination task."""
    task_id: str
    status: TaskStatus
    progress_percentage: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationResult:
    """Result of task coordination execution."""
    success: bool
    execution_context: ExecutionContext
    task_results: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    total_execution_time_seconds: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_skipped: int = 0


class TaskCoordinator:
    """Advanced task coordination service."""
    
    def __init__(
        self,
        redis_manager: RedisConnectionManager,
        max_concurrent_tasks: int = 10,
        progress_update_interval: int = 5
    ):
        """Initialize task coordinator.
        
        Args:
            redis_manager: Redis connection manager
            max_concurrent_tasks: Maximum concurrent task executions
            progress_update_interval: Progress update interval in seconds
        """
        self.redis_manager = redis_manager
        self.max_concurrent_tasks = max_concurrent_tasks
        self.progress_update_interval = progress_update_interval
        self.initialized = False
        
        # Task handlers
        self._task_handlers: Dict[str, Callable] = {}
        
        # Active coordinations
        self._active_coordinations: Dict[str, ExecutionContext] = {}
        
        # Task progress tracking
        self._task_progress: Dict[str, TaskProgress] = {}
        
        # Coordination graph for dependency management
        self._coordination_graph: Dict[str, Set[str]] = {}
        
        # Concurrency control
        self._task_semaphore: Optional[asyncio.Semaphore] = None
    
    async def initialize(self) -> bool:
        """Initialize the task coordinator.
        
        Returns:
            True if initialized successfully
        """
        try:
            if self.initialized:
                return True
            
            # Initialize concurrency control
            self._task_semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
            
            # Verify Redis connection
            if not await self.redis_manager.ping():
                logger.error("Redis connection failed during task coordinator initialization")
                return False
            
            self.initialized = True
            logger.info("Task coordinator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize task coordinator: {e}")
            return False
    
    async def coordinate_tasks(
        self,
        tasks: List[CoordinationTask],
        project_id: str,
        execution_context: ExecutionContext
    ) -> CoordinationResult:
        """Coordinate execution of multiple tasks with dependencies.
        
        Args:
            tasks: List of tasks to coordinate
            project_id: Project identifier
            execution_context: Execution context
            
        Returns:
            CoordinationResult with execution results
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Register coordination
            coord_id = str(uuid.uuid4())
            self._active_coordinations[coord_id] = execution_context
            
            # Initialize task progress
            for task in tasks:
                self._task_progress[task.task_id] = TaskProgress(
                    task_id=task.task_id,
                    status=TaskStatus.PENDING
                )
            
            # Build dependency graph
            dependency_graph = self._build_task_dependency_graph(tasks)
            
            # Execute tasks in dependency order
            task_results = []
            completed_tasks = set()
            failed_tasks = set()
            skipped_tasks = set()
            
            # Track execution metrics
            tasks_completed = 0
            tasks_failed = 0
            tasks_skipped = 0
            
            while len(completed_tasks) + len(failed_tasks) + len(skipped_tasks) < len(tasks):
                # Find tasks ready to execute
                ready_tasks = []
                
                for task in tasks:
                    if (task.task_id not in completed_tasks and
                        task.task_id not in failed_tasks and
                        task.task_id not in skipped_tasks):
                        
                        # Check if dependencies are satisfied
                        if self._task_dependencies_satisfied(task, completed_tasks, dependency_graph):
                            ready_tasks.append(task)
                
                if not ready_tasks:
                    # No tasks ready - check for circular dependencies or failures
                    remaining_tasks = len(tasks) - len(completed_tasks) - len(failed_tasks) - len(skipped_tasks)
                    if remaining_tasks > 0:
                        # Mark remaining tasks as skipped due to failed dependencies
                        for task in tasks:
                            if (task.task_id not in completed_tasks and
                                task.task_id not in failed_tasks and
                                task.task_id not in skipped_tasks):
                                
                                skipped_tasks.add(task.task_id)
                                self._task_progress[task.task_id].status = TaskStatus.SKIPPED
                                tasks_skipped += 1
                    break
                
                # Execute ready tasks in parallel
                if len(ready_tasks) == 1:
                    # Single task execution
                    task = ready_tasks[0]
                    result = await self._execute_coordination_task(task, execution_context)
                    task_results.append(result)
                    
                    if result.get("success", False):
                        completed_tasks.add(task.task_id)
                        tasks_completed += 1
                    else:
                        failed_tasks.add(task.task_id)
                        tasks_failed += 1
                        
                        # Check if other tasks depend on this failed task
                        await self._handle_task_failure(task, tasks, dependency_graph, skipped_tasks)
                        tasks_skipped += len(skipped_tasks) - tasks_skipped - tasks_completed - tasks_failed
                else:
                    # Parallel task execution
                    parallel_tasks = [
                        self._execute_coordination_task(task, execution_context)
                        for task in ready_tasks
                    ]
                    
                    parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
                    
                    for i, result in enumerate(parallel_results):
                        task = ready_tasks[i]
                        
                        if isinstance(result, Exception):
                            task_result = {
                                "task_id": task.task_id,
                                "success": False,
                                "error": str(result)
                            }
                            failed_tasks.add(task.task_id)
                            tasks_failed += 1
                            await self._handle_task_failure(task, tasks, dependency_graph, skipped_tasks)
                        else:
                            task_result = result
                            if task_result.get("success", False):
                                completed_tasks.add(task.task_id)
                                tasks_completed += 1
                            else:
                                failed_tasks.add(task.task_id)
                                tasks_failed += 1
                                await self._handle_task_failure(task, tasks, dependency_graph, skipped_tasks)
                        
                        task_results.append(task_result)
            
            # Calculate final metrics
            end_time = asyncio.get_event_loop().time()
            total_time = end_time - start_time
            
            # Determine overall success
            overall_success = tasks_failed == 0 and len(completed_tasks) > 0
            
            result = CoordinationResult(
                success=overall_success,
                execution_context=execution_context,
                task_results=task_results,
                total_execution_time_seconds=total_time,
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                tasks_skipped=len(skipped_tasks)
            )
            
            if not overall_success and tasks_failed > 0:
                failed_task_names = [task.name for task in tasks if task.task_id in failed_tasks]
                result.error_message = f"Tasks failed: {', '.join(failed_task_names)}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in task coordination: {e}")
            end_time = asyncio.get_event_loop().time()
            return CoordinationResult(
                success=False,
                execution_context=execution_context,
                error_message=str(e),
                total_execution_time_seconds=end_time - start_time
            )
            
        finally:
            # Cleanup coordination
            if coord_id in self._active_coordinations:
                del self._active_coordinations[coord_id]
    
    async def register_task_handler(
        self,
        action_name: str,
        handler: Callable
    ) -> bool:
        """Register a handler for a coordination task action.
        
        Args:
            action_name: Name of the action
            handler: Async callable to handle the action
            
        Returns:
            True if registered successfully
        """
        try:
            self._task_handlers[action_name] = handler
            logger.debug(f"Registered task handler: {action_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering task handler {action_name}: {e}")
            return False
    
    async def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get progress for a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskProgress or None if not found
        """
        return self._task_progress.get(task_id)
    
    async def update_task_progress(
        self,
        task_id: str,
        progress_percentage: float,
        current_stage: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update progress for a task.
        
        Args:
            task_id: Task identifier
            progress_percentage: Progress percentage (0.0 to 1.0)
            current_stage: Optional current stage description
            result_data: Optional result data
            
        Returns:
            True if updated successfully
        """
        try:
            progress = self._task_progress.get(task_id)
            if progress:
                progress.progress_percentage = progress_percentage
                if current_stage:
                    progress.current_stage = current_stage
                if result_data:
                    progress.result_data.update(result_data)
                
                # Persist progress update to Redis
                await self._persist_task_progress(progress)
                
                logger.debug(f"Updated task progress for {task_id}: {progress_percentage:.1%}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating task progress: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup task coordinator resources."""
        try:
            # Cancel all active coordinations
            for coord_id in list(self._active_coordinations.keys()):
                del self._active_coordinations[coord_id]
            
            self._task_handlers.clear()
            self._task_progress.clear()
            self._coordination_graph.clear()
            
            self.initialized = False
            logger.info("Task coordinator cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Private implementation methods
    
    async def _execute_coordination_task(
        self,
        task: CoordinationTask,
        execution_context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a single coordination task."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Update task progress
            progress = self._task_progress[task.task_id]
            progress.status = TaskStatus.RUNNING
            progress.started_at = datetime.utcnow()
            
            # Get task handler
            handler = self._task_handlers.get(task.action)
            if not handler:
                error_msg = f"No handler registered for action: {task.action}"
                progress.status = TaskStatus.FAILED
                progress.error_message = error_msg
                return {
                    "task_id": task.task_id,
                    "success": False,
                    "error": error_msg
                }
            
            # Execute task with concurrency control
            async with self._task_semaphore:
                # Execute with timeout
                timeout_seconds = task.timeout_minutes * 60
                
                try:
                    result = await asyncio.wait_for(
                        handler(**task.parameters),
                        timeout=timeout_seconds
                    )
                    
                    # Update progress on success
                    progress.status = TaskStatus.COMPLETED
                    progress.completed_at = datetime.utcnow()
                    progress.progress_percentage = 1.0
                    
                    execution_time = asyncio.get_event_loop().time() - start_time
                    
                    task_result = {
                        "task_id": task.task_id,
                        "success": True,
                        "result": result,
                        "execution_time_seconds": execution_time
                    }
                    
                    # Store result data
                    if isinstance(result, dict):
                        progress.result_data.update(result)
                    
                    return task_result
                    
                except asyncio.TimeoutError:
                    error_msg = f"Task {task.task_id} timed out after {timeout_seconds} seconds"
                    progress.status = TaskStatus.FAILED
                    progress.error_message = error_msg
                    return {
                        "task_id": task.task_id,
                        "success": False,
                        "error": error_msg
                    }
                    
                except Exception as task_error:
                    error_msg = str(task_error)
                    progress.status = TaskStatus.FAILED
                    progress.error_message = error_msg
                    
                    # Consider retry logic
                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count})")
                        await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
                        return await self._execute_coordination_task(task, execution_context)
                    
                    return {
                        "task_id": task.task_id,
                        "success": False,
                        "error": error_msg,
                        "retry_count": task.retry_count
                    }
                    
        except Exception as e:
            logger.error(f"Error executing coordination task {task.task_id}: {e}")
            progress = self._task_progress[task.task_id]
            progress.status = TaskStatus.FAILED
            progress.error_message = str(e)
            
            return {
                "task_id": task.task_id,
                "success": False,
                "error": str(e)
            }
    
    def _build_task_dependency_graph(self, tasks: List[CoordinationTask]) -> Dict[str, Set[str]]:
        """Build task dependency graph."""
        graph = {}
        
        for task in tasks:
            dependencies = set()
            for dep in task.dependencies:
                if dep.dependency_type == "blocks":
                    dependencies.add(dep.task_id)
            graph[task.task_id] = dependencies
        
        return graph
    
    def _task_dependencies_satisfied(
        self,
        task: CoordinationTask,
        completed_tasks: Set[str],
        dependency_graph: Dict[str, Set[str]]
    ) -> bool:
        """Check if task dependencies are satisfied."""
        dependencies = dependency_graph.get(task.task_id, set())
        return dependencies.issubset(completed_tasks)
    
    async def _handle_task_failure(
        self,
        failed_task: CoordinationTask,
        all_tasks: List[CoordinationTask],
        dependency_graph: Dict[str, Set[str]],
        skipped_tasks: Set[str]
    ):
        """Handle task failure and mark dependent tasks as skipped."""
        try:
            # Find tasks that depend on the failed task
            for task in all_tasks:
                dependencies = dependency_graph.get(task.task_id, set())
                if failed_task.task_id in dependencies and task.task_id not in skipped_tasks:
                    skipped_tasks.add(task.task_id)
                    progress = self._task_progress.get(task.task_id)
                    if progress:
                        progress.status = TaskStatus.SKIPPED
                        progress.error_message = f"Skipped due to failed dependency: {failed_task.task_id}"
                    
                    # Recursively skip tasks that depend on this skipped task
                    await self._handle_task_failure(task, all_tasks, dependency_graph, skipped_tasks)
                    
        except Exception as e:
            logger.error(f"Error handling task failure: {e}")
    
    async def _persist_task_progress(self, progress: TaskProgress):
        """Persist task progress to Redis."""
        try:
            key = f"task_progress:{progress.task_id}"
            data = json.dumps(asdict(progress), default=str)
            await self.redis_manager.setex(key, 3600, data)  # 1 hour TTL
            
        except Exception as e:
            logger.error(f"Error persisting task progress: {e}")
    
    async def _load_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Load task progress from Redis."""
        try:
            key = f"task_progress:{task_id}"
            data = await self.redis_manager.get(key)
            if data:
                progress_dict = json.loads(data)
                return TaskProgress(**progress_dict)
            return None
            
        except Exception as e:
            logger.error(f"Error loading task progress: {e}")
            return None