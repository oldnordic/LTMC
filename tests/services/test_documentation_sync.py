"""
Test suite for Phase 3 Component 2: Documentation Synchronization System.

This comprehensive test suite validates the dual-source documentation synchronization system
including real-time synchronization, change detection, and consistency scoring.

Test Coverage:
- Dual-source validation (Neo4j blueprints vs code)
- Real-time synchronization with file system monitoring
- Consistency scoring with >90% accuracy target
- Change detection and automated updates
- Performance targets: <5ms sync operations
- Integration with Phase 2 DocumentationGenerator
- MCP tools functionality
"""

import pytest
import asyncio
import tempfile
import sqlite3
import os
import time
import json
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Import system under test
from ltms.services.documentation_sync_service import (
    DocumentationSyncManager,
    DualSourceValidator,
    ChangeDetectionEngine,
    ConsistencyScorer,
    DocumentationSyncError,
    SyncConflictError,
    ValidationFailureError
)

# Import supporting components
from ltms.models.blueprint_schemas import (
    BlueprintNode,
    FunctionNode,
    ClassNode,
    ModuleNode,
    BlueprintRelationship,
    BlueprintNodeType,
    RelationshipType,
    CodeStructure,
    ConsistencyLevel
)

from ltms.database.neo4j_store import Neo4jGraphStore
from ltms.services.documentation_generator import DocumentationGenerator
from ltms.database.connection import get_db_connection
from ltms.config import DB_PATH


class TestDualSourceValidator:
    """Test dual-source validation between Neo4j blueprints and actual code."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.project_id = "test_project"
        self.validator = DualSourceValidator()
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_dual_source_validator_initialization(self):
        """Test DualSourceValidator initialization."""
        validator = DualSourceValidator()
        assert validator is not None
        assert hasattr(validator, 'neo4j_store')
        assert hasattr(validator, 'code_analyzer')
    
    def test_compare_structures_identical(self):
        """Test structure comparison when code and blueprint are identical."""
        # Create test Python file
        test_file = Path(self.test_dir) / "test_module.py"
        test_file.write_text("""
def test_function(param1: str, param2: int) -> bool:
    '''Test function docstring'''
    return True

class TestClass:
    '''Test class docstring'''
    
    def test_method(self, value: str) -> None:
        '''Test method docstring'''
        pass
""")
        
        # Create matching blueprint structure
        blueprint_structure = self._create_test_blueprint_structure()
        
        # Validate structures are identical
        comparison_result = self.validator.compare_structures(
            blueprint_structure, 
            str(test_file),
            self.project_id
        )
        
        assert comparison_result["success"] is True
        assert comparison_result["consistency_score"] > 0.90
        assert comparison_result["total_nodes"] > 0
        assert comparison_result["matching_nodes"] == comparison_result["total_nodes"]
        assert len(comparison_result["inconsistencies"]) == 0
    
    def test_compare_structures_with_differences(self):
        """Test structure comparison when there are differences."""
        # Create test Python file with different structure
        test_file = Path(self.test_dir) / "test_module.py"
        test_file.write_text("""
def different_function(param1: str) -> str:
    '''Different function'''
    return param1

class DifferentClass:
    '''Different class'''
    pass
