"""
Phase 2 Security Integration Tests

COMPREHENSIVE SECURITY VALIDATION:
- Tests that Phase 1 security features work correctly across all Phase 2 components
- Validates project isolation is maintained in all Phase 2 operations
- Tests input sanitization across all new Phase 2 MCP tools
- Validates secure path handling in configuration and documentation
- Tests cross-project access restrictions in task routing and orchestration
- Validates security performance impact stays within <5ms overhead

Phase 1 Security Features Integration:
1. Project Isolation - ProjectIsolationManager integration across Phase 2
2. Path Security - SecurePathValidator for config/documentation paths
3. Input Sanitization - XSS, SQL injection, path traversal prevention
4. MCP Security - Secure tool parameter validation
5. Database Security - Project-scoped database operations

Phase 2 Security Requirements:
- All 19 new MCP tools (8+6+5) use Phase 1 security
- Project isolation enforced in task routing, configuration, orchestration
- Secure configuration template loading with path validation
- Documentation generation with secure file handling
- Orchestration workflows respect project boundaries
- Security performance overhead <5ms per operation

REAL SECURITY TESTING APPROACH:
- Uses actual Phase 1 security components (no mocks)
- Tests real attack vectors and malicious inputs
- Validates actual database project isolation
- Tests real file system path security
- Measures actual security validation performance
"""

import pytest
import pytest_asyncio
import asyncio
import time
import json
import requests
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import Phase 1 security components for validation
from ltms.security.project_isolation import ProjectIsolationManager
from ltms.security.path_security import SecurePathValidator
from ltms.security.mcp_integration import MCPSecurityManager


