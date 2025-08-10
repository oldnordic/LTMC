"""
Comprehensive test suite for Phase 3 Component 1: Neo4j Blueprint Enhancement System.

Tests cover:
- BlueprintManager with code structure mapping
- AST analysis and code structure extraction
- Neo4j blueprint node management
- Blueprint validation and consistency checking
- MCP tools integration
- Performance targets (<5ms blueprint operations)

Test methodology: TDD with real Neo4j integration (no mocks).
"""

import pytest
import asyncio
import time
import ast
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Test framework imports
from ltms.database.neo4j_store import Neo4jGraphStore
from ltms.models.task_blueprint import TaskBlueprint, TaskComplexity, TaskMetadata
from ltms.services.blueprint_service import BlueprintManager

# Placeholder imports for components to be implemented
# These will be created in the implementation phase
try:
    from ltms.tools.blueprint_tools import (
        create_blueprint_from_code,
        update_blueprint_structure,
        validate_blueprint_consistency,
        query_blueprint_relationships,
        generate_blueprint_documentation
    )
    from ltms.models.blueprint_schemas import (
        BlueprintNode,
        DocumentationFile,
        CodeStructure
    )
    BLUEPRINT_TOOLS_AVAILABLE = True
except ImportError:
    BLUEPRINT_TOOLS_AVAILABLE = False


class TestBlueprintSystemIntegration:
    """Test suite for Blueprint System integration with Neo4j and code analysis."""
    
    @pytest.fixture
    async def neo4j_store(self):
        """Create Neo4j store for testing with real database connection."""
        config = {
            "uri": "bolt://localhost:7687",
            "user": "neo4j", 
            "password": "ltmc_neo4j",
            "database": "ltmc_test"
        }
        store = Neo4jGraphStore(config)
        
        # Clean up any existing test data
        if store.is_available():
            with store.driver.session() as session:
                session.run("MATCH (n) WHERE n.test_data = true DELETE n")
        
        yield store
        
        # Cleanup after test
        if store.is_available():
            with store.driver.session() as session:
                session.run("MATCH (n) WHERE n.test_data = true DELETE n")
        store.close()
    
    
    @pytest.fixture
    def temp_python_file(self, sample_python_code):
        """Create temporary Python file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_python_code)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)


class TestCodeStructureAnalysis:
    """Test code structure analysis and AST parsing."""
    
    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for AST analysis testing."""
        return '''
"""Sample module for blueprint analysis."""

import asyncio
from typing import List, Dict, Any

class UserService:
    """Service for managing user operations."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def create_user(self, username: str, email: str) -> Dict[str, Any]:
        """Create a new user."""
        user_data = {
            "username": username,
            "email": email,
            "created_at": datetime.now()
        }
        result = await self.db.insert("users", user_data)
        return result
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

async def get_user_stats() -> Dict[str, int]:
    """Get user statistics."""
    return {"total_users": 100, "active_users": 85}

def process_batch_users(users: List[Dict[str, Any]]) -> List[str]:
    """Process a batch of users."""
    processed = []
    for user in users:
        if user.get("active", False):
            processed.append(user["username"])
    return processed
'''
    
    def test_ast_analysis_extracts_functions(self, sample_python_code):
        """Test that AST analysis correctly extracts function definitions."""
        # This test will fail initially - we need to implement code analysis
        tree = ast.parse(sample_python_code)
        
        # Expected to extract: __init__, create_user, validate_email, get_user_stats, process_batch_users
        functions = self._extract_functions_from_ast(tree)
        
        assert len(functions) == 5
        function_names = [f["name"] for f in functions]
        assert "__init__" in function_names
        assert "create_user" in function_names
        assert "validate_email" in function_names
        assert "get_user_stats" in function_names
        assert "process_batch_users" in function_names
        
        # Check async function detection
        async_functions = [f for f in functions if f["is_async"]]
        assert len(async_functions) == 2
        assert "create_user" in [f["name"] for f in async_functions]
        assert "get_user_stats" in [f["name"] for f in async_functions]
    
    def test_ast_analysis_extracts_classes(self, sample_python_code):
        """Test that AST analysis correctly extracts class definitions."""
        tree = ast.parse(sample_python_code)
        
        classes = self._extract_classes_from_ast(tree)
        
        assert len(classes) == 1
        assert classes[0]["name"] == "UserService"
        assert classes[0]["docstring"] == "Service for managing user operations."
        assert len(classes[0]["methods"]) == 3  # __init__, create_user, validate_email
    
    def test_ast_analysis_extracts_imports(self, sample_python_code):
        """Test that AST analysis correctly extracts import statements."""
        tree = ast.parse(sample_python_code)
        
        imports = self._extract_imports_from_ast(tree)
        
        expected_imports = ["asyncio", "typing.List", "typing.Dict", "typing.Any"]
        for expected in expected_imports:
            assert any(expected in imp["module"] for imp in imports)
    
    def _extract_functions_from_ast(self, tree) -> List[Dict[str, Any]]:
        """Extract function information from AST."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    "name": node.name,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "line_number": node.lineno,
                    "parameters": [arg.arg for arg in node.args.args],
                    "docstring": ast.get_docstring(node)
                }
                functions.append(func_info)
        
        return functions
    
    def _extract_classes_from_ast(self, tree) -> List[Dict[str, Any]]:
        """Extract class information from AST."""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(child.name)
                
                class_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "line_number": node.lineno,
                    "methods": methods,
                    "base_classes": [ast.unparse(base) for base in node.bases]
                }
                classes.append(class_info)
        
        return classes
    
    def _extract_imports_from_ast(self, tree) -> List[Dict[str, Any]]:
        """Extract import information from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_info = {
                        "module": alias.name,
                        "alias": alias.asname,
                        "type": "import"
                    }
                    imports.append(import_info)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                for alias in node.names:
                    import_info = {
                        "module": f"{module_name}.{alias.name}" if module_name else alias.name,
                        "alias": alias.asname,
                        "type": "from_import", 
                        "from_module": module_name
                    }
                    imports.append(import_info)
        
        return imports


