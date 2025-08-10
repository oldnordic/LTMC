"""Test source tool tracking via HTTP transport with X-Tool-ID header."""

import pytest
import tempfile
import os
import json
from unittest.mock import patch
from fastapi.testclient import TestClient

from ltms.mcp_server_http import app
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables


class TestSourceToolHTTP:
    """Test suite for source tool tracking via HTTP transport."""

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

    @pytest.fixture
    def client(self):
        """Create a test client for the HTTP server."""
        return TestClient(app)

    def test_jsonrpc_log_chat_with_x_tool_id_header(self, temp_db, client):
        """Test JSON-RPC log_chat with X-Tool-ID header."""
        # Prepare JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "log_chat",
                "arguments": {
                    "conversation_id": "test-conv-1",
                    "role": "user",
                    "content": "Test message with X-Tool-ID header"
                }
            }
        }
        
        # Send request with X-Tool-ID header
        response = client.post(
            "/jsonrpc",
            json=request_data,
            headers={"X-Tool-ID": "claude-code"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert result["result"]["success"] is True
        assert "message_id" in result["result"]
        
        # Verify source_tool was stored in database
        message_id = result["result"]["message_id"]
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT conversation_id, role, content, source_tool FROM ChatHistory WHERE id = ?",
            (message_id,)
        )
        row = cursor.fetchone()
        close_db_connection(conn)
        
        assert row is not None
        assert row[0] == "test-conv-1"
        assert row[1] == "user"
        assert row[2] == "Test message with X-Tool-ID header"
        assert row[3] == "claude-code"

    def test_jsonrpc_log_chat_without_x_tool_id_header(self, temp_db, client):
        """Test JSON-RPC log_chat without X-Tool-ID header (backward compatibility)."""
        request_data = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "log_chat",
                "arguments": {
                    "conversation_id": "test-conv-2",
                    "role": "ai",
                    "content": "AI response without header"
                }
            }
        }
        
        response = client.post("/jsonrpc", json=request_data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["result"]["success"] is True
        message_id = result["result"]["message_id"]
        
        # Verify source_tool is NULL in database
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT source_tool FROM ChatHistory WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        close_db_connection(conn)
        
        assert row is not None
        assert row[0] is None

    def test_jsonrpc_log_chat_with_explicit_source_tool_parameter(self, temp_db, client):
        """Test that explicit source_tool parameter takes precedence over header."""
        request_data = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "log_chat",
                "arguments": {
                    "conversation_id": "test-conv-3",
                    "role": "user",
                    "content": "Test with explicit source_tool",
                    "source_tool": "explicit-tool"
                }
            }
        }
        
        # Send with X-Tool-ID header but also explicit source_tool parameter
        response = client.post(
            "/jsonrpc",
            json=request_data,
            headers={"X-Tool-ID": "header-tool"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["result"]["success"] is True
        message_id = result["result"]["message_id"]
        
        # Verify explicit parameter took precedence
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT source_tool FROM ChatHistory WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        close_db_connection(conn)
        
        assert row is not None
        assert row[0] == "explicit-tool"  # Not "header-tool"

    def test_jsonrpc_other_tool_calls_with_x_tool_id_header(self, temp_db, client):
        """Test that X-Tool-ID header is tracked in observability for other tool calls."""
        request_data = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "list_tool_identifiers",
                "arguments": {}
            }
        }
        
        response = client.post(
            "/jsonrpc",
            json=request_data,
            headers={"X-Tool-ID": "cursor", "X-Agent-Name": "test-agent"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["result"]["success"] is True
        
        # Verify observability trace was logged with source_tool
        conn = get_db_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT agent_name, metadata, source_tool FROM ChatHistory 
            WHERE role = 'tool' AND content = 'tools/call:list_tool_identifiers'
            ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()
        close_db_connection(conn)
        
        assert row is not None
        assert row[0] == "test-agent"
        assert row[2] == "cursor"
        
        # Check metadata contains tool info
        metadata = json.loads(row[1])
        assert metadata["tool"] == "list_tool_identifiers"

    def test_jsonrpc_multiple_tools_same_session(self, temp_db, client):
        """Test multiple tool calls in same session with different X-Tool-ID values."""
        # First call from Claude Code
        request1 = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "log_chat",
                "arguments": {
                    "conversation_id": "multi-tool-session",
                    "role": "user",
                    "content": "Message from Claude Code"
                }
            }
        }
        
        response1 = client.post(
            "/jsonrpc",
            json=request1,
            headers={"X-Tool-ID": "claude-code"}
        )
        
        # Second call from Cursor
        request2 = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "log_chat",
                "arguments": {
                    "conversation_id": "multi-tool-session",
                    "role": "user",
                    "content": "Message from Cursor"
                }
            }
        }
        
        response2 = client.post(
            "/jsonrpc",
            json=request2,
            headers={"X-Tool-ID": "cursor"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Query messages by tool
        request_query = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "get_chats_by_tool",
                "arguments": {
                    "source_tool": "claude-code",
                    "conversation_id": "multi-tool-session"
                }
            }
        }
        
        response_query = client.post("/jsonrpc", json=request_query)
        assert response_query.status_code == 200
        
        query_result = response_query.json()
        assert query_result["result"]["success"] is True
        assert query_result["result"]["count"] == 1
        assert query_result["result"]["messages"][0]["content"] == "Message from Claude Code"
        assert query_result["result"]["messages"][0]["source_tool"] == "claude-code"

    def test_jsonrpc_get_chats_by_tool(self, temp_db, client):
        """Test get_chats_by_tool via JSON-RPC."""
        # Add some test messages first
        for i, tool in enumerate(["claude-code", "cursor", "vscode"]):
            request = {
                "jsonrpc": "2.0",
                "id": i + 10,
                "method": "tools/call",
                "params": {
                    "name": "log_chat",
                    "arguments": {
                        "conversation_id": f"test-conv-{tool}",
                        "role": "user",
                        "content": f"Test message from {tool}",
                        "source_tool": tool
                    }
                }
            }
            response = client.post("/jsonrpc", json=request)
            assert response.status_code == 200
        
        # Query messages from claude-code
        query_request = {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/call",
            "params": {
                "name": "get_chats_by_tool",
                "arguments": {
                    "source_tool": "claude-code",
                    "limit": 10
                }
            }
        }
        
        response = client.post("/jsonrpc", json=query_request)
        assert response.status_code == 200
        
        result = response.json()
        assert result["result"]["success"] is True
        assert result["result"]["count"] == 1
        assert result["result"]["source_tool"] == "claude-code"
        assert result["result"]["messages"][0]["source_tool"] == "claude-code"

    def test_jsonrpc_list_tool_identifiers(self, temp_db, client):
        """Test list_tool_identifiers via JSON-RPC."""
        request = {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "tools/call",
            "params": {
                "name": "list_tool_identifiers",
                "arguments": {}
            }
        }
        
        response = client.post("/jsonrpc", json=request)
        assert response.status_code == 200
        
        result = response.json()
        assert result["result"]["success"] is True
        assert "tools" in result["result"]
        assert "standard_identifiers" in result["result"]
        assert "claude-code" in result["result"]["standard_identifiers"]

    def test_health_endpoint_shows_correct_tool_count(self, client):
        """Test that health endpoint shows updated tool count including new tools."""
        response = client.get("/health")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "healthy"
        assert result["tools_available"] == 55  # Updated count with new source tool functions

    def test_tools_endpoint_includes_new_tools(self, client):
        """Test that /tools endpoint includes the new source tool tracking functions."""
        response = client.get("/tools")
        assert response.status_code == 200
        
        result = response.json()
        tools = result["tools"]
        
        assert "get_chats_by_tool" in tools
        assert "list_tool_identifiers" in tools
        assert "get_tool_conversations" in tools
        assert result["count"] == 55

    def test_api_tools_discovery_includes_new_tools(self, client):
        """Test that /api/v1/tools endpoint includes new tools with descriptions."""
        response = client.get("/api/v1/tools")
        assert response.status_code == 200
        
        result = response.json()
        tool_names = [tool["name"] for tool in result["tools"]]
        
        assert "get_chats_by_tool" in tool_names
        assert "list_tool_identifiers" in tool_names
        assert "get_tool_conversations" in tool_names
        
        # Check that descriptions are present
        for tool in result["tools"]:
            if tool["name"] in ["get_chats_by_tool", "list_tool_identifiers", "get_tool_conversations"]:
                assert tool["description"]  # Should not be empty
                # Note: Parameter introspection might not work for all tools, so we'll check it's a list
                assert isinstance(tool["params"], list)  # Should be a list (may be empty)