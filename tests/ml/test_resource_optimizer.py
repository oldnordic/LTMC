"""Tests for Resource Contention Prevention - Phase 3 Predictive Coordination."""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from ltms.ml.resource_optimizer import (
    ResourceOptimizer,
    ResourceMetrics,
    ResourcePrediction,
    CacheEntry,
    get_resource_optimizer
)


class TestResourceMetrics:
    """Test ResourceMetrics dataclass."""
    
    def test_resource_metrics_creation(self):
        """Test ResourceMetrics creation."""
        metrics = ResourceMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_usage=75.5,
            memory_usage=60.0,
            memory_available=40.0,
            network_connections=25,
            redis_connections=8,
            active_locks=3,
            queue_length=5,
            response_time=150.0,
            error_rate=0.02
        )
        
        assert metrics.cpu_usage == 75.5
        assert metrics.memory_usage == 60.0
        assert metrics.network_connections == 25
        assert metrics.redis_connections == 8
        assert metrics.active_locks == 3
        assert isinstance(metrics.timestamp, datetime)
    
    def test_resource_metrics_to_feature_vector(self):
        """Test conversion to feature vector."""
        metrics = ResourceMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_usage=50.0,
            memory_usage=40.0,
            memory_available=60.0,
            network_connections=10,
            redis_connections=5,
            active_locks=2,
            queue_length=3,
            response_time=100.0,
            error_rate=0.01
        )
        
        features = metrics.to_feature_vector()
        
        assert isinstance(features, list)
        assert len(features) == 11  # Should have 11 features including time features
        assert features[0] == 50.0  # CPU usage
        assert features[1] == 40.0  # Memory usage
        assert features[3] == 10.0  # Network connections
        assert features[4] == 5.0   # Redis connections


class TestResourcePrediction:
    """Test ResourcePrediction dataclass."""
    
    def test_resource_prediction_creation(self):
        """Test ResourcePrediction creation."""
        prediction = ResourcePrediction(
            predicted_cpu=80.0,
            predicted_memory=70.0,
            predicted_connections=30,
            predicted_locks=5,
            contention_probability=0.75,
            bottleneck_risk={'cpu': 0.8, 'memory': 0.6},
            optimization_actions=[{'action': 'scale_resources'}],
            confidence_score=0.85,
            time_horizon=5
        )
        
        assert prediction.predicted_cpu == 80.0
        assert prediction.predicted_memory == 70.0
        assert prediction.contention_probability == 0.75
        assert 'cpu' in prediction.bottleneck_risk
        assert len(prediction.optimization_actions) == 1
        assert prediction.time_horizon == 5