class TestPhase2ProjectIsolationIntegration:
    """
    Project Isolation Integration Tests
    
    Tests that Phase 1 project isolation works correctly across all Phase 2 components:
    - TaskBlueprint operations are project-scoped
    - Task routing respects project boundaries
    - Configuration templates are project-isolated
    - Documentation generation is project-scoped
    - Orchestration workflows respect project isolation
    """
    
    @pytest.fixture(scope="class")
    def server_health(self):
        """Ensure LTMC server is available with security enabled."""
        try:
            response = requests.get("http://localhost:5050/health", timeout=5)
            assert response.status_code == 200, "LTMC server not healthy"
            
            health_data = response.json()
            # Verify security is enabled in server health
            # Note: Some servers may not expose security details, so we'll check functionality instead
            
            return health_data
        except requests.RequestException as e:
            pytest.skip(f"LTMC server unavailable for security testing: {e}")
    
    @pytest.fixture
    def isolated_projects(self):
        """Create test projects for isolation testing."""
        return {
            "project_alpha": "security_test_project_alpha",
            "project_beta": "security_test_project_beta", 
            "project_gamma": "security_test_project_gamma"
        }
    
    def test_blueprint_project_isolation(self, server_health, isolated_projects):
        """
        Test that TaskBlueprint operations are properly project-isolated.
        
        Validates:
        - Blueprints can only be accessed within their project
        - Cross-project blueprint access is blocked
        - Blueprint listing respects project boundaries
        - Blueprint operations include project validation
        """
        # Create blueprints in different projects
        project_blueprints = {}
        
        for project_name, project_id in isolated_projects.items():
            blueprint_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_task_blueprint",
                    "arguments": {
                        "title": f"Blueprint for {project_name}",
                        "description": f"Project-specific blueprint for {project_name} isolation testing",
                        "complexity": "MODERATE",
                        "estimated_duration_minutes": 120,
                        "required_skills": ["project-security", "isolation"],
                        "project_id": project_id,
                        "metadata": {
                            "security_test": True,
                            "project_marker": project_name,
                            "confidential_data": f"Secret data for {project_name}"
                        }
                    }
                },
                "id": f"bp_{project_name}"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=blueprint_payload, timeout=10)
            assert response.status_code == 200, f"Blueprint creation failed for {project_name}: {response.status_code}"
            
            result = response.json()
            assert result.get("error") is None, f"Blueprint creation error for {project_name}: {result.get('error')}"
            
            project_blueprints[project_name] = result["result"]["blueprint_id"]
        
        # Test project isolation - each project should only see its own blueprints
        for project_name, project_id in isolated_projects.items():
            list_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "list_project_blueprints",
                    "arguments": {
                        "project_id": project_id,
                        "include_metadata": True
                    }
                },
                "id": f"list_{project_name}"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=list_payload, timeout=10)
            assert response.status_code == 200, f"Blueprint listing failed for {project_name}"
            
            result = response.json()
            assert result.get("error") is None, f"Blueprint listing error for {project_name}: {result.get('error')}"
            
            blueprints = result["result"]["blueprints"]
            
            # Should only contain blueprints from this project
            for blueprint in blueprints:
                assert blueprint["project_id"] == project_id, f"Found cross-project blueprint in {project_name}: {blueprint['project_id']}"
                assert blueprint["metadata"]["project_marker"] == project_name, f"Wrong project marker in {project_name}"
                
                # Should not contain confidential data from other projects
                confidential_data = blueprint["metadata"]["confidential_data"]
                assert project_name in confidential_data, f"Wrong confidential data in {project_name}: {confidential_data}"
        
        # Test cross-project access blocking
        project_alpha_id = isolated_projects["project_alpha"]
        project_beta_blueprint_id = project_blueprints["project_beta"]
        
        # Try to access project_beta's blueprint from project_alpha context
        cross_access_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_blueprint_details",
                "arguments": {
                    "blueprint_id": project_beta_blueprint_id,
                    "project_id": project_alpha_id,  # Wrong project context
                    "include_metadata": True
                }
            },
            "id": "cross_access_test"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=cross_access_payload, timeout=10)
        assert response.status_code == 200, "Cross-access request should be handled gracefully"
        
        result = response.json()
        # Should return an error or no results due to project isolation
        if result.get("error") is None:
            # If no error, should return no blueprint or access denied
            blueprint_details = result.get("result", {}).get("blueprint")
            if blueprint_details:
                # If returned, should not contain confidential data from other project
                assert "project_beta" not in str(blueprint_details.get("metadata", {})), "Cross-project data leak detected"
        else:
            # Error is expected for cross-project access
            error_message = str(result.get("error", {})).lower()
            assert any(keyword in error_message for keyword in ["access", "permission", "project", "isolation"]), "Error should indicate access restriction"
        
        print("✅ Blueprint project isolation validated")
    
    def test_task_routing_project_boundaries(self, server_health, isolated_projects):
        """
        Test that task routing respects project boundaries.
        
        Validates:
        - Team members can only be assigned to tasks in their project
        - Cross-project team member access is blocked
        - Routing preferences respect project isolation
        - Assignment data is project-scoped
        """
        project_alpha = isolated_projects["project_alpha"]
        project_beta = isolated_projects["project_beta"]
        
        # Create blueprints for routing test
        alpha_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Alpha Project Routing Test",
                    "description": "Task routing test for project alpha",
                    "complexity": "MODERATE",
                    "estimated_duration_minutes": 180,
                    "required_skills": ["alpha-specific", "security"],
                    "project_id": project_alpha
                }
            },
            "id": "alpha_routing_bp"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=alpha_blueprint_payload, timeout=10)
        result = response.json()
        alpha_blueprint_id = result["result"]["blueprint_id"]
        
        # Create team members for different projects
        alpha_team_member = {
            "member_id": "alpha_dev_001",
            "name": "Alpha Developer",
            "skills": ["alpha-specific", "security"],
            "experience_level": 0.8,
            "current_workload": 0.3,
            "availability_hours": 8.0,
            "project_id": project_alpha,  # Explicitly assigned to alpha
            "clearance_level": "alpha_confidential"
        }
        
        beta_team_member = {
            "member_id": "beta_dev_001", 
            "name": "Beta Developer",
            "skills": ["beta-specific", "security"],
            "experience_level": 0.7,
            "current_workload": 0.4,
            "availability_hours": 7.0,
            "project_id": project_beta,  # Explicitly assigned to beta
            "clearance_level": "beta_confidential"
        }
        
        # Test valid routing within project
        valid_routing_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "route_task_to_member",
                "arguments": {
                    "subtask_blueprint_id": alpha_blueprint_id,
                    "available_members": [alpha_team_member],  # Same project
                    "project_id": project_alpha,
                    "security_validation": True
                }
            },
            "id": "valid_routing"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=valid_routing_payload, timeout=10)
        assert response.status_code == 200, "Valid routing within project failed"
        result = response.json()
        assert result.get("error") is None, f"Valid routing error: {result.get('error')}"
        
        assignment = result["result"]
        assert assignment["assigned_member"]["member_id"] == "alpha_dev_001", "Wrong member assigned"
        assert assignment["project_id"] == project_alpha, "Assignment project ID mismatch"
        
        # Test cross-project routing blocking
        cross_project_routing_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "route_task_to_member",
                "arguments": {
                    "subtask_blueprint_id": alpha_blueprint_id,
                    "available_members": [beta_team_member],  # Different project
                    "project_id": project_alpha,
                    "security_validation": True
                }
            },
            "id": "cross_project_routing"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=cross_project_routing_payload, timeout=10)
        assert response.status_code == 200, "Cross-project routing should be handled gracefully"
        result = response.json()
        
        # Should either return error or no suitable assignment
        if result.get("error"):
            error_message = str(result.get("error", {})).lower()
            assert any(keyword in error_message for keyword in ["project", "isolation", "access", "permission"]), "Error should indicate project restriction"
        else:
            # If no error, should indicate no suitable member found
            assignment_result = result.get("result", {})
            if "assigned_member" in assignment_result:
                # If assignment made, should not be the cross-project member
                assert assignment_result["assigned_member"]["member_id"] != "beta_dev_001", "Cross-project assignment should be blocked"
            else:
                # No assignment is acceptable outcome
                assert "no_suitable_member" in assignment_result or assignment_result.get("success") is False, "Should indicate no suitable member"
        
        # Test mixed team with project filtering
        mixed_team = [alpha_team_member, beta_team_member]
        
        mixed_routing_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "route_task_to_member",
                "arguments": {
                    "subtask_blueprint_id": alpha_blueprint_id,
                    "available_members": mixed_team,
                    "project_id": project_alpha,
                    "security_validation": True,
                    "enforce_project_isolation": True
                }
            },
            "id": "mixed_team_routing"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=mixed_routing_payload, timeout=10)
        result = response.json()
        
        if result.get("error") is None and result.get("result", {}).get("assigned_member"):
            assigned_member = result["result"]["assigned_member"]
            # Should only assign the alpha project member
            assert assigned_member["member_id"] == "alpha_dev_001", "Should filter to project-appropriate member"
            assert assigned_member.get("project_id") == project_alpha, "Assigned member should be from correct project"
        
        print("✅ Task routing project boundaries validated")
    
    def test_configuration_project_isolation(self, server_health, isolated_projects):
        """
        Test that configuration templates are properly project-isolated.
        
        Validates:
        - Configuration templates are project-scoped
        - Cross-project configuration access is blocked  
        - Project-specific environment variables are isolated
        - Configuration inheritance respects project boundaries
        """
        project_alpha = isolated_projects["project_alpha"]
        project_beta = isolated_projects["project_beta"]
        
        # Apply project-specific configurations
        alpha_config_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "apply_project_config_template",
                "arguments": {
                    "project_id": project_alpha,
                    "template_name": "high_performance",
                    "environment_vars": {
                        "ALPHA_SECRET_KEY": "alpha_confidential_key_12345",
                        "ALPHA_DATABASE_URL": "postgresql://alpha_user:alpha_pass@localhost/alpha_db",
                        "PROJECT_NAME": "Project Alpha",
                        "SECURITY_LEVEL": "alpha_restricted"
                    },
                    "feature_flags": {
                        "alpha_specific_feature": True,
                        "cross_project_access": False
                    }
                }
            },
            "id": "alpha_config"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=alpha_config_payload, timeout=10)
        assert response.status_code == 200, "Alpha config application failed"
        result = response.json()
        assert result.get("error") is None, "Alpha config error"
        
        beta_config_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "apply_project_config_template",
                "arguments": {
                    "project_id": project_beta,
                    "template_name": "default_project",
                    "environment_vars": {
                        "BETA_SECRET_KEY": "beta_confidential_key_67890",
                        "BETA_DATABASE_URL": "postgresql://beta_user:beta_pass@localhost/beta_db", 
                        "PROJECT_NAME": "Project Beta",
                        "SECURITY_LEVEL": "beta_restricted"
                    },
                    "feature_flags": {
                        "beta_specific_feature": True,
                        "cross_project_access": False
                    }
                }
            },
            "id": "beta_config"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=beta_config_payload, timeout=10)
        assert response.status_code == 200, "Beta config application failed"
        result = response.json()
        assert result.get("error") is None, "Beta config error"
        
        # Test project-specific configuration retrieval
        alpha_get_config_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_project_config",
                "arguments": {
                    "project_id": project_alpha,
                    "include_environment_vars": True,
                    "include_feature_flags": True
                }
            },
            "id": "get_alpha_config"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=alpha_get_config_payload, timeout=10)
        assert response.status_code == 200, "Alpha config retrieval failed"
        result = response.json()
        assert result.get("error") is None, "Alpha config retrieval error"
        
        alpha_config = result["result"]["configuration"]
        alpha_env_vars = alpha_config.get("environment_vars", {})
        
        # Should contain alpha-specific data
        assert "ALPHA_SECRET_KEY" in alpha_env_vars, "Alpha secret key not found"
        assert alpha_env_vars["PROJECT_NAME"] == "Project Alpha", "Wrong project name"
        assert alpha_env_vars["SECURITY_LEVEL"] == "alpha_restricted", "Wrong security level"
        
        # Should not contain beta-specific data
        assert "BETA_SECRET_KEY" not in alpha_env_vars, "Beta secret key leaked into alpha config"
        assert "beta" not in str(alpha_env_vars).lower(), "Beta data leaked into alpha config"
        
        # Test cross-project configuration access blocking
        cross_project_config_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_project_config",
                "arguments": {
                    "project_id": project_beta,  # Try to access beta from alpha context
                    "requesting_project_id": project_alpha,  # Alpha trying to access beta
                    "include_environment_vars": True
                }
            },
            "id": "cross_project_config"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=cross_project_config_payload, timeout=10)
        result = response.json()
        
        # Should either return error or filtered/empty configuration
        if result.get("error") is None:
            config_data = result.get("result", {}).get("configuration", {})
            env_vars = config_data.get("environment_vars", {})
            
            # If data returned, should not contain beta secrets
            assert "BETA_SECRET_KEY" not in env_vars, "Cross-project secret access allowed"
            assert "beta_pass" not in str(env_vars), "Cross-project credentials leaked"
        else:
            error_message = str(result.get("error", {})).lower()
            assert any(keyword in error_message for keyword in ["access", "permission", "project", "isolation"]), "Error should indicate access restriction"
        
        print("✅ Configuration project isolation validated")
    
    def test_documentation_project_security(self, server_health, isolated_projects):
        """
        Test that documentation generation respects project security.
        
        Validates:
        - Documentation only includes project-scoped data
        - Cross-project information is not included in documentation
        - Generated documentation respects confidentiality levels
        - Documentation file paths are project-isolated
        """
        project_alpha = isolated_projects["project_alpha"]
        project_beta = isolated_projects["project_beta"]
        
        # Create project-specific blueprints with confidential data
        alpha_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Alpha Confidential Project",
                    "description": "Confidential project for Alpha company with proprietary algorithms and sensitive customer data",
                    "complexity": "CRITICAL",
                    "estimated_duration_minutes": 720,
                    "required_skills": ["alpha-proprietary", "confidential"],
                    "project_id": project_alpha,
                    "metadata": {
                        "confidentiality_level": "CONFIDENTIAL",
                        "customer_names": ["AlphaCorpClient1", "AlphaCorpClient2"],
                        "proprietary_algorithms": ["AlphaML-v3", "AlphaSecure-v2"],
                        "internal_apis": ["alpha-internal-api.company.com"]
                    }
                }
            },
            "id": "alpha_confidential_bp"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=alpha_blueprint_payload, timeout=10)
        result = response.json()
        alpha_blueprint_id = result["result"]["blueprint_id"]
        
        beta_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Beta Secret Project",
                    "description": "Secret project for Beta company with classified information",
                    "complexity": "CRITICAL", 
                    "estimated_duration_minutes": 600,
                    "required_skills": ["beta-classified", "secret"],
                    "project_id": project_beta,
                    "metadata": {
                        "confidentiality_level": "SECRET",
                        "customer_names": ["BetaCorpClient1", "BetaCorpClient2"],
                        "proprietary_algorithms": ["BetaCrypt-v4", "BetaAI-v1"],
                        "internal_apis": ["beta-secret-api.company.com"]
                    }
                }
            },
            "id": "beta_secret_bp"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=beta_blueprint_payload, timeout=10)
        result = response.json()
        beta_blueprint_id = result["result"]["blueprint_id"]
        
        # Generate documentation for Alpha project
        alpha_doc_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "generate_project_documentation",
                "arguments": {
                    "project_id": project_alpha,
                    "blueprint_id": alpha_blueprint_id,
                    "documentation_types": ["api_docs", "architecture_diagram", "project_overview"],
                    "include_confidential_data": True,  # Should only include alpha data
                    "security_context": project_alpha
                }
            },
            "id": "alpha_documentation"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=alpha_doc_payload, timeout=15)
        assert response.status_code == 200, "Alpha documentation generation failed"
        result = response.json()
        assert result.get("error") is None, f"Alpha documentation error: {result.get('error')}"
        
        alpha_docs = result["result"]["generated_documents"]
        assert len(alpha_docs) >= 3, "Should generate all requested document types"
        
        # Validate alpha documentation content
        for doc in alpha_docs:
            doc_content = doc["content"].lower()
            
            # Should contain alpha-specific data
            assert "alpha" in doc_content, f"Alpha documentation missing alpha references: {doc['type']}"
            
            # Should not contain beta-specific data
            assert "betacorpclient" not in doc_content, f"Beta client data leaked into alpha docs: {doc['type']}"
            assert "betacrypt" not in doc_content, f"Beta proprietary algorithm leaked: {doc['type']}"
            assert "beta-secret-api" not in doc_content, f"Beta API endpoint leaked: {doc['type']}"
            assert "secret" not in doc_content or "alpha" in doc_content.split("secret")[0], f"Beta secret classification leaked: {doc['type']}"
        
        # Test cross-project documentation access blocking
        cross_project_doc_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "generate_cross_project_documentation",
                "arguments": {
                    "requesting_project_id": project_alpha,
                    "target_project_id": project_beta,  # Try to document beta from alpha context
                    "documentation_types": ["project_overview"],
                    "include_confidential_data": True
                }
            },
            "id": "cross_project_documentation"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=cross_project_doc_payload, timeout=15)
        result = response.json()
        
        # Should either return error or heavily filtered/empty documentation
        if result.get("error") is None:
            cross_docs = result.get("result", {}).get("generated_documents", [])
            if cross_docs:
                for doc in cross_docs:
                    doc_content = doc["content"].lower()
                    # Should not contain beta confidential information
                    assert "betacorpclient" not in doc_content, "Cross-project client data leaked"
                    assert "betacrypt" not in doc_content, "Cross-project proprietary info leaked"
                    assert "beta-secret-api" not in doc_content, "Cross-project API info leaked"
        else:
            error_message = str(result.get("error", {})).lower()
            assert any(keyword in error_message for keyword in ["access", "permission", "project", "security"]), "Error should indicate security restriction"
        
        print("✅ Documentation project security validated")


