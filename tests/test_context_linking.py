"""Tests for context linking functionality."""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime
from typing import List, Dict, Any

# Import the functions we'll implement
from ltms.database.context_linking import (
    store_context_links,
    get_context_links_for_message,
    get_messages_for_chunk,
    create_context_links_table
)


class TestContextLinking:
    """Test suite for context linking functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create connection and tables
        conn = sqlite3.connect(db_path)
        create_context_links_table(conn)
        
        # Create test data
        cursor = conn.cursor()
        
        # Create Resources table
        cursor.execute('''CREATE TABLE IF NOT EXISTS Resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            type TEXT NOT NULL,
            created_at TEXT NOT NULL
        )''')
        
        # Create ResourceChunks table
        cursor.execute('''CREATE TABLE IF NOT EXISTS ResourceChunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER,
            chunk_text TEXT NOT NULL,
            vector_id INTEGER UNIQUE NOT NULL,
            FOREIGN KEY(resource_id) REFERENCES Resources(id)
        )''')
        
        # Create ChatHistory table
        cursor.execute('''CREATE TABLE IF NOT EXISTS ChatHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )''')
        
        # Insert test data
        cursor.execute(
            "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
            ("test_doc.txt", "document", datetime.now().isoformat())
        )
        resource_id = cursor.lastrowid
        
        # Create multiple chunks for testing
        for i in range(1, 4):  # Create chunks with IDs 1, 2, 3
            cursor.execute(
                "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
                (resource_id, f"Test chunk content {i}", 100 + i)
            )
        
        # Create multiple messages for testing
        cursor.execute(
            "INSERT INTO ChatHistory (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            ("test_conv", "user", "What is this about?", datetime.now().isoformat())
        )
        message_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO ChatHistory (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            ("test_conv", "assistant", "This is about testing.", datetime.now().isoformat())
        )
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    def test_create_context_links_table(self, temp_db):
        """Test that context links table is created correctly."""
        conn = sqlite3.connect(temp_db)
        create_context_links_table(conn)
        
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ContextLinks'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 'ContextLinks'
        
        # Check table structure
        cursor.execute("PRAGMA table_info(ContextLinks)")
        columns = cursor.fetchall()
        
        expected_columns = ['id', 'message_id', 'chunk_id']
        actual_columns = [col[1] for col in columns]
        
        for expected in expected_columns:
            assert expected in actual_columns
        
        conn.close()
    
    def test_store_context_links(self, temp_db):
        """Test storing context links between messages and chunks."""
        conn = sqlite3.connect(temp_db)
        create_context_links_table(conn)
        
        # Store context links
        message_id = 1
        chunk_ids = [1, 2, 3]
        
        result = store_context_links(conn, message_id, chunk_ids)
        
        assert result['success'] is True
        assert result['links_created'] == 3
        
        # Verify links were stored
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message_id, chunk_id FROM ContextLinks WHERE message_id = ?",
            (message_id,)
        )
        links = cursor.fetchall()
        
        assert len(links) == 3
        stored_chunk_ids = [link[1] for link in links]
        assert set(stored_chunk_ids) == set(chunk_ids)
        
        conn.close()
    
    def test_store_context_links_invalid_message(self, temp_db):
        """Test storing context links with invalid message ID."""
        conn = sqlite3.connect(temp_db)
        create_context_links_table(conn)
        
        # Try to store links for non-existent message
        message_id = 999
        chunk_ids = [1, 2, 3]
        
        result = store_context_links(conn, message_id, chunk_ids)
        
        assert result['success'] is False
        assert 'error' in result
        
        conn.close()
    
    def test_get_context_links_for_message(self, temp_db):
        """Test retrieving context links for a specific message."""
        conn = sqlite3.connect(temp_db)
        create_context_links_table(conn)
        
        # Store some context links
        message_id = 1
        chunk_ids = [1, 2]
        store_context_links(conn, message_id, chunk_ids)
        
        # Retrieve context links
        result = get_context_links_for_message(conn, message_id)
        
        assert result['success'] is True
        assert len(result['links']) == 2
        
        # Verify chunk IDs
        retrieved_chunk_ids = [link['chunk_id'] for link in result['links']]
        assert set(retrieved_chunk_ids) == set(chunk_ids)
        
        conn.close()
    
    def test_get_context_links_for_nonexistent_message(self, temp_db):
        """Test retrieving context links for non-existent message."""
        conn = sqlite3.connect(temp_db)
        create_context_links_table(conn)
        
        result = get_context_links_for_message(conn, 999)
        
        assert result['success'] is True
        assert len(result['links']) == 0
        
        conn.close()
    
    def test_get_messages_for_chunk(self, temp_db):
        """Test retrieving messages that used a specific chunk."""
        conn = sqlite3.connect(temp_db)
        create_context_links_table(conn)
        
        # Store context links for multiple messages
        store_context_links(conn, 1, [1, 2])
        store_context_links(conn, 2, [2, 3])
        
        # Get messages for chunk 2
        result = get_messages_for_chunk(conn, 2)
        
        assert result['success'] is True
        assert len(result['messages']) == 2
        
        # Verify message IDs
        message_ids = [msg['message_id'] for msg in result['messages']]
        assert set(message_ids) == {1, 2}
        
        conn.close()
    
    def test_get_messages_for_nonexistent_chunk(self, temp_db):
        """Test retrieving messages for non-existent chunk."""
        conn = sqlite3.connect(temp_db)
        create_context_links_table(conn)
        
        result = get_messages_for_chunk(conn, 999)
        
        assert result['success'] is True
        assert len(result['messages']) == 0
        
        conn.close()
    
    def test_context_linking_with_real_data(self, temp_db):
        """Test context linking with realistic data flow."""
        conn = sqlite3.connect(temp_db)
        create_context_links_table(conn)
        
        # Simulate a conversation flow
        cursor = conn.cursor()
        
        # Add a chat message
        cursor.execute(
            "INSERT INTO ChatHistory (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            ("conv_123", "user", "What is machine learning?", datetime.now().isoformat())
        )
        message_id = cursor.lastrowid
        
        # Store context links (simulating chunks used to answer the question)
        chunk_ids = [1, 2, 3]
        result = store_context_links(conn, message_id, chunk_ids)
        
        assert result['success'] is True
        assert result['links_created'] == 3
        
        # Retrieve the context links
        links_result = get_context_links_for_message(conn, message_id)
        assert links_result['success'] is True
        assert len(links_result['links']) == 3
        
        # Get messages for one of the chunks
        messages_result = get_messages_for_chunk(conn, 1)
        assert messages_result['success'] is True
        assert len(messages_result['messages']) == 1
        assert messages_result['messages'][0]['message_id'] == message_id
        
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__])