class TestBlueprintNodeManagement:
    """Test Neo4j blueprint node management."""
    
    async def test_create_function_blueprint_node(self, neo4j_store):
        """Test creating function blueprint nodes in Neo4j."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        # This will fail initially - need to implement blueprint node types
        function_data = {
            "name": "create_user",
            "node_type": "function",
            "is_async": True,
            "parameters": ["username", "email"],
            "return_type": "Dict[str, Any]",
            "docstring": "Create a new user.",
            "complexity_score": 0.5,
            "test_data": True
        }
        
        result = await self._create_blueprint_node(neo4j_store, function_data)
        
        assert result["success"] is True
        assert result["node_type"] == "function"
        assert result["node_id"] is not None
    
    async def test_create_class_blueprint_node(self, neo4j_store):
        """Test creating class blueprint nodes in Neo4j."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        class_data = {
            "name": "UserService",
            "node_type": "class", 
            "docstring": "Service for managing user operations.",
            "methods": ["__init__", "create_user", "validate_email"],
            "complexity_score": 0.7,
            "test_data": True
        }
        
        result = await self._create_blueprint_node(neo4j_store, class_data)
        
        assert result["success"] is True
        assert result["node_type"] == "class"
        assert len(result["methods"]) == 3
    
    async def test_create_module_blueprint_node(self, neo4j_store):
        """Test creating module blueprint nodes in Neo4j."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        module_data = {
            "name": "user_service",
            "node_type": "module",
            "file_path": "/project/services/user_service.py", 
            "functions": ["get_user_stats", "process_batch_users"],
            "classes": ["UserService"],
            "imports": ["asyncio", "typing"],
            "test_data": True
        }
        
        result = await self._create_blueprint_node(neo4j_store, module_data)
        
        assert result["success"] is True
        assert result["node_type"] == "module"
        assert result["file_path"] == "/project/services/user_service.py"
    
    async def test_create_api_endpoint_blueprint_node(self, neo4j_store):
        """Test creating API endpoint blueprint nodes in Neo4j."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        endpoint_data = {
            "name": "POST /api/users",
            "node_type": "api_endpoint",
            "http_method": "POST",
            "path": "/api/users",
            "handler_function": "create_user_endpoint",
            "request_schema": {"username": "str", "email": "str"},
            "response_schema": {"user_id": "int", "created": "bool"},
            "test_data": True
        }
        
        result = await self._create_blueprint_node(neo4j_store, endpoint_data)
        
        assert result["success"] is True
        assert result["node_type"] == "api_endpoint"
        assert result["http_method"] == "POST"
    
    async def _create_blueprint_node(self, store, node_data) -> Dict[str, Any]:
        """Create blueprint node - to be implemented."""
        # This method needs to be implemented to create specialized blueprint nodes
        raise NotImplementedError("Blueprint node creation not yet implemented")