""")
        
        # Create original blueprint structure
        blueprint_structure = self._create_test_blueprint_structure()
        
        # Validate structures have differences
        comparison_result = self.validator.compare_structures(
            blueprint_structure,
            str(test_file),
            self.project_id
        )
        
        assert comparison_result["success"] is True
        assert comparison_result["consistency_score"] < 0.90
        assert len(comparison_result["inconsistencies"]) > 0
        assert "missing_from_code" in comparison_result["inconsistencies"][0]
    
    def test_validate_node_consistency_function(self):
        """Test node consistency validation for functions."""
        # Create function node
        function_node = FunctionNode(
            node_id="func_test_function",
            name="test_function",
            node_type=BlueprintNodeType.FUNCTION,
            project_id=self.project_id,
            file_path="/test/file.py",
            line_number=1,
            parameters=[{"name": "param1", "type": "str"}],
            return_type="bool",
            is_async=False
        )
        
        # Create matching code AST node (mock)
        code_node_data = {
            "name": "test_function",
            "type": "function",
            "parameters": [{"name": "param1", "type": "str"}],
            "return_type": "bool",
            "is_async": False
        }
        
        consistency = self.validator._validate_node_consistency(
            function_node, 
            code_node_data
        )
        
        assert consistency["is_consistent"] is True
        assert consistency["score"] == 1.0
        assert len(consistency["differences"]) == 0
    
    def test_validate_node_consistency_with_differences(self):
        """Test node consistency validation with differences."""
        # Create function node
        function_node = FunctionNode(
            node_id="func_test_function", 
            name="test_function",
            node_type=BlueprintNodeType.FUNCTION,
            project_id=self.project_id,
            file_path="/test/file.py",
            line_number=1,
            parameters=[{"name": "param1", "type": "str"}, {"name": "param2", "type": "int"}],
            return_type="bool",
            is_async=False
        )
        
        # Create different code AST node
        code_node_data = {
            "name": "test_function",
            "type": "function",
            "parameters": [{"name": "param1", "type": "str"}],  # Missing param2
            "return_type": "str",  # Different return type
            "is_async": False
        }
        
        consistency = self.validator._validate_node_consistency(
            function_node,
            code_node_data
        )
        
        assert consistency["is_consistent"] is False
        assert consistency["score"] < 1.0
        assert len(consistency["differences"]) > 0
        assert "parameters" in str(consistency["differences"])
        assert "return_type" in str(consistency["differences"])
    
    def test_performance_dual_source_validation(self):
        """Test dual-source validation performance meets <10ms target."""
        # Create test file
        test_file = Path(self.test_dir) / "performance_test.py"
        test_file.write_text("""
