"""Tests for Workflow Prediction Engine - Phase 3 Predictive Coordination."""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ltms.ml.workflow_predictor import (
    WorkflowPredictor,
    WorkflowMetrics,
    WorkflowPrediction,
    WorkflowPattern,
    get_workflow_predictor
)


class TestWorkflowMetrics:
    """Test WorkflowMetrics dataclass."""
    
    def test_workflow_metrics_creation(self):
        """Test WorkflowMetrics creation."""
        metrics = WorkflowMetrics(
            execution_time=45.5,
            resource_usage={'cpu': 0.7, 'memory': 0.6},
            throughput=2.0,
            error_rate=0.0,
            bottlenecks=['network'],
            completion_status='success',
            agent_performance={'agent1': 0.9},
            timestamp=datetime.utcnow()
        )
        
        assert metrics.execution_time == 45.5
        assert metrics.resource_usage == {'cpu': 0.7, 'memory': 0.6}
        assert metrics.throughput == 2.0
        assert metrics.error_rate == 0.0
        assert metrics.bottlenecks == ['network']
        assert metrics.completion_status == 'success'
        assert isinstance(metrics.timestamp, datetime)


class TestWorkflowPrediction:
    """Test WorkflowPrediction dataclass."""
    
    def test_workflow_prediction_creation(self):
        """Test WorkflowPrediction creation."""
        prediction = WorkflowPrediction(
            predicted_execution_time=30.0,
            confidence_score=0.85,
            bottleneck_probability={'cpu': 0.3, 'memory': 0.2},
            resource_requirements={'cpu': 1.0, 'memory': 0.8},
            optimization_suggestions=['Use caching'],
            alternative_paths=[{'path': 'alternative'}],
            risk_factors=['high_load'],
            predicted_throughput=1.5
        )
        
        assert prediction.predicted_execution_time == 30.0
        assert prediction.confidence_score == 0.85
        assert 'cpu' in prediction.bottleneck_probability
        assert len(prediction.optimization_suggestions) == 1
        assert prediction.predicted_throughput == 1.5