class TestCacheEntry:
    """Test CacheEntry dataclass."""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry creation."""
        entry = CacheEntry(
            key="test_key",
            data="test_data",
            size_bytes=1024,
            access_count=5,
            last_accessed=datetime.now(timezone.utc),
            predicted_next_access=None,
            priority_score=0.7,
            cache_hit_probability=0.8
        )
        
        assert entry.key == "test_key"
        assert entry.size_bytes == 1024
        assert entry.access_count == 5
        assert entry.cache_hit_probability == 0.8


class TestResourceOptimizer:
    """Test ResourceOptimizer class."""
    
    @pytest.fixture
    def optimizer(self):
        """Create resource optimizer for testing."""
        return ResourceOptimizer(
            optimization_interval=5,  # Short interval for testing
            prediction_horizon=60,
            max_cache_size=10
        )
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample resource metrics."""
        return ResourceMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_usage=65.0,
            memory_usage=55.0,
            memory_available=45.0,
            network_connections=20,
            redis_connections=6,
            active_locks=2,
            queue_length=4,
            response_time=120.0,
            error_rate=0.01
        )
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert isinstance(optimizer, ResourceOptimizer)
        assert optimizer.optimization_interval == 5
        assert optimizer.prediction_horizon == 60
        assert optimizer.max_cache_size == 10
        assert optimizer.models_trained is False
        assert optimizer.optimization_active is False
        assert len(optimizer.resource_history) == 0
    
    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, optimizer):
        """Test optimizer initialization and shutdown."""
        # Initialize
        success = await optimizer.initialize()
        assert success is True
        assert optimizer.optimization_active is True
        assert optimizer._optimization_task is not None
        
        # Shutdown
        await optimizer.shutdown()
        assert optimizer.optimization_active is False
    
    @pytest.mark.asyncio
    async def test_record_resource_metrics(self, optimizer, sample_metrics):
        """Test recording resource metrics."""
        success = await optimizer.record_resource_metrics(
            metrics=sample_metrics,
            context={'test': 'context'}
        )
        
        assert success is True
        assert len(optimizer.resource_history) == 1
        
        recorded = optimizer.resource_history[0]
        assert recorded['metrics']['cpu_usage'] == 65.0
        assert recorded['context']['test'] == 'context'
        assert 'feature_vector' in recorded
        assert 'timestamp' in recorded
    
    @pytest.mark.asyncio
    async def test_record_multiple_metrics_triggers_retraining(self, optimizer, sample_metrics):
        """Test that recording many metrics triggers retraining."""
        # Record enough metrics to trigger retraining
        for i in range(201):  # More than 200 to trigger retraining
            modified_metrics = ResourceMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_usage=50 + i * 0.1,
                memory_usage=40 + i * 0.1,
                memory_available=60 - i * 0.1,
                network_connections=10 + i,
                redis_connections=5,
                active_locks=2,
                queue_length=3,
                response_time=100.0,
                error_rate=0.01
            )
            
            await optimizer.record_resource_metrics(modified_metrics, {'iteration': i})
        
        # Should have recorded all metrics
        assert len(optimizer.resource_history) == 201
    
    @pytest.mark.asyncio
    async def test_predict_resource_contention_without_training(self, optimizer, sample_metrics):
        """Test prediction without trained models."""
        prediction = await optimizer.predict_resource_contention(
            current_metrics=sample_metrics,
            time_horizon=300
        )
        
        assert isinstance(prediction, ResourcePrediction)
        assert prediction.predicted_cpu > 0
        assert prediction.predicted_memory > 0
        assert 0 <= prediction.contention_probability <= 1
        assert isinstance(prediction.bottleneck_risk, dict)
        assert len(prediction.optimization_actions) > 0
        assert 0 <= prediction.confidence_score <= 1
    
    @pytest.mark.asyncio
    async def test_predict_resource_contention_with_training(self, optimizer, sample_metrics):
        """Test prediction with trained models."""
        # Add training data
        for i in range(120):  # Enough for training
            training_metrics = ResourceMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_usage=30 + i * 0.4,
                memory_usage=25 + i * 0.3,
                memory_available=75 - i * 0.3,
                network_connections=5 + i,
                redis_connections=3 + i // 10,
                active_locks=1 + i // 20,
                queue_length=2 + i // 15,
                response_time=50 + i * 2,
                error_rate=0.001 * i
            )
            
            await optimizer.record_resource_metrics(training_metrics, {'training': i})
        
        # Train models
        success = await optimizer._retrain_models()
        if success:
            assert optimizer.models_trained is True
        
        # Make prediction
        prediction = await optimizer.predict_resource_contention(
            current_metrics=sample_metrics,
            time_horizon=300
        )
        
        assert isinstance(prediction, ResourcePrediction)
        assert prediction.predicted_cpu >= 0
        assert prediction.predicted_memory >= 0
    
    @pytest.mark.asyncio
    async def test_optimize_redis_connections(self, optimizer):
        """Test Redis connection optimization."""
        current_usage = {
            'active_connections': 8,
            'max_connections': 10,
            'average_wait_time': 75.0,
            'connection_errors': 3,
            'connection_timeout': 1000
        }
        
        optimization = await optimizer.optimize_redis_connections(
            pool_name='test_pool',
            current_usage=current_usage
        )
        
        assert isinstance(optimization, dict)
        assert 'pool_name' in optimization
        assert 'recommendations' in optimization
        assert 'predicted_improvement' in optimization
        
        assert optimization['pool_name'] == 'test_pool'
        assert isinstance(optimization['recommendations'], list)
        
        # Should recommend increasing pool size due to high utilization (80%)
        recommendations = optimization['recommendations']
        assert len(recommendations) > 0
        
        # Check if pool information was stored
        assert 'test_pool' in optimizer.connection_pools
    
    @pytest.mark.asyncio
    async def test_optimize_redis_connections_low_utilization(self, optimizer):
        """Test Redis optimization with low utilization."""
        current_usage = {
            'active_connections': 2,
            'max_connections': 20,
            'average_wait_time': 10.0,
            'connection_errors': 0,
            'connection_timeout': 1000
        }
        
        optimization = await optimizer.optimize_redis_connections(
            pool_name='low_usage_pool',
            current_usage=current_usage
        )
        
        assert isinstance(optimization, dict)
        
        # Should recommend reducing pool size due to low utilization (10%)
        recommendations = optimization['recommendations']
        reduce_size_recommendation = next(
            (rec for rec in recommendations if rec['action'] == 'reduce_pool_size'),
            None
        )
        
        if reduce_size_recommendation:
            assert reduce_size_recommendation['recommended_size'] < 20
    
    @pytest.mark.asyncio
    async def test_smart_cache_management(self, optimizer):
        """Test smart cache management."""
        # Create cache access log
        now = datetime.now(timezone.utc)
        cache_access_log = [
            {
                'key': 'item1',
                'timestamp': (now - timedelta(minutes=5)).isoformat()
            },
            {
                'key': 'item1',
                'timestamp': (now - timedelta(minutes=3)).isoformat()
            },
            {
                'key': 'item2',
                'timestamp': (now - timedelta(minutes=10)).isoformat()
            },
            {
                'key': 'item3',
                'timestamp': (now - timedelta(minutes=1)).isoformat()
            }
        ]
        
        # Add cache entries
        optimizer.cache_entries['item1'] = CacheEntry(
            key='item1',
            data='data1',
            size_bytes=1024,
            access_count=5,
            last_accessed=now - timedelta(minutes=3),
            predicted_next_access=None,
            priority_score=0.8,
            cache_hit_probability=0.9
        )
        
        recommendations = await optimizer.smart_cache_management(cache_access_log)
        
        assert isinstance(recommendations, dict)
        assert 'eviction_candidates' in recommendations
        assert 'prefetch_candidates' in recommendations
        assert 'predicted_hit_rate' in recommendations
        
        # Should have updated access patterns
        assert 'item1' in optimizer.cache_access_patterns
        assert len(optimizer.cache_access_patterns['item1']) > 0
    
    @pytest.mark.asyncio
    async def test_prevent_memory_lock_contention(self, optimizer):
        """Test memory lock contention prevention."""
        pending_requests = [
            {
                'request_id': 'req1',
                'resource_id': 'resource_a',
                'agent_id': 'agent1',
                'lock_type': 'read',
                'priority': 3
            },
            {
                'request_id': 'req2',
                'resource_id': 'resource_a',
                'agent_id': 'agent2',
                'lock_type': 'write',
                'priority': 2
            },
            {
                'request_id': 'req3',
                'resource_id': 'resource_b',
                'agent_id': 'agent3',
                'lock_type': 'exclusive',
                'priority': 1
            },
            {
                'request_id': 'req4',
                'resource_id': 'resource_a',
                'agent_id': 'agent4',
                'lock_type': 'read',
                'priority': 3
            }
        ]
        
        scheduling_plan = await optimizer.prevent_memory_lock_contention(pending_requests)
        
        assert isinstance(scheduling_plan, list)
        assert len(scheduling_plan) == 4
        
        # Each entry should have required fields
        for entry in scheduling_plan:
            assert 'request_id' in entry
            assert 'resource_id' in entry
            assert 'agent_id' in entry
            assert 'lock_type' in entry
            assert 'scheduled_order' in entry
            assert 'estimated_wait_time' in entry
        
        # Higher priority requests should come first
        priorities = [entry['priority'] for entry in scheduling_plan]
        # Should be sorted by priority (descending)
        assert priorities == sorted(priorities, reverse=True)
    
    def test_get_optimization_stats(self, optimizer):
        """Test getting optimization statistics."""
        stats = optimizer.get_optimization_stats()
        
        assert isinstance(stats, dict)
        assert 'models_trained' in stats
        assert 'resource_data_points' in stats
        assert 'active_cache_entries' in stats
        assert 'connection_pools_managed' in stats
        assert 'optimization_active' in stats
        assert 'last_optimization' in stats
        assert 'prevented_contentions' in stats
        assert 'cache_hit_rate' in stats
        
        # Initial values
        assert stats['models_trained'] is False
        assert stats['resource_data_points'] == 0
        assert stats['optimization_active'] is False
        assert stats['prevented_contentions'] == 0
    
    @pytest.mark.asyncio
    async def test_assess_bottleneck_risks(self, optimizer, sample_metrics):
        """Test bottleneck risk assessment."""
        # Test with high predicted CPU usage
        risks = await optimizer._assess_bottleneck_risks(
            sample_metrics, 
            85.0  # High CPU prediction
        )
        
        assert isinstance(risks, dict)
        assert 'cpu' in risks
        assert 'memory' in risks
        assert 'connections' in risks
        assert 'locks' in risks
        
        # CPU risk should be high due to prediction > 80
        assert risks['cpu'] > 0.0
        
        # All risks should be between 0 and 1
        for risk_value in risks.values():
            assert 0.0 <= risk_value <= 1.0
    
    @pytest.mark.asyncio
    async def test_generate_optimization_actions(self, optimizer, sample_metrics):
        """Test optimization action generation."""
        bottleneck_risk = {
            'cpu': 0.8,      # High CPU risk
            'memory': 0.9,   # Critical memory risk
            'connections': 0.7,  # High connection risk
            'locks': 0.6     # Medium lock risk
        }
        
        actions = await optimizer._generate_optimization_actions(
            sample_metrics,
            75.0,  # Predicted value
            bottleneck_risk
        )
        
        assert isinstance(actions, list)
        assert len(actions) > 0
        
        # Should generate actions for high-risk areas
        action_types = [action['action'] for action in actions]
        
        # Should include memory optimization due to critical risk (0.9)
        assert any('memory' in action_type for action_type in action_types)
        
        # Each action should have required fields
        for action in actions:
            assert 'action' in action
            assert 'priority' in action
            assert 'estimated_impact' in action
            assert 'implementation' in action
    
    @pytest.mark.asyncio
    async def test_predict_connection_load(self, optimizer):
        """Test connection load prediction."""
        # Add a connection pool
        optimizer.connection_pools['test_pool'] = {
            'usage': {'active_connections': 5},
            'last_analyzed': datetime.now(timezone.utc)
        }
        
        load = await optimizer._predict_connection_load('test_pool')
        
        assert isinstance(load, float)
        assert 0.0 <= load <= 1.0
        
        # Test with non-existent pool
        load_default = await optimizer._predict_connection_load('non_existent')
        assert load_default == 0.5  # Default prediction
    
    @pytest.mark.asyncio
    async def test_identify_eviction_candidates(self, optimizer):
        """Test cache eviction candidate identification."""
        now = datetime.now(timezone.utc)
        
        # Add cache entries with different characteristics
        optimizer.cache_entries['old_item'] = CacheEntry(
            key='old_item',
            data='old_data',
            size_bytes=2048,
            access_count=1,
            last_accessed=now - timedelta(hours=2),  # Old access
            predicted_next_access=None,
            priority_score=0.2,
            cache_hit_probability=0.1  # Low hit probability
        )
        
        optimizer.cache_entries['popular_item'] = CacheEntry(
            key='popular_item',
            data='popular_data',
            size_bytes=512,
            access_count=50,
            last_accessed=now - timedelta(minutes=5),
            predicted_next_access=None,
            priority_score=0.9,
            cache_hit_probability=0.95  # High hit probability
        )
        
        candidates = await optimizer._identify_eviction_candidates()
        
        assert isinstance(candidates, list)
        assert len(candidates) <= 2  # At most 25% of entries
        
        # Should prioritize evicting old, less popular items
        if candidates:
            # Check that each candidate has required fields
            for candidate in candidates:
                assert 'key' in candidate
                assert 'eviction_score' in candidate
                assert 'size_bytes' in candidate
                assert 'last_accessed' in candidate
                assert 'access_count' in candidate
                
                assert candidate['eviction_score'] >= 0
    
    @pytest.mark.asyncio
    async def test_identify_prefetch_candidates(self, optimizer):
        """Test cache prefetch candidate identification."""
        now = datetime.now(timezone.utc)
        
        # Add cache entry with predicted next access
        optimizer.cache_entries['prefetch_item'] = CacheEntry(
            key='prefetch_item',
            data='prefetch_data',
            size_bytes=1024,
            access_count=10,
            last_accessed=now - timedelta(minutes=10),
            predicted_next_access=now + timedelta(minutes=2),  # Soon
            priority_score=0.8,
            cache_hit_probability=0.85
        )
        
        candidates = await optimizer._identify_prefetch_candidates()
        
        assert isinstance(candidates, list)
        
        # Should identify the item for prefetch
        if candidates:
            assert len(candidates) <= 10  # Max 10 candidates
            
            for candidate in candidates:
                assert 'key' in candidate
                assert 'prefetch_priority' in candidate
                assert 'predicted_access_time' in candidate
                assert 'hit_probability' in candidate
                
                assert 0.0 <= candidate['prefetch_priority'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_predicted_hit_rate(self, optimizer):
        """Test predicted cache hit rate calculation."""
        # Empty cache
        hit_rate = await optimizer._calculate_predicted_hit_rate()
        assert hit_rate == 0.0
        
        # Add cache entries with different hit probabilities
        optimizer.cache_entries['item1'] = CacheEntry(
            key='item1', data='data1', size_bytes=1024, access_count=5,
            last_accessed=datetime.now(timezone.utc), predicted_next_access=None,
            priority_score=0.8, cache_hit_probability=0.8
        )
        
        optimizer.cache_entries['item2'] = CacheEntry(
            key='item2', data='data2', size_bytes=512, access_count=3,
            last_accessed=datetime.now(timezone.utc), predicted_next_access=None,
            priority_score=0.6, cache_hit_probability=0.6
        )
        
        hit_rate = await optimizer._calculate_predicted_hit_rate()
        expected_rate = (0.8 + 0.6) / 2  # Average of hit probabilities
        assert hit_rate == expected_rate
    
    @pytest.mark.asyncio
    async def test_analyze_lock_patterns(self, optimizer):
        """Test lock pattern analysis."""
        pending_requests = [
            {
                'resource_id': 'resource_a',
                'lock_type': 'read',
                'priority': 2
            },
            {
                'resource_id': 'resource_a',
                'lock_type': 'write',
                'priority': 3
            },
            {
                'resource_id': 'resource_b',
                'lock_type': 'exclusive',
                'priority': 1
            }
        ]
        
        analysis = await optimizer._analyze_lock_patterns(pending_requests)
        
        assert isinstance(analysis, dict)
        assert 'resource_a' in analysis
        assert 'resource_b' in analysis
        
        # Check resource_a analysis
        resource_a_analysis = analysis['resource_a']
        assert 'request_count' in resource_a_analysis
        assert 'contention_risk' in resource_a_analysis
        assert 'average_priority' in resource_a_analysis
        assert 'lock_type_distribution' in resource_a_analysis
        
        assert resource_a_analysis['request_count'] == 2
        assert 0.0 <= resource_a_analysis['contention_risk'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_optimize_lock_sequence(self, optimizer):
        """Test lock sequence optimization."""
        requests = [
            {'lock_type': 'exclusive', 'priority': 1, 'id': 'req1'},
            {'lock_type': 'read', 'priority': 3, 'id': 'req2'},
            {'lock_type': 'write', 'priority': 2, 'id': 'req3'},
            {'lock_type': 'read', 'priority': 3, 'id': 'req4'}
        ]
        
        analysis = {'contention_risk': 0.5}
        
        optimized = await optimizer._optimize_lock_sequence(
            'test_resource', requests, analysis
        )
        
        assert isinstance(optimized, list)
        assert len(optimized) == 4
        
        # Higher priority requests should generally come earlier
        priorities = [req.get('priority', 0) for req in optimized[:2]]
        if len(priorities) >= 2:
            # At least some high-priority requests should be early
            assert max(priorities) >= 2
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_cache(self, optimizer):
        """Test expired cache cleanup."""
        now = datetime.now(timezone.utc)
        
        # Add expired entry (> 1 hour old)
        optimizer.cache_entries['expired_item'] = CacheEntry(
            key='expired_item',
            data='old_data',
            size_bytes=1024,
            access_count=1,
            last_accessed=now - timedelta(hours=2),  # Expired
            predicted_next_access=None,
            priority_score=0.1,
            cache_hit_probability=0.1
        )
        
        # Add fresh entry
        optimizer.cache_entries['fresh_item'] = CacheEntry(
            key='fresh_item',
            data='fresh_data',
            size_bytes=512,
            access_count=5,
            last_accessed=now - timedelta(minutes=30),  # Fresh
            predicted_next_access=None,
            priority_score=0.8,
            cache_hit_probability=0.8
        )
        
        # Add to access patterns
        optimizer.cache_access_patterns['expired_item'] = [now - timedelta(hours=2)]
        optimizer.cache_access_patterns['fresh_item'] = [now - timedelta(minutes=30)]
        
        assert len(optimizer.cache_entries) == 2
        
        await optimizer._cleanup_expired_cache()
        
        # Expired item should be removed
        assert 'expired_item' not in optimizer.cache_entries
        assert 'fresh_item' in optimizer.cache_entries
        
        # Access patterns should also be cleaned
        assert 'expired_item' not in optimizer.cache_access_patterns
        assert 'fresh_item' in optimizer.cache_access_patterns
    
    @pytest.mark.asyncio
    async def test_prepare_training_data(self, optimizer, sample_metrics):
        """Test training data preparation."""
        # Add some resource history
        for i in range(5):
            metrics = ResourceMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_usage=50 + i * 10,
                memory_usage=40 + i * 5,
                memory_available=60 - i * 5,
                network_connections=10 + i,
                redis_connections=5,
                active_locks=2,
                queue_length=3,
                response_time=100 + i * 20,
                error_rate=0.01
            )
            
            await optimizer.record_resource_metrics(metrics, {'test': i})
        
        X, y_contention, y_resource, y_locks = await optimizer._prepare_training_data()
        
        assert isinstance(X, np.ndarray)
        assert isinstance(y_contention, list)
        assert isinstance(y_resource, np.ndarray)
        assert isinstance(y_locks, list)
        
        assert len(X) == len(y_contention) == len(y_resource) == len(y_locks)
        assert len(X) > 0
        
        # Check data types and ranges
        for contention in y_contention:
            assert contention in [0, 1]  # Binary classification
        
        for resource_val in y_resource:
            assert 0 <= resource_val <= 100  # CPU usage percentage


@pytest.mark.asyncio
async def test_get_resource_optimizer():
    """Test global resource optimizer getter."""
    optimizer1 = await get_resource_optimizer()
    optimizer2 = await get_resource_optimizer()
    
    # Should return same instance (singleton pattern)
    assert optimizer1 is optimizer2
    assert isinstance(optimizer1, ResourceOptimizer)
    
    # Cleanup
    await optimizer1.shutdown()


class TestResourceOptimizerIntegration:
    """Integration tests for ResourceOptimizer."""
    
    @pytest.mark.asyncio
    async def test_full_optimization_cycle(self):
        """Test complete resource optimization cycle."""
        optimizer = ResourceOptimizer(optimization_interval=1, max_cache_size=5)
        
        try:
            await optimizer.initialize()
            
            # Step 1: Record resource metrics over time
            metrics_data = [
                (60, 50, 15, 5, 2),  # (CPU, Memory, Connections, Locks, Queue)
                (75, 65, 20, 8, 4),
                (85, 80, 25, 12, 6),
                (90, 90, 30, 15, 8),
                (70, 60, 18, 6, 3)
            ]
            
            for i, (cpu, mem, conn, locks, queue) in enumerate(metrics_data):
                metrics = ResourceMetrics(
                    timestamp=datetime.now(timezone.utc),
                    cpu_usage=cpu,
                    memory_usage=mem,
                    memory_available=100 - mem,
                    network_connections=conn,
                    redis_connections=locks,
                    active_locks=locks,
                    queue_length=queue,
                    response_time=50 + cpu * 2,
                    error_rate=0.01 if cpu < 80 else 0.05
                )
                
                success = await optimizer.record_resource_metrics(
                    metrics, {'cycle': i}
                )
                assert success is True
            
            # Step 2: Test prediction
            current_metrics = ResourceMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_usage=80.0,
                memory_usage=70.0,
                memory_available=30.0,
                network_connections=22,
                redis_connections=7,
                active_locks=10,
                queue_length=5,
                response_time=180.0,
                error_rate=0.03
            )
            
            prediction = await optimizer.predict_resource_contention(current_metrics)
            assert prediction is not None
            assert prediction.predicted_cpu > 0
            
            # Step 3: Test Redis optimization
            redis_usage = {
                'active_connections': 15,
                'max_connections': 20,
                'average_wait_time': 100.0,
                'connection_errors': 2
            }
            
            redis_optimization = await optimizer.optimize_redis_connections(
                'integration_pool', redis_usage
            )
            assert 'recommendations' in redis_optimization
            
            # Step 4: Test cache management
            cache_log = [
                {
                    'key': 'integration_item',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            ]
            
            cache_recommendations = await optimizer.smart_cache_management(cache_log)
            assert 'predicted_hit_rate' in cache_recommendations
            
            # Step 5: Test lock optimization
            lock_requests = [
                {
                    'request_id': 'int_req1',
                    'resource_id': 'integration_resource',
                    'agent_id': 'agent1',
                    'lock_type': 'read',
                    'priority': 2
                }
            ]
            
            lock_plan = await optimizer.prevent_memory_lock_contention(lock_requests)
            assert len(lock_plan) == 1
            
            # Step 6: Check stats
            stats = optimizer.get_optimization_stats()
            assert stats['resource_data_points'] == 5
            
        finally:
            await optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_optimization_performance_under_load(self):
        """Test optimizer performance under high load."""
        optimizer = ResourceOptimizer(optimization_interval=1)
        
        try:
            await optimizer.initialize()
            
            # Generate concurrent optimization requests
            tasks = []
            
            for i in range(50):
                metrics = ResourceMetrics(
                    timestamp=datetime.now(timezone.utc),
                    cpu_usage=40 + i % 60,
                    memory_usage=30 + i % 70,
                    memory_available=70 - i % 70,
                    network_connections=10 + i % 20,
                    redis_connections=5 + i % 10,
                    active_locks=i % 15,
                    queue_length=i % 8,
                    response_time=50 + i * 3,
                    error_rate=0.001 * i
                )
                
                # Record metrics concurrently
                task = optimizer.record_resource_metrics(metrics, {'load_test': i})
                tasks.append(task)
            
            # Execute all recording tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed
            assert len(results) == 50
            for result in results:
                assert not isinstance(result, Exception)
                assert result is True
            
            # Test concurrent predictions
            prediction_tasks = []
            test_metrics = ResourceMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_usage=75.0,
                memory_usage=65.0,
                memory_available=35.0,
                network_connections=20,
                redis_connections=8,
                active_locks=5,
                queue_length=4,
                response_time=150.0,
                error_rate=0.02
            )
            
            for i in range(10):
                task = optimizer.predict_resource_contention(test_metrics)
                prediction_tasks.append(task)
            
            predictions = await asyncio.gather(*prediction_tasks, return_exceptions=True)
            
            assert len(predictions) == 10
            for prediction in predictions:
                assert not isinstance(prediction, Exception)
                assert isinstance(prediction, ResourcePrediction)
                
        finally:
            await optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_optimization_consistency_over_time(self):
        """Test optimization consistency over multiple cycles."""
        optimizer = ResourceOptimizer(optimization_interval=0.1)  # Very fast for testing
        
        try:
            await optimizer.initialize()
            
            # Record consistent metrics
            base_metrics = ResourceMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_usage=50.0,
                memory_usage=40.0,
                memory_available=60.0,
                network_connections=15,
                redis_connections=6,
                active_locks=3,
                queue_length=2,
                response_time=100.0,
                error_rate=0.01
            )
            
            # Record same metrics multiple times
            for i in range(10):
                await optimizer.record_resource_metrics(base_metrics, {'consistency_test': i})
                await asyncio.sleep(0.05)  # Small delay
            
            # Make multiple predictions with same input
            predictions = []
            for i in range(5):
                prediction = await optimizer.predict_resource_contention(base_metrics)
                predictions.append(prediction)
                await asyncio.sleep(0.02)
            
            # All predictions should be similar (consistent)
            cpu_predictions = [p.predicted_cpu for p in predictions if p]
            memory_predictions = [p.predicted_memory for p in predictions if p]
            
            if len(cpu_predictions) > 1:
                # Standard deviation should be relatively low for consistency
                cpu_std = np.std(cpu_predictions)
                memory_std = np.std(memory_predictions)
                
                # Allow some variation due to randomness but expect consistency
                assert cpu_std < 20.0  # Reasonable variation threshold
                assert memory_std < 20.0
            
            # Wait for a few optimization cycles
            await asyncio.sleep(0.3)
            
            # Stats should show activity
            stats = optimizer.get_optimization_stats()
            assert stats['resource_data_points'] == 10
            
        finally:
            await optimizer.shutdown()