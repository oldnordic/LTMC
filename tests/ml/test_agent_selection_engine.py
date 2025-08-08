"""Tests for Agent Selection Engine - Phase 2 Agent Intelligence Layer."""

import pytest
import pytest_asyncio
import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

# Import the actual implementation classes from ltms.ml.agent_selection_engine
from ltms.ml.agent_selection_engine import (
    TaskComplexityScore,
    AgentRecommendation,
    PerformancePrediction,
    SelectionReasoning,
    AgentSelectionEngine
)


class TestAgentSelectionEngine:
    """Test suite for Agent Selection Engine."""
    
    @pytest_asyncio.fixture
    async def mock_ollama_client(self):
        """Mock Ollama client for Qwen3-Coder integration."""
        client = AsyncMock()
        
        # Mock complexity analysis response
        client.analyze_task_complexity = AsyncMock(return_value={
            'overall_complexity': 0.3,
            'technical_complexity': 0.2,
            'implementation_complexity': 0.4,
            'maintenance_complexity': 0.3,
            'estimated_time_hours': 2.5,
            'difficulty_level': 'medium',
            'reasoning': 'Moderate complexity task requiring basic programming skills',
            'confidence': 0.85
        })
        
        return client
    
    @pytest_asyncio.fixture
    async def mock_agent_registry(self):
        """Mock agent registry service."""
        registry = AsyncMock()
        
        # Mock agent data
        registry.find_agents_by_capability = AsyncMock(return_value=[
            MagicMock(
                agent_id='agent_001',
                name='Python Developer Agent',
                capabilities=[MagicMock(name='python_coding')],
                metadata={'performance_score': 0.85}
            ),
            MagicMock(
                agent_id='agent_002', 
                name='JavaScript Developer Agent',
                capabilities=[MagicMock(name='javascript_coding')],
                metadata={'performance_score': 0.75}
            )
        ])
        
        return registry
    
    @pytest_asyncio.fixture
    async def mock_performance_history(self):
        """Mock performance history data."""
        return {
            'agent_001': {
                'python_coding': {'success_rate': 0.90, 'avg_time': 1.5},
                'debugging': {'success_rate': 0.85, 'avg_time': 2.0}
            },
            'agent_002': {
                'javascript_coding': {'success_rate': 0.80, 'avg_time': 1.8},
                'web_development': {'success_rate': 0.75, 'avg_time': 3.0}
            }
        }
    
    @pytest_asyncio.fixture
    async def agent_selection_engine(self, mock_ollama_client, mock_agent_registry):
        """Create Agent Selection Engine instance for testing."""
        # AgentSelectionEngine already imported at module level
        
        engine = AgentSelectionEngine(
            ollama_client=mock_ollama_client,
            agent_registry=mock_agent_registry
        )
        await engine.initialize()
        return engine
    
    @pytest.mark.asyncio
    async def test_analyze_task_complexity_simple_task(self, agent_selection_engine):
        """Test task complexity analysis for simple tasks."""
        simple_task = "Create a function that adds two numbers"
        
        complexity_score = await agent_selection_engine.analyze_task_complexity(simple_task)
        
        assert isinstance(complexity_score, TaskComplexityScore)
        assert 0.0 <= complexity_score.overall_complexity <= 1.0
        assert complexity_score.difficulty_level in [
            "very_easy", "easy", "medium", "hard", "very_hard"
        ]
        assert complexity_score.estimated_time_hours > 0
        assert complexity_score.confidence > 0.5
        assert len(complexity_score.reasoning) > 10
    
    @pytest.mark.asyncio
    async def test_analyze_task_complexity_complex_task(self, agent_selection_engine):
        """Test task complexity analysis for complex tasks."""
        complex_task = """
        Build a distributed microservices architecture with:
        - Event-driven communication using RabbitMQ
        - Redis caching layer with clustering
        - PostgreSQL with replication
        - Docker containerization
        - Kubernetes orchestration
        - CI/CD pipeline with automated testing
        """
        
        complexity_score = await agent_selection_engine.analyze_task_complexity(complex_task)
        
        assert isinstance(complexity_score, TaskComplexityScore)
        assert complexity_score.overall_complexity > 0.7  # Should be high complexity
        assert complexity_score.difficulty_level in ["hard", "very_hard"]
        assert complexity_score.estimated_time_hours > 20  # Complex tasks take longer
        assert complexity_score.technical_complexity > 0.7
    
    @pytest.mark.asyncio
    async def test_select_optimal_agent_based_on_complexity(self, agent_selection_engine):
        """Test optimal agent selection based on task complexity."""
        task_description = "Debug Python memory leak in web scraping application"
        
        recommendation = await agent_selection_engine.select_optimal_agent(
            task_description=task_description,
            required_capabilities=["python_coding", "debugging"]
        )
        
        assert isinstance(recommendation, AgentRecommendation)
        assert recommendation.agent_id is not None
        assert 0.0 <= recommendation.confidence_score <= 1.0
        assert 0.0 <= recommendation.predicted_success_rate <= 1.0
        assert recommendation.estimated_completion_time > 0
        assert len(recommendation.reasoning) > 10
        assert isinstance(recommendation.alternative_agents, list)
    
    @pytest.mark.asyncio
    async def test_predict_performance_with_historical_data(self, agent_selection_engine, mock_performance_history):
        """Test performance prediction using historical data."""
        with patch.object(agent_selection_engine, '_get_performance_history', return_value=mock_performance_history):
            prediction = await agent_selection_engine.predict_performance(
                agent_id="agent_001",
                task_type="python_coding"
            )
            
            assert isinstance(prediction, PerformancePrediction)
            assert prediction.agent_id == "agent_001"
            assert prediction.task_type == "python_coding"
            assert 0.0 <= prediction.success_probability <= 1.0
            assert prediction.estimated_time > 0
            assert isinstance(prediction.confidence_interval, tuple)
            assert len(prediction.factors_considered) > 0
    
    @pytest.mark.asyncio
    async def test_selection_reasoning_explanation(self, agent_selection_engine):
        """Test detailed reasoning explanation for agent selection."""
        task_description = "Implement REST API with authentication"
        
        reasoning = await agent_selection_engine.get_selection_reasoning(
            task_description=task_description,
            selected_agent_id="agent_001"
        )
        
        assert isinstance(reasoning, SelectionReasoning)
        assert len(reasoning.selection_criteria) > 0
        assert isinstance(reasoning.eliminated_agents, list)
        assert len(reasoning.final_decision_factors) > 0
        assert isinstance(reasoning.alternative_scenarios, list)
    
    @pytest.mark.asyncio
    async def test_response_time_under_50ms(self, agent_selection_engine):
        """Test that agent selection responds under 50ms for performance requirement."""
        task_description = "Simple function to validate email format"
        
        start_time = time.perf_counter()
        
        recommendation = await agent_selection_engine.select_optimal_agent(
            task_description=task_description,
            required_capabilities=["python_coding"]
        )
        
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000
        
        assert isinstance(recommendation, AgentRecommendation)
        assert response_time_ms < 50.0, f"Response time {response_time_ms:.2f}ms exceeds 50ms requirement"
    
    @pytest.mark.asyncio
    async def test_handles_empty_agent_registry(self, mock_ollama_client):
        """Test graceful handling when no agents are available."""
        empty_registry = AsyncMock()
        empty_registry.find_agents_by_capability = AsyncMock(return_value=[])
        
        from ltms.ml.agent_selection_engine import AgentSelectionEngine
        engine = AgentSelectionEngine(
            ollama_client=mock_ollama_client,
            agent_registry=empty_registry
        )
        await engine.initialize()
        
        recommendation = await engine.select_optimal_agent(
            task_description="Any task",
            required_capabilities=["any_capability"]
        )
        
        # Should return a meaningful response even with no agents
        assert recommendation is None or recommendation.confidence_score == 0.0
    
    @pytest.mark.asyncio
    async def test_handles_ollama_service_unavailable(self, mock_agent_registry):
        """Test graceful degradation when Qwen3-Coder service is unavailable."""
        failing_client = AsyncMock()
        failing_client.analyze_task_complexity = AsyncMock(side_effect=Exception("Ollama service unavailable"))
        
        from ltms.ml.agent_selection_engine import AgentSelectionEngine
        engine = AgentSelectionEngine(
            ollama_client=failing_client,
            agent_registry=mock_agent_registry
        )
        await engine.initialize()
        
        # Should fall back to basic complexity estimation
        complexity_score = await engine.analyze_task_complexity("Simple task")
        
        assert isinstance(complexity_score, TaskComplexityScore)
        assert complexity_score.confidence < 0.5  # Lower confidence for fallback
    
    @pytest.mark.asyncio  
    async def test_capability_matching_precision(self, agent_selection_engine):
        """Test precise capability matching for agent selection."""
        task_description = "Build machine learning model for text classification"
        
        recommendation = await agent_selection_engine.select_optimal_agent(
            task_description=task_description,
            required_capabilities=["machine_learning", "python_coding", "data_science"]
        )
        
        assert isinstance(recommendation, AgentRecommendation)
        # Should prioritize agents with ML capabilities over general coding agents
        if recommendation:
            assert recommendation.confidence_score > 0.0