def func1(): pass
def func2(): pass
class Class1: pass
class Class2: pass
""")
        
        blueprint_structure = self._create_test_blueprint_structure()
        
        # Measure validation performance
        start_time = time.perf_counter()
        
        result = self.validator.compare_structures(
            blueprint_structure,
            str(test_file),
            self.project_id
        )
        
        end_time = time.perf_counter()
        validation_time_ms = (end_time - start_time) * 1000
        
        assert result["success"] is True
        assert validation_time_ms < 10.0  # <10ms target
        assert "validation_time_ms" in result
        assert result["validation_time_ms"] < 10.0
    
    def _create_test_blueprint_structure(self) -> CodeStructure:
        """Create test blueprint structure."""
        structure = CodeStructure(
            structure_id="test_structure",
            file_path="/test/file.py", 
            project_id=self.project_id
        )
        
        # Add function node
        function_node = FunctionNode(
            node_id="func_test_function",
            name="test_function",
            node_type=BlueprintNodeType.FUNCTION,
            project_id=self.project_id,
            file_path="/test/file.py",
            line_number=1,
            parameters=[{"name": "param1", "type": "str"}, {"name": "param2", "type": "int"}],
            return_type="bool",
            is_async=False
        )
        structure.add_node(function_node)
        
        # Add class node
        class_node = ClassNode(
            node_id="class_test_class",
            name="TestClass",
            node_type=BlueprintNodeType.CLASS,
            project_id=self.project_id,
            file_path="/test/file.py",
            line_number=5,
            methods=["test_method"]
        )
        structure.add_node(class_node)
        
        return structure


class TestChangeDetectionEngine:
    """Test change detection engine for real-time synchronization."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.project_id = "test_project"
        self.change_detector = ChangeDetectionEngine()
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_change_detection_engine_initialization(self):
        """Test ChangeDetectionEngine initialization."""
        engine = ChangeDetectionEngine()
        assert engine is not None
        assert hasattr(engine, 'file_watchers')
        assert hasattr(engine, 'change_queue')
        assert hasattr(engine, 'sync_callbacks')
    
    def test_detect_file_changes(self):
        """Test file change detection."""
        test_file = Path(self.test_dir) / "test_file.py"
        test_file.write_text("def original_function(): pass")
        
        # Start monitoring
        self.change_detector.start_monitoring(str(test_file))
        
        # Modify file
        test_file.write_text("def modified_function(): pass")
        
        # Wait briefly for file system event
        time.sleep(0.1)
        
        # Check for detected changes
        changes = self.change_detector.get_pending_changes()
        assert len(changes) > 0
        assert changes[0]["file_path"] == str(test_file)
        assert changes[0]["change_type"] in ["modified", "created"]
    
    @pytest.mark.asyncio
    async def test_real_time_sync_trigger(self):
        """Test real-time synchronization trigger."""
        test_file = Path(self.test_dir) / "sync_test.py"
        test_file.write_text("def test(): pass")
        
        sync_triggered = False
        
        def sync_callback(file_path: str, change_type: str):
            nonlocal sync_triggered
            sync_triggered = True
        
        # Register callback and start monitoring
        self.change_detector.register_sync_callback(sync_callback)
        self.change_detector.start_monitoring(str(test_file))
        
        # Modify file to trigger sync
        test_file.write_text("def modified_test(): pass")
        
        # Wait for async processing
        await asyncio.sleep(0.2)
        
        assert sync_triggered is True
    
    def test_blueprint_change_tracking(self):
        """Test blueprint change tracking in Neo4j."""
        # Mock Neo4j change detection
        blueprint_changes = self.change_detector.detect_blueprint_changes(self.project_id)
        
        assert "success" in blueprint_changes
        assert "changes" in blueprint_changes
        assert isinstance(blueprint_changes["changes"], list)
    
    def test_performance_change_detection(self):
        """Test change detection performance."""
        test_file = Path(self.test_dir) / "performance_test.py"
        test_file.write_text("def test(): pass")
        
        start_time = time.perf_counter()
        
        self.change_detector.start_monitoring(str(test_file))
        test_file.write_text("def modified_test(): pass")
        
        # Allow brief processing time
        time.sleep(0.05)
        
        changes = self.change_detector.get_pending_changes()
        
        end_time = time.perf_counter()
        detection_time_ms = (end_time - start_time) * 1000
        
        assert len(changes) > 0
        assert detection_time_ms < 100.0  # Should be very fast


