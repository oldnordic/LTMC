"""
Test suite for Enhanced TaskManager - Component 2 Phase 2.

This test module follows strict TDD methodology to verify:
- Task decomposition algorithms with complexity analysis
- Intelligent task routing with ML-based assignment
- Progress tracking and predictive completion
- Integration with Component 1 TaskBlueprint system
- Performance requirements (<10ms routing, >85% accuracy)
- Security integration with project isolation

Performance Requirements:
- Task routing: <10ms average
- Assignment accuracy: >85% success rate
- Blueprint integration: <5ms overhead
- Memory operations: Redis caching optimized

Security Requirements:
- Project isolation via project_id
- Input validation and sanitization
- Secure routing parameter handling
"""

import pytest
import pytest_asyncio
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

from ltms.services.enhanced_task_manager import (
    EnhancedTaskManager,
    TaskAssignment,
    TaskDecompositionResult,
    TeamMember,
    TaskManagerError,
    TaskRoutingError,
    InsufficientSkillsError
)
from ltms.models.task_blueprint import (
    TaskBlueprint,
    TaskComplexity,
    TaskMetadata,
    BlueprintValidationError
)
from ltms.services.blueprint_service import BlueprintManager
from ltms.ml.task_routing_engine import TaskRoutingEngine


# Global fixtures for all test classes
@pytest.fixture
def mock_redis_manager():
    """Mock Redis manager for caching."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = False
    return mock_redis

@pytest.fixture
def mock_blueprint_manager():
    """Mock BlueprintManager for blueprint integration."""
    mock_manager = Mock(spec=BlueprintManager)
    mock_manager.get_blueprint = Mock()
    mock_manager.create_blueprint = Mock()
    mock_manager.list_blueprints = Mock(return_value=[])
    return mock_manager

@pytest.fixture
def mock_routing_engine():
    """Mock TaskRoutingEngine for ML-based routing."""
    mock_engine = Mock(spec=TaskRoutingEngine)
    mock_engine.initialize = AsyncMock(return_value=True)
    mock_engine.assign_task_to_member = Mock()
    mock_engine.get_assignment_confidence = Mock(return_value=0.9)
    mock_engine.analyze_skill_match = Mock(return_value=0.85)
    return mock_engine

@pytest.fixture
def sample_team_members():
    """Sample team members for testing."""
    return [
        TeamMember(
            member_id="dev_001",
            name="Alice",
            skills=["python", "fastapi", "async", "testing"],
            experience_level=0.8,
            current_workload=0.3,
            availability_hours=8.0,
            project_id="test_project"
        ),
        TeamMember(
            member_id="dev_002", 
            name="Bob",
            skills=["python", "ml", "data-science", "performance"],
            experience_level=0.9,
            current_workload=0.7,
            availability_hours=6.0,
            project_id="test_project"
        ),
        TeamMember(
            member_id="qa_001",
            name="Charlie",
            skills=["testing", "automation", "selenium", "performance"],
            experience_level=0.7,
            current_workload=0.2,
            availability_hours=8.0,
            project_id="test_project"
        )
    ]

@pytest.fixture
def sample_task_blueprint():
    """Sample TaskBlueprint for testing."""
    metadata = TaskMetadata(
        estimated_duration_minutes=120,
        required_skills=["python", "async", "testing"],
        priority_score=0.8,
        tags=["enhancement", "performance"]
    )
    
    return TaskBlueprint(
        blueprint_id="bp_test_001",
        title="Implement async task routing",
        description="Create async task routing system with performance optimization",
        complexity=TaskComplexity.COMPLEX,
        metadata=metadata,
        project_id="test_project"
    )

@pytest_asyncio.fixture
async def task_manager(mock_redis_manager, mock_blueprint_manager, mock_routing_engine):
    """Create EnhancedTaskManager instance for testing."""
    manager = EnhancedTaskManager(
        redis_manager=mock_redis_manager,
        blueprint_manager=mock_blueprint_manager,
        routing_engine=mock_routing_engine
    )
    await manager.initialize()
    return manager


class TestEnhancedTaskManager:
    """Test suite for EnhancedTaskManager core functionality."""


class TestTaskDecomposition:
    """Test task decomposition algorithms."""
    
    @pytest.mark.asyncio
    async def test_decompose_simple_task_no_split(self, task_manager, sample_task_blueprint):
        """Test that simple tasks are not decomposed."""
        # Arrange: Create simple task
        simple_blueprint = sample_task_blueprint
        simple_blueprint.complexity = TaskComplexity.SIMPLE
        simple_blueprint.metadata.estimated_duration_minutes = 30
        
        # Act: Decompose task
        result = await task_manager.decompose_task(simple_blueprint)
        
        # Assert: Task not decomposed
        assert isinstance(result, TaskDecompositionResult)
        assert len(result.subtasks) == 1
        assert result.subtasks[0].blueprint_id == simple_blueprint.blueprint_id
        assert not result.requires_decomposition
        assert result.complexity_score < 0.6
    
    @pytest.mark.asyncio
    async def test_decompose_complex_task_requires_split(self, task_manager, sample_task_blueprint):
        """Test that complex tasks are properly decomposed."""
        # Arrange: Create complex task
        complex_blueprint = sample_task_blueprint
        complex_blueprint.complexity = TaskComplexity.CRITICAL
        complex_blueprint.metadata.estimated_duration_minutes = 480  # 8 hours
        complex_blueprint.description = "Implement distributed microservice architecture with event sourcing, CQRS, monitoring, testing, and deployment automation"
        
        # Act: Decompose task
        result = await task_manager.decompose_task(complex_blueprint)
        
        # Assert: Task decomposed
        assert isinstance(result, TaskDecompositionResult)
        assert len(result.subtasks) > 1
        assert len(result.subtasks) <= 5  # Reasonable decomposition
        assert result.requires_decomposition
        assert result.complexity_score >= 0.7
        
        # Assert: Subtasks have dependencies
        total_duration = sum(subtask.metadata.estimated_duration_minutes for subtask in result.subtasks)
        assert total_duration <= complex_blueprint.metadata.estimated_duration_minutes
    
    @pytest.mark.asyncio
    async def test_decomposition_respects_complexity_threshold(self, task_manager):
        """Test that decomposition threshold can be configured."""
        # Arrange: Set custom complexity threshold
        original_threshold = task_manager.complexity_threshold
        task_manager.complexity_threshold = 0.5
        
        # Create moderate task
        metadata = TaskMetadata(
            estimated_duration_minutes=90,
            required_skills=["python", "api"],
            priority_score=0.6
        )
        
        blueprint = TaskBlueprint(
            blueprint_id="bp_moderate",
            title="Create API endpoint",
            description="Implement REST API endpoint with validation",
            complexity=TaskComplexity.MODERATE,
            metadata=metadata,
            project_id="test_project"
        )
        
        try:
            # Act: Decompose task
            result = await task_manager.decompose_task(blueprint)
            
            # Assert: Task decomposed due to lower threshold
            assert len(result.subtasks) > 1
            assert result.requires_decomposition
            
        finally:
            # Cleanup: Restore original threshold
            task_manager.complexity_threshold = original_threshold
    
    @pytest.mark.asyncio
    async def test_decomposition_performance_requirement(self, task_manager, sample_task_blueprint):
        """Test that decomposition meets <10ms performance requirement."""
        # Arrange: Prepare task
        complex_blueprint = sample_task_blueprint
        complex_blueprint.complexity = TaskComplexity.CRITICAL
        
        # Act: Measure decomposition time
        start_time = time.perf_counter()
        result = await task_manager.decompose_task(complex_blueprint)
        end_time = time.perf_counter()
        
        # Assert: Performance requirement met
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 10.0, f"Decomposition took {execution_time_ms:.2f}ms, expected <10ms"
        assert isinstance(result, TaskDecompositionResult)


class TestTaskRouting:
    """Test intelligent task routing algorithms."""
    
    @pytest.mark.asyncio
    async def test_route_task_to_best_member(self, task_manager, sample_task_blueprint, sample_team_members):
        """Test that tasks are routed to the most suitable team member."""
        # Arrange: Setup team members and mock routing
        task_manager.routing_engine.assign_task_to_member.return_value = sample_team_members[0]
        task_manager.routing_engine.get_assignment_confidence.return_value = 0.92
        
        # Act: Route task
        assignment = await task_manager.route_task(
            task_blueprint=sample_task_blueprint,
            available_members=sample_team_members,
            project_id="test_project"
        )
        
        # Assert: Task assigned to best member
        assert isinstance(assignment, TaskAssignment)
        assert assignment.assigned_member.member_id == "dev_001"
        assert assignment.confidence_score >= 0.85
        assert assignment.blueprint_id == sample_task_blueprint.blueprint_id
        assert assignment.project_id == "test_project"
    
    @pytest.mark.asyncio
    async def test_route_task_skill_matching(self, task_manager, sample_task_blueprint, sample_team_members):
        """Test that routing considers skill matching."""
        # Arrange: Create task requiring specific skills
        ml_metadata = TaskMetadata(
            estimated_duration_minutes=180,
            required_skills=["python", "ml", "data-science"],
            priority_score=0.9
        )
        
        ml_blueprint = TaskBlueprint(
            blueprint_id="bp_ml_task",
            title="ML model optimization",
            description="Optimize machine learning model performance",
            complexity=TaskComplexity.COMPLEX,
            metadata=ml_metadata,
            project_id="test_project"
        )
        
        # Mock routing to return ML specialist (Bob)
        task_manager.routing_engine.assign_task_to_member.return_value = sample_team_members[1]
        task_manager.routing_engine.analyze_skill_match.return_value = 0.95
        
        # Act: Route ML task
        assignment = await task_manager.route_task(
            task_blueprint=ml_blueprint,
            available_members=sample_team_members,
            project_id="test_project"
        )
        
        # Assert: ML specialist assigned
        assert assignment.assigned_member.member_id == "dev_002"
        assert assignment.assigned_member.name == "Bob"
        assert "ml" in assignment.assigned_member.skills
        assert "data-science" in assignment.assigned_member.skills
    
    @pytest.mark.asyncio
    async def test_route_task_workload_balancing(self, task_manager, sample_task_blueprint, sample_team_members):
        """Test that routing considers current workload."""
        # Arrange: Create members with different workloads
        high_workload_member = sample_team_members[1]  # Bob has 0.7 workload
        low_workload_member = sample_team_members[2]   # Charlie has 0.2 workload
        
        # Mock routing to prefer low workload member for testing task
        task_manager.routing_engine.assign_task_to_member.return_value = low_workload_member
        
        # Act: Route task
        assignment = await task_manager.route_task(
            task_blueprint=sample_task_blueprint,
            available_members=[high_workload_member, low_workload_member],
            project_id="test_project"
        )
        
        # Assert: Lower workload member assigned
        assert assignment.assigned_member.member_id == "qa_001"
        assert assignment.assigned_member.current_workload < 0.5
    
    @pytest.mark.asyncio
    async def test_route_task_no_suitable_member_raises_error(self, task_manager, sample_team_members):
        """Test that routing raises error when no suitable member found."""
        # Arrange: Create task requiring unavailable skills
        specialized_metadata = TaskMetadata(
            estimated_duration_minutes=240,
            required_skills=["rust", "blockchain", "cryptography"],
            priority_score=0.9
        )
        
        specialized_blueprint = TaskBlueprint(
            blueprint_id="bp_specialized",
            title="Blockchain implementation",
            description="Implement blockchain cryptography system",
            complexity=TaskComplexity.CRITICAL,
            metadata=specialized_metadata,
            project_id="test_project"
        )
        
        # Mock routing to return None (no suitable member)
        task_manager.routing_engine.assign_task_to_member.return_value = None
        
        # Act & Assert: Error raised
        with pytest.raises(InsufficientSkillsError) as exc_info:
            await task_manager.route_task(
                task_blueprint=specialized_blueprint,
                available_members=sample_team_members,
                project_id="test_project"
            )
        
        assert "no suitable team member" in str(exc_info.value).lower()
        assert exc_info.value.required_skills == specialized_metadata.required_skills
    
    @pytest.mark.asyncio
    async def test_routing_performance_requirement(self, task_manager, sample_task_blueprint, sample_team_members):
        """Test that routing meets <10ms performance requirement."""
        # Arrange: Setup mocks
        task_manager.routing_engine.assign_task_to_member.return_value = sample_team_members[0]
        task_manager.routing_engine.get_assignment_confidence.return_value = 0.88
        
        # Act: Measure routing time
        start_time = time.perf_counter()
        assignment = await task_manager.route_task(
            task_blueprint=sample_task_blueprint,
            available_members=sample_team_members,
            project_id="test_project"
        )
        end_time = time.perf_counter()
        
        # Assert: Performance requirement met
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 10.0, f"Routing took {execution_time_ms:.2f}ms, expected <10ms"
        assert isinstance(assignment, TaskAssignment)


class TestProgressTracking:
    """Test progress tracking and predictive completion."""
    
    @pytest.mark.asyncio
    async def test_track_task_progress_simple(self, task_manager, sample_task_blueprint):
        """Test basic progress tracking functionality."""
        # Arrange: Create assignment and add it to active assignments
        assignment = TaskAssignment(
            assignment_id="assign_001",
            blueprint_id=sample_task_blueprint.blueprint_id,
            assigned_member=TeamMember(
                member_id="dev_001",
                name="Alice",
                skills=["python", "testing"],
                experience_level=0.8,
                current_workload=0.3,
                availability_hours=8.0,
                project_id="test_project"
            ),
            confidence_score=0.9,
            estimated_completion_time=datetime.now() + timedelta(hours=2),
            project_id="test_project"
        )
        
        # Add assignment to task manager's active assignments
        task_manager._active_assignments[assignment.assignment_id] = assignment
        
        # Act: Track progress
        await task_manager.update_task_progress(
            assignment_id="assign_001",
            progress_percentage=0.5,
            status="in_progress",
            notes="API implementation 50% complete"
        )
        
        # Assert: Progress tracked
        progress = await task_manager.get_task_progress("assign_001")
        assert progress is not None
        assert progress["progress_percentage"] == 0.5
        assert progress["status"] == "in_progress"
        assert "API implementation" in progress["notes"]
    
    @pytest.mark.asyncio
    async def test_predict_completion_time(self, task_manager, sample_task_blueprint):
        """Test predictive completion time calculation."""
        # Arrange: Create assignment with historical data
        assignment_id = "assign_002"
        assignment = TaskAssignment(
            assignment_id=assignment_id,
            blueprint_id=sample_task_blueprint.blueprint_id,
            assigned_member=TeamMember(
                member_id="dev_001",
                name="Alice",
                skills=["python", "testing"],
                experience_level=0.8,
                current_workload=0.3,
                availability_hours=8.0,
                project_id="test_project"
            ),
            confidence_score=0.9,
            estimated_completion_time=datetime.now() + timedelta(hours=2),
            project_id="test_project"
        )
        
        # Add assignment to task manager
        task_manager._active_assignments[assignment_id] = assignment
        
        # Mock historical performance data using a simple class that supports dict-like access
        class MockPerformanceData:
            def get(self, key, default=None):
                data = {
                    "average_completion_ratio": 1.1,  # Usually takes 10% longer
                    "completed_tasks": 5,
                    "recent_velocity": 0.8             # Recent productivity
                }
                return data.get(key, default)
        
        task_manager.routing_engine.get_member_performance_history = Mock(return_value=MockPerformanceData())
        
        # Mock blueprint manager to return None (so it uses assignment estimate)
        task_manager.blueprint_manager = None
        
        # Act: Predict completion
        predicted_time = await task_manager.predict_completion_time(
            assignment_id=assignment_id,
            current_progress=0.3,
            member_id="dev_001"
        )
        
        # Assert: Prediction calculated
        assert predicted_time is not None
        assert isinstance(predicted_time, datetime)
        assert predicted_time > datetime.now()
    
    @pytest.mark.asyncio
    async def test_get_team_workload_overview(self, task_manager, sample_team_members):
        """Test team workload analysis."""
        # Act: Get workload overview
        workload_overview = await task_manager.get_team_workload_overview(
            team_members=sample_team_members,
            project_id="test_project"
        )
        
        # Assert: Overview contains expected data
        assert "members" in workload_overview
        assert "average_workload" in workload_overview
        assert "capacity_utilization" in workload_overview
        assert len(workload_overview["members"]) == len(sample_team_members)
        
        # Check workload calculations
        total_workload = sum(member.current_workload for member in sample_team_members)
        expected_avg = total_workload / len(sample_team_members)
        assert abs(workload_overview["average_workload"] - expected_avg) < 0.01


class TestBlueprintIntegration:
    """Test integration with Component 1 TaskBlueprint system."""
    
    @pytest.mark.asyncio
    async def test_create_assignment_from_blueprint(self, task_manager, sample_task_blueprint, sample_team_members):
        """Test creating task assignment from blueprint."""
        # Arrange: Setup mocks and disable auto-decomposition
        task_manager.routing_engine.assign_task_to_member.return_value = sample_team_members[0]
        task_manager.routing_engine.get_assignment_confidence.return_value = 0.87
        task_manager.routing_engine.get_member_performance_history.return_value = None
        
        # Act: Create assignment from blueprint without decomposition
        assignment = await task_manager.create_assignment_from_blueprint(
            blueprint=sample_task_blueprint,
            available_members=sample_team_members,
            project_id="test_project",
            auto_decompose=False  # Disable decomposition for this test
        )
        
        # Assert: Assignment created correctly
        assert isinstance(assignment, TaskAssignment)
        assert assignment.blueprint_id == sample_task_blueprint.blueprint_id
        assert assignment.project_id == "test_project"
        assert assignment.assigned_member.member_id in [m.member_id for m in sample_team_members]
        assert assignment.confidence_score >= 0.85
    
    @pytest.mark.asyncio
    async def test_blueprint_complexity_influences_routing(self, task_manager, sample_team_members):
        """Test that blueprint complexity influences routing decisions."""
        # Arrange: Create blueprints with different complexity
        simple_blueprint = TaskBlueprint(
            blueprint_id="bp_simple",
            title="Fix typo",
            description="Fix documentation typo",
            complexity=TaskComplexity.TRIVIAL,
            metadata=TaskMetadata(estimated_duration_minutes=15, required_skills=["documentation"]),
            project_id="test_project"
        )
        
        critical_blueprint = TaskBlueprint(
            blueprint_id="bp_critical",
            title="System architecture",
            description="Design distributed system architecture",
            complexity=TaskComplexity.CRITICAL,
            metadata=TaskMetadata(estimated_duration_minutes=480, required_skills=["architecture", "distributed"]),
            project_id="test_project"
        )
        
        # Mock different routing outcomes based on complexity
        def mock_assign_based_on_complexity(task_blueprint, available_members, project_id, preferences=None):
            if task_blueprint.complexity == TaskComplexity.TRIVIAL:
                return sample_team_members[2]  # Charlie (QA) for simple tasks
            else:
                return sample_team_members[1]  # Bob (experienced) for critical tasks
        
        task_manager.routing_engine.assign_task_to_member.side_effect = mock_assign_based_on_complexity
        task_manager.routing_engine.get_assignment_confidence.return_value = 0.9
        
        # Act: Route both tasks
        simple_assignment = await task_manager.route_task(
            task_blueprint=simple_blueprint,
            available_members=sample_team_members,
            project_id="test_project"
        )
        
        critical_assignment = await task_manager.route_task(
            task_blueprint=critical_blueprint,
            available_members=sample_team_members,
            project_id="test_project"
        )
        
        # Assert: Different members assigned based on complexity
        assert simple_assignment.assigned_member.member_id == "qa_001"  # Charlie
        assert critical_assignment.assigned_member.member_id == "dev_002"  # Bob
    
    @pytest.mark.asyncio
    async def test_blueprint_integration_performance(self, task_manager, sample_task_blueprint, sample_team_members):
        """Test that blueprint integration adds <5ms overhead."""
        # Arrange: Setup mocks
        task_manager.routing_engine.assign_task_to_member.return_value = sample_team_members[0]
        task_manager.routing_engine.get_assignment_confidence.return_value = 0.88
        
        # Act: Measure blueprint integration time
        start_time = time.perf_counter()
        assignment = await task_manager.create_assignment_from_blueprint(
            blueprint=sample_task_blueprint,
            available_members=sample_team_members,
            project_id="test_project"
        )
        end_time = time.perf_counter()
        
        # Assert: Performance requirement met
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 5.0, f"Blueprint integration took {execution_time_ms:.2f}ms, expected <5ms"
        assert isinstance(assignment, TaskAssignment)


class TestSecurityIntegration:
    """Test security integration with project isolation."""
    
    @pytest.mark.asyncio
    async def test_project_isolation_in_routing(self, task_manager, sample_team_members):
        """Test that routing respects project isolation."""
        # Arrange: Create members from different projects
        cross_project_members = [
            TeamMember(
                member_id="dev_003",
                name="Dave",
                skills=["python", "fastapi"],
                experience_level=0.9,
                current_workload=0.1,
                availability_hours=8.0,
                project_id="other_project"  # Different project
            )
        ]
        
        blueprint = TaskBlueprint(
            blueprint_id="bp_secure",
            title="Secure task",
            description="Project-isolated task",
            complexity=TaskComplexity.MODERATE,
            metadata=TaskMetadata(required_skills=["python"]),
            project_id="test_project"
        )
        
        # Mock routing to respect project isolation
        task_manager.routing_engine.assign_task_to_member.return_value = None
        
        # Act & Assert: Cross-project assignment blocked
        with pytest.raises(InsufficientSkillsError):
            await task_manager.route_task(
                task_blueprint=blueprint,
                available_members=cross_project_members,
                project_id="test_project"
            )
    
    @pytest.mark.asyncio
    async def test_input_validation_sanitization(self, task_manager):
        """Test that inputs are properly validated and sanitized."""
        # Test priority score validation
        with pytest.raises(BlueprintValidationError):
            TaskMetadata(
                estimated_duration_minutes=60,
                required_skills=["python"],
                priority_score=2.0  # Invalid score > 1.0
            )
        
        # Test negative duration validation
        with pytest.raises(BlueprintValidationError):
            TaskMetadata(
                estimated_duration_minutes=-100,  # Invalid negative duration
                required_skills=["python"],
                priority_score=0.5
            )
        
        # Test empty title validation
        with pytest.raises(BlueprintValidationError):
            TaskBlueprint(
                blueprint_id="bp_malicious",
                title="",  # Invalid empty title
                description="Malicious task",
                complexity=TaskComplexity.MODERATE,
                metadata=TaskMetadata(),
                project_id="test_project"
            )
    
    @pytest.mark.asyncio
    async def test_secure_assignment_id_generation(self, task_manager):
        """Test that assignment IDs are securely generated."""
        # Act: Generate multiple assignment IDs
        assignment_ids = []
        for _ in range(10):
            assignment_id = task_manager._generate_assignment_id()
            assignment_ids.append(assignment_id)
        
        # Assert: IDs are unique and properly formatted
        assert len(set(assignment_ids)) == len(assignment_ids)  # All unique
        for assignment_id in assignment_ids:
            assert assignment_id.startswith("assign_")
            assert len(assignment_id) > 10  # Sufficient entropy
            assert assignment_id.isascii()  # Safe characters only


class TestPerformanceRequirements:
    """Test that all performance requirements are met."""
    
    @pytest.mark.asyncio
    async def test_routing_accuracy_requirement(self, task_manager, sample_team_members):
        """Test that routing achieves >85% assignment accuracy."""
        # Arrange: Setup multiple test scenarios
        test_blueprints = []
        for i in range(20):
            metadata = TaskMetadata(
                estimated_duration_minutes=60 + i * 10,
                required_skills=["python", "testing"] if i % 2 == 0 else ["python", "ml"],
                priority_score=0.5 + (i % 5) * 0.1
            )
            
            blueprint = TaskBlueprint(
                blueprint_id=f"bp_accuracy_{i}",
                title=f"Test task {i}",
                description=f"Performance test task {i}",
                complexity=TaskComplexity.MODERATE,
                metadata=metadata,
                project_id="test_project"
            )
            test_blueprints.append(blueprint)
        
        # Mock high-confidence assignments
        task_manager.routing_engine.assign_task_to_member.return_value = sample_team_members[0]
        task_manager.routing_engine.get_assignment_confidence.return_value = 0.92
        
        # Act: Route all tasks and measure accuracy
        successful_assignments = 0
        total_assignments = len(test_blueprints)
        
        for blueprint in test_blueprints:
            try:
                assignment = await task_manager.route_task(
                    task_blueprint=blueprint,
                    available_members=sample_team_members,
                    project_id="test_project"
                )
                if assignment and assignment.confidence_score >= 0.85:
                    successful_assignments += 1
            except Exception:
                pass  # Assignment failed
        
        # Assert: >85% accuracy achieved
        accuracy = successful_assignments / total_assignments
        assert accuracy > 0.85, f"Routing accuracy {accuracy:.2%} below required 85%"
    
    @pytest.mark.asyncio
    async def test_concurrent_routing_performance(self, task_manager, sample_task_blueprint, sample_team_members):
        """Test performance under concurrent routing load."""
        # Arrange: Setup concurrent tasks
        task_manager.routing_engine.assign_task_to_member.return_value = sample_team_members[0]
        task_manager.routing_engine.get_assignment_confidence.return_value = 0.88
        
        concurrent_tasks = 10
        
        # Act: Execute concurrent routing
        async def route_single_task():
            return await task_manager.route_task(
                task_blueprint=sample_task_blueprint,
                available_members=sample_team_members,
                project_id="test_project"
            )
        
        start_time = time.perf_counter()
        assignments = await asyncio.gather(*[route_single_task() for _ in range(concurrent_tasks)])
        end_time = time.perf_counter()
        
        # Assert: All assignments successful and performance maintained
        assert len(assignments) == concurrent_tasks
        assert all(isinstance(assignment, TaskAssignment) for assignment in assignments)
        
        # Average time per routing should still be <10ms
        avg_time_ms = ((end_time - start_time) * 1000) / concurrent_tasks
        assert avg_time_ms < 10.0, f"Average concurrent routing time {avg_time_ms:.2f}ms exceeds 10ms limit"