"""
Comprehensive TDD tests for LegacyCodeAnalyzer class.
Tests the agent that will be extracted from legacy_removal_coordinated_agents.py.

Following TDD methodology: Tests written FIRST before implementation.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List


class TestLegacyCodeAnalyzer:
    """Test LegacyCodeAnalyzer agent class - to be extracted from legacy_removal_coordinated_agents.py"""
    
    def test_legacy_code_analyzer_creation(self):
        """Test LegacyCodeAnalyzer class can be instantiated with coordinator and state manager"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        from ltms.coordination.agent_coordination_framework import LTMCAgentCoordinator
        from ltms.coordination.agent_state_manager import LTMCAgentStateManager
        
        coordinator = Mock(spec=LTMCAgentCoordinator)
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock(spec=LTMCAgentStateManager)
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        assert analyzer.agent_id == "legacy_code_analyzer"
        assert analyzer.agent_type == "ltmc-legacy-analyzer"
        assert analyzer.coordinator == coordinator
        assert analyzer.state_manager == state_manager
        assert hasattr(analyzer, 'message_broker')
        assert hasattr(analyzer, 'legacy_decorators')
        assert hasattr(analyzer, 'functional_tools')
        assert hasattr(analyzer, 'analysis_report')
        assert isinstance(analyzer.legacy_decorators, list)
        assert isinstance(analyzer.functional_tools, list)
        assert isinstance(analyzer.analysis_report, dict)
    
    def test_initialize_agent_method_exists(self):
        """Test that initialize_agent method exists and is callable"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        assert hasattr(analyzer, 'initialize_agent')
        assert callable(analyzer.initialize_agent)
    
    def test_analyze_legacy_code_method_exists(self):
        """Test that analyze_legacy_code method exists and is callable"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"  
        state_manager = Mock()
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        assert hasattr(analyzer, 'analyze_legacy_code')
        assert callable(analyzer.analyze_legacy_code)
    
    @patch('ltms.coordination.legacy_code_analyzer.chat_action')
    @patch('ltms.coordination.legacy_code_analyzer.memory_action')
    def test_initialize_agent_successful_registration(self, mock_memory_action, mock_chat_action):
        """Test successful agent initialization and registration"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mocks
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        coordinator.register_agent.return_value = True
        
        state_manager = Mock()
        state_manager.create_agent_state.return_value = True
        
        mock_chat_action.return_value = {'success': True}
        mock_memory_action.return_value = {'success': True}
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        # Test initialization
        result = analyzer.initialize_agent()
        
        # Verify successful initialization
        assert result is True
        
        # Verify coordinator registration was called correctly
        coordinator.register_agent.assert_called_once_with(
            "legacy_code_analyzer",
            "ltmc-legacy-analyzer",
            task_scope=["legacy_analysis", "decorator_mapping", "code_structure_analysis"],
            outputs=["legacy_inventory", "functional_tool_mapping", "removal_recommendations"]
        )
        
        # Verify state manager create_agent_state was called
        state_manager.create_agent_state.assert_called_once()
        call_args = state_manager.create_agent_state.call_args
        assert call_args[0][0] == "legacy_code_analyzer"  # agent_id
        assert call_args[0][1] == AgentStatus.INITIALIZING  # status
        
        # Verify state data structure
        state_data = call_args[0][2]
        assert state_data["agent_id"] == "legacy_code_analyzer"
        assert state_data["task_scope"] == ["legacy_analysis", "decorator_mapping", "code_structure_analysis"]
        assert state_data["current_task"] == "initialization"
        
        # Verify LTMC tools were used
        assert mock_chat_action.called
        assert mock_memory_action.called
    
    def test_initialize_agent_coordinator_registration_failure(self):
        """Test initialization handles coordinator registration failure"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        # Setup coordinator to fail registration
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        coordinator.register_agent.return_value = False
        
        state_manager = Mock()
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        # Test initialization
        result = analyzer.initialize_agent()
        
        # Should return False on registration failure
        assert result is False
        
        # State manager should not be called if registration fails
        state_manager.create_agent_state.assert_not_called()
    
    def test_initialize_agent_state_creation_failure(self):
        """Test initialization handles state creation failure"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        # Setup successful coordinator but failing state manager
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        coordinator.register_agent.return_value = True
        
        state_manager = Mock()
        state_manager.create_agent_state.return_value = False
        
        with patch('ltms.coordination.legacy_code_analyzer.chat_action') as mock_chat:
            mock_chat.return_value = {'success': True}
            
            analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
            
            # Test initialization  
            result = analyzer.initialize_agent()
            
            # Should still return True even if state creation fails
            # (agent can continue without state management)
            assert result is True
    
    @patch('ltms.coordination.legacy_code_analyzer.pattern_action')
    @patch('ltms.coordination.legacy_code_analyzer.unix_action')
    @patch('ltms.coordination.legacy_code_analyzer.memory_action')
    def test_analyze_legacy_code_file_scanning(self, mock_memory_action, mock_unix_action, mock_pattern_action):
        """Test legacy code analysis file scanning functionality"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        # Setup mock responses
        mock_unix_action.return_value = {
            'success': True,
            'files': ['ltms/tools/consolidated.py', 'ltms/tools/legacy.py']
        }
        
        mock_pattern_action.return_value = {
            'success': True,
            'functions': [
                {'name': 'legacy_tool_1', 'decorators': ['@mcp.tool']},
                {'name': 'functional_tool_1', 'decorators': []}
            ]
        }
        
        mock_memory_action.return_value = {'success': True}
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        # Test analysis
        result = analyzer.analyze_legacy_code()
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'legacy_decorators' in result
        assert 'functional_tools' in result
        assert 'analysis_report' in result
        
        # Verify LTMC tools were used
        assert mock_unix_action.called
        assert mock_pattern_action.called
        assert mock_memory_action.called
    
    @patch('ltms.coordination.legacy_code_analyzer.pattern_action')
    def test_analyze_legacy_code_decorator_detection(self, mock_pattern_action):
        """Test that legacy @mcp.tool decorators are properly detected"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        # Setup mock to return legacy decorators
        mock_pattern_action.return_value = {
            'success': True,
            'functions': [
                {
                    'name': 'legacy_memory_tool',
                    'file': 'ltms/tools/legacy.py',
                    'line': 45,
                    'decorators': ['@mcp.tool'],
                    'signature': 'def legacy_memory_tool(action: str) -> dict'
                },
                {
                    'name': 'consolidated_memory_action', 
                    'file': 'ltms/tools/consolidated.py',
                    'line': 23,
                    'decorators': [],
                    'signature': 'def memory_action(action: str) -> dict'
                }
            ]
        }
        
        with patch('ltms.coordination.legacy_code_analyzer.unix_action') as mock_unix:
            mock_unix.return_value = {'success': True, 'files': ['test.py']}
            
            with patch('ltms.coordination.legacy_code_analyzer.memory_action') as mock_memory:
                mock_memory.return_value = {'success': True}
                
                analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
                result = analyzer.analyze_legacy_code()
                
                # Verify legacy decorator was identified
                assert len(analyzer.legacy_decorators) > 0
                legacy_tool = analyzer.legacy_decorators[0]
                assert legacy_tool['name'] == 'legacy_memory_tool'
                assert '@mcp.tool' in legacy_tool['decorators']
                
                # Verify functional tool was identified
                assert len(analyzer.functional_tools) > 0
                functional_tool = analyzer.functional_tools[0] 
                assert functional_tool['name'] == 'consolidated_memory_action'
                assert functional_tool['decorators'] == []
    
    @patch('ltms.coordination.legacy_code_analyzer.memory_action')
    def test_analyze_legacy_code_ltmc_storage(self, mock_memory_action):
        """Test that analysis results are stored in LTMC memory"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        mock_memory_action.return_value = {'success': True, 'doc_id': 123}
        
        with patch('ltms.coordination.legacy_code_analyzer.unix_action') as mock_unix:
            mock_unix.return_value = {'success': True, 'files': []}
            
            with patch('ltms.coordination.legacy_code_analyzer.pattern_action') as mock_pattern:
                mock_pattern.return_value = {'success': True, 'functions': []}
                
                analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
                analyzer.analyze_legacy_code()
                
                # Verify memory_action was called for storage
                assert mock_memory_action.called
                
                # Check if storage call has correct structure
                storage_calls = [call for call in mock_memory_action.call_args_list if call[1].get('action') == 'store']
                assert len(storage_calls) > 0
                
                storage_call = storage_calls[0]
                assert 'legacy_analysis' in storage_call[1]['file_name']
                assert 'tags' in storage_call[1]
                assert 'legacy_analysis' in storage_call[1]['tags']
    
    def test_send_analysis_to_next_agent_method_exists(self):
        """Test that send_analysis_to_next_agent method exists"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        assert hasattr(analyzer, 'send_analysis_to_next_agent')
        assert callable(analyzer.send_analysis_to_next_agent)
    
    @patch('ltms.coordination.legacy_code_analyzer.chat_action')
    def test_send_analysis_to_next_agent_message_sending(self, mock_chat_action):
        """Test sending analysis results to next agent in workflow"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        mock_chat_action.return_value = {'success': True}
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        # Set up some analysis results
        analyzer.legacy_decorators = [{'name': 'test_tool', 'decorators': ['@mcp.tool']}]
        analyzer.functional_tools = [{'name': 'real_tool', 'decorators': []}]
        analyzer.analysis_report = {'total_legacy': 1, 'total_functional': 1}
        
        # Test sending to next agent
        result = analyzer.send_analysis_to_next_agent("safety_validator")
        
        # Verify successful sending
        assert result is True
        
        # Verify chat_action was called for message logging
        assert mock_chat_action.called
        call_args = mock_chat_action.call_args
        assert call_args[1]['action'] == 'log'
        assert 'legacy_code_analyzer' in call_args[1]['content']
        assert 'safety_validator' in call_args[1]['content']
    
    def test_message_broker_integration(self):
        """Test that analyzer properly integrates with message broker"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        from ltms.coordination.mcp_communication_patterns import LTMCMessageBroker
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        # Verify message broker is created
        assert hasattr(analyzer, 'message_broker')
        assert isinstance(analyzer.message_broker, LTMCMessageBroker)
        assert analyzer.message_broker.conversation_id == "test_conversation"
    
    @patch('ltms.coordination.legacy_code_analyzer.graph_action')
    def test_analysis_graph_relationships(self, mock_graph_action):
        """Test that analysis creates proper graph relationships"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        mock_graph_action.return_value = {'success': True}
        
        with patch('ltms.coordination.legacy_code_analyzer.unix_action') as mock_unix:
            mock_unix.return_value = {'success': True, 'files': []}
            
            with patch('ltms.coordination.legacy_code_analyzer.pattern_action') as mock_pattern:
                mock_pattern.return_value = {'success': True, 'functions': []}
                
                with patch('ltms.coordination.legacy_code_analyzer.memory_action') as mock_memory:
                    mock_memory.return_value = {'success': True}
                    
                    analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
                    analyzer.analyze_legacy_code()
                    
                    # Verify graph relationships were created
                    assert mock_graph_action.called
                    
                    # Check for entity relationship creation
                    graph_calls = mock_graph_action.call_args_list
                    link_calls = [call for call in graph_calls if call[1].get('action') == 'link']
                    assert len(link_calls) > 0


