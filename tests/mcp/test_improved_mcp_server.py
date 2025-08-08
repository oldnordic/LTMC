"""Tests for improved LTMC MCP Server using proper stdio communication."""

import pytest
import tempfile
import os
import subprocess
import json
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Test that the server uses proper MCP SDK (not FastMCP)
class TestImprovedMCPServerStructure:
    """Test that the MCP server uses proper stdio communication."""
    
    def test_server_uses_proper_mcp_sdk(self):
        """Test that server uses proper MCP SDK, not FastMCP."""
        # This will fail until we fix the implementation
        try:
            from ltms.mcp_server import mcp
            # Should not be FastMCP
            assert not hasattr(mcp, 'run'), "Should not use FastMCP.run()"
            assert hasattr(mcp, 'run_stdio'), "Should use proper MCP SDK"
        except ImportError:
            pytest.fail("Server module should be importable")

    def test_server_has_stdio_communication(self):
        """Test that server communicates via stdio, not HTTP."""
        # This will fail until we implement proper stdio
        try:
            from ltms.mcp_server import mcp
            # Should have stdio-specific methods
            assert hasattr(mcp, 'run_stdio'), "Should support stdio communication"
        except ImportError:
            pytest.fail("Server module should be importable")


class TestImprovedMCPServerTools:
    """Test that the MCP server tools integrate with enhanced ingest.py."""
    
    @pytest.mark.asyncio
    async def test_store_memory_integrates_with_enhanced_ingest(self):
        """Test that store_memory uses enhanced ingest.py functions."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Test the store_memory method
        result = await mcp.store_memory("test.txt", "Test content", "document")
        
        assert result["success"] is True
        assert "id" in result
        assert "title" in result

    @pytest.mark.asyncio
    async def test_retrieve_memory_integrates_with_enhanced_ingest(self):
        """Test that retrieve_memory uses enhanced ingest.py query_documents."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        result = await mcp.retrieve_memory("conv123", "test query", 3)
        
        assert result["success"] is True
        assert "retrieved_chunks" in result
        assert len(result["retrieved_chunks"]) > 0

    @pytest.mark.asyncio
    async def test_log_chat_integrates_with_enhanced_ingest(self):
        """Test that log_chat uses enhanced ingest.py store_document."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        result = await mcp.log_chat("conv123", "user", "Hello world")
        
        assert result["success"] is True
        assert "message_id" in result


class TestAdvancedMCPServerTools:
    """Test advanced MCP server tools that integrate with new tool files."""
    
    @pytest.mark.asyncio
    async def test_ask_with_context_tool_available(self):
        """Test that ask_with_context tool is available and works."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Test that the tool exists
        assert hasattr(mcp, 'ask_with_context'), "ask_with_context tool should be available"
        
        # Test the tool functionality
        result = await mcp.ask_with_context("What is the main topic?", "conv123", 5)
        
        assert result["success"] is True
        assert "answer" in result
        assert "context" in result

    @pytest.mark.asyncio
    async def test_route_query_tool_available(self):
        """Test that route_query tool is available and works."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Test that the tool exists
        assert hasattr(mcp, 'route_query'), "route_query tool should be available"
        
        # Test the tool functionality
        result = await mcp.route_query("What is this about?", ["document", "code"], 5)
        
        assert result["success"] is True
        assert "combined_answer" in result
        assert "source_types" in result

    @pytest.mark.asyncio
    async def test_build_context_tool_available(self):
        """Test that build_context tool is available and works."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Test that the tool exists
        assert hasattr(mcp, 'build_context'), "build_context tool should be available"
        
        # Test the tool functionality
        documents = [
            {"title": "Doc1", "content": "Content 1", "score": 0.9},
            {"title": "Doc2", "content": "Content 2", "score": 0.8}
        ]
        result = await mcp.build_context(documents, 4000)
        
        assert result["success"] is True
        assert "context" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_retrieve_by_type_tool_available(self):
        """Test that retrieve_by_type tool is available and works."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Test that the tool exists
        assert hasattr(mcp, 'retrieve_by_type'), "retrieve_by_type tool should be available"
        
        # Test the tool functionality
        result = await mcp.retrieve_by_type("test query", "document", 5)
        
        assert result["success"] is True
        assert "documents" in result
        assert "doc_type" in result


class TestCompleteRetrievalFlow:
    """Test the complete retrieval and reasoning flow."""
    
    @pytest.mark.asyncio
    async def test_complete_retrieval_flow(self):
        """Test the complete flow: store → retrieve → build context → ask."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Step 1: Store memory
        store_result = await mcp.store_memory("test_doc.txt", "This is about AI and machine learning", "document")
        assert store_result["success"] is True
        
        # Step 2: Retrieve by type
        retrieve_result = await mcp.retrieve_by_type("AI machine learning", "document", 3)
        assert retrieve_result["success"] is True
        assert len(retrieve_result["documents"]) > 0
        
        # Step 3: Build context
        build_result = await mcp.build_context(retrieve_result["documents"], 4000)
        assert build_result["success"] is True
        assert "context" in build_result
        
        # Step 4: Ask with context
        ask_result = await mcp.ask_with_context("What is the main topic?", "conv123", 5)
        assert ask_result["success"] is True
        assert "answer" in ask_result

    @pytest.mark.asyncio
    async def test_multi_source_routing_flow(self):
        """Test the multi-source routing flow."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Store different types of content
        await mcp.store_memory("code.py", "def ai_function(): return 'AI'", "code")
        await mcp.store_memory("chat.txt", "User: What is AI?\nAssistant: AI is artificial intelligence", "chat")
        
        # Route query across multiple sources
        route_result = await mcp.route_query("What is AI?", ["code", "chat"], 5)
        assert route_result["success"] is True
        assert "combined_answer" in route_result
        assert "source_types" in route_result
        assert len(route_result["source_types"]) == 2


class TestImprovedMCPServerIntegration:
    """Test the complete MCP server integration."""
    
    def test_server_can_start_with_stdio(self):
        """Test that the server can start using stdio communication."""
        # This will fail until we implement proper stdio
        try:
            # Test that the module can be imported
            import ltms.mcp_server
            assert True, "Server module should be importable"
        except ImportError as e:
            pytest.fail(f"Server module should be importable: {e}")

    def test_server_has_enhanced_ingest_functions(self):
        """Test that server has access to enhanced ingest.py functions."""
        # This will fail until we integrate enhanced ingest.py
        try:
            from ltms.mcp_server import (
                store_document, 
                query_documents, 
                summarize_documents
            )
            assert callable(store_document), "store_document should be available"
            assert callable(query_documents), "query_documents should be available"
            assert callable(summarize_documents), "summarize_documents should be available"
        except ImportError as e:
            pytest.fail(f"Enhanced ingest functions should be available: {e}")


class TestImprovedMCPServerErrorHandling:
    """Test error handling in the improved MCP server."""
    
    @pytest.mark.asyncio
    async def test_store_memory_handles_invalid_input(self):
        """Test store_memory tool with invalid input."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Test with missing required parameters
        with pytest.raises(ValueError):
            await mcp.store_memory("", "")  # Empty content should raise error

    @pytest.mark.asyncio
    async def test_retrieve_memory_handles_invalid_input(self):
        """Test retrieve_memory tool with invalid input."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Test with missing required parameters
        with pytest.raises(ValueError):
            await mcp.retrieve_memory("", "")  # Empty query should raise error

    @pytest.mark.asyncio
    async def test_log_chat_handles_invalid_input(self):
        """Test log_chat tool with invalid input."""
        # Import the server instance
        from ltms.mcp_server import mcp
        
        # Test with missing required parameters
        with pytest.raises(ValueError):
            await mcp.log_chat("", "", "")  # Empty parameters should raise error


class TestImprovedMCPServerEndToEnd:
    """Test end-to-end functionality of the improved MCP server."""
    
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

    @pytest.mark.asyncio
    async def test_store_and_retrieve_memory(self, temp_db, temp_index):
        """Test storing and retrieving memory using enhanced ingest.py."""
        # This will fail until we implement the integration
        with patch.dict(os.environ, {
            'DB_PATH': temp_db,
            'FAISS_INDEX_PATH': temp_index
        }):
            from ltms.mcp_server import mcp
            
            # Store memory
            store_result = await mcp.store_memory("test.txt", "This is test content", "document")
            assert store_result["success"] is True
            
            # Retrieve memory
            retrieve_result = await mcp.retrieve_memory("conv123", "test content", 3)
            assert retrieve_result["success"] is True
            assert "retrieved_chunks" in retrieve_result