class TestAgentSelectionEngineIntegration:
    """Integration tests for Agent Selection Engine with real services."""
    
    @pytest.mark.asyncio
    async def test_integration_with_redis_agent_registry(self):
        """Test integration with real Redis agent registry service."""
        # Import will fail initially - TDD approach
        from ltms.ml.agent_selection_engine import AgentSelectionEngine
        from ltms.services.agent_registry_service import get_agent_registry_service
        
        # Initialize real services
        agent_registry = await get_agent_registry_service()
        
        # This will use real Qwen3-Coder model
        engine = AgentSelectionEngine(agent_registry=agent_registry)
        await engine.initialize()
        
        # Test with real agent data
        task_description = "Simple Python function"
        recommendation = await engine.select_optimal_agent(
            task_description=task_description,
            required_capabilities=["python_coding"]
        )
        
        # Should work with real services
        assert recommendation is not None or len(await agent_registry.get_active_agents()) == 0
    
    @pytest.mark.asyncio
    async def test_qwen_coder_real_integration(self):
        """Test integration with real Qwen3-Coder-30B via Ollama."""
        from ltms.ml.agent_selection_engine import AgentSelectionEngine
        
        engine = AgentSelectionEngine()
        await engine.initialize()
        
        task_description = "Create a REST API endpoint for user authentication"
        complexity_score = await engine.analyze_task_complexity(task_description)
        
        assert isinstance(complexity_score, TaskComplexityScore)
        assert complexity_score.confidence > 0.5  # Real model should be confident
        assert complexity_score.overall_complexity > 0.0
        assert complexity_score.reasoning  # Should have detailed reasoning