class TestLegacyCodeAnalyzerIntegration:
    """Test integration scenarios for LegacyCodeAnalyzer"""
    
    @patch('ltms.coordination.legacy_code_analyzer.memory_action')
    @patch('ltms.coordination.legacy_code_analyzer.pattern_action') 
    @patch('ltms.coordination.legacy_code_analyzer.unix_action')
    @patch('ltms.coordination.legacy_code_analyzer.chat_action')
    def test_complete_analysis_workflow(self, mock_chat, mock_unix, mock_pattern, mock_memory):
        """Test complete legacy code analysis workflow"""
        from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup comprehensive mocks
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        coordinator.register_agent.return_value = True
        
        state_manager = Mock()
        state_manager.create_agent_state.return_value = True
        
        mock_chat.return_value = {'success': True}
        mock_memory.return_value = {'success': True, 'doc_id': 123}
        mock_unix.return_value = {
            'success': True,
            'files': ['ltms/tools/legacy.py', 'ltms/tools/consolidated.py']
        }
        mock_pattern.return_value = {
            'success': True,
            'functions': [
                {'name': 'legacy_tool', 'decorators': ['@mcp.tool'], 'file': 'legacy.py'},
                {'name': 'functional_tool', 'decorators': [], 'file': 'consolidated.py'}
            ]
        }
        
        analyzer = LegacyCodeAnalyzer(coordinator, state_manager)
        
        # Test complete workflow
        init_result = analyzer.initialize_agent()
        assert init_result is True
        
        analysis_result = analyzer.analyze_legacy_code()
        assert analysis_result['success'] is True
        
        send_result = analyzer.send_analysis_to_next_agent("safety_validator")
        assert send_result is True
        
        # Verify all LTMC tools were used appropriately
        assert mock_chat.called
        assert mock_unix.called
        assert mock_pattern.called
        assert mock_memory.called