class TestBlueprintRelationships:
    """Test blueprint relationship management."""
    
    async def test_function_to_class_relationship(self, neo4j_store):
        """Test creating relationships between function and class nodes."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        # Create function and class nodes first
        function_id = "test_function_123"
        class_id = "test_class_456"
        
        # This will fail initially - need relationship management
        result = await self._create_blueprint_relationship(
            neo4j_store,
            source_id=function_id,
            target_id=class_id,
            relationship_type="BELONGS_TO",
            properties={"member_type": "method"}
        )
        
        assert result["success"] is True
        assert result["relationship_type"] == "BELONGS_TO"
    
    async def test_module_dependency_relationship(self, neo4j_store):
        """Test creating module dependency relationships."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        module_a_id = "test_module_a"
        module_b_id = "test_module_b"
        
        result = await self._create_blueprint_relationship(
            neo4j_store,
            source_id=module_a_id,
            target_id=module_b_id,
            relationship_type="IMPORTS",
            properties={"import_type": "module"}
        )
        
        assert result["success"] is True
        assert result["relationship_type"] == "IMPORTS"
    
    async def test_api_endpoint_to_function_relationship(self, neo4j_store):
        """Test creating API endpoint to function relationships."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        endpoint_id = "test_endpoint_789"
        function_id = "test_handler_123"
        
        result = await self._create_blueprint_relationship(
            neo4j_store,
            source_id=endpoint_id,
            target_id=function_id,
            relationship_type="HANDLED_BY",
            properties={"handler_type": "async"}
        )
        
        assert result["success"] is True
        assert result["relationship_type"] == "HANDLED_BY"
    
    async def _create_blueprint_relationship(self, store, source_id, target_id, relationship_type, properties) -> Dict[str, Any]:
        """Create blueprint relationship - to be implemented."""
        # This method needs to be implemented for specialized blueprint relationships
        raise NotImplementedError("Blueprint relationship creation not yet implemented")


class TestBlueprintConsistencyValidation:
    """Test blueprint-code consistency validation."""
    
    async def test_validate_function_consistency(self, temp_python_file):
        """Test validating function blueprint against actual code."""
        # This will fail initially - need consistency validation
        function_blueprint = {
            "name": "create_user",
            "node_type": "function",
            "is_async": True,
            "parameters": ["username", "email"],
            "return_type": "Dict[str, Any]"
        }
        
        result = await self._validate_function_consistency(function_blueprint, temp_python_file)
        
        assert result["consistent"] is True
        assert result["consistency_score"] > 0.9
    
    async def test_detect_function_inconsistency(self, temp_python_file):
        """Test detecting inconsistencies between blueprint and code."""
        # Intentionally inconsistent blueprint
        function_blueprint = {
            "name": "create_user",
            "node_type": "function", 
            "is_async": False,  # Should be True
            "parameters": ["username"],  # Missing email parameter
            "return_type": "str"  # Should be Dict[str, Any]
        }
        
        result = await self._validate_function_consistency(function_blueprint, temp_python_file)
        
        assert result["consistent"] is False
        assert result["consistency_score"] < 0.5
        assert len(result["inconsistencies"]) >= 3  # async, parameters, return_type
    
    async def test_validate_class_consistency(self, temp_python_file):
        """Test validating class blueprint against actual code."""
        class_blueprint = {
            "name": "UserService",
            "node_type": "class",
            "docstring": "Service for managing user operations.",
            "methods": ["__init__", "create_user", "validate_email"]
        }
        
        result = await self._validate_class_consistency(class_blueprint, temp_python_file)
        
        assert result["consistent"] is True
        assert result["consistency_score"] > 0.9
    
    async def test_validate_module_consistency(self, temp_python_file):
        """Test validating module blueprint against actual code."""
        module_blueprint = {
            "name": "user_service",
            "node_type": "module",
            "functions": ["get_user_stats", "process_batch_users"],
            "classes": ["UserService"],
            "imports": ["asyncio", "typing"]
        }
        
        result = await self._validate_module_consistency(module_blueprint, temp_python_file)
        
        assert result["consistent"] is True
        assert result["consistency_score"] > 0.8
    
    async def _validate_function_consistency(self, blueprint, file_path) -> Dict[str, Any]:
        """Validate function blueprint consistency - to be implemented."""
        raise NotImplementedError("Function consistency validation not yet implemented")
    
    async def _validate_class_consistency(self, blueprint, file_path) -> Dict[str, Any]:
        """Validate class blueprint consistency - to be implemented."""
        raise NotImplementedError("Class consistency validation not yet implemented")
    
    async def _validate_module_consistency(self, blueprint, file_path) -> Dict[str, Any]:
        """Validate module blueprint consistency - to be implemented."""
        raise NotImplementedError("Module consistency validation not yet implemented")


class TestBlueprintPerformance:
    """Test blueprint system performance requirements."""
    
    async def test_blueprint_creation_performance(self, neo4j_store):
        """Test that blueprint creation meets <5ms performance target."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        start_time = time.perf_counter()
        
        # Create multiple blueprint nodes rapidly
        for i in range(10):
            node_data = {
                "name": f"test_function_{i}",
                "node_type": "function",
                "is_async": False,
                "test_data": True
            }
            await self._create_blueprint_node(neo4j_store, node_data)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) * 1000) / 10
        
        # Must be under 5ms per operation
        assert avg_time_ms < 5.0, f"Blueprint creation took {avg_time_ms:.2f}ms, expected <5ms"
    
    async def test_blueprint_query_performance(self, neo4j_store):
        """Test that blueprint queries meet performance targets."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        # Create test data first
        for i in range(20):
            node_data = {
                "name": f"perf_test_{i}",
                "node_type": "function",
                "test_data": True
            }
            await self._create_blueprint_node(neo4j_store, node_data)
        
        # Test query performance
        start_time = time.perf_counter()
        
        for i in range(10):
            result = await self._query_blueprint_nodes(neo4j_store, {"node_type": "function"})
            assert len(result) > 0
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) * 1000) / 10
        
        # Must be under 5ms per query
        assert avg_time_ms < 5.0, f"Blueprint query took {avg_time_ms:.2f}ms, expected <5ms"
    
    async def test_consistency_validation_performance(self, temp_python_file):
        """Test that consistency validation meets performance targets."""
        function_blueprint = {
            "name": "create_user",
            "node_type": "function",
            "is_async": True,
            "parameters": ["username", "email"]
        }
        
        start_time = time.perf_counter()
        
        for i in range(5):
            result = await self._validate_function_consistency(function_blueprint, temp_python_file)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) * 1000) / 5
        
        # Must be under 10ms per validation
        assert avg_time_ms < 10.0, f"Consistency validation took {avg_time_ms:.2f}ms, expected <10ms"
    
    async def _query_blueprint_nodes(self, store, filters) -> List[Dict[str, Any]]:
        """Query blueprint nodes - to be implemented."""
        raise NotImplementedError("Blueprint node querying not yet implemented")


class TestMCPBlueprintTools:
    """Test MCP blueprint tools integration."""
    
    @pytest.mark.skipif(not BLUEPRINT_TOOLS_AVAILABLE, reason="Blueprint MCP tools not yet implemented")
    def test_create_blueprint_from_code_tool(self, temp_python_file):
        """Test create_blueprint_from_code MCP tool."""
        result = create_blueprint_from_code(
            file_path=temp_python_file,
            project_id="test_project"
        )
        
        assert result["success"] is True
        assert "blueprint_id" in result
        assert len(result["nodes_created"]) > 0
        assert len(result["relationships_created"]) > 0
    
    @pytest.mark.skipif(not BLUEPRINT_TOOLS_AVAILABLE, reason="Blueprint MCP tools not yet implemented") 
    def test_update_blueprint_structure_tool(self, temp_python_file):
        """Test update_blueprint_structure MCP tool."""
        # First create blueprint
        create_result = create_blueprint_from_code(
            file_path=temp_python_file,
            project_id="test_project"
        )
        blueprint_id = create_result["blueprint_id"]
        
        # Then update it
        result = update_blueprint_structure(
            blueprint_id=blueprint_id,
            file_path=temp_python_file
        )
        
        assert result["success"] is True
        assert result["nodes_updated"] >= 0
        assert result["consistency_maintained"] is True
    
    @pytest.mark.skipif(not BLUEPRINT_TOOLS_AVAILABLE, reason="Blueprint MCP tools not yet implemented")
    def test_validate_blueprint_consistency_tool(self, temp_python_file):
        """Test validate_blueprint_consistency MCP tool."""
        # Create blueprint first
        create_result = create_blueprint_from_code(
            file_path=temp_python_file,
            project_id="test_project"
        )
        blueprint_id = create_result["blueprint_id"]
        
        result = validate_blueprint_consistency(
            blueprint_id=blueprint_id,
            file_path=temp_python_file
        )
        
        assert result["success"] is True
        assert result["consistency_score"] > 0.8
        assert len(result["inconsistencies"]) == 0
    
    @pytest.mark.skipif(not BLUEPRINT_TOOLS_AVAILABLE, reason="Blueprint MCP tools not yet implemented")
    def test_query_blueprint_relationships_tool(self):
        """Test query_blueprint_relationships MCP tool."""
        result = query_blueprint_relationships(
            node_id="test_function_123",
            relationship_types=["BELONGS_TO", "CALLS"],
            max_depth=2
        )
        
        assert result["success"] is True
        assert "relationships" in result
        assert isinstance(result["relationships"], list)
    
    @pytest.mark.skipif(not BLUEPRINT_TOOLS_AVAILABLE, reason="Blueprint MCP tools not yet implemented")
    def test_generate_blueprint_documentation_tool(self):
        """Test generate_blueprint_documentation MCP tool."""
        result = generate_blueprint_documentation(
            blueprint_id="test_blueprint_456",
            format="markdown",
            include_relationships=True
        )
        
        assert result["success"] is True
        assert "documentation" in result
        assert len(result["documentation"]) > 0


class TestBlueprintSystemIntegration:
    """Test full system integration across components."""
    
    async def test_end_to_end_blueprint_workflow(self, neo4j_store, temp_python_file):
        """Test complete workflow from code analysis to documentation generation."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        # This is a comprehensive integration test
        # 1. Analyze code structure
        # 2. Create blueprint nodes in Neo4j  
        # 3. Establish relationships
        # 4. Validate consistency
        # 5. Generate documentation
        
        workflow_result = await self._run_complete_blueprint_workflow(
            neo4j_store,
            temp_python_file,
            "integration_test_project"
        )
        
        assert workflow_result["success"] is True
        assert workflow_result["nodes_created"] >= 4  # Functions + class + module
        assert workflow_result["relationships_created"] >= 3
        assert workflow_result["consistency_score"] > 0.9
        assert workflow_result["documentation_generated"] is True
    
    async def test_system_performance_under_load(self, neo4j_store):
        """Test system performance under concurrent load."""
        if not neo4j_store.is_available():
            pytest.skip("Neo4j not available")
        
        # Create 50 concurrent blueprint operations
        tasks = []
        for i in range(50):
            task = self._create_test_blueprint_operation(neo4j_store, i)
            tasks.append(task)
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        end_time = time.perf_counter()
        
        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_op = total_time_ms / 50
        
        # System should handle 50 operations in reasonable time
        assert total_time_ms < 1000, f"50 operations took {total_time_ms:.2f}ms, expected <1000ms"
        assert avg_time_per_op < 20, f"Average operation took {avg_time_per_op:.2f}ms, expected <20ms"
        
        # All operations should succeed
        successful_ops = sum(1 for result in results if result["success"])
        assert successful_ops == 50, f"Only {successful_ops}/50 operations succeeded"
    
    async def _run_complete_blueprint_workflow(self, store, file_path, project_id) -> Dict[str, Any]:
        """Run complete blueprint workflow - to be implemented."""
        raise NotImplementedError("Complete blueprint workflow not yet implemented")
    
    async def _create_test_blueprint_operation(self, store, operation_id) -> Dict[str, Any]:
        """Create test blueprint operation - to be implemented."""
        raise NotImplementedError("Test blueprint operation not yet implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])