"""Tests for Intelligent Orchestration Integration - Phase 2.3 Agent Intelligence Layer."""

import pytest
import pytest_asyncio
import asyncio
import time
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Import implementation classes (will fail initially - TDD approach)
from ltms.ml.intelligent_orchestration import (
    IntelligentOrchestration,
    CoordinationPlan,
    MLEnhancedAgentSelection,
    IntelligentCoordinationPolicy,
    OrchestrationInsight
)


class TestIntelligentOrchestration:
    """Test suite for Intelligent Orchestration Integration."""
    
    @pytest_asyncio.fixture
    async def mock_agent_selection_engine(self):
        """Mock Agent Selection Engine."""
        engine = AsyncMock()
        
        # Mock agent selection responses
        engine.select_optimal_agent = AsyncMock(return_value=MagicMock(
            agent_id='agent_001',
            agent_name='Python Expert Agent',
            confidence_score=0.9,
            predicted_success_rate=0.85,
            estimated_completion_time=2.5,
            reasoning='High Python expertise and good performance history',
            alternative_agents=[
                {'agent_id': 'agent_002', 'confidence_score': 0.7}
            ]
        ))
        
        engine.analyze_task_complexity = AsyncMock(return_value=MagicMock(
            overall_complexity=0.6,
            difficulty_level='medium',
            confidence=0.8
        ))
        
        return engine
    
    @pytest_asyncio.fixture
    async def mock_performance_learning(self):
        """Mock Performance Learning System."""
        learning = AsyncMock()
        
        # Mock capability predictions
        learning.predict_agent_capabilities = AsyncMock(return_value=MagicMock(
            agent_id='agent_001',
            capabilities={
                'python_coding': {
                    'success_probability': 0.9,
                    'time_estimate': 2.0,
                    'confidence_level': 'high'
                },
                'debugging': {
                    'success_probability': 0.75,
                    'time_estimate': 3.0,
                    'confidence_level': 'medium'
                }
            },
            specialization_areas=['python_coding']
        ))
        
        # Mock performance metrics
        learning.get_performance_metrics = AsyncMock(return_value=MagicMock(
            success_rate=0.85,
            average_duration=2.5,
            improvement_trend='improving',
            trend_strength=0.6
        ))
        
        return learning
    
    @pytest_asyncio.fixture
    async def mock_orchestration_service(self):
        """Mock existing Orchestration Service."""
        service = AsyncMock()
        
        # Mock agent registry integration
        service.find_capable_agents = AsyncMock(return_value=[
            {
                'agent_id': 'agent_001',
                'name': 'Python Expert Agent',
                'capabilities': ['python_coding', 'debugging'],
                'status': 'active'
            },
            {
                'agent_id': 'agent_002',
                'name': 'JavaScript Developer',
                'capabilities': ['javascript_coding', 'web_development'],
                'status': 'active'
            }
        ])
        
        service.execute_tool_with_coordination = AsyncMock(return_value={'success': True})
        service.get_orchestration_status = AsyncMock(return_value={'active_agents': 2})
        
        return service
    
    @pytest_asyncio.fixture
    async def mock_redis_service(self):
        """Mock Redis service for ML data storage."""
        redis = AsyncMock()
        
        # Mock ML scoring storage
        redis.hset = AsyncMock(return_value=True)
        redis.hget = AsyncMock(return_value=b'0.85')
        redis.hgetall = AsyncMock(return_value={
            b'agent_001': b'0.9',
            b'agent_002': b'0.75'
        })
        
        return redis
    
    @pytest_asyncio.fixture
    async def intelligent_orchestration(
        self, 
        mock_agent_selection_engine,
        mock_performance_learning,
        mock_orchestration_service,
        mock_redis_service
    ):
        """Create Intelligent Orchestration instance for testing."""
        orchestration = IntelligentOrchestration(
            agent_selection_engine=mock_agent_selection_engine,
            performance_learning=mock_performance_learning,
            orchestration_service=mock_orchestration_service,
            redis_service=mock_redis_service
        )
        await orchestration.initialize()
        return orchestration
    
    @pytest.mark.asyncio
    async def test_enhance_agent_registry_with_ml_scores(self, intelligent_orchestration):
        """Test enhancing agent registry with ML-based scores."""
        ml_scores = {
            'agent_001': 0.9,
            'agent_002': 0.75,
            'agent_003': 0.6
        }
        
        success = await intelligent_orchestration.enhance_agent_registry(ml_scores)
        
        assert success is True
        
        # Verify Redis calls for storing ML scores
        intelligent_orchestration.redis_service.hset.assert_called()
        
        # Verify integration with orchestration service
        assert intelligent_orchestration._ml_scores == ml_scores
    
    @pytest.mark.asyncio
    async def test_smart_coordination_policy_application(self, intelligent_orchestration):
        """Test application of smart coordination policies based on ML insights."""
        task = {
            'description': 'Debug Python memory leak',
            'required_capabilities': ['python_coding', 'debugging'],
            'priority': 'high',
            'estimated_complexity': 0.7
        }
        
        coordination_plan = await intelligent_orchestration.apply_smart_coordination_policy(task)
        
        assert isinstance(coordination_plan, CoordinationPlan)
        assert coordination_plan.selected_agent_id is not None
        assert coordination_plan.confidence_score > 0.0
        assert len(coordination_plan.coordination_steps) > 0
        assert coordination_plan.fallback_agents is not None
        assert coordination_plan.resource_allocation is not None
    
    @pytest.mark.asyncio
    async def test_ml_enhanced_agent_selection(self, intelligent_orchestration):
        """Test ML-enhanced agent selection with performance history."""
        task_description = "Implement REST API with authentication"
        required_capabilities = ['python_coding', 'web_development']
        
        selection = await intelligent_orchestration.ml_enhanced_agent_selection(
            task_description=task_description,
            required_capabilities=required_capabilities
        )
        
        assert isinstance(selection, MLEnhancedAgentSelection)
        assert selection.primary_agent is not None
        assert selection.ml_confidence > 0.0
        assert selection.performance_prediction is not None
        assert len(selection.selection_reasoning) > 0
        assert selection.fallback_options is not None
    
    @pytest.mark.asyncio
    async def test_redis_services_integration_compatibility(self, intelligent_orchestration):
        """Test compatibility with existing Redis orchestration services."""
        # Test that ML enhancements don't break existing functionality
        
        # Simulate existing orchestration service call
        result = await intelligent_orchestration.orchestration_service.execute_tool_with_coordination(
            agent_id='agent_001',
            tool_name='store_memory',
            tool_function=AsyncMock(),
            parameters={'content': 'test'}
        )
        
        assert result['success'] is True
        
        # Test ML enhancement overlay
        ml_insights = await intelligent_orchestration.get_orchestration_insights()
        
        assert isinstance(ml_insights, OrchestrationInsight)
        assert ml_insights.total_agents >= 0
        assert ml_insights.ml_score_coverage >= 0.0
    
    @pytest.mark.asyncio
    async def test_coordination_policy_optimization(self, intelligent_orchestration):
        """Test coordination policy optimization based on learning."""
        # Historical coordination data
        coordination_history = [
            {
                'task_type': 'python_coding',
                'selected_agent': 'agent_001',
                'success': True,
                'duration': 2.0,
                'quality': 0.9
            },
            {
                'task_type': 'python_coding', 
                'selected_agent': 'agent_002',
                'success': False,
                'duration': 4.0,
                'quality': 0.3
            }
        ]
        
        policy = await intelligent_orchestration.optimize_coordination_policy(
            task_type='python_coding',
            coordination_history=coordination_history
        )
        
        assert isinstance(policy, IntelligentCoordinationPolicy)
        assert policy.task_type == 'python_coding'
        assert len(policy.agent_preferences) > 0
        assert policy.confidence_threshold > 0.0
        assert policy.performance_weight > 0.0
    
    @pytest.mark.asyncio
    async def test_real_time_ml_scoring_updates(self, intelligent_orchestration):
        """Test real-time ML scoring updates for agents."""
        agent_id = 'agent_001'
        performance_data = {
            'task_type': 'python_coding',
            'success': True,
            'duration': 1.5,
            'quality': 0.95
        }
        
        new_score = await intelligent_orchestration.update_real_time_ml_score(
            agent_id=agent_id,
            performance_data=performance_data
        )
        
        assert 0.0 <= new_score <= 1.0
        
        # Verify score storage
        intelligent_orchestration.redis_service.hset.assert_called()
        
        # Verify performance learning integration
        intelligent_orchestration.performance_learning.record_agent_performance.assert_called()
    
    @pytest.mark.asyncio
    async def test_intelligent_load_balancing(self, intelligent_orchestration):
        """Test intelligent load balancing based on agent capabilities and current load."""
        tasks = [
            {'description': 'Python task 1', 'capabilities': ['python_coding']},
            {'description': 'Python task 2', 'capabilities': ['python_coding']}, 
            {'description': 'JS task 1', 'capabilities': ['javascript_coding']},
            {'description': 'Debug task', 'capabilities': ['debugging']}
        ]
        
        load_balance_plan = await intelligent_orchestration.create_intelligent_load_balance_plan(tasks)
        
        assert isinstance(load_balance_plan, dict)
        assert 'agent_assignments' in load_balance_plan
        assert 'load_distribution' in load_balance_plan
        assert 'expected_completion_times' in load_balance_plan
        
        # Should distribute tasks intelligently based on capabilities
        assignments = load_balance_plan['agent_assignments']
        assert len(assignments) > 0
        
        # Should consider agent capabilities in assignments
        for agent_id, assigned_tasks in assignments.items():
            assert isinstance(assigned_tasks, list)
    
    @pytest.mark.asyncio
    async def test_orchestration_performance_monitoring(self, intelligent_orchestration):
        """Test orchestration performance monitoring and optimization suggestions."""
        monitoring_data = await intelligent_orchestration.monitor_orchestration_performance()
        
        assert isinstance(monitoring_data, dict)
        assert 'agent_utilization' in monitoring_data
        assert 'ml_score_accuracy' in monitoring_data
        assert 'coordination_efficiency' in monitoring_data
        assert 'optimization_suggestions' in monitoring_data
        
        # Performance metrics should be reasonable
        assert 0.0 <= monitoring_data['coordination_efficiency'] <= 1.0
        assert isinstance(monitoring_data['optimization_suggestions'], list)
    
    @pytest.mark.asyncio
    async def test_adaptive_coordination_strategies(self, intelligent_orchestration):
        """Test adaptive coordination strategies based on system state."""
        system_state = {
            'agent_availability': {'agent_001': 'busy', 'agent_002': 'idle'},
            'current_load': 0.7,
            'recent_failures': ['agent_003'],
            'performance_trends': {'agent_001': 'improving', 'agent_002': 'stable'}
        }
        
        adaptive_strategy = await intelligent_orchestration.generate_adaptive_coordination_strategy(
            system_state=system_state,
            task_urgency='high'
        )
        
        assert isinstance(adaptive_strategy, dict)
        assert 'primary_strategy' in adaptive_strategy
        assert 'fallback_strategies' in adaptive_strategy
        assert 'resource_allocation' in adaptive_strategy
        assert 'expected_outcomes' in adaptive_strategy
        
        # Strategy should adapt to system state
        assert adaptive_strategy['primary_strategy'] is not None
    
    @pytest.mark.asyncio
    async def test_ml_prediction_accuracy_tracking(self, intelligent_orchestration):
        """Test tracking and improvement of ML prediction accuracy."""
        prediction_feedback = [
            {
                'task_id': 'task_001',
                'predicted_agent': 'agent_001',
                'predicted_success_rate': 0.9,
                'actual_outcome': 'success',
                'actual_duration': 2.5,
                'predicted_duration': 2.0
            },
            {
                'task_id': 'task_002',
                'predicted_agent': 'agent_002',
                'predicted_success_rate': 0.7,
                'actual_outcome': 'failure',
                'actual_duration': 5.0,
                'predicted_duration': 3.0
            }
        ]
        
        accuracy_report = await intelligent_orchestration.track_ml_prediction_accuracy(
            prediction_feedback
        )
        
        assert isinstance(accuracy_report, dict)
        assert 'overall_accuracy' in accuracy_report
        assert 'success_prediction_accuracy' in accuracy_report
        assert 'time_prediction_accuracy' in accuracy_report
        assert 'improvement_suggestions' in accuracy_report
        
        # Accuracy metrics should be valid
        assert 0.0 <= accuracy_report['overall_accuracy'] <= 1.0