class TestConsistencyScorer:
    """Test consistency scoring algorithm."""
    
    def setup_method(self):
        """Setup test environment."""
        self.scorer = ConsistencyScorer()
        self.project_id = "test_project"
    
    def test_consistency_scorer_initialization(self):
        """Test ConsistencyScorer initialization."""
        scorer = ConsistencyScorer()
        assert scorer is not None
        assert hasattr(scorer, 'scoring_weights')
        assert hasattr(scorer, 'consistency_thresholds')
    
    def test_calculate_consistency_score_perfect(self):
        """Test consistency score calculation for perfect match."""
        blueprint_structure = self._create_test_structure()
        code_structure = self._create_matching_code_structure()
        
        score_result = self.scorer.calculate_consistency_score(
            blueprint_structure,
            code_structure
        )
        
        assert score_result["success"] is True
        assert score_result["consistency_score"] >= 0.95
        assert score_result["consistency_level"] == ConsistencyLevel.HIGH.name
        assert score_result["node_consistency"] >= 0.95
        assert score_result["relationship_consistency"] >= 0.95
    
    def test_calculate_consistency_score_partial(self):
        """Test consistency score calculation for partial match."""
        blueprint_structure = self._create_test_structure()
        code_structure = self._create_partial_code_structure()
        
        score_result = self.scorer.calculate_consistency_score(
            blueprint_structure,
            code_structure
        )
        
        assert score_result["success"] is True
        assert 0.5 <= score_result["consistency_score"] < 0.90
        assert score_result["consistency_level"] in [ConsistencyLevel.MEDIUM.name, ConsistencyLevel.LOW.name]
    
    def test_calculate_consistency_score_performance(self):
        """Test consistency scoring performance meets <5ms target."""
        blueprint_structure = self._create_large_test_structure()
        code_structure = self._create_large_code_structure()
        
        start_time = time.perf_counter()
        
        score_result = self.scorer.calculate_consistency_score(
            blueprint_structure,
            code_structure
        )
        
        end_time = time.perf_counter()
        scoring_time_ms = (end_time - start_time) * 1000
        
        assert score_result["success"] is True
        assert scoring_time_ms < 5.0  # <5ms target
        assert "scoring_time_ms" in score_result
        assert score_result["scoring_time_ms"] < 5.0
    
    def _create_test_structure(self) -> CodeStructure:
        """Create test blueprint structure."""
        structure = CodeStructure(
            structure_id="test_structure",
            file_path="/test/file.py",
            project_id=self.project_id
        )
        
        function_node = FunctionNode(
            node_id="func_test",
            name="test_function",
            node_type=BlueprintNodeType.FUNCTION,
            project_id=self.project_id,
            file_path="/test/file.py",
            line_number=1
        )
        structure.add_node(function_node)
        
        return structure
    
    def _create_matching_code_structure(self) -> Dict[str, Any]:
        """Create matching code structure."""
        return {
            "nodes": [
                {
                    "name": "test_function",
                    "type": "function",
                    "line_number": 1,
                    "parameters": [],
                    "return_type": None
                }
            ],
            "relationships": []
        }
    
    def _create_partial_code_structure(self) -> Dict[str, Any]:
        """Create partial matching code structure."""
        return {
            "nodes": [
                {
                    "name": "different_function",
                    "type": "function",
                    "line_number": 1,
                    "parameters": [],
                    "return_type": None
                }
            ],
            "relationships": []
        }
    
    def _create_large_test_structure(self) -> CodeStructure:
        """Create large test structure for performance testing."""
        structure = CodeStructure(
            structure_id="large_structure",
            file_path="/test/large_file.py",
            project_id=self.project_id
        )
        
        # Add 50 function nodes
        for i in range(50):
            function_node = FunctionNode(
                node_id=f"func_{i}",
                name=f"function_{i}",
                node_type=BlueprintNodeType.FUNCTION,
                project_id=self.project_id,
                file_path="/test/large_file.py",
                line_number=i+1
            )
            structure.add_node(function_node)
        
        return structure
    
    def _create_large_code_structure(self) -> Dict[str, Any]:
        """Create large matching code structure."""
        nodes = []
        for i in range(50):
            nodes.append({
                "name": f"function_{i}",
                "type": "function",
                "line_number": i+1,
                "parameters": [],
                "return_type": None
            })
        
        return {"nodes": nodes, "relationships": []}


class TestDocumentationSyncManager:
    """Test main DocumentationSyncManager coordination."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.project_id = "test_project"
        
        # Mock dependencies
        self.mock_neo4j = Mock()
        self.mock_documentation_generator = Mock()
        
        self.sync_manager = DocumentationSyncManager(
            neo4j_store=self.mock_neo4j,
            documentation_generator=self.mock_documentation_generator
        )
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_sync_manager_initialization(self):
        """Test DocumentationSyncManager initialization."""
        manager = DocumentationSyncManager()
        assert manager is not None
        assert hasattr(manager, 'dual_source_validator')
        assert hasattr(manager, 'change_detector')
        assert hasattr(manager, 'consistency_scorer')
        assert hasattr(manager, 'documentation_generator')
    
    @pytest.mark.asyncio
    async def test_sync_documentation_with_code_success(self):
        """Test successful documentation synchronization."""
        test_file = Path(self.test_dir) / "test_sync.py"
        test_file.write_text("""
def test_function():
    '''Test function for sync'''
    pass
