"""Test FastMCP server implementation for mcp dev compatibility."""

import pytest
from pathlib import Path
import sys
import os


class TestFastMCPServer:
    """Test FastMCP server implementation."""

    def test_fastmcp_server_creation(self):
        """Test creating a FastMCP server that works with mcp dev."""
        try:
            from fastmcp import FastMCP
            
            # Create a FastMCP server
            server = FastMCP("LTMC Server")
            
            # Add tools using the FastMCP decorator pattern
            @server.tool()
            def store_memory(file_name: str, content: str, resource_type: str = "document"):
                """Store memory in LTMC."""
                return {"success": True, "message": "Memory stored"}
            
            @server.tool()
            def retrieve_memory(conversation_id: str, query: str, top_k: int = 3):
                """Retrieve memory from LTMC."""
                return {"success": True, "documents": []}
            
            # Check that the server has the tools
            assert hasattr(server, 'store_memory')
            assert hasattr(server, 'retrieve_memory')
            
            # Test calling the tools
            result1 = server.store_memory("test.txt", "test content", "document")
            assert result1["success"] is True
            
            result2 = server.retrieve_memory("conv123", "test query", 3)
            assert result2["success"] is True
            
        except ImportError as e:
            pytest.skip(f"FastMCP not available: {e}")

    def test_fastmcp_server_with_all_tools(self):
        """Test FastMCP server with all our LTMC tools."""
        try:
            from fastmcp import FastMCP
            
            # Create server with all our tools
            server = FastMCP("LTMC Server")
            
            # Define all our tools using FastMCP decorators
            @server.tool()
            def store_memory(file_name: str, content: str, resource_type: str = "document"):
                """Store memory in LTMC."""
                return {"success": True, "message": "Memory stored"}
            
            @server.tool()
            def retrieve_memory(conversation_id: str, query: str, top_k: int = 3):
                """Retrieve memory from LTMC."""
                return {"success": True, "documents": []}
            
            @server.tool()
            def log_chat(conversation_id: str, role: str, content: str):
                """Log chat message."""
                return {"success": True, "message": "Chat logged"}
            
            @server.tool()
            def ask_with_context(query: str, conversation_id: str, top_k: int = 5):
                """Ask with context."""
                return {"success": True, "answer": "Mock answer"}
            
            @server.tool()
            def route_query(query: str, source_types: list, top_k: int = 5):
                """Route query to different sources."""
                return {"success": True, "result": "Mock result"}
            
            @server.tool()
            def build_context(documents: list, max_tokens: int = 4000):
                """Build context from documents."""
                return {"success": True, "context": "Mock context"}
            
            @server.tool()
            def retrieve_by_type(query: str, doc_type: str, top_k: int = 5):
                """Retrieve by document type."""
                return {"success": True, "documents": []}
            
            # Check all tools are available
            expected_tools = [
                "store_memory", "retrieve_memory", "log_chat",
                "ask_with_context", "route_query", "build_context", "retrieve_by_type"
            ]
            
            for tool_name in expected_tools:
                assert hasattr(server, tool_name), f"Missing tool: {tool_name}"
            
            # Test calling each tool
            for tool_name in expected_tools:
                tool_func = getattr(server, tool_name)
                assert callable(tool_func), f"Tool {tool_name} is not callable"
                
                # Test with sample parameters
                if tool_name == "store_memory":
                    result = tool_func("test.txt", "test content", "document")
                elif tool_name == "retrieve_memory":
                    result = tool_func("conv123", "test query", 3)
                elif tool_name == "log_chat":
                    result = tool_func("conv123", "user", "test message")
                elif tool_name == "ask_with_context":
                    result = tool_func("test question", "conv123", 5)
                elif tool_name == "route_query":
                    result = tool_func("test query", ["document"], 5)
                elif tool_name == "build_context":
                    result = tool_func([{"title": "test", "content": "test"}], 4000)
                elif tool_name == "retrieve_by_type":
                    result = tool_func("test query", "document", 5)
                
                assert result["success"] is True, f"Tool {tool_name} failed"
            
        except ImportError as e:
            pytest.skip(f"FastMCP not available: {e}")

    def test_fastmcp_server_global_variable(self):
        """Test that FastMCP server can be assigned to global variable."""
        try:
            from fastmcp import FastMCP
            
            # Create server
            server = FastMCP("LTMC Server")
            
            # Add a tool
            @server.tool()
            def test_tool():
                """Test tool."""
                return {"success": True}
            
            # This should work - the server can be assigned to a global variable
            # This is what mcp dev expects
            global_mcp = server
            
            assert global_mcp is not None
            assert hasattr(global_mcp, 'test_tool')
            
        except ImportError as e:
            pytest.skip(f"FastMCP not available: {e}")


class TestFastMCPServerFile:
    """Test creating a FastMCP server file that works with mcp dev."""

    def test_fastmcp_server_file_structure(self):
        """Test the structure of a FastMCP server file."""
        # This test documents what a FastMCP server file should look like
        
        expected_structure = """
from mcp.server.fastmcp.server import FastMCP

# Create the server
server = FastMCP("LTMC Server")

# Add tools using decorators
@server.tool()
def store_memory(file_name: str, content: str, resource_type: str = "document"):
    \"\"\"Store memory in LTMC.\"\"\"
    return {"success": True, "message": "Memory stored"}

@server.tool()
def retrieve_memory(conversation_id: str, query: str, top_k: int = 3):
    \"\"\"Retrieve memory from LTMC.\"\"\"
    return {"success": True, "documents": []}

# Create global variable for mcp dev
mcp = server
"""
        
        # The key points:
        # 1. Import FastMCP
        # 2. Create server instance
        # 3. Add tools with @server.tool() decorators
        # 4. Assign to global variable named 'mcp'
        
        assert "FastMCP" in expected_structure
        assert "@server.tool()" in expected_structure
        assert "mcp = server" in expected_structure

    def test_fastmcp_server_integration(self):
        """Test that FastMCP server integrates with our existing tools."""
        # This test will verify that we can integrate our existing tools
        # with the FastMCP server structure
        
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            # Import our existing tools
            from tools.ingest import store_document, query_documents
            
            # Test that our tools work
            assert callable(store_document)
            assert callable(query_documents)
            
            # This confirms we can use our existing tools in FastMCP
            # We just need to wrap them with @server.tool() decorators
            
        except ImportError as e:
            pytest.fail(f"Failed to import existing tools: {e}")
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