# Pytest fixtures for common test data
@pytest.fixture
def mock_coordinator():
    """Fixture providing a mock LTMCAgentCoordinator"""
    coordinator = Mock()
    coordinator.conversation_id = "test_conversation"
    coordinator.register_agent.return_value = True
    return coordinator

@pytest.fixture
def mock_state_manager():
    """Fixture providing a mock LTMCAgentStateManager"""
    state_manager = Mock()
    state_manager.create_agent_state.return_value = True
    return state_manager

@pytest.fixture
def analyzer_instance(mock_coordinator, mock_state_manager):
    """Fixture providing a LegacyCodeAnalyzer instance"""
    from ltms.coordination.legacy_code_analyzer import LegacyCodeAnalyzer
    return LegacyCodeAnalyzer(mock_coordinator, mock_state_manager)

@pytest.fixture
def sample_legacy_functions():
    """Fixture providing sample legacy function data"""
    return [
        {
            'name': 'legacy_memory_tool',
            'file': 'ltms/tools/legacy.py',
            'line': 45,
            'decorators': ['@mcp.tool'],
            'signature': 'def legacy_memory_tool(action: str) -> dict'
        },
        {
            'name': 'legacy_todo_tool',
            'file': 'ltms/tools/legacy.py', 
            'line': 78,
            'decorators': ['@mcp.tool'],
            'signature': 'def legacy_todo_tool(task: str) -> dict'
        }
    ]

@pytest.fixture
def sample_functional_tools():
    """Fixture providing sample functional tool data"""
    return [
        {
            'name': 'memory_action',
            'file': 'ltms/tools/consolidated.py',
            'line': 23,
            'decorators': [],
            'signature': 'def memory_action(action: str) -> dict'
        }
    ]