""")
        
        # Mock successful operations
        self.mock_neo4j.is_available.return_value = True
        
        result = await self.sync_manager.sync_documentation_with_code(
            file_path=str(test_file),
            project_id=self.project_id
        )
        
        assert result["success"] is True
        assert "sync_time_ms" in result
        assert result["sync_time_ms"] < 5.0  # <5ms target
        assert "consistency_score" in result
        assert "documentation_updated" in result
    
    @pytest.mark.asyncio
    async def test_validate_documentation_consistency(self):
        """Test documentation consistency validation."""
        test_file = Path(self.test_dir) / "consistency_test.py"
        test_file.write_text("def test(): pass")
        
        result = await self.sync_manager.validate_documentation_consistency(
            file_path=str(test_file),
            project_id=self.project_id
        )
        
        assert result["success"] is True
        assert "consistency_score" in result
        assert "validation_time_ms" in result
        assert result["validation_time_ms"] < 10.0  # <10ms target
    
    @pytest.mark.asyncio
    async def test_detect_documentation_drift(self):
        """Test documentation drift detection."""
        test_file = Path(self.test_dir) / "drift_test.py" 
        test_file.write_text("def original(): pass")
        
        # Simulate drift detection
        result = await self.sync_manager.detect_documentation_drift(
            file_path=str(test_file),
            project_id=self.project_id
        )
        
        assert result["success"] is True
        assert "drift_detected" in result
        assert "drift_score" in result
        assert "affected_sections" in result
    
    @pytest.mark.asyncio
    async def test_update_documentation_from_blueprint(self):
        """Test documentation update from Neo4j blueprint."""
        blueprint_id = "test_blueprint"
        
        result = await self.sync_manager.update_documentation_from_blueprint(
            blueprint_id=blueprint_id,
            project_id=self.project_id
        )
        
        assert result["success"] is True
        assert "update_time_ms" in result
        assert result["update_time_ms"] < 10.0  # <10ms target
        assert "documentation_sections_updated" in result
    
    @pytest.mark.asyncio
    async def test_get_documentation_consistency_score(self):
        """Test consistency score retrieval."""
        test_file = Path(self.test_dir) / "score_test.py"
        test_file.write_text("def test(): pass")
        
        result = await self.sync_manager.get_documentation_consistency_score(
            file_path=str(test_file),
            project_id=self.project_id
        )
        
        assert result["success"] is True
        assert "consistency_score" in result
        assert 0.0 <= result["consistency_score"] <= 1.0
        assert "consistency_level" in result
        assert "calculation_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_real_time_sync_workflow(self):
        """Test end-to-end real-time synchronization workflow."""
        test_file = Path(self.test_dir) / "realtime_test.py"
        test_file.write_text("def initial_function(): pass")
        
        # Start real-time monitoring
        await self.sync_manager.start_real_time_sync(
            file_paths=[str(test_file)],
            project_id=self.project_id
        )
        
        # Modify file to trigger sync
        test_file.write_text("def modified_function(): pass")
        
        # Wait for async processing
        await asyncio.sleep(0.2)
        
        # Verify sync was triggered
        sync_status = await self.sync_manager.get_sync_status(self.project_id)
        
        assert sync_status["success"] is True
        assert "last_sync_time" in sync_status
        assert "files_monitored" in sync_status
        assert len(sync_status["files_monitored"]) > 0
    
    def test_sync_manager_error_handling(self):
        """Test error handling in sync manager."""
        # Test with invalid file path
        with pytest.raises(DocumentationSyncError):
            self.sync_manager._validate_sync_inputs("", "")
        
        # Test with invalid project_id
        with pytest.raises(DocumentationSyncError):
            self.sync_manager._validate_sync_inputs("/valid/path.py", "")


class TestDocumentationSyncIntegration:
    """Test integration with existing Phase 2 components."""
    
    def setup_method(self):
        """Setup integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.project_id = "integration_test"
        self.sync_manager = DocumentationSyncManager()
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_integration_with_documentation_generator(self):
        """Test integration with Phase 2 DocumentationGenerator."""
        test_file = Path(self.test_dir) / "integration_test.py"
        test_file.write_text("""
def api_endpoint():
    '''API endpoint for testing'''
    return {"status": "ok"}

class DataModel:
    '''Data model for testing'''
    pass
""")
        
        # Test integration workflow
        result = await self.sync_manager.sync_with_documentation_generator(
            file_path=str(test_file),
            project_id=self.project_id
        )
        
        assert result["success"] is True
        assert "api_documentation_updated" in result
        assert "architecture_diagrams_updated" in result
        assert "integration_time_ms" in result
    
    @pytest.mark.asyncio 
    async def test_integration_with_neo4j_blueprints(self):
        """Test integration with Phase 3 Component 1 Neo4j blueprints."""
        test_file = Path(self.test_dir) / "blueprint_integration.py"
        test_file.write_text("""
class BlueprintClass:
    def blueprint_method(self):
        pass
""")
        
        result = await self.sync_manager.sync_with_neo4j_blueprints(
            file_path=str(test_file),
            project_id=self.project_id
        )
        
        assert result["success"] is True
        assert "blueprint_nodes_synced" in result
        assert "blueprint_relationships_synced" in result
        assert "neo4j_sync_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_cross_component_consistency(self):
        """Test consistency across Phase 2 and Phase 3 Component 1."""
        test_file = Path(self.test_dir) / "cross_component_test.py"
        test_file.write_text("""
def shared_function():
    '''Shared across components'''
    pass
""")
        
        result = await self.sync_manager.validate_cross_component_consistency(
            file_path=str(test_file),
            project_id=self.project_id
        )
        
        assert result["success"] is True
        assert "phase2_consistency" in result
        assert "phase3_consistency" in result
        assert "overall_consistency_score" in result
        assert result["overall_consistency_score"] >= 0.90  # >90% target