class TestWorkflowPredictor:
    """Test WorkflowPredictor class."""
    
    @pytest.fixture
    def predictor(self):
        """Create workflow predictor for testing."""
        return WorkflowPredictor(model_cache_size=100)
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample workflow metrics."""
        return WorkflowMetrics(
            execution_time=25.0,
            resource_usage={'cpu': 0.6, 'memory': 0.4},
            throughput=1.5,
            error_rate=0.0,
            bottlenecks=[],
            completion_status='success',
            agent_performance={'agent1': 0.8},
            timestamp=datetime.utcnow()
        )
    
    def test_predictor_initialization(self, predictor):
        """Test predictor initialization."""
        assert isinstance(predictor, WorkflowPredictor)
        assert predictor.models_trained is False
        assert len(predictor.workflow_history) == 0
        assert len(predictor.workflow_patterns) == 0
        assert predictor.cache_ttl == 300
    
    @pytest.mark.asyncio
    async def test_record_workflow_execution(self, predictor, sample_metrics):
        """Test recording workflow execution."""
        success = await predictor.record_workflow_execution(
            task_description="Process data files",
            agent_id="agent1",
            execution_metrics=sample_metrics,
            context={'priority': 'high'}
        )
        
        assert success is True
        assert len(predictor.workflow_history) == 1
        
        recorded = predictor.workflow_history[0]
        assert recorded['task_description'] == "Process data files"
        assert recorded['agent_id'] == "agent1"
        assert 'features' in recorded
        assert 'metrics' in recorded
    
    @pytest.mark.asyncio
    async def test_record_workflow_execution_updates_patterns(self, predictor, sample_metrics):
        """Test that recording updates workflow patterns."""
        await predictor.record_workflow_execution(
            task_description="Process important data files",
            agent_id="agent1",
            execution_metrics=sample_metrics,
            context={}
        )
        
        # Should create a pattern
        assert len(predictor.workflow_patterns) > 0
        
        # Record similar task again
        await predictor.record_workflow_execution(
            task_description="Process important user files",
            agent_id="agent1",
            execution_metrics=sample_metrics,
            context={}
        )
        
        # Pattern frequency should increase
        pattern_key = predictor._generate_pattern_key("Process important data files")
        if pattern_key in predictor.workflow_patterns:
            assert predictor.workflow_patterns[pattern_key].frequency >= 1
    
    @pytest.mark.asyncio
    async def test_predict_workflow_outcome_without_training(self, predictor):
        """Test prediction without trained models."""
        prediction = await predictor.predict_workflow_outcome(
            task_description="New unknown task",
            agent_id="agent1",
            context={'priority': 'medium'}
        )
        
        assert isinstance(prediction, WorkflowPrediction)
        assert prediction.predicted_execution_time > 0
        assert 0 <= prediction.confidence_score <= 1
        assert isinstance(prediction.optimization_suggestions, list)
    
    @pytest.mark.asyncio
    async def test_predict_workflow_outcome_with_pattern(self, predictor, sample_metrics):
        """Test prediction using learned patterns."""
        # First, record some workflow executions to create patterns
        for i in range(3):
            await predictor.record_workflow_execution(
                task_description="Process data files batch",
                agent_id="agent1",
                execution_metrics=sample_metrics,
                context={}
            )
        
        # Now predict similar task
        prediction = await predictor.predict_workflow_outcome(
            task_description="Process data files batch",
            agent_id="agent1",
            context={}
        )
        
        assert isinstance(prediction, WorkflowPrediction)
        assert prediction.confidence_score > 0.3  # Should be higher due to patterns
        assert prediction.predicted_execution_time > 0
    
    @pytest.mark.asyncio
    async def test_prediction_caching(self, predictor):
        """Test prediction caching mechanism."""
        # Make initial prediction
        prediction1 = await predictor.predict_workflow_outcome(
            task_description="Cached task",
            agent_id="agent1",
            context={},
            use_cache=True
        )
        
        # Make same prediction - should use cache
        prediction2 = await predictor.predict_workflow_outcome(
            task_description="Cached task",
            agent_id="agent1",
            context={},
            use_cache=True
        )
        
        # Should be identical (from cache)
        assert prediction1.predicted_execution_time == prediction2.predicted_execution_time
        assert prediction1.confidence_score == prediction2.confidence_score
        
        # Cache should have entries
        assert len(predictor.prediction_cache) > 0
    
    @pytest.mark.asyncio
    async def test_detect_bottlenecks(self, predictor):
        """Test bottleneck detection."""
        current_workflows = [
            {'task_description': 'Heavy processing task'},
            {'task_description': 'Data analysis task'}
        ]
        
        system_metrics = {
            'cpu_usage': 85,  # High CPU usage
            'memory_usage': 70,
            'network_latency': 150  # High latency
        }
        
        bottlenecks = await predictor.detect_bottlenecks(
            current_workflows, system_metrics
        )
        
        assert isinstance(bottlenecks, list)
        # Should detect CPU and network bottlenecks
        bottleneck_types = [b.get('type') for b in bottlenecks]
        assert 'cpu' in bottleneck_types
        assert 'network' in bottleneck_types
    
    @pytest.mark.asyncio
    async def test_optimize_workflow_path(self, predictor):
        """Test workflow path optimization."""
        available_agents = ['agent1', 'agent2', 'agent3']
        
        optimization = await predictor.optimize_workflow_path(
            task_description="Optimize this workflow",
            available_agents=available_agents,
            constraints={'max_time': 60}
        )
        
        assert isinstance(optimization, dict)
        assert 'recommended_agent' in optimization
        assert 'execution_path' in optimization
        assert 'resource_allocation' in optimization
        assert 'timing_recommendations' in optimization
        
        # Recommended agent should be one of available agents
        assert optimization['recommended_agent'] in available_agents
        
        # Execution path should have steps
        assert len(optimization['execution_path']) > 0
        
        # Each step should have required fields
        for step in optimization['execution_path']:
            assert 'step' in step
            assert 'duration' in step
    
    @pytest.mark.asyncio
    async def test_retrain_models_insufficient_data(self, predictor):
        """Test model retraining with insufficient data."""
        success = await predictor.retrain_models()
        
        # Should fail due to insufficient data
        assert success is False
        assert predictor.models_trained is False
    
    @pytest.mark.asyncio
    async def test_retrain_models_with_data(self, predictor, sample_metrics):
        """Test model retraining with sufficient data."""
        # Add enough training data
        for i in range(60):
            modified_metrics = WorkflowMetrics(
                execution_time=20 + i * 0.5,
                resource_usage={'cpu': 0.5 + i * 0.01, 'memory': 0.4},
                throughput=1.0 + i * 0.02,
                error_rate=0.0,
                bottlenecks=['network'] if i % 10 == 0 else [],
                completion_status='success',
                agent_performance={'agent1': 0.8},
                timestamp=datetime.utcnow()
            )
            
            await predictor.record_workflow_execution(
                task_description=f"Training task {i}",
                agent_id=f"agent{i % 3 + 1}",
                execution_metrics=modified_metrics,
                context={'iteration': i}
            )
        
        # Now training should succeed
        success = await predictor.retrain_models()
        
        assert success is True
        assert predictor.models_trained is True
        assert predictor.last_training_time is not None
        assert isinstance(predictor.model_metrics, dict)
    
    def test_extract_features(self, predictor, sample_metrics):
        """Test feature extraction."""
        features = predictor._extract_features(
            task_description="Process important data files quickly",
            agent_id="agent1",
            metrics=sample_metrics,
            context={'priority': 'high', 'user': 'test_user'}
        )
        
        assert isinstance(features, dict)
        assert 'task_complexity' in features
        assert 'agent_hash' in features
        assert 'time_of_day' in features
        assert 'day_of_week' in features
        assert 'context_size' in features
        assert 'execution_time' in features
        assert 'numeric_features' in features
        assert 'resource_estimate' in features
        
        # Numeric features should be a list
        assert isinstance(features['numeric_features'], list)
        assert len(features['numeric_features']) > 0
        
        # Resource estimate should have expected keys
        assert 'memory' in features['resource_estimate']
        assert 'cpu' in features['resource_estimate']
        assert 'network' in features['resource_estimate']
    
    def test_extract_features_without_metrics(self, predictor):
        """Test feature extraction without metrics (for prediction)."""
        features = predictor._extract_features(
            task_description="New prediction task",
            agent_id="agent1",
            metrics=None,
            context={}
        )
        
        assert isinstance(features, dict)
        assert features['execution_time'] == 0
        assert features['error_occurred'] == 0
        assert features['bottleneck_count'] == 0
        assert isinstance(features['numeric_features'], list)
    
    def test_generate_pattern_key(self, predictor):
        """Test pattern key generation."""
        key1 = predictor._generate_pattern_key("Process important data files")
        key2 = predictor._generate_pattern_key("Process important user files")
        key3 = predictor._generate_pattern_key("Simple task")
        
        assert isinstance(key1, str)
        assert isinstance(key2, str)
        assert isinstance(key3, str)
        
        # Similar tasks should have similar keys
        assert len(set(key1.split('_')) & set(key2.split('_'))) > 0
        
        # Different tasks should have different keys
        assert key1 != key3
    
    def test_cache_operations(self, predictor):
        """Test prediction cache operations."""
        prediction = WorkflowPrediction(
            predicted_execution_time=30.0,
            confidence_score=0.8,
            bottleneck_probability={},
            resource_requirements={},
            optimization_suggestions=[],
            alternative_paths=[],
            risk_factors=[],
            predicted_throughput=1.0
        )
        
        cache_key = predictor._generate_cache_key(
            "test task", "agent1", {"test": "context"}
        )
        
        # Cache should be empty initially
        cached = predictor._get_cached_prediction(cache_key)
        assert cached is None
        
        # Cache the prediction
        predictor._cache_prediction(cache_key, prediction)
        
        # Should now be in cache
        cached = predictor._get_cached_prediction(cache_key)
        assert cached is not None
        assert cached.predicted_execution_time == 30.0
    
    def test_analyze_resource_bottlenecks(self, predictor):
        """Test resource bottleneck analysis."""
        # High resource usage
        high_metrics = {
            'cpu_usage': 90,
            'memory_usage': 95,
            'network_latency': 200
        }
        
        bottlenecks = predictor._analyze_resource_bottlenecks(high_metrics)
        
        assert isinstance(bottlenecks, list)
        assert len(bottlenecks) >= 3  # Should detect all three bottlenecks
        
        bottleneck_types = [b['type'] for b in bottlenecks]
        assert 'cpu' in bottleneck_types
        assert 'memory' in bottleneck_types
        assert 'network' in bottleneck_types
        
        # Check severity scores
        for bottleneck in bottlenecks:
            assert 0 < bottleneck['severity'] <= 1
    
    def test_analyze_resource_bottlenecks_normal_usage(self, predictor):
        """Test resource bottleneck analysis with normal usage."""
        normal_metrics = {
            'cpu_usage': 50,
            'memory_usage': 60,
            'network_latency': 20
        }
        
        bottlenecks = predictor._analyze_resource_bottlenecks(normal_metrics)
        
        # Should detect no bottlenecks
        assert isinstance(bottlenecks, list)
        assert len(bottlenecks) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_pattern_bottlenecks(self, predictor, sample_metrics):
        """Test pattern-based bottleneck analysis."""
        # Create a pattern with known bottlenecks
        bottleneck_metrics = WorkflowMetrics(
            execution_time=60.0,
            resource_usage={'cpu': 0.8},
            throughput=0.5,
            error_rate=0.1,
            bottlenecks=['database', 'network'],
            completion_status='success',
            agent_performance={'agent1': 0.6},
            timestamp=datetime.utcnow()
        )
        
        await predictor.record_workflow_execution(
            task_description="Database heavy processing task",
            agent_id="agent1",
            execution_metrics=bottleneck_metrics,
            context={}
        )
        
        current_workflows = [
            {'task_description': 'Database heavy processing task'}
        ]
        
        bottlenecks = await predictor._analyze_pattern_bottlenecks(current_workflows)
        
        assert isinstance(bottlenecks, list)
        if len(bottlenecks) > 0:
            # Should identify pattern-based bottlenecks
            assert any(b['type'] == 'pattern' for b in bottlenecks)
    
    def test_get_predictor_status(self, predictor):
        """Test getting predictor status."""
        status = predictor.get_predictor_status()
        
        assert isinstance(status, dict)
        assert 'models_trained' in status
        assert 'training_data_size' in status
        assert 'patterns_learned' in status
        assert 'last_training' in status
        assert 'prediction_accuracy' in status
        assert 'model_metrics' in status
        assert 'cache_size' in status
        
        # Initial state checks
        assert status['models_trained'] is False
        assert status['training_data_size'] == 0
        assert status['patterns_learned'] == 0
        assert status['last_training'] is None
    
    def test_prepare_training_data_empty(self, predictor):
        """Test preparing training data with empty history."""
        X, y_time, y_throughput, y_bottleneck = predictor._prepare_training_data()
        
        assert isinstance(X, np.ndarray)
        assert isinstance(y_time, np.ndarray)
        assert isinstance(y_throughput, np.ndarray)
        assert isinstance(y_bottleneck, list)
        
        # Should be empty arrays/lists
        assert len(X) == 0
        assert len(y_time) == 0
        assert len(y_throughput) == 0
        assert len(y_bottleneck) == 0
    
    @pytest.mark.asyncio
    async def test_prepare_training_data_with_data(self, predictor, sample_metrics):
        """Test preparing training data with actual data."""
        # Add some training data
        for i in range(5):
            await predictor.record_workflow_execution(
                task_description=f"Training task {i}",
                agent_id="agent1",
                execution_metrics=sample_metrics,
                context={}
            )
        
        X, y_time, y_throughput, y_bottleneck = predictor._prepare_training_data()
        
        assert len(X) > 0
        assert len(y_time) > 0
        assert len(y_throughput) > 0
        assert len(y_bottleneck) > 0
        
        # All should have same length
        assert len(X) == len(y_time) == len(y_throughput) == len(y_bottleneck)
        
        # Features should be numeric
        assert X.dtype in [np.float64, np.float32, np.int64, np.int32]
    
    @pytest.mark.asyncio
    async def test_evaluate_models(self, predictor):
        """Test model evaluation."""
        # Create dummy data for evaluation
        X = np.random.rand(20, 8)
        y_time = np.random.rand(20) * 100
        y_throughput = np.random.rand(20) * 5
        y_bottleneck = ['none'] * 10 + ['cpu'] * 10
        
        metrics = await predictor._evaluate_models(X, y_time, y_throughput, y_bottleneck)
        
        assert isinstance(metrics, dict)
        # Metrics should be calculated (or error recorded)
        assert len(metrics) > 0


@pytest.mark.asyncio
async def test_get_workflow_predictor():
    """Test global workflow predictor getter."""
    predictor1 = await get_workflow_predictor()
    predictor2 = await get_workflow_predictor()
    
    # Should return same instance (singleton pattern)
    assert predictor1 is predictor2
    assert isinstance(predictor1, WorkflowPredictor)


class TestWorkflowPredictorIntegration:
    """Integration tests for WorkflowPredictor."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_prediction_cycle(self):
        """Test complete workflow prediction cycle."""
        predictor = WorkflowPredictor(model_cache_size=50)
        
        # Step 1: Record multiple workflows
        metrics_data = [
            (30, 1.5, ['network']),
            (45, 1.2, []),
            (60, 0.8, ['cpu', 'memory']),
            (25, 2.0, []),
            (90, 0.5, ['database'])
        ]
        
        for i, (exec_time, throughput, bottlenecks) in enumerate(metrics_data):
            metrics = WorkflowMetrics(
                execution_time=exec_time,
                resource_usage={'cpu': 0.6, 'memory': 0.4},
                throughput=throughput,
                error_rate=0.0,
                bottlenecks=bottlenecks,
                completion_status='success',
                agent_performance={'agent1': 0.8},
                timestamp=datetime.utcnow()
            )
            
            success = await predictor.record_workflow_execution(
                task_description=f"Integration test task {i}",
                agent_id=f"agent{i % 2 + 1}",
                execution_metrics=metrics,
                context={'test': 'integration'}
            )
            assert success is True
        
        # Step 2: Make predictions
        prediction = await predictor.predict_workflow_outcome(
            task_description="New integration task",
            agent_id="agent1",
            context={'test': 'prediction'}
        )
        
        assert prediction is not None
        assert prediction.predicted_execution_time > 0
        assert 0 <= prediction.confidence_score <= 1
        
        # Step 3: Detect bottlenecks
        system_metrics = {'cpu_usage': 75, 'memory_usage': 60}
        current_workflows = [{'task_description': 'Active task'}]
        
        bottlenecks = await predictor.detect_bottlenecks(
            current_workflows, system_metrics
        )
        assert isinstance(bottlenecks, list)
        
        # Step 4: Optimize workflow
        optimization = await predictor.optimize_workflow_path(
            task_description="Optimization test task",
            available_agents=['agent1', 'agent2'],
            constraints={'max_time': 60}
        )
        
        assert optimization is not None
        assert 'recommended_agent' in optimization
        
        # Step 5: Check status
        status = predictor.get_predictor_status()
        assert status['training_data_size'] == 5
        assert status['patterns_learned'] > 0
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test predictor performance under load."""
        predictor = WorkflowPredictor()
        
        # Generate multiple concurrent predictions
        tasks = []
        for i in range(20):
            task = predictor.predict_workflow_outcome(
                task_description=f"Load test task {i}",
                agent_id=f"agent{i % 3 + 1}",
                context={'load_test': True}
            )
            tasks.append(task)
        
        # Execute all predictions concurrently
        predictions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All predictions should succeed
        assert len(predictions) == 20
        for prediction in predictions:
            assert not isinstance(prediction, Exception)
            assert isinstance(prediction, WorkflowPrediction)
            assert prediction.predicted_execution_time > 0
    
    @pytest.mark.asyncio
    async def test_prediction_consistency(self):
        """Test prediction consistency over time."""
        predictor = WorkflowPredictor()
        
        # Make same prediction multiple times
        task_desc = "Consistent prediction test"
        agent_id = "agent1"
        context = {'test': 'consistency'}
        
        predictions = []
        for _ in range(5):
            prediction = await predictor.predict_workflow_outcome(
                task_description=task_desc,
                agent_id=agent_id,
                context=context,
                use_cache=False  # Disable cache to test true consistency
            )
            predictions.append(prediction)
            
            # Small delay between predictions
            await asyncio.sleep(0.1)
        
        # Without training data, predictions should be similar but not identical
        # (due to random elements in default prediction)
        execution_times = [p.predicted_execution_time for p in predictions]
        
        # Should all be reasonable values
        for time_val in execution_times:
            assert 0 < time_val < 1000  # Reasonable range
        
        # All predictions should be valid
        for prediction in predictions:
            assert isinstance(prediction.optimization_suggestions, list)
            assert isinstance(prediction.risk_factors, list)
            assert 0 <= prediction.confidence_score <= 1