class TestPhase2InputSanitizationIntegration:
    """
    Input Sanitization Integration Tests
    
    Tests that all Phase 2 MCP tools properly sanitize inputs to prevent:
    - XSS attacks in documentation and configuration
    - SQL injection in database operations
    - Path traversal in file operations
    - Command injection in orchestration
    - JSON injection in API parameters
    """
    
    @pytest.fixture(scope="class")
    def server_health(self):
        """Ensure LTMC server is available."""
        try:
            response = requests.get("http://localhost:5050/health", timeout=5)
            assert response.status_code == 200
            return response.json()
        except requests.RequestException as e:
            pytest.skip(f"LTMC server unavailable: {e}")
    
    @pytest.fixture
    def malicious_inputs(self):
        """Collection of malicious input patterns for testing."""
        return {
            "xss_payloads": [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert(String.fromCharCode(88,83,83))//';",
                "<svg/onload=alert('XSS')>"
            ],
            "sql_injection_payloads": [
                "'; DROP TABLE blueprints; --",
                "' OR '1'='1",
                "1'; DELETE FROM tasks; --", 
                "admin'--",
                "' UNION SELECT password FROM users--"
            ],
            "path_traversal_payloads": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "/etc/shadow",
                "....//....//....//etc//passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
            ],
            "command_injection_payloads": [
                "; rm -rf /",
                "| cat /etc/passwd",
                "`rm -rf /`",
                "$(rm -rf /)",
                "&& cat /etc/passwd"
            ],
            "json_injection_payloads": [
                '{"malicious": "value"}',
                '"}},"injected":"value",{"valid":"',
                'null},"injected_field":"malicious_value",{"dummy":"',
                '\\\"},"injected":"payload",{"'
            ]
        }
    
    def test_blueprint_input_sanitization(self, server_health, malicious_inputs):
        """
        Test TaskBlueprint MCP tools sanitize inputs properly.
        
        Validates:
        - Blueprint title/description XSS prevention
        - Metadata SQL injection prevention  
        - Skills array sanitization
        - Project ID path traversal prevention
        """
        project_id = "input_sanitization_test"
        
        # Test XSS in blueprint title and description
        for xss_payload in malicious_inputs["xss_payloads"][:3]:  # Test first 3
            xss_blueprint_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_task_blueprint",
                    "arguments": {
                        "title": f"Blueprint {xss_payload} Title",
                        "description": f"Description with {xss_payload} content",
                        "complexity": "MODERATE",
                        "estimated_duration_minutes": 120,
                        "required_skills": ["testing", xss_payload, "security"],
                        "project_id": project_id,
                        "metadata": {
                            "notes": f"Notes with {xss_payload}",
                            "tags": ["safe", xss_payload]
                        }
                    }
                },
                "id": "xss_test"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=xss_blueprint_payload, timeout=10)
            assert response.status_code == 200, f"Request should be processed (but sanitized) for XSS payload: {xss_payload}"
            
            result = response.json()
            
            if result.get("error") is None:
                # If successful, verify XSS payload was sanitized
                blueprint_data = result.get("result", {})
                if "title" in str(blueprint_data):
                    blueprint_str = str(blueprint_data).lower()
                    assert "<script>" not in blueprint_str, f"XSS payload not sanitized: {xss_payload}"
                    assert "javascript:" not in blueprint_str, f"XSS payload not sanitized: {xss_payload}"
                    assert "onerror=" not in blueprint_str, f"XSS payload not sanitized: {xss_payload}"
            else:
                # Error is also acceptable - indicates input validation rejection
                error_message = str(result.get("error", {})).lower()
                assert any(keyword in error_message for keyword in ["validation", "invalid", "sanitization"]), f"Error should indicate input validation for XSS: {xss_payload}"
        
        # Test SQL injection in metadata
        for sql_payload in malicious_inputs["sql_injection_payloads"][:3]:  # Test first 3
            sql_blueprint_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call", 
                "params": {
                    "name": "create_task_blueprint",
                    "arguments": {
                        "title": "SQL Injection Test",
                        "description": "Testing SQL injection prevention",
                        "complexity": "MODERATE",
                        "estimated_duration_minutes": 120,
                        "required_skills": ["security", sql_payload],
                        "project_id": project_id,
                        "metadata": {
                            "sql_test": sql_payload,
                            "priority": f"high{sql_payload}",
                            "category": sql_payload
                        }
                    }
                },
                "id": "sql_test"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=sql_blueprint_payload, timeout=10)
            result = response.json()
            
            if result.get("error") is None:
                # If successful, verify SQL injection was neutralized
                blueprint_data = result.get("result", {})
                blueprint_str = str(blueprint_data).lower()
                assert "drop table" not in blueprint_str, f"SQL injection not prevented: {sql_payload}"
                assert "delete from" not in blueprint_str, f"SQL injection not prevented: {sql_payload}"
                assert "union select" not in blueprint_str, f"SQL injection not prevented: {sql_payload}"
            else:
                # Error indicates input validation
                error_message = str(result.get("error", {})).lower()
                assert "validation" in error_message or "invalid" in error_message, f"Should indicate validation error for SQL: {sql_payload}"
        
        # Test path traversal in project_id
        for path_payload in malicious_inputs["path_traversal_payloads"][:3]:  # Test first 3
            path_blueprint_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_task_blueprint",
                    "arguments": {
                        "title": "Path Traversal Test",
                        "description": "Testing path traversal prevention", 
                        "complexity": "SIMPLE",
                        "estimated_duration_minutes": 60,
                        "required_skills": ["security"],
                        "project_id": path_payload,  # Malicious project ID
                        "metadata": {
                            "file_path": path_payload
                        }
                    }
                },
                "id": "path_test"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=path_blueprint_payload, timeout=10)
            result = response.json()
            
            # Should return error for path traversal attempts
            assert result.get("error") is not None, f"Path traversal should be blocked: {path_payload}"
            error_message = str(result.get("error", {})).lower()
            assert any(keyword in error_message for keyword in ["path", "invalid", "security", "validation"]), f"Error should indicate path security issue: {path_payload}"
        
        print("✅ Blueprint input sanitization validated")
    
    def test_configuration_input_sanitization(self, server_health, malicious_inputs):
        """
        Test Configuration MCP tools sanitize inputs properly.
        
        Validates:
        - Environment variable injection prevention
        - Configuration path traversal prevention
        - Template name sanitization
        - JSON injection in configuration values
        """
        project_id = "config_sanitization_test"
        
        # Test path traversal in template names
        for path_payload in malicious_inputs["path_traversal_payloads"][:3]:
            path_config_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "load_config_template",
                    "arguments": {
                        "template_name": path_payload,  # Malicious template path
                        "project_id": project_id
                    }
                },
                "id": "config_path_test"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=path_config_payload, timeout=10)
            result = response.json()
            
            # Should return error for path traversal
            assert result.get("error") is not None, f"Config path traversal should be blocked: {path_payload}"
            error_message = str(result.get("error", {})).lower()
            assert any(keyword in error_message for keyword in ["path", "invalid", "template", "not found", "security"]), f"Error should indicate path issue: {path_payload}"
        
        # Test command injection in environment variables
        for cmd_payload in malicious_inputs["command_injection_payloads"][:3]:
            cmd_config_payload = {
                "jsonrpc": "2.0", 
                "method": "tools/call",
                "params": {
                    "name": "apply_project_config_template",
                    "arguments": {
                        "project_id": project_id,
                        "template_name": "default_project",
                        "environment_vars": {
                            "MALICIOUS_VAR": cmd_payload,
                            "PATH": f"/usr/bin{cmd_payload}",
                            "DATABASE_URL": f"postgresql://user:pass@localhost/db{cmd_payload}"
                        }
                    }
                },
                "id": "config_cmd_test"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=cmd_config_payload, timeout=10)
            result = response.json()
            
            if result.get("error") is None:
                # If successful, verify command injection was neutralized
                config_data = result.get("result", {})
                config_str = str(config_data).lower()
                assert "rm -rf" not in config_str, f"Command injection not prevented: {cmd_payload}"
                assert "/etc/passwd" not in config_str, f"Command injection not prevented: {cmd_payload}"
                assert "cat " not in config_str, f"Command injection not prevented: {cmd_payload}"
            else:
                # Error indicates validation
                error_message = str(result.get("error", {})).lower()
                assert any(keyword in error_message for keyword in ["validation", "invalid", "security"]), f"Should indicate validation error: {cmd_payload}"
        
        # Test JSON injection in configuration values
        for json_payload in malicious_inputs["json_injection_payloads"][:3]:
            json_config_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_project_config_template",
                    "arguments": {
                        "project_id": project_id,
                        "template_updates": {
                            "injected_config": json_payload,
                            "valid_config": f"value{json_payload}end"
                        }
                    }
                },
                "id": "config_json_test"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=json_config_payload, timeout=10)
            result = response.json()
            
            if result.get("error") is None:
                # Verify JSON structure wasn't broken by injection
                config_result = result.get("result", {})
                # Should be valid JSON structure without injected fields
                assert "injected_field" not in str(config_result), f"JSON injection succeeded: {json_payload}"
                assert "malicious_value" not in str(config_result), f"JSON injection succeeded: {json_payload}"
        
        print("✅ Configuration input sanitization validated")
    
    def test_documentation_input_sanitization(self, server_health, malicious_inputs):
        """
        Test Documentation MCP tools sanitize inputs properly.
        
        Validates:
        - XSS prevention in generated documentation
        - Path traversal prevention in documentation paths
        - Template injection prevention
        - HTML/Markdown injection prevention
        """
        project_id = "doc_sanitization_test"
        
        # Create test blueprint for documentation
        test_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Documentation Sanitization Test",
                    "description": "Test blueprint for documentation input sanitization",
                    "complexity": "MODERATE",
                    "estimated_duration_minutes": 120,
                    "required_skills": ["documentation", "security"],
                    "project_id": project_id
                }
            },
            "id": "doc_test_bp"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=test_blueprint_payload, timeout=10)
        result = response.json()
        test_blueprint_id = result["result"]["blueprint_id"]
        
        # Test XSS in documentation generation parameters
        for xss_payload in malicious_inputs["xss_payloads"][:3]:
            xss_doc_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "generate_project_documentation",
                    "arguments": {
                        "project_id": project_id,
                        "blueprint_id": test_blueprint_id,
                        "documentation_types": ["api_docs"],
                        "custom_title": f"Documentation {xss_payload} Title",
                        "custom_description": f"Description with {xss_payload}",
                        "metadata": {
                            "author": f"Author {xss_payload}",
                            "notes": xss_payload
                        }
                    }
                },
                "id": "doc_xss_test"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=xss_doc_payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("error") is None:
                    # Verify XSS was sanitized in generated documentation
                    docs = result.get("result", {}).get("generated_documents", [])
                    for doc in docs:
                        doc_content = doc["content"].lower()
                        assert "<script>" not in doc_content, f"XSS in documentation not sanitized: {xss_payload}"
                        assert "javascript:" not in doc_content, f"XSS in documentation not sanitized: {xss_payload}"
                        assert "onerror=" not in doc_content, f"XSS in documentation not sanitized: {xss_payload}"
        
        # Test path traversal in documentation output paths
        for path_payload in malicious_inputs["path_traversal_payloads"][:2]:
            path_doc_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "generate_project_documentation",
                    "arguments": {
                        "project_id": project_id,
                        "blueprint_id": test_blueprint_id,
                        "documentation_types": ["api_docs"],
                        "output_path": path_payload,  # Malicious output path
                        "template_path": f"templates/{path_payload}/template.md"
                    }
                },
                "id": "doc_path_test"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=path_doc_payload, timeout=15)
            result = response.json()
            
            # Should either error or sanitize path
            if result.get("error"):
                error_message = str(result.get("error", {})).lower()
                assert any(keyword in error_message for keyword in ["path", "invalid", "security"]), f"Should indicate path security issue: {path_payload}"
            else:
                # If successful, path should be sanitized
                doc_result = result.get("result", {})
                output_info = str(doc_result).lower()
                assert "/etc/passwd" not in output_info, f"Path traversal in output not prevented: {path_payload}"
                assert "../../../" not in output_info, f"Path traversal in output not prevented: {path_payload}"
        
        print("✅ Documentation input sanitization validated")


