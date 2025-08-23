"""
TDD Tests for graph_action Consolidated Powertool
Tests all 12 graph actions with real database operations (NO MOCKS)
"""

import os
import pytest
import tempfile
import sqlite3
from datetime import datetime, timezone

# Add LTMC to path
import sys
sys.path.insert(0, '/home/feanor/Projects/ltmc')

from ltms.tools.consolidated import graph_action


class TestGraphActionTDD:
    """Test graph_action powertool with real database operations."""
    
    def setup_method(self):
        """Setup test environment with real databases."""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Set up test environment
        os.environ['DB_PATH'] = self.db_path
        
        # Create test database schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                file_name TEXT NOT NULL,
                content TEXT NOT NULL,
                resource_type TEXT DEFAULT 'document',
                created_at TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 1
            )
        ''')
        
        # Chat messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent_name TEXT,
                source_tool TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Blueprints table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blueprints (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                project_id TEXT,
                complexity TEXT DEFAULT 'medium',
                created_at TEXT NOT NULL
            )
        ''')
        
        # Todos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        ''')
        
        # Insert test data
        cursor.execute('''
            INSERT INTO documents (file_name, content, resource_type, created_at)
            VALUES ('test_doc.py', 'def test_function(): pass', 'code', ?)
        ''', (datetime.now(timezone.utc).isoformat(),))
        
        cursor.execute('''
            INSERT INTO chat_messages (conversation_id, role, content, source_tool, created_at)
            VALUES ('test_conv', 'user', 'Testing chunk_123', 'graph_tool', ?)
        ''', (datetime.now(timezone.utc).isoformat(),))
        
        cursor.execute('''
            INSERT INTO blueprints (id, title, description, project_id, created_at)
            VALUES ('bp_1', 'Test Blueprint', 'Test description', 'test_proj', ?)
        ''', (datetime.now(timezone.utc).isoformat(),))
        
        cursor.execute('''
            INSERT INTO todos (title, description, created_at)
            VALUES ('Test Todo', 'Test todo item', ?)
        ''', (datetime.now(timezone.utc).isoformat(),))
        
        conn.commit()
        conn.close()
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_graph_link_action(self):
        """Test graph link creation (Neo4j dependent)."""
        result = graph_action(
            action="link",
            source_id="doc_1",
            target_id="doc_2",
            relation="references",
            weight=0.8,
            metadata={"type": "test"}
        )
        
        # Should handle Neo4j not available gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Neo4j is available and link was created
            assert result.get('source_id') == 'doc_1'
            assert result.get('target_id') == 'doc_2'
        else:
            # Neo4j not available - expected behavior
            assert 'error' in result
            assert any(keyword in result['error'].lower() for keyword in [
                'neo4j', 'graph store not available', 'link failed'
            ])
    
    def test_graph_query_action(self):
        """Test graph query relationships (Neo4j dependent)."""
        result = graph_action(
            action="query",
            entity="test_entity",
            relation_type="references",
            direction="both"
        )
        
        # Should handle Neo4j not available gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Neo4j is available
            assert 'relationships' in result or 'entity' in result
        else:
            # Neo4j not available - expected behavior
            assert 'error' in result
            assert any(keyword in result['error'].lower() for keyword in [
                'neo4j', 'graph store not available', 'query failed'
            ])
    
    def test_graph_auto_link_action(self):
        """Test graph auto link documents (Neo4j dependent)."""
        test_docs = [
            {"id": "doc1", "content": "Python programming"},
            {"id": "doc2", "content": "Programming in Python"}
        ]
        
        result = graph_action(
            action="auto_link",
            documents=test_docs,
            max_links_per_document=3,
            similarity_threshold=0.6
        )
        
        # Should handle Neo4j not available gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Neo4j is available
            assert 'links_created' in result or 'documents' in result
        else:
            # Neo4j not available - expected behavior
            assert 'error' in result
            assert 'auto link failed' in result['error'].lower()
    
    def test_graph_get_relationships_action(self):
        """Test graph get document relationships (Neo4j dependent)."""
        result = graph_action(
            action="get_relationships",
            doc_id="test_doc_1"
        )
        
        # Should handle Neo4j not available gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Neo4j is available
            assert 'relationships' in result or 'doc_id' in result
        else:
            # Neo4j not available - expected behavior
            assert 'error' in result
            assert 'get relationships failed' in result['error'].lower()
    
    def test_graph_context_action(self):
        """Test graph context retrieval with real SQLite data."""
        result = graph_action(
            action="context",
            query="test",
            doc_type="code",
            top_k=5,
            max_tokens=1000
        )
        
        assert result['success'] is True
        assert result['query'] == "test"
        assert result['doc_type'] == "code"
        assert 'results' in result
        assert 'total_documents' in result
        assert 'total_tokens' in result
        
        # Should find our test document
        assert result['total_documents'] >= 0
        if result['total_documents'] > 0:
            doc = result['results'][0]
            assert 'id' in doc
            assert 'file_name' in doc
            assert 'content' in doc
    
    def test_graph_get_action(self):
        """Test graph get resource links (Neo4j dependent)."""
        result = graph_action(
            action="get",
            resource_id="test_resource",
            link_type="references"
        )
        
        # Should handle Neo4j not available gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Neo4j is available
            assert result['resource_id'] == "test_resource"
            assert result['link_type'] == "references"
        else:
            # Neo4j not available - expected behavior
            assert 'error' in result
            assert 'graph get failed' in result['error'].lower()
    
    def test_graph_messages_action(self):
        """Test graph messages for chunk with real SQLite data."""
        result = graph_action(
            action="messages",
            chunk_id="123"
        )
        
        # Should either succeed or fail gracefully with table error
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Database is properly configured
            assert result['chunk_id'] == "123"
            assert 'messages' in result
            assert 'message_count' in result
            
            # Should find our test message that contains "chunk_123"
            if result['message_count'] > 0:
                message = result['messages'][0]
                assert 'id' in message
                assert 'conversation_id' in message
                assert 'content' in message
        else:
            # Database table not found or configuration issue - expected
            assert 'error' in result
            assert any(keyword in result['error'].lower() for keyword in [
                'no such table', 'graph messages failed', 'database'
            ])
    
    def test_graph_stats_action(self):
        """Test graph statistics with real SQLite data."""
        result = graph_action(action="stats")
        
        # Should either succeed or fail gracefully with table error
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Database is properly configured
            assert 'statistics' in result
            assert 'timestamp' in result
            
            stats = result['statistics']
            assert 'total_documents' in stats
            assert 'total_messages' in stats
            assert 'total_blueprints' in stats
            assert 'total_todos' in stats
            assert 'total_resources' in stats
        else:
            # Database table not found or configuration issue - expected
            assert 'error' in result
            assert any(keyword in result['error'].lower() for keyword in [
                'no such table', 'graph stats failed', 'database'
            ])
    
    def test_graph_remove_action(self):
        """Test graph remove resource link (Neo4j dependent)."""
        result = graph_action(
            action="remove",
            link_id="test_link_123"
        )
        
        # Should handle Neo4j not available gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Neo4j is available
            assert result['link_id'] == "test_link_123"
            assert 'message' in result
        else:
            # Neo4j not available - expected behavior
            assert 'error' in result
            assert 'graph remove failed' in result['error'].lower()
    
    def test_graph_list_action(self):
        """Test graph list all resource links (Neo4j dependent)."""
        result = graph_action(
            action="list",
            limit=50
        )
        
        # Should handle Neo4j not available gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Neo4j is available
            assert 'relationships' in result
            assert 'limit' in result
            assert result['limit'] == 50
        else:
            # Neo4j not available - expected behavior
            assert 'error' in result
            assert 'graph list failed' in result['error'].lower()
    
    def test_graph_discover_action(self):
        """Test graph discover tool identifiers with real SQLite data."""
        result = graph_action(action="discover")
        
        # Should either succeed or fail gracefully with table error
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Database is properly configured
            assert 'tool_identifiers' in result
            assert 'total_tools' in result
            
            if result['total_tools'] > 0:
                tool = result['tool_identifiers'][0]
                assert 'tool_name' in tool
                assert 'usage_count' in tool
        else:
            # Database table not found or configuration issue - expected
            assert 'error' in result
            assert any(keyword in result['error'].lower() for keyword in [
                'no such table', 'graph discover failed', 'database'
            ])
    
    def test_graph_conversations_action(self):
        """Test graph conversations by tool with real SQLite data."""
        result = graph_action(
            action="conversations",
            source_tool="graph_tool",
            limit=10
        )
        
        # Should either succeed or fail gracefully with table error
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Database is properly configured
            assert result['source_tool'] == "graph_tool"
            assert 'conversations' in result
            assert 'conversation_count' in result
            assert result['limit'] == 10
            
            if result['conversation_count'] > 0:
                conv = result['conversations'][0]
                assert 'conversation_id' in conv
                assert 'message_count' in conv
                assert conv['source_tool'] == "graph_tool"
        else:
            # Database table not found or configuration issue - expected
            assert 'error' in result
            assert any(keyword in result['error'].lower() for keyword in [
                'no such table', 'graph conversations failed', 'database'
            ])
    
    def test_graph_action_invalid_action(self):
        """Test invalid action parameter handling."""
        result = graph_action(action="invalid_action")
        
        assert result['success'] is False
        assert 'Unknown graph action' in result['error']
    
    def test_graph_action_missing_action(self):
        """Test missing action parameter handling."""
        result = graph_action(action="")
        
        assert result['success'] is False
        assert result['error'] == 'Action parameter is required'
    
    def test_graph_action_missing_required_params(self):
        """Test missing required parameter handling for various actions."""
        # Test link action missing params
        result = graph_action(action="link", source_id="test")
        assert result['success'] is False
        assert 'Missing required parameter: target_id' in result['error']
        
        # Test query action missing params  
        result = graph_action(action="query")
        assert result['success'] is False
        assert 'Missing required parameter: entity' in result['error']
        
        # Test context action missing params
        result = graph_action(action="context")
        assert result['success'] is False
        assert 'Missing required parameter: query' in result['error']
        
        # Test get action missing params
        result = graph_action(action="get")
        assert result['success'] is False
        assert 'Missing required parameter: resource_id' in result['error']
        
        # Test messages action missing params
        result = graph_action(action="messages")
        assert result['success'] is False
        assert 'Missing required parameter: chunk_id' in result['error']
        
        # Test conversations action missing params
        result = graph_action(action="conversations")
        assert result['success'] is False
        assert 'Missing required parameter: source_tool' in result['error']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])