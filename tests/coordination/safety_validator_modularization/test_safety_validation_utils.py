"""
Comprehensive TDD tests for Safety Validation Utils extraction.
Tests utility functions and helper methods for safety validation.

Following TDD methodology: Tests written FIRST before extraction.
SafetyValidationUtils will provide utility functions for recommendation logic.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock


class TestSafetyValidationUtils:
    """Test Safety Validation Utils functions - to be extracted from safety_validator.py"""
    
    def test_generate_next_steps_approved(self):
        """Test next steps generation for APPROVED recommendation"""
        from ltms.coordination.safety_validation_utils import generate_next_steps
        
        safety_checks = [
            {"check": "functional_tools", "status": "PASS"},
            {"check": "configuration", "status": "PASS"},
            {"check": "cache_health", "status": "PASS"}
        ]
        
        next_steps = generate_next_steps("APPROVED", safety_checks)
        
        assert isinstance(next_steps, list)
        assert len(next_steps) >= 3
        assert "Proceed with legacy removal execution" in next_steps
        assert "Create system backup before removal" in next_steps
        assert "Execute removal tasks in sequence" in next_steps
    
    def test_generate_next_steps_approved_with_caution(self):
        """Test next steps generation for APPROVED_WITH_CAUTION recommendation"""
        from ltms.coordination.safety_validation_utils import generate_next_steps
        
        safety_checks = [
            {"check": "functional_tools", "status": "PASS"},
            {"check": "configuration", "status": "WARN"},
            {"check": "cache_health", "status": "PASS"}
        ]
        
        next_steps = generate_next_steps("APPROVED_WITH_CAUTION", safety_checks)
        
        assert isinstance(next_steps, list)
        assert "Review failed safety checks before proceeding" in next_steps
        assert "Create comprehensive backup and rollback plan" in next_steps
        assert "Execute removal with enhanced monitoring" in next_steps
    
    def test_generate_next_steps_requires_review(self):
        """Test next steps generation for REQUIRES_REVIEW recommendation"""
        from ltms.coordination.safety_validation_utils import generate_next_steps
        
        safety_checks = [
            {"check": "functional_tools", "status": "FAIL"},
            {"check": "configuration", "status": "FAIL"},
            {"check": "cache_health", "status": "WARN"}
        ]
        
        next_steps = generate_next_steps("REQUIRES_REVIEW", safety_checks)
        
        assert isinstance(next_steps, list)
        assert "Address failed safety checks" in next_steps
        assert "Perform additional analysis on high-risk components" in next_steps
        assert "Re-validate after resolving safety concerns" in next_steps
    
    def test_generate_next_steps_with_failed_functional_tools(self):
        """Test next steps generation with failed functional tools check"""
        from ltms.coordination.safety_validation_utils import generate_next_steps
        
        safety_checks = [
            {"check": "functional_tools_available", "status": "FAIL"},
            {"check": "configuration_valid", "status": "PASS"}
        ]
        
        next_steps = generate_next_steps("REQUIRES_REVIEW", safety_checks)
        
        assert "Ensure all 11 LTMC consolidated tools are properly implemented" in next_steps
    
    def test_generate_next_steps_with_failed_configuration(self):
        """Test next steps generation with failed configuration check"""
        from ltms.coordination.safety_validation_utils import generate_next_steps
        
        safety_checks = [
            {"check": "configuration_valid", "status": "FAIL"},
            {"check": "functional_tools", "status": "PASS"}
        ]
        
        next_steps = generate_next_steps("REQUIRES_REVIEW", safety_checks)
        
        assert "Fix system configuration issues before proceeding" in next_steps
    
    def test_create_removal_recommendations_basic(self):
        """Test basic removal recommendations creation"""
        from ltms.coordination.safety_validation_utils import create_removal_recommendations
        
        analysis_data = {
            "legacy_decorators": [
                {"name": "memory_tool", "file": "/test/file1.py", "line": 42},
                {"name": "chat_tool", "file": "/test/file2.py", "line": 24},
                {"name": "custom_tool", "file": "/test/file3.py", "line": 15}
            ],
            "functional_tools": [
                {"name": "memory_action"}, 
                {"name": "chat_action"}
            ]
        }
        
        recommendations = create_removal_recommendations(analysis_data)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) == 3
        
        # Check first recommendation (memory_tool)
        memory_rec = recommendations[0]
        assert memory_rec["legacy_tool"] == "memory_tool"
        assert memory_rec["file_location"] == "/test/file1.py:42"
        assert memory_rec["action"] == "remove"
        assert memory_rec["replacement"] == "memory_action"
        assert memory_rec["priority"] == "high"
        
        # Check second recommendation (chat_tool)
        chat_rec = recommendations[1]
        assert chat_rec["legacy_tool"] == "chat_tool"
        assert chat_rec["file_location"] == "/test/file2.py:24"
        assert chat_rec["replacement"] == "chat_action"
        assert chat_rec["priority"] == "high"
        
        # Check third recommendation (custom_tool)
        custom_rec = recommendations[2]
        assert custom_rec["legacy_tool"] == "custom_tool"
        assert custom_rec["priority"] == "medium"  # Not in high-priority list
    
    def test_create_removal_recommendations_empty_data(self):
        """Test removal recommendations with empty analysis data"""
        from ltms.coordination.safety_validation_utils import create_removal_recommendations
        
        analysis_data = {"legacy_decorators": [], "functional_tools": []}
        
        recommendations = create_removal_recommendations(analysis_data)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) == 0
    
    def test_create_removal_recommendations_missing_fields(self):
        """Test removal recommendations with missing data fields"""
        from ltms.coordination.safety_validation_utils import create_removal_recommendations
        
        analysis_data = {
            "legacy_decorators": [
                {"name": "incomplete_tool"}  # Missing file and line
            ]
        }
        
        recommendations = create_removal_recommendations(analysis_data)
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec["legacy_tool"] == "incomplete_tool"
        assert rec["file_location"] == "None:None"  # Should handle missing fields
        assert rec["replacement"] == "consolidated_tool"  # Default replacement
    
    def test_find_functional_replacement_known_mappings(self):
        """Test functional replacement finding for known mappings"""
        from ltms.coordination.safety_validation_utils import find_functional_replacement
        
        functional_tools = [
            {"name": "memory_action"},
            {"name": "chat_action"},
            {"name": "todo_action"}
        ]
        
        # Test known mappings
        assert find_functional_replacement("memory_tool", functional_tools) == "memory_action"
        assert find_functional_replacement("chat_tool", functional_tools) == "chat_action"
        assert find_functional_replacement("todo_tool", functional_tools) == "todo_action"
        assert find_functional_replacement("unix_tool", functional_tools) == "unix_action"
    
    def test_find_functional_replacement_unknown_tool(self):
        """Test functional replacement finding for unknown tools"""
        from ltms.coordination.safety_validation_utils import find_functional_replacement
        
        functional_tools = [{"name": "some_tool"}]
        
        # Unknown tool should return default
        assert find_functional_replacement("unknown_tool", functional_tools) == "consolidated_tool"
    
    def test_find_functional_replacement_empty_tools(self):
        """Test functional replacement finding with empty functional tools"""
        from ltms.coordination.safety_validation_utils import find_functional_replacement
        
        functional_tools = []
        
        # Should still return proper mapping
        assert find_functional_replacement("memory_tool", functional_tools) == "memory_action"
        assert find_functional_replacement("unknown_tool", functional_tools) == "consolidated_tool"


class TestSafetyValidationUtilsIntegration:
    """Test Safety Validation Utils integration scenarios"""
    
    def test_complete_recommendation_workflow(self):
        """Test complete workflow from analysis data to recommendations"""
        from ltms.coordination.safety_validation_utils import create_removal_recommendations, generate_next_steps
        
        # Simulate analysis data from LegacyCodeAnalyzer
        analysis_data = {
            "legacy_decorators": [
                {"name": "memory_tool", "file": "/ltmc/tools/memory.py", "line": 25},
                {"name": "chat_tool", "file": "/ltmc/tools/chat.py", "line": 18},
                {"name": "pattern_tool", "file": "/ltmc/tools/pattern.py", "line": 33}
            ],
            "functional_tools": [
                {"name": "memory_action"},
                {"name": "chat_action"},
                {"name": "pattern_action"}
            ]
        }
        
        # Generate removal recommendations
        recommendations = create_removal_recommendations(analysis_data)
        
        assert len(recommendations) == 3
        assert all(rec["action"] == "remove" for rec in recommendations)
        assert all(rec["replacement"] != "consolidated_tool" for rec in recommendations)  # All should have specific mappings
        
        # Generate next steps for approved scenario
        safety_checks = [
            {"check": "functional_tools_available", "status": "PASS"},
            {"check": "configuration_valid", "status": "PASS"}
        ]
        
        next_steps = generate_next_steps("APPROVED", safety_checks)
        
        assert "Proceed with legacy removal execution" in next_steps
        assert len(next_steps) >= 3
    
    def test_high_risk_scenario_handling(self):
        """Test handling of high-risk removal scenarios"""
        from ltms.coordination.safety_validation_utils import generate_next_steps
        
        # Multiple failed checks
        safety_checks = [
            {"check": "functional_tools_available", "status": "FAIL"},
            {"check": "configuration_valid", "status": "FAIL"},
            {"check": "cache_healthy", "status": "WARN"}
        ]
        
        next_steps = generate_next_steps("REQUIRES_REVIEW", safety_checks)
        
        # Should include specific remediation steps for each failure
        assert "Ensure all 11 LTMC consolidated tools are properly implemented" in next_steps
        assert "Fix system configuration issues before proceeding" in next_steps
        assert "Address failed safety checks" in next_steps
    
    def test_priority_assignment_logic(self):
        """Test priority assignment logic for different tools"""
        from ltms.coordination.safety_validation_utils import create_removal_recommendations
        
        analysis_data = {
            "legacy_decorators": [
                {"name": "memory_tool", "file": "/test1.py", "line": 1},
                {"name": "chat_tool", "file": "/test2.py", "line": 1}, 
                {"name": "unix_tool", "file": "/test3.py", "line": 1},
                {"name": "custom_tool", "file": "/test4.py", "line": 1}
            ]
        }
        
        recommendations = create_removal_recommendations(analysis_data)
        
        # Memory and chat tools should be high priority
        memory_rec = next(r for r in recommendations if r["legacy_tool"] == "memory_tool")
        chat_rec = next(r for r in recommendations if r["legacy_tool"] == "chat_tool")
        assert memory_rec["priority"] == "high"
        assert chat_rec["priority"] == "high"
        
        # Other tools should be medium priority
        unix_rec = next(r for r in recommendations if r["legacy_tool"] == "unix_tool")
        custom_rec = next(r for r in recommendations if r["legacy_tool"] == "custom_tool")
        assert unix_rec["priority"] == "medium"
        assert custom_rec["priority"] == "medium"


class TestSafetyValidationUtilsEdgeCases:
    """Test edge cases and error handling for Safety Validation Utils"""
    
    def test_generate_next_steps_unknown_recommendation(self):
        """Test next steps generation with unknown recommendation"""
        from ltms.coordination.safety_validation_utils import generate_next_steps
        
        safety_checks = []
        next_steps = generate_next_steps("UNKNOWN_RECOMMENDATION", safety_checks)
        
        # Should default to REQUIRES_REVIEW behavior
        assert isinstance(next_steps, list)
        assert "Address failed safety checks" in next_steps
    
    def test_create_removal_recommendations_malformed_data(self):
        """Test removal recommendations with malformed analysis data"""
        from ltms.coordination.safety_validation_utils import create_removal_recommendations
        
        # Test with non-dict entries
        analysis_data = {
            "legacy_decorators": [
                "invalid_string_entry",
                {"name": "valid_tool", "file": "/test.py", "line": 1},
                None,  # Null entry
                {"file": "/test2.py", "line": 2}  # Missing name
            ]
        }
        
        recommendations = create_removal_recommendations(analysis_data)
        
        # Should only process valid entries
        assert len(recommendations) == 1
        assert recommendations[0]["legacy_tool"] == "valid_tool"
    
    def test_find_functional_replacement_case_sensitivity(self):
        """Test functional replacement with different cases"""
        from ltms.coordination.safety_validation_utils import find_functional_replacement
        
        functional_tools = []
        
        # Test case variations
        assert find_functional_replacement("Memory_Tool", functional_tools) == "consolidated_tool"
        assert find_functional_replacement("MEMORY_TOOL", functional_tools) == "consolidated_tool"
        assert find_functional_replacement("memory_tool", functional_tools) == "memory_action"  # Exact match
    
    def test_generate_next_steps_empty_checks(self):
        """Test next steps generation with empty safety checks"""
        from ltms.coordination.safety_validation_utils import generate_next_steps
        
        next_steps = generate_next_steps("APPROVED", [])
        
        assert isinstance(next_steps, list)
        assert "Proceed with legacy removal execution" in next_steps


# Pytest fixtures for utils testing
@pytest.fixture
def sample_analysis_data():
    """Fixture providing sample analysis data for testing"""
    return {
        "legacy_decorators": [
            {"name": "memory_tool", "file": "/ltmc/memory.py", "line": 42},
            {"name": "chat_tool", "file": "/ltmc/chat.py", "line": 28},
            {"name": "todo_tool", "file": "/ltmc/todo.py", "line": 15},
            {"name": "unix_tool", "file": "/ltmc/unix.py", "line": 33}
        ],
        "functional_tools": [
            {"name": "memory_action"},
            {"name": "chat_action"},
            {"name": "todo_action"},
            {"name": "unix_action"}
        ]
    }

@pytest.fixture
def sample_safety_checks_passed():
    """Fixture providing sample safety checks that all passed"""
    return [
        {"check": "functional_tools_available", "status": "PASS"},
        {"check": "configuration_valid", "status": "PASS"},
        {"check": "cache_healthy", "status": "PASS"},
        {"check": "dependency_analysis_complete", "status": "PASS"}
    ]

@pytest.fixture
def sample_safety_checks_mixed():
    """Fixture providing sample safety checks with mixed results"""
    return [
        {"check": "functional_tools_available", "status": "PASS"},
        {"check": "configuration_valid", "status": "FAIL"},
        {"check": "cache_healthy", "status": "WARN"},
        {"check": "dependency_analysis_complete", "status": "PASS"}
    ]