class TestPerformanceAndScaling:
    """Test performance and scaling requirements."""
    
    def setup_method(self):
        """Setup performance testing."""
        self.sync_manager = DocumentationSyncManager()
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup performance testing."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_sync_performance_single_file(self):
        """Test sync performance for single file meets <5ms target."""
        test_file = Path(self.test_dir) / "perf_test.py"
        test_file.write_text("def simple_function(): pass")
        
        start_time = time.perf_counter()
        
        result = await self.sync_manager.sync_documentation_with_code(
            file_path=str(test_file),
            project_id="perf_test"
        )
        
        end_time = time.perf_counter()
        operation_time_ms = (end_time - start_time) * 1000
        
        assert result["success"] is True
        assert operation_time_ms < 5.0  # <5ms target
        assert result.get("sync_time_ms", 0) < 5.0
    
    @pytest.mark.asyncio
    async def test_consistency_validation_performance(self):
        """Test consistency validation performance meets <10ms target."""
        test_file = Path(self.test_dir) / "consistency_perf.py"
        test_file.write_text("""
def func1(): pass
def func2(): pass
class Class1: pass
class Class2: pass
""")
        
        start_time = time.perf_counter()
        
        result = await self.sync_manager.validate_documentation_consistency(
            file_path=str(test_file),
            project_id="perf_test"
        )
        
        end_time = time.perf_counter()
        validation_time_ms = (end_time - start_time) * 1000
        
        assert result["success"] is True
        assert validation_time_ms < 10.0  # <10ms target
        assert result.get("validation_time_ms", 0) < 10.0
    
    @pytest.mark.asyncio
    async def test_concurrent_sync_operations(self):
        """Test concurrent synchronization operations."""
        # Create multiple test files
        test_files = []
        for i in range(10):
            test_file = Path(self.test_dir) / f"concurrent_{i}.py"
            test_file.write_text(f"def function_{i}(): pass")
            test_files.append(str(test_file))
        
        # Run concurrent sync operations
        start_time = time.perf_counter()
        
        tasks = [
            self.sync_manager.sync_documentation_with_code(
                file_path=file_path,
                project_id="concurrent_test"
            )
            for file_path in test_files
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        # All operations should succeed
        for result in results:
            assert result["success"] is True
        
        # Total time should be reasonable (not significantly longer than single operation)
        assert total_time_ms < 100.0  # Should complete within 100ms for 10 files
    
    @pytest.mark.asyncio
    async def test_large_file_sync_performance(self):
        """Test sync performance for large files."""
        # Create large test file
        large_content = ""
        for i in range(100):
            large_content += f"""
def function_{i}(param1: str, param2: int, param3: bool) -> str:
    '''Function {i} with multiple parameters'''
    if param3:
        return param1 + str(param2)
    return param1

class Class_{i}:
    '''Class {i} documentation'''
    
    def method_{i}(self, value: Any) -> None:
        '''Method {i} documentation'''
        self.value = value
        
    def another_method_{i}(self, data: Dict[str, Any]) -> List[str]:
        '''Another method {i}'''
        return list(data.keys())
"""
        
        large_file = Path(self.test_dir) / "large_file.py"
        large_file.write_text(large_content)
        
        start_time = time.perf_counter()
        
        result = await self.sync_manager.sync_documentation_with_code(
            file_path=str(large_file),
            project_id="large_file_test"
        )
        
        end_time = time.perf_counter()
        sync_time_ms = (end_time - start_time) * 1000
        
        assert result["success"] is True
        # Large files should still complete reasonably quickly
        assert sync_time_ms < 50.0  # <50ms for large files
        assert result.get("sync_time_ms", 0) < 50.0


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios."""
    
    def setup_method(self):
        """Setup error testing."""
        self.sync_manager = DocumentationSyncManager()
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup error testing."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_handle_missing_file_error(self):
        """Test handling of missing file errors."""
        result = await self.sync_manager.sync_documentation_with_code(
            file_path="/nonexistent/file.py",
            project_id="error_test"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_invalid_python_file(self):
        """Test handling of invalid Python file."""
        invalid_file = Path(self.test_dir) / "invalid.py"
        invalid_file.write_text("invalid python syntax !!!")
        
        result = await self.sync_manager.sync_documentation_with_code(
            file_path=str(invalid_file),
            project_id="error_test"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "syntax" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_neo4j_connection_error(self):
        """Test handling of Neo4j connection errors."""
        # Mock Neo4j unavailable
        with patch.object(self.sync_manager.dual_source_validator.neo4j_store, 'is_available', return_value=False):
            test_file = Path(self.test_dir) / "neo4j_error.py"
            test_file.write_text("def test(): pass")
            
            result = await self.sync_manager.sync_documentation_with_code(
                file_path=str(test_file),
                project_id="error_test"
            )
            
            # Should still succeed but with limited functionality
            assert result["success"] is True
            assert "neo4j_unavailable" in result.get("warnings", [])
    
    @pytest.mark.asyncio
    async def test_sync_conflict_resolution(self):
        """Test sync conflict resolution."""
        test_file = Path(self.test_dir) / "conflict_test.py"
        test_file.write_text("def original_function(): pass")
        
        # Simulate sync conflict
        with pytest.raises(SyncConflictError):
            await self.sync_manager._handle_sync_conflict(
                file_path=str(test_file),
                project_id="conflict_test",
                conflict_type="structure_mismatch"
            )
    
    @pytest.mark.asyncio
    async def test_validation_failure_recovery(self):
        """Test recovery from validation failures."""
        test_file = Path(self.test_dir) / "validation_failure.py"
        test_file.write_text("def test(): pass")
        
        # Mock validation failure
        with patch.object(self.sync_manager.dual_source_validator, 'compare_structures', side_effect=ValidationFailureError("Mock failure")):
            result = await self.sync_manager.validate_documentation_consistency(
                file_path=str(test_file),
                project_id="validation_test"
            )
            
            assert result["success"] is False
            assert "validation_failure" in result["error"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])