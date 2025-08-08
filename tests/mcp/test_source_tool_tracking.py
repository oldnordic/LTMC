"""Test source tool tracking functionality in LTMC MCP server."""

import pytest
import tempfile
import os
from unittest.mock import patch

from ltms.mcp_server import (
    log_chat,
    get_chats_by_tool,
    list_tool_identifiers,
    get_tool_conversations
)
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables
from ltms.services.context_service import log_chat_message


class TestSourceToolTracking:
    """Test suite for source tool tracking functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Set environment variable for the test database
        with patch.dict(os.environ, {"DB_PATH": db_path}):
            # Create tables
            conn = get_db_connection(db_path)
            create_tables(conn)
            close_db_connection(conn)
            
            yield db_path
        
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_log_chat_with_source_tool(self, temp_db):
        """Test logging chat messages with source tool tracking."""
        # Test with source_tool parameter
        result = log_chat(
            conversation_id="test-conv-1",
            role="user",
            content="Test message from Claude Code",
            source_tool="claude-code"
        )
        
        assert result["success"] is True
        assert "message_id" in result
        
        # Verify in database
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT source_tool FROM ChatHistory WHERE id = ?", (result["message_id"],))
        row = cursor.fetchone()
        close_db_connection(conn)
        
        assert row is not None
        assert row[0] == "claude-code"

    def test_log_chat_without_source_tool(self, temp_db):
        """Test logging chat messages without source tool (backward compatibility)."""
        result = log_chat(
            conversation_id="test-conv-2",
            role="user",
            content="Test message without source tool"
        )
        
        assert result["success"] is True
        assert "message_id" in result
        
        # Verify in database
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT source_tool FROM ChatHistory WHERE id = ?", (result["message_id"],))
        row = cursor.fetchone()
        close_db_connection(conn)
        
        assert row is not None
        assert row[0] is None  # Should be NULL for backward compatibility

    def test_log_chat_message_direct_with_source_tool(self, temp_db):
        """Test direct log_chat_message function with source_tool parameter."""
        conn = get_db_connection(temp_db)
        
        message_id = log_chat_message(
            conn,
            conversation_id="test-conv-3",
            role="ai",
            content="AI response from Cursor",
            source_tool="cursor"
        )
        
        # Verify in database
        cursor = conn.cursor()
        cursor.execute(
            "SELECT conversation_id, role, content, source_tool FROM ChatHistory WHERE id = ?",
            (message_id,)
        )
        row = cursor.fetchone()
        close_db_connection(conn)
        
        assert row is not None
        assert row[0] == "test-conv-3"
        assert row[1] == "ai"
        assert row[2] == "AI response from Cursor"
        assert row[3] == "cursor"

    def test_get_chats_by_tool(self, temp_db):
        """Test retrieving chat messages by source tool."""
        # Add test messages from different tools
        log_chat("conv-1", "user", "Message 1 from Claude Code", source_tool="claude-code")
        log_chat("conv-1", "ai", "Response 1", source_tool="claude-code")
        log_chat("conv-2", "user", "Message 1 from Cursor", source_tool="cursor")
        log_chat("conv-2", "user", "Message 2 from Cursor", source_tool="cursor")
        log_chat("conv-3", "user", "Message without source tool")
        
        # Test getting messages from Claude Code
        result = get_chats_by_tool("claude-code", limit=10)
        
        assert result["success"] is True
        assert result["count"] == 2
        assert result["source_tool"] == "claude-code"
        assert len(result["messages"]) == 2
        
        # Verify messages are ordered by timestamp (newest first)
        messages = result["messages"]
        assert messages[0]["role"] == "ai"
        assert messages[1]["role"] == "user"
        assert all(msg["source_tool"] == "claude-code" for msg in messages)

    def test_get_chats_by_tool_with_conversation_filter(self, temp_db):
        """Test retrieving chat messages by source tool with conversation filter."""
        # Add test messages
        log_chat("conv-1", "user", "Message 1", source_tool="cursor")
        log_chat("conv-2", "user", "Message 2", source_tool="cursor")
        log_chat("conv-1", "ai", "Response 1", source_tool="cursor")
        
        # Test with conversation filter
        result = get_chats_by_tool("cursor", limit=10, conversation_id="conv-1")
        
        assert result["success"] is True
        assert result["count"] == 2
        assert all(msg["conversation_id"] == "conv-1" for msg in result["messages"])
        assert all(msg["source_tool"] == "cursor" for msg in result["messages"])

    def test_get_chats_by_tool_validation(self, temp_db):
        """Test input validation for get_chats_by_tool."""
        # Test missing source_tool
        result = get_chats_by_tool("", limit=10)
        assert result["success"] is False
        assert "source_tool is required" in result["error"]
        
        # Test invalid limit
        result = get_chats_by_tool("claude-code", limit=0)
        assert result["success"] is False
        assert "limit must be between 1 and 1000" in result["error"]
        
        result = get_chats_by_tool("claude-code", limit=1001)
        assert result["success"] is False
        assert "limit must be between 1 and 1000" in result["error"]

    def test_list_tool_identifiers(self, temp_db):
        """Test listing all tool identifiers and usage statistics."""
        # Add test messages from different tools
        log_chat("conv-1", "user", "Message 1", source_tool="claude-code")
        log_chat("conv-1", "ai", "Response 1", source_tool="claude-code")
        log_chat("conv-2", "user", "Message 2", source_tool="cursor")
        log_chat("conv-3", "user", "Message 3", source_tool="vscode")
        log_chat("conv-4", "user", "Message without source tool")  # No source_tool
        
        result = list_tool_identifiers()
        
        assert result["success"] is True
        assert result["total_tools"] == 3  # claude-code, cursor, vscode
        assert result["total_messages"] == 4  # Excludes message without source_tool
        
        # Check standard identifiers are present
        assert "claude-code" in result["standard_identifiers"]
        assert "cursor" in result["standard_identifiers"]
        assert "vscode" in result["standard_identifiers"]
        
        # Verify tool statistics
        tools = {tool["identifier"]: tool for tool in result["tools"]}
        assert "claude-code" in tools
        assert tools["claude-code"]["message_count"] == 2
        assert tools["claude-code"]["conversation_count"] == 1
        assert tools["claude-code"]["status"] == "active"

    def test_get_tool_conversations(self, temp_db):
        """Test getting conversation summaries for a specific tool."""
        # Add test messages across different conversations
        log_chat("conv-1", "user", "Message 1", source_tool="claude-code")
        log_chat("conv-1", "ai", "Response 1", source_tool="claude-code")
        log_chat("conv-2", "user", "Message 2", source_tool="claude-code")
        log_chat("conv-2", "ai", "Response 2", source_tool="claude-code")
        log_chat("conv-2", "user", "Message 3", source_tool="claude-code")
        log_chat("conv-3", "user", "Message from cursor", source_tool="cursor")
        
        result = get_tool_conversations("claude-code", limit=10)
        
        assert result["success"] is True
        assert result["count"] == 2  # conv-1 and conv-2
        assert result["source_tool"] == "claude-code"
        
        # Verify conversation summaries
        conversations = {conv["conversation_id"]: conv for conv in result["conversations"]}
        assert "conv-1" in conversations
        assert "conv-2" in conversations
        assert "conv-3" not in conversations  # Different source tool
        
        # Check message counts
        assert conversations["conv-1"]["message_count"] == 2
        assert conversations["conv-2"]["message_count"] == 3
        
        # Check roles
        assert set(conversations["conv-1"]["roles"]) == {"user", "ai"}
        assert set(conversations["conv-2"]["roles"]) == {"user", "ai"}

    def test_get_tool_conversations_validation(self, temp_db):
        """Test input validation for get_tool_conversations."""
        # Test missing source_tool
        result = get_tool_conversations("", limit=10)
        assert result["success"] is False
        assert "source_tool is required" in result["error"]
        
        # Test invalid limit
        result = get_tool_conversations("claude-code", limit=0)
        assert result["success"] is False
        assert "limit must be between 1 and 200" in result["error"]
        
        result = get_tool_conversations("claude-code", limit=201)
        assert result["success"] is False
        assert "limit must be between 1 and 200" in result["error"]

    def test_backward_compatibility(self, temp_db):
        """Test that existing functionality still works without source_tool."""
        # Old-style log_chat call without source_tool
        result = log_chat(
            conversation_id="test-conv",
            role="user",
            content="Test message",
            agent_name="test-agent",
            metadata={"key": "value"}
        )
        
        assert result["success"] is True
        
        # Verify message was stored correctly
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT conversation_id, role, content, agent_name, source_tool FROM ChatHistory WHERE id = ?",
            (result["message_id"],)
        )
        row = cursor.fetchone()
        close_db_connection(conn)
        
        assert row is not None
        assert row[0] == "test-conv"
        assert row[1] == "user"
        assert row[2] == "Test message"
        assert row[3] == "test-agent"
        assert row[4] is None  # source_tool should be NULL

    def test_multiple_tool_message_flow(self, temp_db):
        """Test a realistic flow with messages from multiple tools."""
        # Simulate a development session with Claude Code and Cursor
        
        # Claude Code session
        log_chat("dev-session-1", "user", "Create a function to validate email", source_tool="claude-code")
        log_chat("dev-session-1", "ai", "Here's an email validation function...", source_tool="claude-code")
        
        # Switch to Cursor for the same conversation
        log_chat("dev-session-1", "user", "Add unit tests for this function", source_tool="cursor")
        log_chat("dev-session-1", "ai", "Here are comprehensive unit tests...", source_tool="cursor")
        
        # Back to Claude Code for refinement
        log_chat("dev-session-1", "user", "Optimize the regex pattern", source_tool="claude-code")
        log_chat("dev-session-1", "ai", "Here's an optimized version...", source_tool="claude-code")
        
        # Test tool-specific queries
        claude_messages = get_chats_by_tool("claude-code", conversation_id="dev-session-1")
        cursor_messages = get_chats_by_tool("cursor", conversation_id="dev-session-1")
        
        assert claude_messages["count"] == 4  # 2 user + 2 ai
        assert cursor_messages["count"] == 2   # 1 user + 1 ai
        
        # Test tool statistics
        tool_stats = list_tool_identifiers()
        tools = {t["identifier"]: t for t in tool_stats["tools"]}
        
        assert tools["claude-code"]["message_count"] == 4
        assert tools["claude-code"]["conversation_count"] == 1
        assert tools["cursor"]["message_count"] == 2
        assert tools["cursor"]["conversation_count"] == 1

    def test_edge_cases(self, temp_db):
        """Test edge cases and error handling."""
        # Test with None values
        result = log_chat("conv-1", "user", "Test", source_tool=None)
        assert result["success"] is True
        
        # Test with empty string source_tool
        result = log_chat("conv-1", "user", "Test", source_tool="")
        assert result["success"] is True
        
        # Test querying non-existent tool
        result = get_chats_by_tool("non-existent-tool")
        assert result["success"] is True
        assert result["count"] == 0
        assert len(result["messages"]) == 0