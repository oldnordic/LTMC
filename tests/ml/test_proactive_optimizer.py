"""Tests for Proactive System Optimization - Phase 3 Predictive Coordination."""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from ltms.ml.proactive_optimizer import (
    ProactiveOptimizer,
    SystemHealthMetrics,
    OptimizationAction,
    SystemPrediction,
    AdaptiveThreshold,
    get_proactive_optimizer
)


class TestSystemHealthMetrics:
    """Test SystemHealthMetrics dataclass."""
    
    def test_system_health_metrics_creation(self):
        """Test SystemHealthMetrics creation."""
        metrics = SystemHealthMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_percent=75.5,
            memory_percent=60.0,
            disk_usage_percent=45.0,
            network_io_bytes=1024000,
            disk_io_bytes=2048000,
            process_count=150,
            open_files=500,
            system_load=1.5,
            temperature=45.0,
            uptime_seconds=86400
        )
        
        assert metrics.cpu_percent == 75.5
        assert metrics.memory_percent == 60.0
        assert metrics.disk_usage_percent == 45.0
        assert metrics.network_io_bytes == 1024000
        assert metrics.process_count == 150
        assert isinstance(metrics.timestamp, datetime)
    
    def test_system_health_metrics_to_feature_vector(self):
        """Test conversion to feature vector."""
        metrics = SystemHealthMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_percent=50.0,
            memory_percent=40.0,
            disk_usage_percent=30.0,
            network_io_bytes=1000000,  # 1MB
            disk_io_bytes=2000000,     # 2MB
            process_count=100,
            open_files=200,
            system_load=2.0,
            temperature=50.0,
            uptime_seconds=3600  # 1 hour
        )
        
        features = metrics.to_feature_vector()
        
        assert isinstance(features, list)
        assert len(features) == 12  # Should have 12 features including time features
        assert features[0] == 50.0  # CPU percent
        assert features[1] == 40.0  # Memory percent
        assert features[2] == 30.0  # Disk usage percent
        assert abs(features[3] - (1000000 / 1024 / 1024)) < 0.01  # Network I/O in MB
        assert abs(features[4] - (2000000 / 1024 / 1024)) < 0.01  # Disk I/O in MB
        assert features[5] == 100.0 # Process count


class TestOptimizationAction:
    """Test OptimizationAction dataclass."""
    
    def test_optimization_action_creation(self):
        """Test OptimizationAction creation."""
        action = OptimizationAction(
            action_id="test_action_001",
            action_type="cleanup",
            priority=3,
            description="Test optimization action",
            estimated_impact=15.0,
            estimated_duration=10,
            prerequisites=["system_access"],
            risk_level="low",
            automated=True,
            parameters={"cleanup_threshold": 80}
        )
        
        assert action.action_id == "test_action_001"
        assert action.action_type == "cleanup"
        assert action.priority == 3
        assert action.estimated_impact == 15.0
        assert action.automated is True
        assert "cleanup_threshold" in action.parameters


class TestAdaptiveThreshold:
    """Test AdaptiveThreshold dataclass."""
    
    def test_adaptive_threshold_creation(self):
        """Test AdaptiveThreshold creation."""
        threshold = AdaptiveThreshold(
            metric_name="cpu_percent",
            current_threshold=80.0,
            baseline_value=50.0,
            volatility=0.1,
            adjustment_factor=5.0,
            last_updated=datetime.now(timezone.utc),
            update_frequency=30,
            min_threshold=60.0,
            max_threshold=95.0
        )
        
        assert threshold.metric_name == "cpu_percent"
        assert threshold.current_threshold == 80.0
        assert threshold.baseline_value == 50.0
        assert threshold.min_threshold == 60.0
        assert threshold.max_threshold == 95.0


