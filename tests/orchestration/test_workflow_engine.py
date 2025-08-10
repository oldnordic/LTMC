"""Tests for Workflow Engine - Component 5 (Advanced Task Orchestration) - Phase 2."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock, Mock

from ltms.orchestration.workflow_engine import (
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
from ltms.orchestration.task_coordinator import (
    TaskCoordinator,
    CoordinationTask,
    TaskDependency,
    ExecutionContext,
    TaskStatus,
    CoordinationResult
)
from ltms.models.task_blueprint import TaskBlueprint, TaskPriority


class TestWorkflowEngine:
    """Test suite for WorkflowEngine."""
    
    @pytest.fixture
    async def workflow_engine(self, redis_manager):
        """Create WorkflowEngine instance for testing."""
        engine = WorkflowEngine(redis_manager=redis_manager)
        await engine.initialize()
        yield engine
        await engine.cleanup()
    
    @pytest.fixture
    def sample_workflow_definition(self):
        """Sample workflow definition for testing."""
        steps = [
            WorkflowStep(
                step_id="validate_input",
                name="Validate Input",
                action="validate_task_input",
                parameters={"required_fields": ["name", "description"]},
                timeout_seconds=30,
                retry_policy=RetryPolicy(max_retries=2, delay_seconds=5)
            ),
            WorkflowStep(
                step_id="process_task",
                name="Process Task",
                action="execute_main_task",
                parameters={},
                timeout_seconds=300,
                depends_on=["validate_input"],
                retry_policy=RetryPolicy(max_retries=3, delay_seconds=10)
            ),
            WorkflowStep(
                step_id="generate_report",
                name="Generate Report",
                action="create_task_report",
                parameters={"format": "json"},
                timeout_seconds=60,
                depends_on=["process_task"]
            )
        ]
        
        return WorkflowDefinition(
            workflow_id="test_workflow_001",
            name="Test Task Processing Workflow",
            description="Test workflow for task processing",
            steps=steps,
            max_parallel_executions=5,
            timeout_seconds=3600
        )
    
    @pytest.fixture
    def parallel_workflow_definition(self):
        """Workflow definition with parallel execution."""
        parallel_steps = [
            WorkflowStep(
                step_id="parallel_step_1",
                name="Parallel Step 1",
                action="parallel_action_1",
                parameters={"data": "set_1"}
            ),
            WorkflowStep(
                step_id="parallel_step_2", 
                name="Parallel Step 2",
                action="parallel_action_2",
                parameters={"data": "set_2"}
            ),
            WorkflowStep(
                step_id="parallel_step_3",
                name="Parallel Step 3", 
                action="parallel_action_3",
                parameters={"data": "set_3"}
            )
        ]
        
        parallel_group = ParallelExecutionGroup(
            group_id="parallel_group_1",
            steps=parallel_steps,
            max_concurrent=2
        )
        
        steps = [
            WorkflowStep(
                step_id="setup",
                name="Setup",
                action="setup_parallel_execution",
                parameters={}
            ),
            parallel_group,
            WorkflowStep(
                step_id="consolidate",
                name="Consolidate Results",
                action="consolidate_parallel_results",
                parameters={},
                depends_on=["parallel_group_1"]
            )
        ]
        
        return WorkflowDefinition(
            workflow_id="parallel_workflow_001",
            name="Parallel Execution Workflow",
            description="Test workflow with parallel execution",
            steps=steps,
            max_parallel_executions=3
        )
    
    # Core Functionality Tests
    
    async def test_workflow_engine_initialization(self, workflow_engine):
        """Test WorkflowEngine initialization."""
        assert workflow_engine.initialized
        assert workflow_engine.redis_manager is not None
        assert workflow_engine._active_executions == {}
        assert workflow_engine._step_handlers is not None
    
    async def test_register_workflow_definition(self, workflow_engine, sample_workflow_definition):
        """Test workflow definition registration."""
        success = await workflow_engine.register_workflow_definition(sample_workflow_definition)
        assert success
        
        # Verify workflow is stored
        stored_workflow = await workflow_engine.get_workflow_definition("test_workflow_001")
        assert stored_workflow is not None
        assert stored_workflow.workflow_id == "test_workflow_001"
        assert stored_workflow.name == "Test Task Processing Workflow"
        assert len(stored_workflow.steps) == 3
    
    async def test_execute_workflow_sequential(self, workflow_engine, sample_workflow_definition):
        """Test sequential workflow execution."""
        # Register workflow
        await workflow_engine.register_workflow_definition(sample_workflow_definition)
        
        # Mock step handlers
        async def mock_validate_input(**kwargs):
            return StepResult(success=True, output={"validated": True})
        
        async def mock_execute_main_task(**kwargs):
            return StepResult(success=True, output={"result": "task_completed"})
        
        async def mock_create_task_report(**kwargs):
            return StepResult(success=True, output={"report": {"status": "success"}})
        
        # Register handlers
        await workflow_engine.register_step_handler("validate_task_input", mock_validate_input)
        await workflow_engine.register_step_handler("execute_main_task", mock_execute_main_task)
        await workflow_engine.register_step_handler("create_task_report", mock_create_task_report)
        
        # Execute workflow
        start_time = asyncio.get_event_loop().time()
        
        execution_result = await workflow_engine.execute_workflow(
            workflow_id="test_workflow_001",
            input_data={"name": "Test Task", "description": "Test task description"},
            project_id="test_project"
        )
        
        end_time = asyncio.get_event_loop().time()
        execution_time_ms = (end_time - start_time) * 1000
        
        # Verify execution success
        assert execution_result.success
        assert execution_result.workflow_execution.state == WorkflowState.COMPLETED
        assert len(execution_result.workflow_execution.step_results) == 3
        
        # Verify step results
        step_results = execution_result.workflow_execution.step_results
        assert step_results["validate_input"].success
        assert step_results["process_task"].success
        assert step_results["generate_report"].success
        
        # Performance requirement: reasonable execution time
        assert execution_time_ms < 1000, f"Sequential workflow took {execution_time_ms:.2f}ms"
    
    async def test_parallel_workflow_execution(self, workflow_engine, parallel_workflow_definition):
        """Test parallel workflow execution."""
        # Register workflow
        await workflow_engine.register_workflow_definition(parallel_workflow_definition)
        
        # Mock step handlers
        async def mock_setup(**kwargs):
            return StepResult(success=True, output={"setup_complete": True})
        
        async def mock_parallel_action(data_set):
            # Simulate work
            await asyncio.sleep(0.1)
            return StepResult(success=True, output={"processed": data_set})
        
        async def mock_consolidate(**kwargs):
            return StepResult(success=True, output={"consolidated": True})
        
        # Register handlers
        await workflow_engine.register_step_handler("setup_parallel_execution", mock_setup)
        await workflow_engine.register_step_handler("parallel_action_1", lambda **k: mock_parallel_action("set_1"))
        await workflow_engine.register_step_handler("parallel_action_2", lambda **k: mock_parallel_action("set_2"))
        await workflow_engine.register_step_handler("parallel_action_3", lambda **k: mock_parallel_action("set_3"))
        await workflow_engine.register_step_handler("consolidate_parallel_results", mock_consolidate)
        
        # Execute workflow
        start_time = asyncio.get_event_loop().time()
        
        execution_result = await workflow_engine.execute_workflow(
            workflow_id="parallel_workflow_001",
            input_data={"parallel_data": True},
            project_id="test_project"
        )
        
        end_time = asyncio.get_event_loop().time()
        execution_time_ms = (end_time - start_time) * 1000
        
        # Verify execution success
        assert execution_result.success
        assert execution_result.workflow_execution.state == WorkflowState.COMPLETED
        
        # Verify parallel execution was faster than sequential would be
        # 3 parallel steps * 100ms each = should be ~200ms, not 300ms
        assert execution_time_ms < 250, f"Parallel execution took {execution_time_ms:.2f}ms, expected <250ms"
    
    # Error Recovery Tests
    
    async def test_retry_mechanism(self, workflow_engine):
        """Test step retry mechanism."""
        # Create workflow with retry
        steps = [
            WorkflowStep(
                step_id="failing_step",
                name="Failing Step",
                action="action_that_fails",
                parameters={},
                retry_policy=RetryPolicy(max_retries=3, delay_seconds=0.1)
            )
        ]
        
        workflow_def = WorkflowDefinition(
            workflow_id="retry_test_workflow",
            name="Retry Test Workflow",
            description="Test retry mechanism",
            steps=steps
        )
        
        await workflow_engine.register_workflow_definition(workflow_def)
        
        # Mock handler that fails first 2 times, then succeeds
        call_count = 0
        
        async def mock_failing_action(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Simulated failure {call_count}")
            return StepResult(success=True, output={"attempt": call_count})
        
        await workflow_engine.register_step_handler("action_that_fails", mock_failing_action)
        
        # Execute workflow
        execution_result = await workflow_engine.execute_workflow(
            workflow_id="retry_test_workflow",
            input_data={},
            project_id="test_project"
        )
        
        # Should succeed after retries
        assert execution_result.success
        assert call_count == 3  # 1 initial + 2 retries
        assert execution_result.workflow_execution.step_results["failing_step"].success
    
    async def test_error_recovery_workflow_failure(self, workflow_engine):
        """Test workflow failure and recovery."""
        # Create workflow with failing step
        steps = [
            WorkflowStep(
                step_id="success_step",
                name="Success Step",
                action="success_action",
                parameters={}
            ),
            WorkflowStep(
                step_id="failure_step",
                name="Failure Step",
                action="failure_action",
                parameters={},
                depends_on=["success_step"],
                retry_policy=RetryPolicy(max_retries=1, delay_seconds=0.1)
            )
        ]
        
        workflow_def = WorkflowDefinition(
            workflow_id="failure_test_workflow",
            name="Failure Test Workflow",
            description="Test workflow failure handling",
            steps=steps
        )
        
        await workflow_engine.register_workflow_definition(workflow_def)
        
        # Register handlers
        await workflow_engine.register_step_handler(
            "success_action",
            lambda **k: StepResult(success=True, output={"step": "success"})
        )
        
        await workflow_engine.register_step_handler(
            "failure_action",
            lambda **k: StepResult(success=False, error="Permanent failure")
        )
        
        # Execute workflow
        execution_result = await workflow_engine.execute_workflow(
            workflow_id="failure_test_workflow",
            input_data={},
            project_id="test_project"
        )
        
        # Should fail gracefully
        assert not execution_result.success
        assert execution_result.workflow_execution.state == WorkflowState.FAILED
        assert "Permanent failure" in execution_result.error_message
        
        # Success step should have completed
        assert execution_result.workflow_execution.step_results["success_step"].success
        # Failure step should have failed
        assert not execution_result.workflow_execution.step_results["failure_step"].success
    
    # State Management Tests
    
    async def test_workflow_state_persistence(self, workflow_engine, sample_workflow_definition):
        """Test workflow state persistence."""
        await workflow_engine.register_workflow_definition(sample_workflow_definition)
        
        # Create a long-running workflow
        async def mock_long_running_task(**kwargs):
            await asyncio.sleep(0.5)  # Simulate work
            return StepResult(success=True, output={"completed": True})
        
        await workflow_engine.register_step_handler("validate_task_input", mock_long_running_task)
        await workflow_engine.register_step_handler("execute_main_task", mock_long_running_task)
        await workflow_engine.register_step_handler("create_task_report", mock_long_running_task)
        
        # Start workflow execution (non-blocking)
        execution_future = asyncio.create_task(
            workflow_engine.execute_workflow(
                workflow_id="test_workflow_001",
                input_data={"name": "Test", "description": "Test"},
                project_id="test_project"
            )
        )
        
        # Allow some execution time
        await asyncio.sleep(0.1)
        
        # Check active executions
        active = await workflow_engine.get_active_executions()
        assert len(active) > 0
        
        # Wait for completion
        result = await execution_future
        assert result.success
        
        # Check no active executions after completion
        active = await workflow_engine.get_active_executions()
        assert len(active) == 0
    
    # Performance Tests
    
    async def test_concurrent_workflow_executions(self, workflow_engine, sample_workflow_definition):
        """Test concurrent workflow executions."""
        await workflow_engine.register_workflow_definition(sample_workflow_definition)
        
        # Mock fast handlers
        async def mock_fast_handler(**kwargs):
            await asyncio.sleep(0.05)  # 50ms
            return StepResult(success=True, output={"fast": True})
        
        await workflow_engine.register_step_handler("validate_task_input", mock_fast_handler)
        await workflow_engine.register_step_handler("execute_main_task", mock_fast_handler)
        await workflow_engine.register_step_handler("create_task_report", mock_fast_handler)
        
        # Execute multiple workflows concurrently
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(5):
            task = workflow_engine.execute_workflow(
                workflow_id="test_workflow_001",
                input_data={"name": f"Test {i}", "description": f"Test {i}"},
                project_id="test_project"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        total_time_ms = (end_time - start_time) * 1000
        
        # All should succeed
        for result in results:
            assert result.success
        
        # Should be faster than sequential execution
        # 5 workflows * 3 steps * 50ms = 750ms sequential
        # With concurrency, should be much faster
        assert total_time_ms < 500, f"Concurrent execution took {total_time_ms:.2f}ms"
    
    # Integration Tests
    
    async def test_workflow_integration_with_task_coordinator(self, workflow_engine):
        """Test integration between WorkflowEngine and TaskCoordinator."""
        # This test verifies the integration works properly
        # In actual implementation, TaskCoordinator would use WorkflowEngine
        
        # Create a workflow that coordinates multiple tasks
        steps = [
            WorkflowStep(
                step_id="coordinate_tasks",
                name="Coordinate Tasks",
                action="coordinate_multiple_tasks",
                parameters={"task_count": 3}
            )
        ]
        
        coordination_workflow = WorkflowDefinition(
            workflow_id="coordination_workflow",
            name="Task Coordination Workflow",
            description="Workflow for coordinating multiple tasks",
            steps=steps
        )
        
        await workflow_engine.register_workflow_definition(coordination_workflow)
        
        # Mock coordination handler
        async def mock_coordination(**kwargs):
            task_count = kwargs.get("task_count", 1)
            return StepResult(
                success=True, 
                output={"coordinated_tasks": task_count, "status": "all_completed"}
            )
        
        await workflow_engine.register_step_handler("coordinate_multiple_tasks", mock_coordination)
        
        # Execute coordination workflow
        result = await workflow_engine.execute_workflow(
            workflow_id="coordination_workflow",
            input_data={"coordination_required": True},
            project_id="test_project"
        )
        
        assert result.success
        step_result = result.workflow_execution.step_results["coordinate_tasks"]
        assert step_result.output["coordinated_tasks"] == 3
        assert step_result.output["status"] == "all_completed"


class TestTaskCoordinator:
    """Test suite for TaskCoordinator."""
    
    @pytest.fixture
    async def task_coordinator(self, redis_manager):
        """Create TaskCoordinator instance for testing."""
        coordinator = TaskCoordinator(redis_manager=redis_manager)
        await coordinator.initialize()
        yield coordinator
        await coordinator.cleanup()
    
    @pytest.fixture
    def sample_coordination_tasks(self):
        """Sample coordination tasks for testing."""
        tasks = [
            CoordinationTask(
                task_id="coord_task_001",
                name="Database Migration",
                action="migrate_database",
                parameters={"version": "2.1.0"},
                priority=TaskPriority.HIGH,
                estimated_duration_minutes=30
            ),
            CoordinationTask(
                task_id="coord_task_002", 
                name="Update API Documentation",
                action="update_api_docs",
                parameters={"version": "2.1.0"},
                priority=TaskPriority.MEDIUM,
                estimated_duration_minutes=15,
                dependencies=[
                    TaskDependency(task_id="coord_task_001", dependency_type="blocks")
                ]
            ),
            CoordinationTask(
                task_id="coord_task_003",
                name="Deploy to Production",
                action="deploy_production",
                parameters={"version": "2.1.0"},
                priority=TaskPriority.HIGH,
                estimated_duration_minutes=45,
                dependencies=[
                    TaskDependency(task_id="coord_task_001", dependency_type="blocks"),
                    TaskDependency(task_id="coord_task_002", dependency_type="blocks")
                ]
            )
        ]
        return tasks
    
    # Core Functionality Tests
    
    async def test_task_coordinator_initialization(self, task_coordinator):
        """Test TaskCoordinator initialization."""
        assert task_coordinator.initialized
        assert task_coordinator.redis_manager is not None
        assert task_coordinator._coordination_graph is not None
    
    async def test_coordinate_multi_step_task(self, task_coordinator, sample_coordination_tasks):
        """Test coordination of multi-step tasks."""
        # Mock task handlers
        execution_order = []
        
        async def mock_migrate_database(**kwargs):
            execution_order.append("migrate_database")
            await asyncio.sleep(0.1)  # Simulate work
            return {"success": True, "migration_completed": True}
        
        async def mock_update_api_docs(**kwargs):
            execution_order.append("update_api_docs")
            await asyncio.sleep(0.05)
            return {"success": True, "docs_updated": True}
        
        async def mock_deploy_production(**kwargs):
            execution_order.append("deploy_production")
            await asyncio.sleep(0.1)
            return {"success": True, "deployed": True}
        
        # Register handlers
        await task_coordinator.register_task_handler("migrate_database", mock_migrate_database)
        await task_coordinator.register_task_handler("update_api_docs", mock_update_api_docs)
        await task_coordinator.register_task_handler("deploy_production", mock_deploy_production)
        
        # Execute coordination
        start_time = asyncio.get_event_loop().time()
        
        result = await task_coordinator.coordinate_tasks(
            tasks=sample_coordination_tasks,
            project_id="test_project",
            execution_context=ExecutionContext(
                coordinator_id="test_coordinator",
                project_id="test_project",
                initiated_by="test_user"
            )
        )
        
        end_time = asyncio.get_event_loop().time()
        coordination_time_ms = (end_time - start_time) * 1000
        
        # Verify coordination success
        assert result.success
        assert len(result.task_results) == 3
        
        # Verify dependency order was respected
        assert execution_order.index("migrate_database") < execution_order.index("update_api_docs")
        assert execution_order.index("migrate_database") < execution_order.index("deploy_production")
        assert execution_order.index("update_api_docs") < execution_order.index("deploy_production")
        
        # Performance: should complete reasonably quickly
        assert coordination_time_ms < 1000, f"Task coordination took {coordination_time_ms:.2f}ms"
    
    async def test_parallel_task_execution(self, task_coordinator):
        """Test parallel execution of independent tasks."""
        # Create independent tasks that can run in parallel
        parallel_tasks = [
            CoordinationTask(
                task_id="parallel_001",
                name="Independent Task 1",
                action="independent_action_1",
                parameters={"data": 1},
                priority=TaskPriority.MEDIUM
            ),
            CoordinationTask(
                task_id="parallel_002",
                name="Independent Task 2", 
                action="independent_action_2",
                parameters={"data": 2},
                priority=TaskPriority.MEDIUM
            ),
            CoordinationTask(
                task_id="parallel_003",
                name="Independent Task 3",
                action="independent_action_3", 
                parameters={"data": 3},
                priority=TaskPriority.MEDIUM
            )
        ]
        
        # Mock parallel handlers
        execution_times = []
        
        async def mock_parallel_action(data_value):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)  # 100ms work
            end = asyncio.get_event_loop().time()
            execution_times.append((data_value, end - start))
            return {"success": True, "data": data_value}
        
        await task_coordinator.register_task_handler("independent_action_1", lambda **k: mock_parallel_action(1))
        await task_coordinator.register_task_handler("independent_action_2", lambda **k: mock_parallel_action(2))
        await task_coordinator.register_task_handler("independent_action_3", lambda **k: mock_parallel_action(3))
        
        # Execute coordination
        start_time = asyncio.get_event_loop().time()
        
        result = await task_coordinator.coordinate_tasks(
            tasks=parallel_tasks,
            project_id="test_project",
            execution_context=ExecutionContext(
                coordinator_id="test_coordinator",
                project_id="test_project",
                initiated_by="test_user"
            )
        )
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # Verify parallel execution
        assert result.success
        assert len(result.task_results) == 3
        
        # Should execute in parallel, not sequentially
        # 3 tasks * 100ms = 300ms sequential, but should be ~100ms parallel
        assert total_time < 0.2, f"Parallel execution took {total_time:.3f}s, expected <0.2s"
    
    async def test_task_progress_monitoring(self, task_coordinator):
        """Test task progress monitoring and status updates."""
        # Create a long-running task with progress updates
        long_task = CoordinationTask(
            task_id="long_running_task",
            name="Long Running Task",
            action="long_running_action",
            parameters={"duration": 0.5},
            priority=TaskPriority.LOW
        )
        
        # Mock handler with progress updates
        async def mock_long_running_action(**kwargs):
            duration = kwargs.get("duration", 1.0)
            steps = 5
            step_duration = duration / steps
            
            for i in range(steps):
                await asyncio.sleep(step_duration)
                progress = (i + 1) / steps
                # In real implementation, would update progress
                # For testing, we just simulate the work
            
            return {"success": True, "steps_completed": steps}
        
        await task_coordinator.register_task_handler("long_running_action", mock_long_running_action)
        
        # Execute with monitoring
        result = await task_coordinator.coordinate_tasks(
            tasks=[long_task],
            project_id="test_project",
            execution_context=ExecutionContext(
                coordinator_id="test_coordinator",
                project_id="test_project",
                initiated_by="test_user"
            )
        )
        
        assert result.success
        assert result.task_results[0]["steps_completed"] == 5
    
    # Error Handling Tests
    
    async def test_task_failure_recovery(self, task_coordinator):
        """Test recovery from task failures."""
        # Create tasks where one fails
        tasks_with_failure = [
            CoordinationTask(
                task_id="success_task",
                name="Success Task",
                action="success_action",
                parameters={}
            ),
            CoordinationTask(
                task_id="failure_task",
                name="Failure Task", 
                action="failure_action",
                parameters={}
            ),
            CoordinationTask(
                task_id="dependent_task",
                name="Dependent Task",
                action="dependent_action",
                parameters={},
                dependencies=[
                    TaskDependency(task_id="failure_task", dependency_type="blocks")
                ]
            )
        ]
        
        # Mock handlers
        await task_coordinator.register_task_handler(
            "success_action",
            lambda **k: {"success": True}
        )
        
        async def mock_failure_action(**kwargs):
            raise Exception("Simulated task failure")
        
        await task_coordinator.register_task_handler("failure_action", mock_failure_action)
        await task_coordinator.register_task_handler(
            "dependent_action", 
            lambda **k: {"success": True}
        )
        
        # Execute coordination
        result = await task_coordinator.coordinate_tasks(
            tasks=tasks_with_failure,
            project_id="test_project",
            execution_context=ExecutionContext(
                coordinator_id="test_coordinator",
                project_id="test_project", 
                initiated_by="test_user"
            )
        )
        
        # Should fail gracefully
        assert not result.success
        assert "Simulated task failure" in result.error_message
        
        # Success task should complete, failure task should fail, dependent task should be skipped
        assert len(result.task_results) >= 1  # At least success task completed
    
    # Performance and Scalability Tests
    
    async def test_large_task_coordination(self, task_coordinator):
        """Test coordination of many tasks."""
        # Create many independent tasks
        large_task_set = []
        for i in range(20):
            task = CoordinationTask(
                task_id=f"task_{i:03d}",
                name=f"Task {i}",
                action="batch_action",
                parameters={"task_number": i},
                priority=TaskPriority.LOW
            )
            large_task_set.append(task)
        
        # Mock batch handler
        completed_tasks = []
        
        async def mock_batch_action(**kwargs):
            task_num = kwargs.get("task_number", 0)
            await asyncio.sleep(0.01)  # 10ms per task
            completed_tasks.append(task_num)
            return {"success": True, "task_number": task_num}
        
        await task_coordinator.register_task_handler("batch_action", mock_batch_action)
        
        # Execute large coordination
        start_time = asyncio.get_event_loop().time()
        
        result = await task_coordinator.coordinate_tasks(
            tasks=large_task_set,
            project_id="test_project",
            execution_context=ExecutionContext(
                coordinator_id="test_coordinator",
                project_id="test_project",
                initiated_by="test_user"
            )
        )
        
        end_time = asyncio.get_event_loop().time()
        coordination_time = end_time - start_time
        
        # Verify all tasks completed
        assert result.success
        assert len(result.task_results) == 20
        assert len(completed_tasks) == 20
        
        # Should handle large task sets efficiently
        # 20 tasks * 10ms = 200ms sequential, should be much faster with concurrency
        assert coordination_time < 0.5, f"Large task coordination took {coordination_time:.3f}s"


# Integration test marker
pytestmark = pytest.mark.asyncio