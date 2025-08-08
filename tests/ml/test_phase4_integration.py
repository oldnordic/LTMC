"""
Comprehensive tests for Phase 4: Advanced Learning Pipeline
Final testing for complete Advanced ML Integration.
"""
import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import numpy as np

from ltms.ml.continuous_learner import ContinuousLearner, ExperienceReplay, LearningMetrics
from ltms.ml.model_manager import ModelManager, ModelVersion, ModelStatus, ABTestConfig
from ltms.ml.experiment_tracker import ExperimentTracker, ExperimentConfig, ExperimentStatus
from ltms.ml.learning_integration import AdvancedLearningIntegration, LearningPhase


class TestContinuousLearner:
    """Test the continuous learning system."""
    
    @pytest.fixture
    async def learner(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        learner = ContinuousLearner(db_path)
        await learner.initialize()
        yield learner
        await learner.cleanup()
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_initialization(self, learner):
        """Test continuous learner initialization."""
        assert learner is not None
        assert learner.learning_active is True
        assert learner.experience_buffer == []
    
    @pytest.mark.asyncio
    async def test_register_experience(self, learner):
        """Test experience registration."""
        success = await learner.register_experience(
            query="test query",
            context="test context", 
            action_taken="test action",
            success=True,
            reward=1.0
        )
        
        assert success is True
        assert len(learner.experience_buffer) == 1
        
        experience = learner.experience_buffer[0]
        assert experience.query == "test query"
        assert experience.success is True
        assert experience.reward == 1.0
    
    @pytest.mark.asyncio
    async def test_experience_buffer_limit(self, learner):
        """Test experience buffer size limit."""
        # Add more experiences than the buffer limit
        for i in range(learner.experience_replay_size + 50):
            await learner.register_experience(
                query=f"query {i}",
                context=f"context {i}",
                action_taken=f"action {i}",
                success=i % 2 == 0
            )
        
        # Buffer should not exceed the limit
        assert len(learner.experience_buffer) <= learner.experience_replay_size
    
    @pytest.mark.asyncio
    async def test_get_experience_insights(self, learner):
        """Test experience insights generation."""
        # Add some test experiences
        for i in range(20):
            await learner.register_experience(
                query=f"test query {i % 3}",  # Create patterns
                context="test context",
                action_taken="test action",
                success=i % 4 != 0  # 75% success rate
            )
        
        insights = await learner.get_experience_insights()
        
        assert 'total_experiences' in insights
        assert 'success_rate' in insights
        assert insights['total_experiences'] == 20
        assert 0.7 <= insights['success_rate'] <= 0.8  # Around 75%


class TestModelManager:
    """Test the ML model management system."""
    
    @pytest.fixture
    async def manager(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        manager = ModelManager(db_path, "test_models")
        await manager.initialize()
        yield manager
        await manager.cleanup()
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_initialization(self, manager):
        """Test model manager initialization."""
        assert manager is not None
        assert manager.model_registry == {}
        assert manager.active_models == {}
    
    @pytest.mark.asyncio
    async def test_register_model(self, manager):
        """Test model registration."""
        # Create a simple mock model
        mock_model = Mock()
        mock_model.predict = Mock(return_value=[1, 0, 1])
        
        model_key = await manager.register_model(
            model=mock_model,
            name="Test Model",
            model_id="test_model",
            version="v1",
            metadata={"test": "data"}
        )
        
        assert model_key == "test_model:v1"
        assert model_key in manager.model_registry
        
        model_version = manager.model_registry[model_key]
        assert model_version.name == "Test Model"
        assert model_version.status == ModelStatus.TRAINING
        assert model_version.metadata == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_model_status_update(self, manager):
        """Test model status updates."""
        # Register a model first
        mock_model = Mock()
        model_key = await manager.register_model(mock_model, "Test Model")
        model_id, version = model_key.split(':')
        
        # Update status
        success = await manager.update_model_status(model_id, version, ModelStatus.PRODUCTION)
        assert success is True
        
        model_version = manager.model_registry[model_key]
        assert model_version.status == ModelStatus.PRODUCTION
    
    @pytest.mark.asyncio
    async def test_ab_test_creation(self, manager):
        """Test A/B test creation."""
        test_id = await manager.create_ab_test(
            name="Test A/B Test",
            model_a_id="model_a",
            model_b_id="model_b",
            traffic_split=0.5,
            success_metric="accuracy"
        )
        
        assert test_id != ""
        assert test_id in manager.ab_tests
        
        ab_test = manager.ab_tests[test_id]
        assert ab_test.name == "Test A/B Test"
        assert ab_test.traffic_split == 0.5
        assert ab_test.success_metric == "accuracy"


class TestExperimentTracker:
    """Test the experiment tracking system."""
    
    @pytest.fixture
    async def tracker(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        tracker = ExperimentTracker(db_path, "test_experiments")
        await tracker.initialize()
        yield tracker
        await tracker.cleanup()
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_initialization(self, tracker):
        """Test experiment tracker initialization."""
        assert tracker is not None
        assert tracker.experiments == {}
        assert tracker.runs == {}
        assert tracker.studies == {}
    
    @pytest.mark.asyncio
    async def test_create_experiment(self, tracker):
        """Test experiment creation."""
        experiment_id = await tracker.create_experiment(
            name="Test Experiment",
            description="Test Description",
            model_type="RandomForest",
            hyperparameters={"n_estimators": 100},
            dataset_info={"size": 1000},
            evaluation_metrics=["accuracy", "f1_score"],
            tags=["test", "ml"]
        )
        
        assert experiment_id != ""
        assert experiment_id in tracker.experiments
        
        experiment = tracker.experiments[experiment_id]
        assert experiment.name == "Test Experiment"
        assert experiment.model_type == "RandomForest"
        assert "test" in experiment.tags
    
    @pytest.mark.asyncio
    async def test_experiment_run_lifecycle(self, tracker):
        """Test complete experiment run lifecycle."""
        # Create experiment
        experiment_id = await tracker.create_experiment(
            name="Test Experiment",
            description="Test Description", 
            model_type="TestModel",
            hyperparameters={"param1": 1},
            dataset_info={"size": 100},
            evaluation_metrics=["accuracy"]
        )
        
        # Start run
        run_id = await tracker.start_run(
            experiment_id=experiment_id,
            hyperparameters={"param1": 2}
        )
        
        assert run_id != ""
        assert run_id in tracker.runs
        
        run = tracker.runs[run_id]
        assert run.experiment_id == experiment_id
        assert run.status == ExperimentStatus.RUNNING
        
        # Log metrics
        success = await tracker.log_metrics(run_id, {"accuracy": 0.85, "loss": 0.2})
        assert success is True
        
        run = tracker.runs[run_id]
        assert run.metrics["accuracy"] == 0.85
        assert run.metrics["loss"] == 0.2
        
        # Finish run
        success = await tracker.finish_run(run_id, ExperimentStatus.COMPLETED)
        assert success is True
        
        run = tracker.runs[run_id]
        assert run.status == ExperimentStatus.COMPLETED
        assert run.end_time is not None
    
    @pytest.mark.asyncio
    async def test_hyperparameter_optimization(self, tracker):
        """Test hyperparameter optimization study."""
        from ltms.ml.experiment_tracker import HyperparameterSpace, OptimizationStrategy
        
        # Create experiment
        experiment_id = await tracker.create_experiment(
            name="Optimization Experiment",
            description="Test Optimization",
            model_type="TestModel", 
            hyperparameters={},
            dataset_info={"size": 100},
            evaluation_metrics=["accuracy"]
        )
        
        # Define search space
        search_space = [
            HyperparameterSpace(
                parameter_name="param1",
                parameter_type="integer",
                min_value=1,
                max_value=10
            ),
            HyperparameterSpace(
                parameter_name="param2",
                parameter_type="continuous",
                min_value=0.1,
                max_value=1.0
            )
        ]
        
        # Create optimization study
        study_id = await tracker.create_optimization_study(
            name="Test Study",
            experiment_id=experiment_id,
            search_space=search_space,
            objective_metric="accuracy",
            strategy=OptimizationStrategy.RANDOM_SEARCH,
            max_trials=10
        )
        
        assert study_id != ""
        assert study_id in tracker.studies
        
        study = tracker.studies[study_id]
        assert study.name == "Test Study"
        assert study.max_trials == 10
        assert len(study.search_space) == 2
        
        # Test hyperparameter suggestion
        suggested_params = await tracker.suggest_hyperparameters(study_id)
        
        assert "param1" in suggested_params
        assert "param2" in suggested_params
        assert isinstance(suggested_params["param1"], int)
        assert isinstance(suggested_params["param2"], float)
        assert 1 <= suggested_params["param1"] <= 10
        assert 0.1 <= suggested_params["param2"] <= 1.0


class TestAdvancedLearningIntegration:
    """Test the complete advanced learning integration system."""
    
    @pytest.fixture
    async def integration(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        # Mock the component imports to avoid complex dependencies
        with patch.multiple(
            'ltms.ml.learning_integration',
            SemanticMemoryManager=Mock,
            IntelligentContextRetrieval=Mock,
            EnhancedTools=Mock,
            AgentSelectionEngine=Mock,
            PerformanceLearning=Mock,
            IntelligentOrchestration=Mock,
            WorkflowPredictor=Mock,
            ResourceOptimizer=Mock,
            ProactiveOptimizer=Mock
        ):
            integration = AdvancedLearningIntegration(db_path)
            
            # Mock component initialization
            for component in integration.component_registry.values():
                if hasattr(component, 'initialize'):
                    component.initialize = Mock(return_value=True)
            
            yield integration
            await integration.cleanup()
            os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_integration_initialization(self, integration):
        """Test advanced learning integration initialization."""
        # Mock all component initializations to return True
        for attr_name in dir(integration):
            attr = getattr(integration, attr_name)
            if hasattr(attr, 'initialize'):
                attr.initialize = Mock(return_value=True)
        
        success = await integration.initialize()
        assert success is True
        
        # Check that all phases are marked as complete
        status = await integration.get_integration_status()
        assert status["integration_completion"] == "100%"
        assert status["overall_status"] in ["active", "partial"]
    
    @pytest.mark.asyncio
    async def test_learning_event_creation(self, integration):
        """Test cross-phase learning event creation."""
        event_id = await integration.create_learning_event(
            source_phase=LearningPhase.ADVANCED_LEARNING,
            target_phases=[LearningPhase.SEMANTIC_MEMORY, LearningPhase.AGENT_INTELLIGENCE],
            event_type="test_event",
            data={"test": "data"}
        )
        
        assert event_id != ""
        assert len(integration.learning_events) == 1
        
        event = integration.learning_events[0]
        assert event.source_phase == LearningPhase.ADVANCED_LEARNING
        assert LearningPhase.SEMANTIC_MEMORY in event.target_phases
        assert event.event_type == "test_event"
        assert event.data == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_system_optimization_trigger(self, integration):
        """Test manual system optimization trigger."""
        # Mock component methods
        for component in integration.component_registry.values():
            if hasattr(component, 'trigger_learning'):
                component.trigger_learning = Mock(return_value="success")
        
        result = await integration.trigger_system_optimization()
        
        assert "triggered_at" in result
        assert "optimizations_performed" in result
        assert "cross_phase_optimization" in result["optimizations_performed"]
    
    @pytest.mark.asyncio
    async def test_learning_insights(self, integration):
        """Test comprehensive learning insights."""
        # Mock component insights
        for component in integration.component_registry.values():
            if hasattr(component, 'get_insights'):
                component.get_insights = Mock(return_value={"test": "insight"})
        
        insights = await integration.get_learning_insights()
        
        assert "system_overview" in insights
        assert "phase_insights" in insights
        assert "cross_phase_patterns" in insights
        assert "optimization_opportunities" in insights
        assert insights["system_overview"]["integration_level"] == "100% Complete"


@pytest.mark.asyncio
async def test_full_phase4_integration():
    """Test complete Phase 4 integration across all components."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Initialize all Phase 4 components
        continuous_learner = ContinuousLearner(db_path)
        model_manager = ModelManager(db_path)
        experiment_tracker = ExperimentTracker(db_path)
        
        # Test initialization
        assert await continuous_learner.initialize()
        assert await model_manager.initialize()
        assert await experiment_tracker.initialize()
        
        # Test cross-component interaction
        # 1. Create experiment
        experiment_id = await experiment_tracker.create_experiment(
            name="Phase 4 Integration Test",
            description="Testing full Phase 4 integration",
            model_type="TestModel",
            hyperparameters={"param1": 1},
            dataset_info={"size": 100},
            evaluation_metrics=["accuracy"]
        )
        assert experiment_id != ""
        
        # 2. Start experiment run
        run_id = await experiment_tracker.start_run(experiment_id)
        assert run_id != ""
        
        # 3. Register experience in continuous learner
        success = await continuous_learner.register_experience(
            query="integration test query",
            context="phase 4 integration",
            action_taken="model training",
            success=True,
            reward=0.85
        )
        assert success
        
        # 4. Register model in model manager
        mock_model = Mock()
        model_key = await model_manager.register_model(
            model=mock_model,
            name="Integration Test Model",
            metadata={"experiment_id": experiment_id, "run_id": run_id}
        )
        assert model_key != ""
        
        # 5. Log experiment metrics
        await experiment_tracker.log_metrics(run_id, {"accuracy": 0.85})
        
        # 6. Finish experiment run
        await experiment_tracker.finish_run(run_id, ExperimentStatus.COMPLETED)
        
        # 7. Get comprehensive status
        learner_insights = await continuous_learner.get_experience_insights()
        manager_status = await model_manager.get_management_status()
        tracker_status = await experiment_tracker.get_tracking_status()
        
        # Verify integration
        assert learner_insights['total_experiences'] > 0
        assert manager_status['total_models'] > 0
        assert tracker_status['experiments']['total'] > 0
        
        # Cleanup
        await continuous_learner.cleanup()
        await model_manager.cleanup()
        await experiment_tracker.cleanup()
        
        print("✅ Phase 4 Advanced Learning Pipeline integration test PASSED")
        
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    # Run the comprehensive Phase 4 integration test
    asyncio.run(test_full_phase4_integration())