class TestProactiveOptimizer:
    """Test ProactiveOptimizer class."""
    
    @pytest.fixture
    def optimizer(self):
        """Create proactive optimizer for testing."""
        return ProactiveOptimizer(
            monitoring_interval=5,  # Short interval for testing
            prediction_horizon=60,
            max_history_size=100
        )
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample system health metrics."""
        return SystemHealthMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_percent=65.0,
            memory_percent=55.0,
            disk_usage_percent=70.0,
            network_io_bytes=5000000,  # 5MB
            disk_io_bytes=10000000,    # 10MB
            process_count=120,
            open_files=300,
            system_load=1.8,
            temperature=42.0,
            uptime_seconds=7200  # 2 hours
        )
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert isinstance(optimizer, ProactiveOptimizer)
        assert optimizer.monitoring_interval == 5
        assert optimizer.prediction_horizon == 60
        assert optimizer.models_trained is False
        assert optimizer.monitoring_active is False
        assert len(optimizer.health_history) == 0
        assert len(optimizer.adaptive_thresholds) == 3  # Default thresholds
    
    def test_default_thresholds_initialization(self, optimizer):
        """Test default adaptive thresholds initialization."""
        thresholds = optimizer.adaptive_thresholds
        
        assert 'cpu_percent' in thresholds
        assert 'memory_percent' in thresholds
        assert 'disk_usage_percent' in thresholds
        
        cpu_threshold = thresholds['cpu_percent']
        assert cpu_threshold.current_threshold == 80.0
        assert cpu_threshold.min_threshold == 60.0
        assert cpu_threshold.max_threshold == 95.0
    
    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, optimizer):
        """Test optimizer initialization and shutdown."""
        # Mock psutil to avoid system dependencies
        with patch('ltms.ml.proactive_optimizer.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 50.0
            mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0)
            mock_psutil.disk_usage.return_value = MagicMock(percent=70.0)
            mock_psutil.net_io_counters.return_value = MagicMock(
                bytes_sent=1000000, bytes_recv=2000000
            )
            mock_psutil.disk_io_counters.return_value = MagicMock(
                read_bytes=5000000, write_bytes=3000000
            )
            mock_psutil.pids.return_value = list(range(100))
            mock_psutil.Process.return_value.open_files.return_value = []
            mock_psutil.getloadavg.return_value = [1.0, 1.2, 1.5]
            mock_psutil.sensors_temperatures.return_value = {}
            mock_psutil.boot_time.return_value = 1000000000
            
            # Initialize
            success = await optimizer.initialize()
            assert success is True
            assert optimizer.monitoring_active is True
            assert optimizer._monitoring_task is not None
            
            # Shutdown
            await optimizer.shutdown()
            assert optimizer.monitoring_active is False
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, optimizer):
        """Test system metrics collection."""
        with patch('ltms.ml.proactive_optimizer.psutil') as mock_psutil:
            # Mock psutil functions
            mock_psutil.cpu_percent.return_value = 75.5
            mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0)
            mock_psutil.disk_usage.return_value = MagicMock(percent=45.0)
            mock_psutil.net_io_counters.return_value = MagicMock(
                bytes_sent=1000000, bytes_recv=1500000
            )
            mock_psutil.disk_io_counters.return_value = MagicMock(
                read_bytes=8000000, write_bytes=2000000
            )
            mock_psutil.pids.return_value = list(range(150))
            mock_psutil.Process.return_value.open_files.return_value = [MagicMock()] * 20
            mock_psutil.getloadavg.return_value = [1.5, 1.8, 2.0]
            mock_psutil.sensors_temperatures.return_value = {
                'cpu': [MagicMock(current=45.0)]
            }
            mock_psutil.boot_time.return_value = 1000000000
            
            with patch('time.time', return_value=1000086400):  # 1 day later
                metrics = await optimizer.collect_system_metrics()
            
            assert isinstance(metrics, SystemHealthMetrics)
            assert metrics.cpu_percent == 75.5
            assert metrics.memory_percent == 60.0
            assert metrics.disk_usage_percent == 45.0
            assert metrics.process_count == 150
            assert metrics.temperature == 45.0
            
            # Should be stored in history
            assert len(optimizer.health_history) == 1
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics_error_handling(self, optimizer):
        """Test error handling in metrics collection."""
        with patch('ltms.ml.proactive_optimizer.psutil') as mock_psutil:
            # Make psutil raise an exception
            mock_psutil.cpu_percent.side_effect = Exception("Psutil error")
            
            metrics = await optimizer.collect_system_metrics()
            assert metrics is None
    
    @pytest.mark.asyncio
    async def test_predict_system_performance_without_training(self, optimizer, sample_metrics):
        """Test prediction without trained models."""
        prediction = await optimizer.predict_system_performance(
            current_metrics=sample_metrics,
            horizon_minutes=60
        )
        
        assert isinstance(prediction, SystemPrediction)
        assert prediction.predicted_cpu > 0
        assert prediction.predicted_memory > 0
        assert 0 <= prediction.performance_score <= 100
        assert isinstance(prediction.bottleneck_probability, dict)
        assert len(prediction.optimization_recommendations) >= 0
        assert 0 <= prediction.confidence_score <= 1
        assert prediction.prediction_horizon == 60
    
    @pytest.mark.asyncio
    async def test_predict_system_performance_with_training(self, optimizer, sample_metrics):
        """Test prediction with trained models."""
        # Add training data
        for i in range(120):  # Enough for training
            training_metrics = SystemHealthMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=30 + i * 0.4,
                memory_percent=25 + i * 0.3,
                disk_usage_percent=40 + i * 0.2,
                network_io_bytes=1000000 + i * 100000,
                disk_io_bytes=2000000 + i * 50000,
                process_count=80 + i,
                open_files=200 + i * 2,
                system_load=0.5 + i * 0.01,
                temperature=35 + i * 0.1,
                uptime_seconds=3600 + i * 60
            )
            
            optimizer.health_history.append({
                'metrics': training_metrics.__dict__,
                'feature_vector': training_metrics.to_feature_vector(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        # Train models
        success = await optimizer._retrain_models()
        if success:
            assert optimizer.models_trained is True
        
        # Make prediction
        prediction = await optimizer.predict_system_performance(
            current_metrics=sample_metrics,
            horizon_minutes=60
        )
        
        assert isinstance(prediction, SystemPrediction)
        assert prediction.predicted_cpu >= 0
        assert prediction.predicted_memory >= 0
    
    @pytest.mark.asyncio
    async def test_execute_optimization_dry_run(self, optimizer):
        """Test optimization execution in dry run mode."""
        action = OptimizationAction(
            action_id="test_dry_run",
            action_type="cleanup",
            priority=2,
            description="Test dry run optimization",
            estimated_impact=10.0,
            estimated_duration=5,
            prerequisites=[],
            risk_level="low",
            automated=True,
            parameters={}
        )
        
        result = await optimizer.execute_optimization(action, dry_run=True)
        
        assert isinstance(result, dict)
        assert result['action_id'] == "test_dry_run"
        assert result['success'] is True
        assert result['dry_run'] is True
        assert result['impact'] == 10.0
        assert 'start_time' in result
        assert 'end_time' in result
    
    @pytest.mark.asyncio
    async def test_execute_optimization_real_execution(self, optimizer):
        """Test real optimization execution."""
        action = OptimizationAction(
            action_id="test_real_exec",
            action_type="tuning",
            priority=3,
            description="Test real execution",
            estimated_impact=15.0,
            estimated_duration=10,
            prerequisites=[],
            risk_level="medium",
            automated=False,
            parameters={}
        )
        
        result = await optimizer.execute_optimization(action, dry_run=False)
        
        assert isinstance(result, dict)
        assert result['action_id'] == "test_real_exec"
        assert result['success'] is True
        assert result['dry_run'] is False
        assert result['impact'] > 0  # Should have some impact
        
        # Should update statistics
        assert optimizer.optimization_stats['total_optimizations'] == 1
    
    @pytest.mark.asyncio
    async def test_execute_optimization_with_prerequisites(self, optimizer):
        """Test optimization execution with unmet prerequisites."""
        action = OptimizationAction(
            action_id="test_prereq",
            action_type="maintenance",
            priority=5,
            description="Test with prerequisites",
            estimated_impact=20.0,
            estimated_duration=30,
            prerequisites=["maintenance_window"],  # This will fail outside maintenance hours
            risk_level="high",
            automated=False,
            parameters={}
        )
        
        # Mock current time to be outside maintenance window (10 AM)
        with patch('ltms.ml.proactive_optimizer.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 10
            mock_dt.now.return_value = datetime.now(timezone.utc).replace(hour=10)
            
            result = await optimizer.execute_optimization(action, dry_run=True)
        
        # Should fail due to unmet prerequisites
        assert result['success'] is False
        assert 'Prerequisites not met' in result['error']
    
    @pytest.mark.asyncio
    async def test_adaptive_threshold_update(self, optimizer):
        """Test adaptive threshold updating."""
        # Update threshold to have old last update time
        optimizer.adaptive_thresholds['cpu_percent'].last_updated = (
            datetime.now(timezone.utc) - timedelta(minutes=35)
        )
        
        # Test updating CPU threshold
        success = await optimizer.adaptive_threshold_update(
            metric_name='cpu_percent',
            current_value=85.0,
            performance_impact=-0.2  # Performance degraded
        )
        
        assert success is True
        
        # Check that threshold was adjusted
        threshold = optimizer.adaptive_thresholds['cpu_percent']
        # Should loosen threshold due to performance degradation
        assert threshold.current_threshold > 80.0  # Original was 80.0
    
    @pytest.mark.asyncio
    async def test_adaptive_threshold_update_improvement(self, optimizer):
        """Test threshold update when performance improves."""
        # Update threshold to have recent update time
        optimizer.adaptive_thresholds['cpu_percent'].last_updated = (
            datetime.now(timezone.utc) - timedelta(minutes=35)
        )
        
        success = await optimizer.adaptive_threshold_update(
            metric_name='cpu_percent',
            current_value=70.0,
            performance_impact=0.3  # Performance improved
        )
        
        assert success is True
        
        # Should tighten threshold due to performance improvement
        threshold = optimizer.adaptive_thresholds['cpu_percent']
        assert threshold.current_threshold < 80.0  # Original was 80.0
    
    @pytest.mark.asyncio
    async def test_adaptive_threshold_update_unknown_metric(self, optimizer):
        """Test threshold update with unknown metric."""
        success = await optimizer.adaptive_threshold_update(
            metric_name='unknown_metric',
            current_value=50.0
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_detect_anomalies_without_training(self, optimizer, sample_metrics):
        """Test anomaly detection without trained models."""
        # Set high values to trigger threshold-based anomalies
        high_cpu_metrics = SystemHealthMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_percent=95.0,  # Above threshold
            memory_percent=90.0,  # Above threshold
            disk_usage_percent=95.0,  # Above threshold
            network_io_bytes=1000000,
            disk_io_bytes=2000000,
            process_count=100,
            open_files=200,
            system_load=1.0,
            temperature=40.0,
            uptime_seconds=3600
        )
        
        anomalies = await optimizer.detect_anomalies(high_cpu_metrics)
        
        assert isinstance(anomalies, list)
        assert len(anomalies) >= 1  # Should detect at least one anomaly
        
        # Check anomaly structure
        for anomaly in anomalies:
            assert 'type' in anomaly
            assert 'description' in anomaly
            assert 'timestamp' in anomaly
    
    @pytest.mark.asyncio
    async def test_detect_anomalies_with_training(self, optimizer, sample_metrics):
        """Test anomaly detection with trained models."""
        # Add normal training data
        for i in range(60):
            normal_metrics = SystemHealthMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=40 + i * 0.2,
                memory_percent=30 + i * 0.1,
                disk_usage_percent=50 + i * 0.1,
                network_io_bytes=1000000,
                disk_io_bytes=2000000,
                process_count=100 + i,
                open_files=200,
                system_load=1.0,
                temperature=40.0,
                uptime_seconds=3600 + i * 60
            )
            
            optimizer.health_history.append({
                'metrics': normal_metrics.__dict__,
                'feature_vector': normal_metrics.to_feature_vector(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        # Train models
        await optimizer._retrain_models()
        
        # Create anomalous metrics
        anomalous_metrics = SystemHealthMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_percent=99.0,  # Very high
            memory_percent=98.0,  # Very high
            disk_usage_percent=40.0,
            network_io_bytes=1000000,
            disk_io_bytes=2000000,
            process_count=100,
            open_files=200,
            system_load=1.0,
            temperature=40.0,
            uptime_seconds=3600
        )
        
        anomalies = await optimizer.detect_anomalies(anomalous_metrics)
        
        assert isinstance(anomalies, list)
        assert len(anomalies) >= 1  # Should detect anomalies
    
    def test_get_optimization_status(self, optimizer):
        """Test getting optimization status."""
        status = optimizer.get_optimization_status()
        
        assert isinstance(status, dict)
        assert 'models_trained' in status
        assert 'monitoring_active' in status
        assert 'health_data_points' in status
        assert 'optimization_history_count' in status
        assert 'pending_optimizations' in status
        assert 'active_optimizations' in status
        assert 'statistics' in status
        assert 'current_thresholds' in status
        
        # Initial state checks
        assert status['models_trained'] is False
        assert status['monitoring_active'] is False
        assert status['health_data_points'] == 0
        assert status['optimization_history_count'] == 0
        
        # Should have default thresholds
        assert len(status['current_thresholds']) == 3
        assert 'cpu_percent' in status['current_thresholds']
    
    @pytest.mark.asyncio
    async def test_calculate_performance_score(self, optimizer):
        """Test performance score calculation."""
        score = await optimizer._calculate_performance_score(
            cpu=60.0,      # 40 points
            memory=70.0,   # 30 points  
            disk_io=50.0   # Simplified disk I/O
        )
        
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    @pytest.mark.asyncio
    async def test_assess_system_bottlenecks(self, optimizer, sample_metrics):
        """Test system bottleneck assessment."""
        bottlenecks = await optimizer._assess_system_bottlenecks(
            sample_metrics,
            predicted_cpu=85.0,  # High CPU
            predicted_memory=90.0  # High memory
        )
        
        assert isinstance(bottlenecks, dict)
        assert 'cpu' in bottlenecks
        assert 'memory' in bottlenecks
        assert 'disk_space' in bottlenecks
        assert 'system_load' in bottlenecks
        
        # Should detect CPU and memory bottlenecks
        assert bottlenecks['cpu'] > 0  # CPU > 80
        assert bottlenecks['memory'] > 0  # Memory > 85
        
        # All values should be 0-1
        for value in bottlenecks.values():
            assert 0 <= value <= 1
    
    @pytest.mark.asyncio
    async def test_calculate_failure_risk(self, optimizer, sample_metrics):
        """Test failure risk calculation."""
        bottlenecks = {'cpu': 0.8, 'memory': 0.9, 'disk_space': 0.3}
        
        risk = await optimizer._calculate_failure_risk(sample_metrics, bottlenecks)
        
        assert isinstance(risk, float)
        assert 0 <= risk <= 1
        
        # Should be relatively high due to high resource usage
        assert risk > 0.5
    
    @pytest.mark.asyncio
    async def test_generate_optimization_recommendations(self, optimizer, sample_metrics):
        """Test optimization recommendation generation."""
        bottlenecks = {
            'cpu': 0.8,      # High CPU bottleneck
            'memory': 0.9,   # Critical memory bottleneck  
            'disk_space': 0.7  # High disk bottleneck
        }
        failure_risk = 0.85
        
        recommendations = await optimizer._generate_optimization_recommendations(
            sample_metrics, bottlenecks, failure_risk
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should generate recommendations for high bottlenecks
        action_types = [rec.action_type for rec in recommendations]
        assert len(action_types) >= 3  # CPU, memory, disk recommendations
        
        # Should include high-priority maintenance due to failure risk
        priorities = [rec.priority for rec in recommendations]
        assert max(priorities) >= 4  # High priority actions
        
        # Check recommendation structure
        for rec in recommendations:
            assert isinstance(rec, OptimizationAction)
            assert rec.action_id
            assert rec.description
            assert rec.estimated_impact > 0
            assert rec.estimated_duration > 0
    
    @pytest.mark.asyncio
    async def test_check_prerequisites(self, optimizer):
        """Test prerequisite checking."""
        # Test with no prerequisites
        result = await optimizer._check_prerequisites([])
        assert result['all_met'] is True
        assert len(result['missing']) == 0
        
        # Test with maintenance window prerequisite (should fail during day)
        with patch('ltms.ml.proactive_optimizer.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 14  # 2 PM
            mock_dt.now.return_value = datetime.now(timezone.utc).replace(hour=14)
            
            result = await optimizer._check_prerequisites(['maintenance_window'])
            assert result['all_met'] is False
            assert 'maintenance_window' in result['missing']
        
        # Test with maintenance window during allowed hours
        with patch('ltms.ml.proactive_optimizer.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 3  # 3 AM
            mock_dt.now.return_value = datetime.now(timezone.utc).replace(hour=3)
            
            result = await optimizer._check_prerequisites(['maintenance_window'])
            assert result['all_met'] is True
    
    @pytest.mark.asyncio
    async def test_simulate_optimization(self, optimizer):
        """Test optimization simulation."""
        action = OptimizationAction(
            action_id="sim_test",
            action_type="cleanup",
            priority=2,
            description="Simulation test",
            estimated_impact=12.5,
            estimated_duration=5,
            prerequisites=[],
            risk_level="low",
            automated=True,
            parameters={}
        )
        
        impact = await optimizer._simulate_optimization(action)
        assert impact == 12.5  # Should return estimated impact
    
    @pytest.mark.asyncio
    async def test_execute_optimization_action(self, optimizer):
        """Test actual optimization action execution."""
        action = OptimizationAction(
            action_id="exec_test",
            action_type="tuning",
            priority=3,
            description="Execution test",
            estimated_impact=20.0,
            estimated_duration=10,
            prerequisites=[],
            risk_level="medium",
            automated=False,
            parameters={}
        )
        
        impact = await optimizer._execute_optimization_action(action)
        assert isinstance(impact, float)
        assert impact > 0
        assert impact <= 20.0  # Should be less than or equal to estimated
    
    @pytest.mark.asyncio
    async def test_prepare_training_data(self, optimizer):
        """Test training data preparation."""
        # Add some health history
        for i in range(10):
            metrics = SystemHealthMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=50 + i * 3,
                memory_percent=40 + i * 2,
                disk_usage_percent=60 + i,
                network_io_bytes=1000000 + i * 100000,
                disk_io_bytes=2000000 + i * 50000,
                process_count=100 + i,
                open_files=200 + i * 5,
                system_load=1.0 + i * 0.1,
                temperature=40 + i,
                uptime_seconds=3600 + i * 300
            )
            
            optimizer.health_history.append({
                'metrics': metrics.__dict__,
                'feature_vector': metrics.to_feature_vector(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        X, y_performance, y_anomaly = await optimizer._prepare_training_data()
        
        assert isinstance(X, np.ndarray)
        assert isinstance(y_performance, np.ndarray)
        assert isinstance(y_anomaly, np.ndarray)
        
        assert len(X) == len(y_performance) == len(y_anomaly)
        assert len(X) > 0
        
        # Check data ranges
        for perf in y_performance:
            assert 0 <= perf <= 100  # Performance percentage
        
        for anomaly in y_anomaly:
            assert anomaly in [-1, 1]  # Anomaly classification
    
    @pytest.mark.asyncio
    async def test_threshold_based_anomaly_detection(self, optimizer, sample_metrics):
        """Test threshold-based anomaly detection."""
        # Create metrics that exceed thresholds
        high_metrics = SystemHealthMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_percent=90.0,  # Above default threshold
            memory_percent=88.0,  # Above default threshold
            disk_usage_percent=92.0,  # Above default threshold
            network_io_bytes=1000000,
            disk_io_bytes=2000000,
            process_count=100,
            open_files=200,
            system_load=1.0,
            temperature=40.0,
            uptime_seconds=3600
        )
        
        anomalies = await optimizer._threshold_based_anomaly_detection(high_metrics)
        
        assert isinstance(anomalies, list)
        assert len(anomalies) >= 2  # Should detect CPU and memory anomalies
        
        # Check anomaly details
        for anomaly in anomalies:
            assert anomaly['type'] == 'threshold_exceeded'
            assert 'metric' in anomaly
            assert 'current_value' in anomaly
            assert 'threshold' in anomaly
            assert 'severity' in anomaly
            assert anomaly['severity'] in ['medium', 'high']


@pytest.mark.asyncio
async def test_get_proactive_optimizer():
    """Test global proactive optimizer getter."""
    with patch('ltms.ml.proactive_optimizer.ProactiveOptimizer.initialize'):
        optimizer1 = await get_proactive_optimizer()
        optimizer2 = await get_proactive_optimizer()
        
        # Should return same instance (singleton pattern)
        assert optimizer1 is optimizer2
        assert isinstance(optimizer1, ProactiveOptimizer)
        
        # Cleanup
        await optimizer1.shutdown()


class TestProactiveOptimizerIntegration:
    """Integration tests for ProactiveOptimizer."""
    
    @pytest.mark.asyncio
    async def test_full_optimization_cycle(self):
        """Test complete proactive optimization cycle."""
        optimizer = ProactiveOptimizer(monitoring_interval=1, max_history_size=50)
        
        try:
            # Mock psutil for consistent testing
            with patch('ltms.ml.proactive_optimizer.psutil') as mock_psutil:
                mock_psutil.cpu_percent.return_value = 70.0
                mock_psutil.virtual_memory.return_value = MagicMock(percent=65.0)
                mock_psutil.disk_usage.return_value = MagicMock(percent=75.0)
                mock_psutil.net_io_counters.return_value = MagicMock(
                    bytes_sent=2000000, bytes_recv=3000000
                )
                mock_psutil.disk_io_counters.return_value = MagicMock(
                    read_bytes=10000000, write_bytes=5000000
                )
                mock_psutil.pids.return_value = list(range(120))
                mock_psutil.Process.return_value.open_files.return_value = [MagicMock()] * 25
                mock_psutil.getloadavg.return_value = [1.8, 2.0, 2.2]
                mock_psutil.sensors_temperatures.return_value = {}
                mock_psutil.boot_time.return_value = 1000000000
                
                await optimizer.initialize()
                
                # Step 1: Collect system metrics
                metrics = await optimizer.collect_system_metrics()
                assert metrics is not None
                assert len(optimizer.health_history) > 0
                
                # Step 2: Test prediction
                prediction = await optimizer.predict_system_performance(
                    metrics, horizon_minutes=60
                )
                assert prediction is not None
                assert isinstance(prediction.optimization_recommendations, list)
                
                # Step 3: Test optimization execution
                if prediction.optimization_recommendations:
                    action = prediction.optimization_recommendations[0]
                    result = await optimizer.execute_optimization(action, dry_run=True)
                    assert result['success'] is True
                
                # Step 4: Test anomaly detection
                anomalies = await optimizer.detect_anomalies(metrics)
                assert isinstance(anomalies, list)
                
                # Step 5: Test adaptive threshold updates
                # Update threshold to have old last update time
                optimizer.adaptive_thresholds['cpu_percent'].last_updated = (
                    datetime.now(timezone.utc) - timedelta(minutes=35)
                )
                success = await optimizer.adaptive_threshold_update(
                    'cpu_percent', metrics.cpu_percent
                )
                assert success is True
                
                # Step 6: Check status
                status = optimizer.get_optimization_status()
                assert status['health_data_points'] > 0
        
        finally:
            await optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_optimization_under_load(self):
        """Test optimizer performance under load."""
        optimizer = ProactiveOptimizer(monitoring_interval=0.1)
        
        try:
            with patch('ltms.ml.proactive_optimizer.psutil') as mock_psutil:
                # Setup mock for varying metrics
                def mock_cpu_percent(interval=1):
                    return 50 + (time.time() % 10) * 3  # Varying CPU
                
                mock_psutil.cpu_percent.side_effect = mock_cpu_percent
                mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0)
                mock_psutil.disk_usage.return_value = MagicMock(percent=70.0)
                mock_psutil.net_io_counters.return_value = MagicMock(
                    bytes_sent=1000000, bytes_recv=2000000
                )
                mock_psutil.disk_io_counters.return_value = MagicMock(
                    read_bytes=5000000, write_bytes=3000000
                )
                mock_psutil.pids.return_value = list(range(100))
                mock_psutil.Process.return_value.open_files.return_value = []
                mock_psutil.getloadavg.return_value = [1.0, 1.2, 1.5]
                mock_psutil.sensors_temperatures.return_value = {}
                mock_psutil.boot_time.return_value = 1000000000
                
                await optimizer.initialize()
                
                # Generate concurrent metric collection and predictions
                tasks = []
                
                # Concurrent metric collections
                for i in range(20):
                    task = optimizer.collect_system_metrics()
                    tasks.append(task)
                
                # Execute all tasks
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Most should succeed
                successful_results = [r for r in results if not isinstance(r, Exception)]
                assert len(successful_results) >= 15  # At least 75% success
                
                # Test concurrent predictions
                if successful_results:
                    prediction_tasks = []
                    test_metrics = successful_results[0]
                    
                    for i in range(10):
                        task = optimizer.predict_system_performance(test_metrics)
                        prediction_tasks.append(task)
                    
                    predictions = await asyncio.gather(*prediction_tasks, return_exceptions=True)
                    successful_predictions = [
                        p for p in predictions if not isinstance(p, Exception)
                    ]
                    assert len(successful_predictions) >= 8  # At least 80% success
        
        finally:
            await optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_adaptive_threshold_behavior_over_time(self):
        """Test adaptive threshold behavior over time."""
        optimizer = ProactiveOptimizer(monitoring_interval=0.1)
        
        try:
            # Record initial threshold
            initial_cpu_threshold = optimizer.adaptive_thresholds['cpu_percent'].current_threshold
            
            # Simulate improving performance over time
            for i in range(10):
                # Update with good performance
                await optimizer.adaptive_threshold_update(
                    'cpu_percent',
                    current_value=60.0,  # Good CPU usage
                    performance_impact=0.2  # Performance improving
                )
                
                # Advance time
                optimizer.adaptive_thresholds['cpu_percent'].last_updated = (
                    datetime.now(timezone.utc) - timedelta(minutes=35)
                )
            
            final_cpu_threshold = optimizer.adaptive_thresholds['cpu_percent'].current_threshold
            
            # Threshold should have tightened due to good performance
            assert final_cpu_threshold <= initial_cpu_threshold
            
            # Now simulate degrading performance
            for i in range(5):
                await optimizer.adaptive_threshold_update(
                    'cpu_percent',
                    current_value=85.0,  # High CPU usage
                    performance_impact=-0.3  # Performance degrading
                )
                
                optimizer.adaptive_thresholds['cpu_percent'].last_updated = (
                    datetime.now(timezone.utc) - timedelta(minutes=35)
                )
            
            degraded_threshold = optimizer.adaptive_thresholds['cpu_percent'].current_threshold
            
            # Threshold should have loosened due to poor performance
            assert degraded_threshold > final_cpu_threshold
            
        finally:
            await optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_optimization_consistency_and_reliability(self):
        """Test optimization consistency and reliability."""
        optimizer = ProactiveOptimizer()
        
        try:
            # Create consistent test metrics
            base_metrics = SystemHealthMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=75.0,
                memory_percent=80.0,
                disk_usage_percent=60.0,
                network_io_bytes=2000000,
                disk_io_bytes=4000000,
                process_count=150,
                open_files=300,
                system_load=2.0,
                temperature=45.0,
                uptime_seconds=10800
            )
            
            # Make multiple predictions with same input
            predictions = []
            for i in range(5):
                prediction = await optimizer.predict_system_performance(base_metrics)
                predictions.append(prediction)
            
            # All predictions should be valid
            for prediction in predictions:
                assert isinstance(prediction, SystemPrediction)
                assert prediction.predicted_cpu > 0
                assert prediction.predicted_memory > 0
                assert 0 <= prediction.performance_score <= 100
                assert 0 <= prediction.confidence_score <= 1
            
            # Test multiple optimization executions
            action = OptimizationAction(
                action_id="consistency_test",
                action_type="cleanup",
                priority=2,
                description="Consistency test action",
                estimated_impact=10.0,
                estimated_duration=5,
                prerequisites=[],
                risk_level="low",
                automated=True,
                parameters={}
            )
            
            execution_results = []
            for i in range(3):
                result = await optimizer.execute_optimization(action, dry_run=True)
                execution_results.append(result)
            
            # All executions should succeed with consistent results
            for result in execution_results:
                assert result['success'] is True
                assert result['impact'] == 10.0  # Should be consistent
                assert result['dry_run'] is True
        
        finally:
            await optimizer.shutdown()