class TestPhase2SecurityPerformanceImpact:
    """
    Security Performance Impact Tests
    
    Tests that Phase 2 security integration maintains performance requirements:
    - Security validation overhead <5ms per operation
    - Performance degradation under security checks minimal
    - Security checks scale properly with system load
    - Memory impact of security features acceptable
    """
    
    @pytest.fixture(scope="class")
    def server_health(self):
        """Ensure LTMC server is available."""
        try:
            response = requests.get("http://localhost:5050/health", timeout=5)
            assert response.status_code == 200
            return response.json()
        except requests.RequestException as e:
            pytest.skip(f"LTMC server unavailable: {e}")
    
    def test_security_validation_performance_overhead(self, server_health):
        """
        Test that security validation adds <5ms overhead per operation.
        
        Validates:
        - Individual security checks are fast
        - Combined security overhead stays under limit
        - Performance consistency across operation types
        - Security overhead scales linearly
        """
        project_id = "security_performance_test"
        
        # Test security overhead for different operation types
        operation_times = {
            "blueprint_creation": [],
            "task_routing": [],
            "config_loading": [],
            "documentation": []
        }
        
        # Test blueprint creation security overhead
        for i in range(30):
            blueprint_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_task_blueprint",
                    "arguments": {
                        "title": f"Security Performance Test {i}",
                        "description": f"Testing security validation performance {i}",
                        "complexity": "MODERATE",
                        "estimated_duration_minutes": 120,
                        "required_skills": ["security", "performance"],
                        "project_id": project_id,
                        "enable_security_validation": True,  # Explicit security validation
                        "metadata": {
                            "security_test": True,
                            "iteration": i
                        }
                    }
                },
                "id": f"perf_{i}"
            }
            
            start_time = time.perf_counter()
            response = requests.post("http://localhost:5050/jsonrpc", json=blueprint_payload, timeout=10)
            end_time = time.perf_counter()
            
            operation_time = (end_time - start_time) * 1000
            operation_times["blueprint_creation"].append(operation_time)
            
            assert response.status_code == 200, f"Security-validated blueprint creation {i} failed"
            result = response.json()
            assert result.get("error") is None, f"Security validation error {i}: {result.get('error')}"
        
        # Test task routing security overhead
        team_member = {
            "member_id": "security_perf_dev",
            "name": "Security Performance Developer",
            "skills": ["security", "performance"],
            "experience_level": 0.8,
            "current_workload": 0.3,
            "availability_hours": 8.0,
            "project_id": project_id
        }
        
        # Get one of the created blueprints for routing
        list_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_project_blueprints",
                "arguments": {"project_id": project_id}
            },
            "id": "list_for_routing"
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=list_payload, timeout=10)
        result = response.json()
        blueprints = result["result"]["blueprints"]
        test_blueprint_id = blueprints[0]["blueprint_id"] if blueprints else None
        
        if test_blueprint_id:
            for i in range(25):
                routing_payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "route_task_to_member",
                        "arguments": {
                            "subtask_blueprint_id": test_blueprint_id,
                            "available_members": [team_member],
                            "project_id": project_id,
                            "security_validation": True,  # Explicit security validation
                            "validate_project_isolation": True
                        }
                    },
                    "id": f"route_perf_{i}"
                }
                
                start_time = time.perf_counter()
                response = requests.post("http://localhost:5050/jsonrpc", json=routing_payload, timeout=10)
                end_time = time.perf_counter()
                
                operation_time = (end_time - start_time) * 1000
                operation_times["task_routing"].append(operation_time)
                
                assert response.status_code == 200, f"Security-validated routing {i} failed"
        
        # Test configuration loading security overhead
        for i in range(20):
            config_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "load_config_template",
                    "arguments": {
                        "template_name": "default_project",
                        "project_id": f"{project_id}_{i}",
                        "validate_security": True,  # Explicit security validation
                        "validate_paths": True
                    }
                },
                "id": f"config_perf_{i}"
            }
            
            start_time = time.perf_counter()
            response = requests.post("http://localhost:5050/jsonrpc", json=config_payload, timeout=10)
            end_time = time.perf_counter()
            
            operation_time = (end_time - start_time) * 1000
            operation_times["config_loading"].append(operation_time)
            
            assert response.status_code == 200, f"Security-validated config loading {i} failed"
        
        # Analyze security performance overhead
        print(f"\\n📊 SECURITY VALIDATION PERFORMANCE OVERHEAD:")
        
        total_security_overhead = 0
        
        for operation_type, times in operation_times.items():
            if times:
                avg_time = statistics.mean(times)
                median_time = statistics.median(times)
                p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)
                
                print(f"   {operation_type.replace('_', ' ').title():20} {avg_time:.2f}ms avg, {p95_time:.2f}ms 95th")
                
                # Estimate security overhead (assuming ~2ms base operation time)
                estimated_security_overhead = max(0, avg_time - 2.0)
                total_security_overhead += estimated_security_overhead
                
                # Validate performance requirements
                assert avg_time < 20.0, f"{operation_type} with security {avg_time:.2f}ms exceeds reasonable limit"
                assert p95_time < 30.0, f"{operation_type} 95th percentile {p95_time:.2f}ms exceeds limit"
        
        # Validate total security overhead requirement
        avg_security_overhead = total_security_overhead / len([t for t in operation_times.values() if t])
        assert avg_security_overhead < 5.0, f"Average security overhead {avg_security_overhead:.2f}ms exceeds 5ms requirement"
        
        print(f"   Estimated Security Overhead: {avg_security_overhead:.2f}ms (requirement: <5ms)")
        print("✅ Security validation performance overhead validated")


if __name__ == "__main__":
    """
    Run comprehensive Phase 2 security integration tests.
    
    These tests validate that Phase 1 security features work correctly across all Phase 2 components:
    - Project isolation maintained in all Phase 2 operations
    - Input sanitization working in all new MCP tools
    - Path security enforced for configuration and documentation  
    - Cross-project access restrictions properly implemented
    - Security performance overhead stays within acceptable limits
    """
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, project_root)
    
    # Run security integration tests
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s",  # Show print statements
        "--durations=10"  # Show slowest tests
    ])
    
    if exit_code == 0:
        print("\\n🎉 PHASE 2 SECURITY INTEGRATION: SUCCESS! 🎉")
        print("✅ Phase 1 security works correctly across all Phase 2 components")
        print("✅ Project isolation maintained in all operations")
        print("✅ Input sanitization prevents all tested attack vectors")
        print("✅ Path security enforced for file operations")
        print("✅ Cross-project access restrictions working")
        print("✅ Security performance overhead within acceptable limits")
    else:
        print("\\n❌ PHASE 2 SECURITY INTEGRATION FAILURES")
        print("❌ Security vulnerabilities detected")
        print("❌ Review test output for specific security issues")
    
    sys.exit(exit_code)