class TestIntelligentOrchestrationIntegration:
    """Integration tests for Intelligent Orchestration with real services."""
    
    @pytest.mark.asyncio
    async def test_integration_with_full_ml_stack(self):
        """Test integration with complete ML stack (Agent Selection + Performance Learning)."""
        from ltms.ml.intelligent_orchestration import IntelligentOrchestration
        from ltms.ml.agent_selection_engine import AgentSelectionEngine
        from ltms.ml.performance_learning import PerformanceLearningSystem
        from ltms.services.orchestration_service import get_orchestration_service
        from ltms.services.redis_service import get_redis_manager
        
        # Initialize real services
        redis_manager = await get_redis_manager()
        orchestration_service = await get_orchestration_service()
        
        # Initialize ML components
        agent_selection_engine = AgentSelectionEngine()
        await agent_selection_engine.initialize()
        
        performance_learning = PerformanceLearningSystem(redis_service=redis_manager.client)
        await performance_learning.initialize()
        
        # Initialize intelligent orchestration
        intelligent_orchestration = IntelligentOrchestration(
            agent_selection_engine=agent_selection_engine,
            performance_learning=performance_learning,
            orchestration_service=orchestration_service,
            redis_service=redis_manager.client
        )
        
        success = await intelligent_orchestration.initialize()
        assert success is True
        
        # Test ML-enhanced functionality
        task = {
            'description': 'Simple Python function test',
            'required_capabilities': ['python_coding'],
            'priority': 'normal'
        }
        
        coordination_plan = await intelligent_orchestration.apply_smart_coordination_policy(task)
        assert isinstance(coordination_plan, CoordinationPlan)
    
    @pytest.mark.asyncio 
    async def test_orchestration_service_compatibility(self):
        """Test compatibility with existing orchestration service without breaking changes."""
        from ltms.ml.intelligent_orchestration import IntelligentOrchestration
        from ltms.services.orchestration_service import get_orchestration_service
        
        # Get existing orchestration service
        existing_service = await get_orchestration_service()
        
        # Initialize intelligent orchestration as overlay
        intelligent_orchestration = IntelligentOrchestration(
            orchestration_service=existing_service
        )
        await intelligent_orchestration.initialize()
        
        # Test that existing functionality still works
        status = await existing_service.get_orchestration_status()
        assert isinstance(status, dict)
        
        # Test ML enhancements don't break existing flows
        ml_insights = await intelligent_orchestration.get_orchestration_insights()
        assert isinstance(ml_insights, OrchestrationInsight)
    
    @pytest.mark.asyncio
    async def test_performance_impact_measurement(self):
        """Test that ML enhancements don't negatively impact orchestration performance."""
        from ltms.ml.intelligent_orchestration import IntelligentOrchestration
        
        intelligent_orchestration = IntelligentOrchestration()
        await intelligent_orchestration.initialize()
        
        # Measure performance of ML-enhanced operations
        start_time = time.perf_counter()
        
        for i in range(10):
            task = {
                'description': f'Performance test task {i}',
                'required_capabilities': ['python_coding'],
                'priority': 'normal'
            }
            
            await intelligent_orchestration.apply_smart_coordination_policy(task)
        
        end_time = time.perf_counter()
        avg_time_per_operation = (end_time - start_time) / 10
        
        # ML enhancement should not significantly slow down orchestration
        assert avg_time_per_operation < 1.0, f"ML orchestration too slow: {avg_time_per_operation:.3f}s per operation"
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_ml_unavailable(self):
        """Test graceful degradation when ML components are unavailable."""
        from ltms.ml.intelligent_orchestration import IntelligentOrchestration
        
        # Initialize with failing ML components
        failing_agent_selection = AsyncMock()
        failing_agent_selection.initialize = AsyncMock(return_value=False)
        failing_agent_selection.select_optimal_agent = AsyncMock(side_effect=Exception("ML service down"))
        
        intelligent_orchestration = IntelligentOrchestration(
            agent_selection_engine=failing_agent_selection
        )
        
        success = await intelligent_orchestration.initialize()
        # Should still initialize successfully with fallback mode
        assert success is True
        
        # Should gracefully handle ML failures
        task = {
            'description': 'Test task with ML unavailable',
            'required_capabilities': ['python_coding']
        }
        
        coordination_plan = await intelligent_orchestration.apply_smart_coordination_policy(task)
        # Should return a basic coordination plan even without ML
        assert isinstance(coordination_plan, CoordinationPlan)
        assert coordination_plan.ml_enhanced is False  # Flag for fallback mode