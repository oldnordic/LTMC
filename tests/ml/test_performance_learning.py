"""Tests for Performance Learning System - Phase 2.2 Agent Intelligence Layer."""

import pytest
import pytest_asyncio
import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Import the implementation classes (will fail initially - TDD approach)
from ltms.ml.performance_learning import (
    PerformanceLearningSystem,
    TaskResult,
    SuccessPattern,
    CapabilityProfile,
    PerformanceMetrics,
    LearningInsight
)


class TestPerformanceLearningSystem:
    """Test suite for Performance Learning System."""
    
    @pytest_asyncio.fixture
    async def mock_redis_service(self):
        """Mock Redis service for performance data storage."""
        redis_service = AsyncMock()
        
        # Mock performance data storage
        redis_service.setex = AsyncMock(return_value=True)
        redis_service.get = AsyncMock(return_value='{"success_rate": 0.85, "avg_time": 2.5}')
        redis_service.hgetall = AsyncMock(return_value={
            b'success_count': b'17',
            b'failure_count': b'3', 
            b'total_time': b'42.5',
            b'last_updated': b'2025-01-08T21:54:00'
        })
        redis_service.hincrby = AsyncMock(return_value=1)
        redis_service.hset = AsyncMock(return_value=True)
        
        return redis_service
    
    @pytest_asyncio.fixture
    async def mock_database_service(self):
        """Mock database service for persistent learning data."""
        db_service = AsyncMock()
        
        # Mock performance history queries
        db_service.execute_query = AsyncMock(return_value=[
            {
                'agent_id': 'agent_001',
                'task_type': 'python_coding',
                'success': True,
                'duration': 1.5,
                'timestamp': datetime.utcnow()
            },
            {
                'agent_id': 'agent_001', 
                'task_type': 'python_coding',
                'success': False,
                'duration': 3.0,
                'timestamp': datetime.utcnow() - timedelta(hours=1)
            }
        ])
        
        db_service.insert_record = AsyncMock(return_value=True)
        
        return db_service
    
    @pytest_asyncio.fixture  
    async def sample_task_results(self):
        """Sample task results for testing."""
        return [
            TaskResult(
                agent_id='agent_001',
                task_type='python_coding',
                task_description='Create REST API endpoint',
                success=True,
                duration_hours=1.5,
                completion_timestamp=datetime.utcnow(),
                quality_score=0.9,
                error_details=None,
                complexity_score=0.6,
                metadata={'framework': 'fastapi', 'lines_of_code': 150}
            ),
            TaskResult(
                agent_id='agent_001',
                task_type='debugging',
                task_description='Fix memory leak in Python app', 
                success=False,
                duration_hours=4.0,
                completion_timestamp=datetime.utcnow() - timedelta(hours=2),
                quality_score=0.0,
                error_details='Unable to identify leak source',
                complexity_score=0.8,
                metadata={'tools_used': ['profiler', 'debugger']}
            ),
            TaskResult(
                agent_id='agent_002',
                task_type='web_development',
                task_description='Build React dashboard',
                success=True,
                duration_hours=6.0,
                completion_timestamp=datetime.utcnow() - timedelta(days=1),
                quality_score=0.85,
                error_details=None,
                complexity_score=0.7,
                metadata={'framework': 'react', 'components': 25}
            )
        ]
    
    @pytest_asyncio.fixture
    async def performance_learning_system(self, mock_redis_service, mock_database_service):
        """Create Performance Learning System instance for testing."""
        learning_system = PerformanceLearningSystem(
            redis_service=mock_redis_service,
            database_service=mock_database_service
        )
        await learning_system.initialize()
        return learning_system
    
    @pytest.mark.asyncio
    async def test_record_agent_performance_success(self, performance_learning_system, sample_task_results):
        """Test recording successful agent performance."""
        success_result = sample_task_results[0]  # Successful task
        
        success = await performance_learning_system.record_agent_performance(success_result)
        
        assert success is True
        
        # Verify Redis calls for performance tracking
        performance_learning_system.redis_service.hincrby.assert_called()
        performance_learning_system.redis_service.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_record_agent_performance_failure(self, performance_learning_system, sample_task_results):
        """Test recording failed agent performance."""
        failure_result = sample_task_results[1]  # Failed task
        
        success = await performance_learning_system.record_agent_performance(failure_result)
        
        assert success is True
        
        # Should record failure metrics and error patterns
        performance_learning_system.redis_service.hset.assert_called()
        # Should store error details for pattern analysis
        call_args = performance_learning_system.redis_service.hset.call_args_list
        assert any('error' in str(call) for call in call_args)
    
    @pytest.mark.asyncio
    async def test_update_capability_scores_trending(self, performance_learning_system):
        """Test updating capability scores based on performance trends."""
        agent_id = 'agent_001'
        
        updated_scores = await performance_learning_system.update_capability_scores(agent_id)
        
        assert isinstance(updated_scores, dict)
        assert len(updated_scores) > 0
        
        # Scores should be between 0.0 and 1.0
        for capability, score in updated_scores.items():
            assert 0.0 <= score <= 1.0
            
        # Should consider recent performance trends
        performance_learning_system.database_service.execute_query.assert_called()
    
    @pytest.mark.asyncio
    async def test_identify_success_patterns_clustering(self, performance_learning_system, sample_task_results):
        """Test identifying success patterns using ML clustering."""
        patterns = await performance_learning_system.identify_success_patterns(
            agent_id='agent_001',
            task_type='python_coding'
        )
        
        assert isinstance(patterns, list)
        assert all(isinstance(pattern, SuccessPattern) for pattern in patterns)
        
        if patterns:
            pattern = patterns[0]
            assert hasattr(pattern, 'pattern_id')
            assert hasattr(pattern, 'success_conditions')
            assert hasattr(pattern, 'confidence_score')
            assert hasattr(pattern, 'occurrence_count')
            assert 0.0 <= pattern.confidence_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_predict_agent_capabilities_accuracy(self, performance_learning_system):
        """Test agent capability prediction accuracy."""
        agent_id = 'agent_001'
        
        capability_profile = await performance_learning_system.predict_agent_capabilities(agent_id)
        
        assert isinstance(capability_profile, CapabilityProfile)
        assert capability_profile.agent_id == agent_id
        assert len(capability_profile.capabilities) > 0
        
        # Check capability predictions
        for capability, prediction in capability_profile.capabilities.items():
            assert 'success_probability' in prediction
            assert 'time_estimate' in prediction
            assert 'confidence_level' in prediction
            assert 0.0 <= prediction['success_probability'] <= 1.0
            assert prediction['time_estimate'] > 0
            assert prediction['confidence_level'] in ['low', 'medium', 'high']
    
    @pytest.mark.asyncio
    async def test_learning_system_performance_metrics(self, performance_learning_system):
        """Test performance metrics collection and analysis."""
        agent_id = 'agent_001'
        
        metrics = await performance_learning_system.get_performance_metrics(
            agent_id=agent_id,
            time_window_hours=168  # 1 week
        )
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.agent_id == agent_id
        assert hasattr(metrics, 'total_tasks')
        assert hasattr(metrics, 'success_rate')
        assert hasattr(metrics, 'average_duration')
        assert hasattr(metrics, 'quality_score_avg')
        assert hasattr(metrics, 'improvement_trend')
        
        # Metrics should be reasonable
        assert 0.0 <= metrics.success_rate <= 1.0
        assert metrics.average_duration >= 0.0
        assert 0.0 <= metrics.quality_score_avg <= 1.0
    
    @pytest.mark.asyncio
    async def test_continuous_learning_from_feedback(self, performance_learning_system):
        """Test continuous learning from performance feedback."""
        feedback_data = {
            'agent_id': 'agent_001',
            'task_type': 'python_coding',
            'actual_outcome': 'success',
            'predicted_success_rate': 0.8,
            'actual_duration': 2.0,
            'predicted_duration': 1.5
        }
        
        learning_insight = await performance_learning_system.learn_from_feedback(feedback_data)
        
        assert isinstance(learning_insight, LearningInsight)
        assert learning_insight.agent_id == feedback_data['agent_id']
        assert learning_insight.prediction_accuracy >= 0.0
        assert len(learning_insight.adjustments_made) > 0
        assert learning_insight.confidence_change != 0.0  # Should adjust confidence
    
    @pytest.mark.asyncio
    async def test_performance_trend_analysis(self, performance_learning_system):
        """Test performance trend analysis over time."""
        agent_id = 'agent_001'
        task_type = 'python_coding'
        
        trend_analysis = await performance_learning_system.analyze_performance_trends(
            agent_id=agent_id,
            task_type=task_type,
            days_back=30
        )
        
        assert isinstance(trend_analysis, dict)
        assert 'trend_direction' in trend_analysis  # 'improving', 'declining', 'stable'
        assert 'trend_strength' in trend_analysis  # How strong the trend is
        assert 'recent_performance' in trend_analysis
        assert 'long_term_average' in trend_analysis
        assert 'volatility_score' in trend_analysis
        
        assert trend_analysis['trend_direction'] in ['improving', 'declining', 'stable']
        assert 0.0 <= trend_analysis['trend_strength'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_agent_specialization_detection(self, performance_learning_system):
        """Test detection of agent specialization areas."""
        agent_id = 'agent_001'
        
        specializations = await performance_learning_system.detect_agent_specializations(agent_id)
        
        assert isinstance(specializations, list)
        
        if specializations:
            specialization = specializations[0]
            assert 'task_type' in specialization
            assert 'expertise_level' in specialization
            assert 'evidence_strength' in specialization
            assert 'sample_successes' in specialization
            
            assert 0.0 <= specialization['expertise_level'] <= 1.0
            assert 0.0 <= specialization['evidence_strength'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_failure_pattern_analysis(self, performance_learning_system):
        """Test analysis of failure patterns for improvement recommendations."""
        agent_id = 'agent_001'
        
        failure_analysis = await performance_learning_system.analyze_failure_patterns(agent_id)
        
        assert isinstance(failure_analysis, dict)
        assert 'common_failure_types' in failure_analysis
        assert 'failure_frequency' in failure_analysis
        assert 'improvement_recommendations' in failure_analysis
        assert 'risk_factors' in failure_analysis
        
        assert isinstance(failure_analysis['common_failure_types'], list)
        assert isinstance(failure_analysis['improvement_recommendations'], list)


class TestPerformanceLearningSystemIntegration:
    """Integration tests for Performance Learning System with real services."""
    
    @pytest.mark.asyncio
    async def test_integration_with_redis_performance_storage(self):
        """Test integration with real Redis for performance data storage."""
        from ltms.ml.performance_learning import PerformanceLearningSystem
        from ltms.services.redis_service import get_redis_manager
        
        # Initialize real Redis service
        redis_manager = await get_redis_manager()
        
        learning_system = PerformanceLearningSystem(redis_service=redis_manager.client)
        await learning_system.initialize()
        
        # Test with real data
        test_result = TaskResult(
            agent_id='test_agent',
            task_type='integration_test',
            task_description='Real Redis integration test',
            success=True,
            duration_hours=0.1,
            completion_timestamp=datetime.utcnow(),
            quality_score=1.0,
            error_details=None,
            complexity_score=0.2,
            metadata={'test': True}
        )
        
        success = await learning_system.record_agent_performance(test_result)
        assert success is True
        
        # Cleanup test data
        await redis_manager.client.delete(f"performance:test_agent:integration_test")
    
    @pytest.mark.asyncio
    async def test_ml_pattern_recognition_accuracy(self):
        """Test ML pattern recognition accuracy with sample data."""
        from ltms.ml.performance_learning import PerformanceLearningSystem
        
        learning_system = PerformanceLearningSystem()
        await learning_system.initialize()
        
        # Generate sample performance data
        sample_results = []
        for i in range(20):
            result = TaskResult(
                agent_id='pattern_test_agent',
                task_type='python_coding' if i % 2 == 0 else 'debugging',
                task_description=f'Pattern test task {i}',
                success=i % 3 != 0,  # Pattern: mostly successful
                duration_hours=1.0 + (i % 4) * 0.5,
                completion_timestamp=datetime.utcnow() - timedelta(hours=i),
                quality_score=0.8 if i % 3 != 0 else 0.3,
                error_details=None if i % 3 != 0 else 'Pattern test error',
                complexity_score=0.5,
                metadata={'test_iteration': i}
            )
            sample_results.append(result)
        
        # Record all sample results
        for result in sample_results:
            await learning_system.record_agent_performance(result)
        
        # Analyze patterns
        patterns = await learning_system.identify_success_patterns(
            agent_id='pattern_test_agent',
            task_type='python_coding'
        )
        
        # Should identify some patterns from the sample data
        assert isinstance(patterns, list)
    
    @pytest.mark.asyncio
    async def test_real_time_learning_performance(self):
        """Test real-time learning performance and responsiveness."""
        from ltms.ml.performance_learning import PerformanceLearningSystem
        
        learning_system = PerformanceLearningSystem()
        await learning_system.initialize()
        
        start_time = time.perf_counter()
        
        # Simulate rapid performance updates
        for i in range(10):
            result = TaskResult(
                agent_id='performance_test_agent',
                task_type='speed_test',
                task_description=f'Speed test {i}',
                success=True,
                duration_hours=0.1,
                completion_timestamp=datetime.utcnow(),
                quality_score=0.9,
                error_details=None,
                complexity_score=0.3,
                metadata={'iteration': i}
            )
            await learning_system.record_agent_performance(result)
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        # Should handle rapid updates efficiently
        avg_time_per_update = total_time_ms / 10
        assert avg_time_per_update < 100, f"Performance learning too slow: {avg_time_per_update:.2f}ms per update"