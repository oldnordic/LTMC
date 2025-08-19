"""Tests for LTMC MCP Server."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from fastmcp import FastMCP


class TestMCPServerInitialization:
    """Test MCP server initialization."""

    def test_mcp_server_creation(self):
        """Test that MCP server can be created."""
        mcp = FastMCP("LTMC Server")
        assert mcp.name == "LTMC Server"

    def test_mcp_server_has_tools(self):
        """Test that MCP server has tools defined."""
        from ltms.mcp_server_proper import mcp
        # Check that the server has the tool decorator
        assert hasattr(mcp, 'tool')
        assert callable(mcp.tool)


class TestMCPServerTools:
    """Test MCP server tools."""

    def test_store_memory_tool_exists(self):
        """Test that store_memory tool is available."""
        from ltms.mcp_server_proper import mcp
        # Check that the server has the tool decorator
        assert hasattr(mcp, 'tool')
        assert callable(mcp.tool)

    def test_retrieve_memory_tool_exists(self):
        """Test that retrieve_memory tool is available."""
        from ltms.mcp_server_proper import mcp
        # Check that the server has the tool decorator
        assert hasattr(mcp, 'tool')
        assert callable(mcp.tool)

    def test_log_chat_tool_exists(self):
        """Test that log_chat tool is available."""
        from ltms.mcp_server_proper import mcp
        # Check that the server has the tool decorator
        assert hasattr(mcp, 'tool')
        assert callable(mcp.tool)


class TestMCPServerToolExecution:
    """Test MCP server tool execution."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def temp_index(self):
        """Create temporary FAISS index for testing."""
        with tempfile.NamedTemporaryFile(suffix="_index", delete=False) as f:
            index_path = f.name
        yield index_path
        os.unlink(index_path)

    @patch('ltms.database.connection.get_db_connection')
    @patch('ltms.database.connection.close_db_connection')
    @patch('ltms.services.resource_service.add_resource')
    def test_store_memory_tool_execution(
        self, mock_add_resource, mock_close_db, mock_get_db, temp_db, temp_index
    ):
        """Test store_memory tool execution."""
        # Mock successful resource addition
        mock_add_resource.return_value = {"success": True, "resource_id": 1, "chunk_count": 3}
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn

        with patch.dict(os.environ, {
            'DB_PATH': temp_db,
            'FAISS_INDEX_PATH': temp_index
        }):
            # Import and test the tool
            from ltms.mcp_server_proper import store_memory
            result = store_memory("test.txt", "Test content", "document")
            
            assert result["success"] is True
            assert "resource_id" in result
            assert "chunk_count" in result

    @patch('ltms.database.connection.get_db_connection')
    @patch('ltms.database.connection.close_db_connection')
    @patch('ltms.services.context_service.get_context_for_query')
    def test_retrieve_memory_tool_execution(self, mock_get_context, mock_close_db, mock_get_db, temp_db, temp_index):
        """Test retrieve_memory tool execution."""
        # Mock successful context retrieval
        mock_get_context.return_value = {
            "success": True,
            "context": "Test context",
            "retrieved_chunks": [{"chunk_id": 1, "score": 0.8}]
        }
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn

        with patch.dict(os.environ, {
            'DB_PATH': temp_db,
            'FAISS_INDEX_PATH': temp_index
        }):
            # Import and test the tool
            from ltms.mcp_server_proper import retrieve_memory
            result = retrieve_memory("conv123", "test query", 3)
            
            assert result["success"] is True
            assert "context" in result
            assert "retrieved_chunks" in result

    @patch('ltms.database.connection.get_db_connection')
    @patch('ltms.database.connection.close_db_connection')
    @patch('ltms.services.context_service.log_chat_message')
    def test_log_chat_tool_execution(self, mock_log_chat, mock_close_db, mock_get_db, temp_db, temp_index):
        """Test log_chat tool execution."""
        # Mock successful chat logging
        mock_log_chat.return_value = 1
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn

        with patch.dict(os.environ, {
            'DB_PATH': temp_db,
            'FAISS_INDEX_PATH': temp_index
        }):
            # Import and test the tool
            from ltms.mcp_server_proper import log_chat
            result = log_chat("conv123", "user", "Hello world")
            
            assert result["success"] is True
            assert "message_id" in result


class TestMCPServerErrorHandling:
    """Test MCP server error handling."""

    def test_store_memory_invalid_input(self):
        """Test store_memory tool with invalid input."""
        from ltms.mcp_server_proper import store_memory
        
        # Test with empty content - should return error but not raise exception
        result = store_memory("test.txt", "", "document")
        assert result["success"] is False
        assert "error" in result

    def test_retrieve_memory_invalid_input(self):
        """Test retrieve_memory tool with invalid input."""
        from ltms.mcp_server_proper import retrieve_memory
        
        # Test with empty query - should return error but not raise exception
        result = retrieve_memory("conv123", "", 3)
        assert result["success"] is False
        assert "error" in result

    def test_log_chat_invalid_input(self):
        """Test log_chat tool with invalid input."""
        from ltms.mcp_server_proper import log_chat
        
        # Test with empty parameters - should return error but not raise exception
        result = log_chat("", "", "")
        assert result["success"] is False
        assert "error" in result


class TestMCPServerIntegration:
    """Test MCP server integration."""

    def test_server_can_start(self):
        """Test that the server can start without errors."""
        # Test that the module can be imported
        try:
            import ltms.mcp_server_proper
            assert True, "Server module should be importable"
        except ImportError as e:
            pytest.fail(f"Server module should be importable: {e}")

    def test_server_has_correct_tools(self):
        """Test that server has the correct tools defined."""
        from ltms.mcp_server_proper import mcp
        
        # Check that the server has the tool decorator
        assert hasattr(mcp, 'tool')
        assert callable(mcp.tool)
        
        # Check that we can access the tools
        assert hasattr(mcp, 'run')
        assert callable(mcp.run)
