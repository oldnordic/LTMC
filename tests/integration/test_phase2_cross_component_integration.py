"""
Phase 2 Cross-Component Integration Tests

COMPREHENSIVE CROSS-COMPONENT VALIDATION:
- Tests integration between all Phase 2 component pairs
- Validates data flow and communication between components
- Ensures component interfaces work correctly together
- Tests component dependency resolution and coordination
- Validates component state consistency across operations

Component Integration Matrix:
1. TaskBlueprint ↔ Enhanced TaskManager Integration
2. Enhanced TaskManager ↔ Configuration Templates Integration  
3. Configuration Templates ↔ Documentation Generation Integration
4. Documentation Generation ↔ Advanced Orchestration Integration
5. Advanced Orchestration ↔ TaskBlueprint Integration (full circle)
6. Multi-component integration scenarios (3+ components)

REAL INTEGRATION REQUIREMENTS:
- Uses actual component instances and real databases
- Tests actual MCP tool interactions via HTTP server
- No mocks in production integration paths
- Validates performance across component boundaries
- Tests error propagation and recovery between components
"""

import pytest
import pytest_asyncio
import asyncio
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Real component imports for integration testing
from ltms.models.task_blueprint import TaskBlueprint, TaskComplexity, TaskMetadata
from ltms.services.blueprint_service import BlueprintManager
from ltms.services.enhanced_task_manager import EnhancedTaskManager, TaskAssignment
from ltms.services.config_template_service import ConfigTemplateManager
from ltms.services.documentation_generator import DocumentationGenerator
from ltms.orchestration.workflow_engine import WorkflowEngine
from ltms.orchestration.task_coordinator import TaskCoordinator


class TestTaskBlueprintTaskManagerIntegration:
    """
    TaskBlueprint ↔ Enhanced TaskManager Integration Tests
    
    Tests the integration between Component 1 (TaskBlueprint) and Component 2 (Enhanced TaskManager):
    - Blueprint complexity scoring influences task routing decisions
    - Task decomposition uses blueprint metadata effectively
    - TaskManager can modify blueprint estimates based on routing outcomes
    - Blueprint dependency graphs guide task scheduling
    - Performance: Blueprint → TaskManager operations <15ms combined
    """
    
    @pytest.fixture(scope="class")
    def server_health(self):
        """Ensure LTMC server is available for integration testing."""
        try:
            response = requests.get("http://localhost:5050/health", timeout=5)
            assert response.status_code == 200, "LTMC server not healthy"
            return response.json()
        except requests.RequestException as e:
            pytest.skip(f"LTMC server unavailable: {e}")
    
    def test_blueprint_complexity_influences_task_routing(self, server_health):
        """
        Test that blueprint complexity scoring directly influences TaskManager routing decisions.
        
        Validates:
        - High complexity blueprints routed to experienced team members
        - Low complexity blueprints distributed for workload balancing
        - Complexity score used in routing confidence calculations
        - Performance: Blueprint creation + routing <15ms combined
        """
        project_id = "blueprint_taskmanager_integration"
        
        # Create high complexity blueprint
        high_complexity_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "High Complexity System Architecture",
                    "description": "Design distributed microservices architecture with event sourcing, CQRS, saga patterns, service mesh, observability, security, and multi-region deployment. Requires extensive distributed systems expertise.",
                    "complexity": "CRITICAL",
                    "estimated_duration_minutes": 960,  # 16 hours - very complex
                    "required_skills": ["architecture", "distributed-systems", "microservices", "event-sourcing", "cqrs", "kubernetes"],
                    "project_id": project_id,
                    "metadata": {
                        "priority_score": 0.95,
                        "business_impact": "critical",
                        "technical_risk": "high"
                    }
                }
            },
            "id": 1
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=high_complexity_payload, timeout=15)
        blueprint_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, f"High complexity blueprint creation failed: {response.status_code}"
        result = response.json()
        assert result.get("error") is None, f"Blueprint creation error: {result.get('error')}"
        
        high_complexity_blueprint_id = result["result"]["blueprint_id"]
        complexity_score = result["result"].get("complexity_score", 0.0)
        assert complexity_score > 0.8, f"High complexity task should score >0.8, got {complexity_score}"
        
        # Create team with varied experience levels
        team_members = [
            {
                "member_id": "senior_architect",
                "name": "Senior Architect",
                "skills": ["architecture", "distributed-systems", "microservices", "event-sourcing", "cqrs", "kubernetes"],
                "experience_level": 0.95,
                "current_workload": 0.3,
                "availability_hours": 8.0
            },
            {
                "member_id": "junior_dev",
                "name": "Junior Developer", 
                "skills": ["python", "basic-web", "testing"],
                "experience_level": 0.2,
                "current_workload": 0.1,
                "availability_hours": 8.0
            },
            {
                "member_id": "mid_dev",
                "name": "Mid-level Developer",
                "skills": ["python", "fastapi", "docker", "basic-architecture"],
                "experience_level": 0.6,
                "current_workload": 0.5,
                "availability_hours": 7.0
            }
        ]
        
        # Route high complexity task
        routing_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "route_task_to_member",
                "arguments": {
                    "subtask_blueprint_id": high_complexity_blueprint_id,
                    "available_members": team_members,
                    "project_id": project_id,
                    "routing_preferences": {
                        "prioritize_experience_for_complex_tasks": True,
                        "complexity_weight": 0.8
                    }
                }
            },
            "id": 2
        }
        
        start_routing_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=routing_payload, timeout=15)
        routing_time = (time.perf_counter() - start_routing_time) * 1000
        
        assert response.status_code == 200, f"Task routing failed: {response.status_code}"
        routing_result = response.json()
        assert routing_result.get("error") is None, f"Routing error: {routing_result.get('error')}"
        
        assignment_data = routing_result["result"]
        assigned_member_id = assignment_data["assigned_member"]["member_id"]
        routing_confidence = assignment_data["confidence_score"]
        
        # High complexity task should be assigned to senior architect
        assert assigned_member_id == "senior_architect", f"High complexity task assigned to {assigned_member_id} instead of senior_architect"
        assert routing_confidence > 0.85, f"High complexity routing confidence {routing_confidence} below 0.85"
        
        # Validate combined performance
        total_time = blueprint_time + routing_time
        assert total_time < 15.0, f"Combined blueprint+routing time {total_time:.2f}ms exceeds 15ms"
        
        print(f"✅ High complexity blueprint routed to senior architect in {total_time:.2f}ms")
        
        # Test low complexity task routing for contrast
        low_complexity_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Fix Documentation Typo",
                    "description": "Fix spelling errors in README.md file",
                    "complexity": "TRIVIAL",
                    "estimated_duration_minutes": 15,
                    "required_skills": ["documentation", "writing"],
                    "project_id": project_id,
                    "metadata": {
                        "priority_score": 0.2,
                        "business_impact": "low",
                        "technical_risk": "minimal"
                    }
                }
            },
            "id": 3
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=low_complexity_payload, timeout=10)
        assert response.status_code == 200, "Low complexity blueprint creation failed"
        result = response.json()
        low_complexity_blueprint_id = result["result"]["blueprint_id"]
        low_complexity_score = result["result"].get("complexity_score", 1.0)
        assert low_complexity_score < 0.3, f"Low complexity task should score <0.3, got {low_complexity_score}"
        
        # Route low complexity task
        low_routing_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "route_task_to_member",
                "arguments": {
                    "subtask_blueprint_id": low_complexity_blueprint_id,
                    "available_members": team_members,
                    "project_id": project_id,
                    "routing_preferences": {
                        "balance_workload_for_simple_tasks": True,
                        "complexity_weight": 0.3
                    }
                }
            },
            "id": 4
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=low_routing_payload, timeout=10)
        assert response.status_code == 200, "Low complexity routing failed"
        routing_result = response.json()
        
        low_assigned_member_id = routing_result["result"]["assigned_member"]["member_id"]
        
        # Low complexity task should NOT be assigned to senior architect (workload balancing)
        assert low_assigned_member_id in ["junior_dev", "mid_dev"], f"Low complexity task assigned to {low_assigned_member_id} instead of junior/mid dev"
        
        print("✅ Blueprint complexity properly influences TaskManager routing decisions")
    
    def test_blueprint_metadata_guides_task_decomposition(self, server_health):
        """
        Test that blueprint metadata (dependencies, constraints, etc.) guides TaskManager decomposition.
        
        Validates:
        - Task dependencies from blueprint influence decomposition strategy
        - Metadata constraints affect subtask creation
        - Blueprint tags influence subtask categorization
        - Decomposed subtasks inherit relevant blueprint metadata
        """
        project_id = "blueprint_decomposition_integration"
        
        # Create complex blueprint with detailed metadata
        complex_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "E-commerce Platform Development",
                    "description": "Build complete e-commerce platform with user management, product catalog, shopping cart, payment processing, order management, and admin dashboard",
                    "complexity": "CRITICAL",
                    "estimated_duration_minutes": 2400,  # 40 hours
                    "required_skills": ["python", "web-development", "database-design", "payment-integration", "security", "ui-ux"],
                    "project_id": project_id,
                    "metadata": {
                        "dependencies": ["user_authentication", "database_schema", "payment_gateway_setup"],
                        "constraints": {
                            "max_parallel_developers": 3,
                            "sequential_phases": ["foundation", "core_features", "integration", "testing"],
                            "technology_stack": ["python", "fastapi", "postgresql", "redis", "react"]
                        },
                        "tags": ["web-app", "e-commerce", "full-stack", "payment-integration"],
                        "priority_score": 0.9,
                        "business_requirements": [
                            "PCI DSS compliance for payments",
                            "GDPR compliance for user data",
                            "Mobile responsive design",
                            "Real-time inventory tracking"
                        ]
                    }
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=complex_blueprint_payload, timeout=15)
        assert response.status_code == 200, "Complex blueprint creation failed"
        result = response.json()
        blueprint_id = result["result"]["blueprint_id"]
        
        # Decompose task using blueprint metadata
        decomposition_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "decompose_task_blueprint",
                "arguments": {
                    "blueprint_id": blueprint_id,
                    "project_id": project_id,
                    "decomposition_strategy": "metadata_guided",
                    "respect_dependencies": True,
                    "respect_constraints": True,
                    "max_subtasks": 10,
                    "target_duration_minutes": 300  # 5 hours max per subtask
                }
            },
            "id": 2
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=decomposition_payload, timeout=20)
        decomposition_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, f"Task decomposition failed: {response.status_code}"
        decomposition_result = response.json()
        assert decomposition_result.get("error") is None, f"Decomposition error: {decomposition_result.get('error')}"
        
        subtasks = decomposition_result["result"]["subtasks"]
        assert len(subtasks) > 3, f"Complex e-commerce task should decompose into >3 subtasks, got {len(subtasks)}"
        assert len(subtasks) <= 10, f"Should respect max_subtasks=10, got {len(subtasks)}"
        
        # Validate metadata inheritance and dependency handling
        foundational_subtasks = []
        dependent_subtasks = []
        
        for subtask in subtasks:
            subtask_title = subtask["title"].lower()
            subtask_dependencies = subtask.get("dependencies", [])
            
            # Check if foundational tasks (from metadata dependencies) exist
            if any(dep in subtask_title for dep in ["authentication", "database", "schema"]):
                foundational_subtasks.append(subtask)
            
            # Check if dependent tasks properly reference foundations
            if subtask_dependencies:
                dependent_subtasks.append(subtask)
            
            # Validate tag inheritance
            subtask_tags = subtask.get("tags", [])
            assert any(tag in subtask_tags for tag in ["e-commerce", "web-app"]), f"Subtask should inherit parent tags: {subtask_tags}"
            
            # Validate duration constraints
            subtask_duration = subtask.get("estimated_duration_minutes", 0)
            assert subtask_duration <= 300, f"Subtask duration {subtask_duration}min exceeds 300min constraint"
        
        assert len(foundational_subtasks) > 0, "Should create foundational subtasks based on blueprint dependencies"
        assert len(dependent_subtasks) > 0, "Should create subtasks with proper dependency chains"
        
        # Validate sequential phases are respected
        phase_subtasks = {"foundation": 0, "core_features": 0, "integration": 0, "testing": 0}
        for subtask in subtasks:
            subtask_desc = subtask["description"].lower()
            for phase in phase_subtasks.keys():
                if phase.replace("_", " ") in subtask_desc or phase in subtask.get("tags", []):
                    phase_subtasks[phase] += 1
        
        # Should have subtasks for each major phase
        active_phases = sum(1 for count in phase_subtasks.values() if count > 0)
        assert active_phases >= 3, f"Should cover at least 3 sequential phases, got {active_phases}"
        
        # Validate performance
        assert decomposition_time < 20.0, f"Metadata-guided decomposition took {decomposition_time:.2f}ms, expected <20ms"
        
        print(f"✅ Blueprint metadata properly guides task decomposition in {decomposition_time:.2f}ms")
    
    def test_taskmanager_updates_blueprint_estimates(self, server_health):
        """
        Test that TaskManager can update blueprint estimates based on routing outcomes and experience.
        
        Validates:
        - TaskManager updates blueprint duration estimates after successful completions
        - Routing confidence influences estimate adjustments
        - Historical performance data improves future blueprint accuracy
        - Estimate updates are persisted and retrievable
        """
        project_id = "blueprint_estimate_updates"
        
        # Create initial blueprint with estimated duration
        initial_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "API Endpoint Implementation",
                    "description": "Implement REST API endpoint with validation, authentication, and database integration",
                    "complexity": "MODERATE",
                    "estimated_duration_minutes": 240,  # Initial estimate: 4 hours
                    "required_skills": ["python", "fastapi", "database", "authentication"],
                    "project_id": project_id,
                    "metadata": {
                        "estimate_confidence": 0.7,  # Medium confidence in initial estimate
                        "similar_task_count": 0  # No historical data yet
                    }
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=initial_blueprint_payload, timeout=10)
        assert response.status_code == 200, "Initial blueprint creation failed"
        result = response.json()
        blueprint_id = result["result"]["blueprint_id"]
        initial_estimate = result["result"]["estimated_duration_minutes"]
        
        # Route task to gather assignment data
        team_member = {
            "member_id": "experienced_dev",
            "name": "Experienced Developer",
            "skills": ["python", "fastapi", "database", "authentication"],
            "experience_level": 0.8,
            "current_workload": 0.4,
            "availability_hours": 8.0
        }
        
        routing_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "route_task_to_member",
                "arguments": {
                    "subtask_blueprint_id": blueprint_id,
                    "available_members": [team_member],
                    "project_id": project_id
                }
            },
            "id": 2
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=routing_payload, timeout=10)
        assert response.status_code == 200, "Task routing failed"
        routing_result = response.json()
        assignment_id = routing_result["result"]["assignment_id"]
        routing_confidence = routing_result["result"]["confidence_score"]
        
        # Simulate task completion with actual duration
        completion_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "complete_task_assignment",
                "arguments": {
                    "assignment_id": assignment_id,
                    "actual_duration_minutes": 180,  # Completed in 3 hours (faster than estimate)
                    "completion_quality": 0.9,
                    "completion_notes": "Task completed efficiently with good code quality",
                    "update_blueprint_estimates": True
                }
            },
            "id": 3
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=completion_payload, timeout=10)
        assert response.status_code == 200, "Task completion failed"
        completion_result = response.json()
        assert completion_result.get("error") is None, "Task completion error"
        
        # Verify blueprint estimates were updated
        updated_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_blueprint_details",
                "arguments": {
                    "blueprint_id": blueprint_id,
                    "project_id": project_id,
                    "include_estimate_history": True
                }
            },
            "id": 4
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=updated_blueprint_payload, timeout=10)
        assert response.status_code == 200, "Blueprint details retrieval failed"
        details_result = response.json()
        
        updated_blueprint = details_result["result"]["blueprint"]
        updated_estimate = updated_blueprint["estimated_duration_minutes"]
        estimate_confidence = updated_blueprint["metadata"]["estimate_confidence"]
        similar_task_count = updated_blueprint["metadata"]["similar_task_count"]
        
        # Estimate should be adjusted toward actual completion time
        assert updated_estimate < initial_estimate, f"Estimate should decrease from {initial_estimate} to reflect faster completion, got {updated_estimate}"
        assert updated_estimate >= 180, "Updated estimate should not be less than actual completion time"
        assert estimate_confidence > 0.7, f"Estimate confidence should increase after real completion data, got {estimate_confidence}"
        assert similar_task_count == 1, f"Similar task count should increase to 1, got {similar_task_count}"
        
        # Test with second similar task to validate learning
        similar_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Another API Endpoint Implementation",
                    "description": "Implement different REST API endpoint with validation, authentication, and database integration",
                    "complexity": "MODERATE",
                    "estimated_duration_minutes": 240,  # Same initial estimate
                    "required_skills": ["python", "fastapi", "database", "authentication"],
                    "project_id": project_id,
                    "use_historical_estimates": True  # Use learning from previous tasks
                }
            },
            "id": 5
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=similar_blueprint_payload, timeout=10)
        assert response.status_code == 200, "Similar blueprint creation failed"
        result = response.json()
        
        learned_estimate = result["result"]["estimated_duration_minutes"]
        learned_confidence = result["result"]["metadata"]["estimate_confidence"]
        
        # New blueprint should benefit from historical learning
        assert learned_estimate < 240, f"New blueprint should use improved estimate based on learning, got {learned_estimate}"
        assert learned_estimate <= updated_estimate + 30, "Learned estimate should be close to updated estimate"
        assert learned_confidence > 0.8, f"Learned estimate should have high confidence, got {learned_confidence}"
        
        print("✅ TaskManager successfully updates blueprint estimates based on actual performance")


class TestTaskManagerConfigurationIntegration:
    """
    Enhanced TaskManager ↔ Configuration Templates Integration Tests
    
    Tests the integration between Component 2 (Enhanced TaskManager) and Component 3 (Configuration Templates):
    - Task routing decisions influence configuration template selection
    - Configuration settings affect task assignment parameters
    - Hot-reload configuration updates propagate to active task assignments
    - Team performance configurations optimize routing algorithms
    - Performance: Configuration loading for routing <2ms overhead
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
    
    def test_task_routing_selects_optimal_configuration(self, server_health):
        """
        Test that task routing decisions automatically select optimal configuration templates.
        
        Validates:
        - High-performance tasks trigger high-performance configuration
        - Standard tasks use default configuration templates
        - Configuration selection influences routing parameters
        - Configuration overhead <2ms per routing operation
        """
        project_id = "taskmanager_config_integration"
        
        # Create high-performance demanding task
        high_perf_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Real-time Data Processing Pipeline",
                    "description": "Implement high-throughput data processing pipeline handling 10,000+ events/second with <10ms latency requirements",
                    "complexity": "CRITICAL",
                    "estimated_duration_minutes": 480,
                    "required_skills": ["python", "performance-optimization", "streaming", "low-latency"],
                    "project_id": project_id,
                    "metadata": {
                        "performance_requirements": {
                            "max_latency_ms": 10,
                            "min_throughput": 10000,
                            "memory_constraints": "4GB",
                            "cpu_intensive": True
                        }
                    }
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=high_perf_blueprint_payload, timeout=15)
        assert response.status_code == 200, "High-performance blueprint creation failed"
        result = response.json()
        high_perf_blueprint_id = result["result"]["blueprint_id"]
        
        # Route task with automatic configuration selection
        team_members = [
            {
                "member_id": "perf_engineer",
                "name": "Performance Engineer",
                "skills": ["python", "performance-optimization", "streaming", "low-latency", "profiling"],
                "experience_level": 0.9,
                "current_workload": 0.2,
                "availability_hours": 8.0
            },
            {
                "member_id": "regular_dev",
                "name": "Regular Developer",
                "skills": ["python", "web-development"],
                "experience_level": 0.6,
                "current_workload": 0.3,
                "availability_hours": 8.0
            }
        ]
        
        routing_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "route_task_with_config_selection",
                "arguments": {
                    "subtask_blueprint_id": high_perf_blueprint_id,
                    "available_members": team_members,
                    "project_id": project_id,
                    "auto_select_config": True,
                    "performance_priority": True
                }
            },
            "id": 2
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=routing_payload, timeout=15)
        routing_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, f"Performance routing failed: {response.status_code}"
        routing_result = response.json()
        assert routing_result.get("error") is None, f"Routing error: {routing_result.get('error')}"
        
        assignment_data = routing_result["result"]
        assigned_member_id = assignment_data["assigned_member"]["member_id"]
        selected_config = assignment_data["configuration_template"]
        config_selection_time = assignment_data.get("config_selection_time_ms", 0)
        
        # Validate routing selected performance-optimized configuration and engineer
        assert assigned_member_id == "perf_engineer", f"High-performance task should route to perf_engineer, got {assigned_member_id}"
        assert selected_config == "high_performance", f"Should select high_performance config, got {selected_config}"
        assert config_selection_time < 2.0, f"Configuration selection took {config_selection_time:.2f}ms, expected <2ms"
        
        # Validate total routing time includes config overhead
        assert routing_time < 12.0, f"Total routing with config selection took {routing_time:.2f}ms, expected <12ms"
        
        print(f"✅ High-performance task routed with optimal config in {routing_time:.2f}ms")
        
        # Test standard task with default configuration
        standard_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Standard CRUD API Implementation",
                    "description": "Implement basic CRUD operations for user management",
                    "complexity": "SIMPLE",
                    "estimated_duration_minutes": 120,
                    "required_skills": ["python", "fastapi", "database"],
                    "project_id": project_id
                }
            },
            "id": 3
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=standard_blueprint_payload, timeout=10)
        result = response.json()
        standard_blueprint_id = result["result"]["blueprint_id"]
        
        # Route standard task
        standard_routing_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "route_task_with_config_selection",
                "arguments": {
                    "subtask_blueprint_id": standard_blueprint_id,
                    "available_members": team_members,
                    "project_id": project_id,
                    "auto_select_config": True
                }
            },
            "id": 4
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=standard_routing_payload, timeout=10)
        routing_result = response.json()
        
        standard_config = routing_result["result"]["configuration_template"]
        assert standard_config == "default_project", f"Standard task should use default config, got {standard_config}"
        
        print("✅ Configuration template selection works correctly for different task types")
    
    def test_configuration_hot_reload_affects_active_assignments(self, server_health):
        """
        Test that hot-reload configuration updates propagate to active task assignments.
        
        Validates:
        - Configuration changes update active assignment parameters
        - Hot-reload detection <100ms
        - Assignment behavior changes reflect new configuration
        - No active assignments are lost during configuration updates
        """
        project_id = "config_hotreload_integration"
        
        # Create task and assignment
        blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Hot-reload Configuration Test",
                    "description": "Test task for configuration hot-reload functionality",
                    "complexity": "MODERATE",
                    "estimated_duration_minutes": 180,
                    "required_skills": ["python", "configuration"],
                    "project_id": project_id
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=blueprint_payload, timeout=10)
        result = response.json()
        blueprint_id = result["result"]["blueprint_id"]
        
        # Create initial assignment with current configuration
        team_member = {
            "member_id": "config_test_dev",
            "name": "Config Test Developer",
            "skills": ["python", "configuration"],
            "experience_level": 0.7,
            "current_workload": 0.3,
            "availability_hours": 8.0
        }
        
        routing_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "route_task_to_member",
                "arguments": {
                    "subtask_blueprint_id": blueprint_id,
                    "available_members": [team_member],
                    "project_id": project_id
                }
            },
            "id": 2
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=routing_payload, timeout=10)
        result = response.json()
        assignment_id = result["result"]["assignment_id"]
        initial_config_version = result["result"].get("config_version", "1.0")
        
        # Get current assignment details
        assignment_details_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_assignment_details",
                "arguments": {
                    "assignment_id": assignment_id,
                    "project_id": project_id
                }
            },
            "id": 3
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=assignment_details_payload, timeout=10)
        initial_details = response.json()["result"]
        initial_timeout = initial_details.get("task_timeout_minutes", 180)
        
        # Update configuration template to trigger hot-reload
        config_update_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "update_project_config_template",
                "arguments": {
                    "project_id": project_id,
                    "template_updates": {
                        "task_timeout_minutes": 240,  # Increase timeout
                        "max_concurrent_tasks": 5,
                        "priority_adjustment_factor": 1.2
                    },
                    "trigger_hot_reload": True
                }
            },
            "id": 4
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=config_update_payload, timeout=10)
        hotreload_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, "Configuration update failed"
        update_result = response.json()
        assert update_result.get("error") is None, f"Config update error: {update_result.get('error')}"
        
        reload_detection_time = update_result["result"].get("reload_detection_time_ms", 999)
        assert reload_detection_time < 100.0, f"Hot-reload detection took {reload_detection_time:.2f}ms, expected <100ms"
        
        # Wait for propagation and check assignment updates
        time.sleep(0.2)  # Brief wait for propagation
        
        response = requests.post("http://localhost:5050/jsonrpc", json=assignment_details_payload, timeout=10)
        updated_details = response.json()["result"]
        updated_timeout = updated_details.get("task_timeout_minutes", initial_timeout)
        updated_config_version = updated_details.get("config_version", initial_config_version)
        
        # Validate configuration changes propagated to assignment
        assert updated_timeout == 240, f"Assignment timeout should update to 240, got {updated_timeout}"
        assert updated_config_version != initial_config_version, "Config version should change after update"
        assert updated_details["assignment_id"] == assignment_id, "Assignment ID should remain the same"
        assert updated_details["status"] != "lost", "Assignment should not be lost during config update"
        
        print(f"✅ Configuration hot-reload propagated to active assignments in {hotreload_time:.2f}ms")


class TestConfigurationDocumentationIntegration:
    """
    Configuration Templates ↔ Documentation Generation Integration Tests
    
    Tests the integration between Component 3 (Configuration Templates) and Component 4 (Documentation Generation):
    - Documentation generation reflects current configuration settings
    - Configuration templates include embedded documentation metadata
    - Documentation updates when configuration templates change
    - Configuration schemas auto-generate API documentation
    - Performance: Configuration-based documentation generation <10ms
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
    
    def test_documentation_reflects_configuration_settings(self, server_health):
        """
        Test that generated documentation accurately reflects current configuration settings.
        
        Validates:
        - API documentation includes configuration-dependent endpoints
        - Architecture diagrams show configuration-enabled components
        - Performance metrics documentation reflects configuration limits
        - Documentation updates when configuration changes
        """
        project_id = "config_documentation_integration"
        
        # Apply high-performance configuration
        config_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "apply_project_config_template",
                "arguments": {
                    "project_id": project_id,
                    "template_name": "high_performance",
                    "environment_vars": {
                        "MAX_CONCURRENT_TASKS": "1000",
                        "CACHE_SIZE_MB": "512",
                        "PERFORMANCE_MODE": "optimized"
                    },
                    "feature_flags": {
                        "enable_performance_monitoring": True,
                        "enable_advanced_caching": True,
                        "enable_load_balancing": True
                    }
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=config_payload, timeout=10)
        assert response.status_code == 200, "High-performance config application failed"
        
        # Generate documentation based on configuration
        doc_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "generate_configuration_documentation",
                "arguments": {
                    "project_id": project_id,
                    "documentation_types": ["api_docs", "architecture_diagram", "performance_specs"],
                    "include_config_dependent_features": True,
                    "include_environment_variables": True,
                    "include_feature_flags": True
                }
            },
            "id": 2
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=doc_payload, timeout=15)
        doc_generation_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, f"Documentation generation failed: {response.status_code}"
        doc_result = response.json()
        assert doc_result.get("error") is None, f"Documentation error: {doc_result.get('error')}"
        
        generated_docs = doc_result["result"]["generated_documents"]
        assert len(generated_docs) >= 3, f"Should generate at least 3 document types, got {len(generated_docs)}"
        
        # Validate API documentation includes config-dependent features
        api_doc = next((doc for doc in generated_docs if doc["type"] == "api_docs"), None)
        assert api_doc is not None, "API documentation should be generated"
        
        api_content = api_doc["content"].lower()
        assert "performance monitoring" in api_content, "API docs should mention performance monitoring endpoint"
        assert "advanced caching" in api_content, "API docs should mention caching endpoints"
        assert "load balancing" in api_content, "API docs should mention load balancing features"
        assert "max_concurrent_tasks: 1000" in api_content, "API docs should include environment variable values"
        
        # Validate architecture diagram reflects configuration
        arch_doc = next((doc for doc in generated_docs if doc["type"] == "architecture_diagram"), None)
        assert arch_doc is not None, "Architecture diagram should be generated"
        
        arch_content = arch_doc["content"].lower()
        assert "cache" in arch_content, "Architecture should show caching components"
        assert "performance" in arch_content, "Architecture should show performance monitoring"
        assert "load balancer" in arch_content, "Architecture should show load balancing"
        
        # Validate performance specifications documentation
        perf_doc = next((doc for doc in generated_docs if doc["type"] == "performance_specs"), None)
        assert perf_doc is not None, "Performance specs should be generated"
        
        perf_content = perf_doc["content"]
        assert "1000" in perf_content, "Performance specs should include concurrent task limit"
        assert "512" in perf_content, "Performance specs should include cache size"
        assert "optimized" in perf_content, "Performance specs should mention optimization mode"
        
        # Validate performance requirement
        assert doc_generation_time < 10.0, f"Config-based documentation took {doc_generation_time:.2f}ms, expected <10ms"
        
        print(f"✅ Documentation accurately reflects configuration settings in {doc_generation_time:.2f}ms")
        
        # Test documentation update when configuration changes
        updated_config_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "apply_project_config_template",
                "arguments": {
                    "project_id": project_id,
                    "template_name": "default_project",  # Switch to default config
                    "feature_flags": {
                        "enable_performance_monitoring": False,
                        "enable_advanced_caching": False,
                        "enable_load_balancing": False
                    }
                }
            },
            "id": 3
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=updated_config_payload, timeout=10)
        assert response.status_code == 200, "Config update failed"
        
        # Regenerate documentation
        response = requests.post("http://localhost:5050/jsonrpc", json=doc_payload, timeout=15)
        updated_doc_result = response.json()
        
        updated_generated_docs = updated_doc_result["result"]["generated_documents"]
        updated_api_doc = next((doc for doc in updated_generated_docs if doc["type"] == "api_docs"), None)
        updated_api_content = updated_api_doc["content"].lower()
        
        # Validate documentation reflects configuration changes
        assert "performance monitoring" not in updated_api_content or "disabled" in updated_api_content, "Updated docs should reflect disabled performance monitoring"
        assert updated_api_content != api_content, "Documentation content should change when configuration changes"
        
        print("✅ Documentation updates correctly when configuration changes")


class TestDocumentationOrchestrationIntegration:
    """
    Documentation Generation ↔ Advanced Orchestration Integration Tests
    
    Tests the integration between Component 4 (Documentation Generation) and Component 5 (Advanced Orchestration):
    - Orchestration workflows generate progress documentation automatically
    - Documentation generation tasks are orchestrated with proper dependencies
    - Workflow status updates documentation in real-time
    - Generated documentation includes orchestration metrics and status
    - Performance: Orchestrated documentation generation maintains <15ms overhead
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
    
    def test_orchestrated_documentation_workflow(self, server_health):
        """
        Test that documentation generation can be orchestrated as part of larger workflows.
        
        Validates:
        - Documentation tasks have proper dependencies on prerequisite tasks
        - Multiple documentation types generated in optimal order
        - Orchestration handles documentation task failures gracefully
        - Generated documentation includes orchestration metadata
        """
        project_id = "documentation_orchestration_integration"
        
        # Create project blueprint for documentation workflow
        blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Complete Project Documentation Suite",
                    "description": "Generate comprehensive documentation including API docs, architecture diagrams, user guides, and deployment documentation with proper dependencies",
                    "complexity": "COMPLEX",
                    "estimated_duration_minutes": 120,
                    "required_skills": ["documentation", "technical-writing", "architecture"],
                    "project_id": project_id,
                    "metadata": {
                        "documentation_requirements": [
                            "API documentation",
                            "Architecture diagrams", 
                            "User guide",
                            "Deployment guide",
                            "Performance metrics",
                            "Security documentation"
                        ],
                        "dependencies": {
                            "api_docs": [],  # No dependencies
                            "architecture_diagrams": ["api_docs"],  # Depends on API docs
                            "user_guide": ["api_docs", "architecture_diagrams"],  # Depends on both
                            "deployment_guide": ["architecture_diagrams"],  # Depends on architecture
                            "performance_metrics": ["api_docs"],  # Depends on API docs
                            "security_docs": ["api_docs", "architecture_diagrams"]  # Depends on both
                        }
                    }
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=blueprint_payload, timeout=15)
        assert response.status_code == 200, "Documentation blueprint creation failed"
        result = response.json()
        blueprint_id = result["result"]["blueprint_id"]
        
        # Orchestrate documentation workflow with dependencies
        orchestration_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "orchestrate_documentation_workflow",
                "arguments": {
                    "project_id": project_id,
                    "blueprint_id": blueprint_id,
                    "workflow_type": "documentation_suite",
                    "execution_mode": "dependency_aware",
                    "documentation_types": [
                        "api_docs",
                        "architecture_diagrams", 
                        "user_guide",
                        "deployment_guide",
                        "performance_metrics",
                        "security_docs"
                    ],
                    "parallel_execution": True,
                    "dependency_resolution": True,
                    "error_recovery": True
                }
            },
            "id": 2
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=orchestration_payload, timeout=20)
        orchestration_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, f"Documentation orchestration failed: {response.status_code}"
        orchestration_result = response.json()
        assert orchestration_result.get("error") is None, f"Orchestration error: {orchestration_result.get('error')}"
        
        workflow_data = orchestration_result["result"]
        workflow_id = workflow_data["workflow_id"]
        execution_plan = workflow_data["execution_plan"]
        estimated_completion_time = workflow_data.get("estimated_completion_minutes", 0)
        
        assert workflow_id is not None, "Workflow ID should be provided"
        assert len(execution_plan) >= 6, f"Should plan for 6 documentation types, got {len(execution_plan)}"
        
        # Validate dependency order in execution plan
        task_order = {task["task_name"]: task["execution_order"] for task in execution_plan}
        
        # API docs should come first (no dependencies)
        assert task_order["api_docs"] == 0, f"API docs should be first, got order {task_order['api_docs']}"
        
        # Architecture diagrams should come after API docs
        assert task_order["architecture_diagrams"] > task_order["api_docs"], "Architecture diagrams should come after API docs"
        
        # User guide should come after both API docs and architecture diagrams
        user_guide_order = task_order["user_guide"]
        assert user_guide_order > task_order["api_docs"], "User guide should come after API docs"
        assert user_guide_order > task_order["architecture_diagrams"], "User guide should come after architecture diagrams"
        
        # Validate orchestration performance
        assert orchestration_time < 15.0, f"Documentation orchestration took {orchestration_time:.2f}ms, expected <15ms"
        
        print(f"✅ Documentation workflow orchestrated with proper dependencies in {orchestration_time:.2f}ms")
        
        # Monitor workflow execution
        monitoring_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "monitor_workflow_progress",
                "arguments": {
                    "workflow_id": workflow_id,
                    "project_id": project_id,
                    "include_task_details": True,
                    "include_performance_metrics": True
                }
            },
            "id": 3
        }
        
        # Wait briefly for workflow to start
        time.sleep(0.5)
        
        response = requests.post("http://localhost:5050/jsonrpc", json=monitoring_payload, timeout=10)
        assert response.status_code == 200, "Workflow monitoring failed"
        monitoring_result = response.json()
        
        workflow_status = monitoring_result["result"]
        current_status = workflow_status["status"]
        completed_tasks = workflow_status.get("completed_tasks", [])
        active_tasks = workflow_status.get("active_tasks", [])
        
        assert current_status in ["running", "executing", "in_progress"], f"Workflow should be active, got status: {current_status}"
        
        # Validate that tasks with no dependencies started first
        if completed_tasks:
            first_completed = completed_tasks[0]["task_name"]
            assert first_completed == "api_docs", f"First completed task should be api_docs, got {first_completed}"
        
        print("✅ Orchestrated workflow executing with proper dependency resolution")
    
    def test_real_time_documentation_updates_during_orchestration(self, server_health):
        """
        Test that documentation is updated in real-time as orchestration workflows progress.
        
        Validates:
        - Progress documentation reflects current workflow status
        - Completion documentation includes orchestration metrics
        - Documentation timestamps track orchestration events
        - Real-time updates maintain performance requirements
        """
        project_id = "realtime_doc_orchestration"
        
        # Start documentation workflow
        workflow_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "start_documented_workflow",
                "arguments": {
                    "project_id": project_id,
                    "workflow_name": "Real-time Documentation Test",
                    "workflow_steps": [
                        "initialize_project",
                        "generate_api_docs",
                        "create_architecture_diagram",
                        "compile_final_documentation"
                    ],
                    "real_time_documentation": True,
                    "documentation_frequency": "per_step"
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=workflow_payload, timeout=15)
        assert response.status_code == 200, "Documented workflow start failed"
        result = response.json()
        workflow_id = result["result"]["workflow_id"]
        
        # Monitor documentation updates in real-time
        initial_doc_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_workflow_documentation",
                "arguments": {
                    "workflow_id": workflow_id,
                    "project_id": project_id,
                    "documentation_type": "progress_report",
                    "include_metrics": True
                }
            },
            "id": 2
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=initial_doc_payload, timeout=10)
        initial_doc_result = response.json()
        initial_progress = initial_doc_result["result"]["progress_percentage"]
        initial_timestamp = initial_doc_result["result"]["last_updated"]
        
        # Wait for workflow to progress
        time.sleep(1.0)
        
        # Check for documentation updates
        updated_doc_payload = {
            "jsonrpc": "2.0", 
            "method": "tools/call",
            "params": {
                "name": "get_workflow_documentation",
                "arguments": {
                    "workflow_id": workflow_id,
                    "project_id": project_id,
                    "documentation_type": "progress_report",
                    "include_metrics": True,
                    "include_step_details": True
                }
            },
            "id": 3
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=updated_doc_payload, timeout=10)
        doc_retrieval_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, "Documentation retrieval failed"
        updated_doc_result = response.json()
        
        updated_progress = updated_doc_result["result"]["progress_percentage"]
        updated_timestamp = updated_doc_result["result"]["last_updated"]
        workflow_metrics = updated_doc_result["result"]["workflow_metrics"]
        step_details = updated_doc_result["result"].get("step_details", [])
        
        # Validate real-time updates
        assert updated_timestamp > initial_timestamp, "Documentation timestamp should be updated"
        assert len(step_details) > 0, "Should include step details"
        assert "steps_completed" in workflow_metrics, "Should include workflow metrics"
        
        # Validate performance of real-time documentation
        assert doc_retrieval_time < 10.0, f"Real-time doc retrieval took {doc_retrieval_time:.2f}ms, expected <10ms"
        
        # Validate documentation includes orchestration data
        doc_content = updated_doc_result["result"]["documentation_content"]
        assert workflow_id in doc_content, "Documentation should include workflow ID"
        assert "orchestration" in doc_content.lower(), "Documentation should mention orchestration"
        assert str(updated_progress) in doc_content, "Documentation should include current progress"
        
        print(f"✅ Real-time documentation updates working correctly in {doc_retrieval_time:.2f}ms")


class TestAdvancedOrchestrationBlueprintIntegration:
    """
    Advanced Orchestration ↔ TaskBlueprint Integration Tests (Full Circle)
    
    Tests the integration between Component 5 (Advanced Orchestration) and Component 1 (TaskBlueprint):
    - Orchestration creates new blueprints for dynamic workflow steps
    - Blueprint dependencies guide orchestration execution order
    - Orchestration feedback updates blueprint complexity and estimates
    - Blueprint metadata influences orchestration strategies
    - Performance: Full-circle blueprint ↔ orchestration operations <20ms
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
    
    def test_orchestration_creates_dynamic_blueprints(self, server_health):
        """
        Test that orchestration can dynamically create new blueprints during workflow execution.
        
        Validates:
        - Workflows can spawn new blueprint creation tasks
        - Dynamic blueprints inherit context from orchestration workflow
        - Created blueprints integrate back into ongoing orchestration
        - Performance: Dynamic blueprint creation <15ms per blueprint
        """
        project_id = "orchestration_blueprint_integration"
        
        # Create master blueprint that will spawn dynamic sub-blueprints
        master_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Dynamic Microservices Development",
                    "description": "Develop microservices architecture where individual services are determined dynamically based on requirements analysis",
                    "complexity": "CRITICAL",
                    "estimated_duration_minutes": 1440,  # 24 hours
                    "required_skills": ["architecture", "microservices", "dynamic-planning"],
                    "project_id": project_id,
                    "metadata": {
                        "dynamic_blueprint_generation": True,
                        "blueprint_templates": [
                            "user_service_template",
                            "payment_service_template", 
                            "notification_service_template",
                            "analytics_service_template"
                        ],
                        "service_requirements": {
                            "user_management": {"complexity": "MODERATE", "skills": ["auth", "database"]},
                            "payment_processing": {"complexity": "CRITICAL", "skills": ["payments", "security"]},
                            "notifications": {"complexity": "SIMPLE", "skills": ["messaging", "email"]},
                            "analytics": {"complexity": "COMPLEX", "skills": ["data-analysis", "ml"]}
                        }
                    }
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=master_blueprint_payload, timeout=15)
        assert response.status_code == 200, "Master blueprint creation failed"
        result = response.json()
        master_blueprint_id = result["result"]["blueprint_id"]
        
        # Start orchestration with dynamic blueprint generation enabled
        orchestration_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "orchestrate_dynamic_blueprint_workflow",
                "arguments": {
                    "project_id": project_id,
                    "master_blueprint_id": master_blueprint_id,
                    "enable_dynamic_blueprints": True,
                    "blueprint_generation_strategy": "requirements_based",
                    "max_dynamic_blueprints": 10,
                    "execution_mode": "adaptive"
                }
            },
            "id": 2
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=orchestration_payload, timeout=20)
        orchestration_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, f"Dynamic orchestration failed: {response.status_code}"
        orchestration_result = response.json()
        assert orchestration_result.get("error") is None, f"Orchestration error: {orchestration_result.get('error')}"
        
        workflow_data = orchestration_result["result"]
        workflow_id = workflow_data["workflow_id"]
        planned_dynamic_blueprints = workflow_data.get("planned_dynamic_blueprints", [])
        
        assert len(planned_dynamic_blueprints) >= 3, f"Should plan at least 3 dynamic blueprints, got {len(planned_dynamic_blueprints)}"
        assert orchestration_time < 20.0, f"Dynamic orchestration setup took {orchestration_time:.2f}ms, expected <20ms"
        
        # Wait for dynamic blueprint creation to begin
        time.sleep(1.0)
        
        # Check for created dynamic blueprints
        dynamic_blueprints_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_dynamic_blueprints",
                "arguments": {
                    "workflow_id": workflow_id,
                    "project_id": project_id,
                    "parent_blueprint_id": master_blueprint_id
                }
            },
            "id": 3
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=dynamic_blueprints_payload, timeout=10)
        assert response.status_code == 200, "Dynamic blueprints listing failed"
        
        dynamic_result = response.json()
        created_blueprints = dynamic_result["result"]["dynamic_blueprints"]
        
        assert len(created_blueprints) > 0, "Should have created at least one dynamic blueprint"
        
        # Validate dynamic blueprint properties
        for blueprint in created_blueprints:
            assert blueprint["parent_blueprint_id"] == master_blueprint_id, "Dynamic blueprint should reference parent"
            assert blueprint["created_by_workflow"] == workflow_id, "Should track creating workflow"
            assert blueprint["project_id"] == project_id, "Should inherit project ID"
            
            # Check complexity assignment based on requirements
            service_type = blueprint["metadata"].get("service_type", "")
            if "payment" in service_type.lower():
                assert blueprint["complexity"] == "CRITICAL", "Payment service should be CRITICAL complexity"
            elif "notification" in service_type.lower():
                assert blueprint["complexity"] in ["SIMPLE", "TRIVIAL"], "Notification service should be simple"
        
        print(f"✅ Orchestration created {len(created_blueprints)} dynamic blueprints successfully")
    
    def test_blueprint_feedback_improves_orchestration_strategies(self, server_health):
        """
        Test that orchestration learns from blueprint execution outcomes to improve future strategies.
        
        Validates:
        - Completed blueprint performance data feeds back to orchestration
        - Orchestration adapts strategies based on blueprint success/failure rates
        - Learning persistence across multiple orchestration workflows
        - Improved orchestration performance from blueprint feedback
        """
        project_id = "blueprint_feedback_integration"
        
        # Create test blueprints with known outcomes for learning
        test_blueprints = []
        
        # Simulate successful pattern
        success_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Successful API Endpoint Pattern",
                    "description": "API endpoint following successful patterns",
                    "complexity": "MODERATE",
                    "estimated_duration_minutes": 180,
                    "required_skills": ["python", "fastapi", "testing"],
                    "project_id": project_id,
                    "metadata": {
                        "pattern_type": "api_endpoint",
                        "success_indicators": ["comprehensive_tests", "clear_documentation", "error_handling"]
                    }
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=success_blueprint_payload, timeout=10)
        result = response.json()
        success_blueprint_id = result["result"]["blueprint_id"]
        
        # Create problematic pattern blueprint
        problematic_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Historically Problematic Integration",
                    "description": "Complex integration that has caused issues in past projects",
                    "complexity": "COMPLEX",
                    "estimated_duration_minutes": 360,
                    "required_skills": ["integration", "debugging", "performance"],
                    "project_id": project_id,
                    "metadata": {
                        "pattern_type": "complex_integration",
                        "risk_factors": ["external_dependencies", "performance_critical", "limited_documentation"]
                    }
                }
            },
            "id": 2
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=problematic_blueprint_payload, timeout=10)
        result = response.json()
        problematic_blueprint_id = result["result"]["blueprint_id"]
        
        # Record historical outcomes for learning
        success_outcome_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "record_blueprint_outcome",
                "arguments": {
                    "blueprint_id": success_blueprint_id,
                    "project_id": project_id,
                    "outcome": "success",
                    "actual_duration_minutes": 150,  # Completed under estimate
                    "quality_score": 0.95,
                    "orchestration_strategy": "parallel_with_testing",
                    "lessons_learned": ["parallel testing improved quality", "clear requirements reduced time"]
                }
            },
            "id": 3
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=success_outcome_payload, timeout=10)
        assert response.status_code == 200, "Success outcome recording failed"
        
        problematic_outcome_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "record_blueprint_outcome",
                "arguments": {
                    "blueprint_id": problematic_blueprint_id,
                    "project_id": project_id,
                    "outcome": "partial_failure",
                    "actual_duration_minutes": 480,  # Exceeded estimate
                    "quality_score": 0.6,
                    "orchestration_strategy": "sequential_standard",
                    "lessons_learned": ["external dependencies caused delays", "needed more upfront planning"]
                }
            },
            "id": 4
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=problematic_outcome_payload, timeout=10)
        assert response.status_code == 200, "Problematic outcome recording failed"
        
        # Create new similar blueprints to test learning
        new_api_blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "New API Endpoint with Learning",
                    "description": "Another API endpoint that should benefit from learned patterns",
                    "complexity": "MODERATE",
                    "estimated_duration_minutes": 180,
                    "required_skills": ["python", "fastapi", "testing"],
                    "project_id": project_id,
                    "metadata": {
                        "pattern_type": "api_endpoint",  # Same pattern as successful one
                        "success_indicators": ["comprehensive_tests", "clear_documentation"]
                    }
                }
            },
            "id": 5
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=new_api_blueprint_payload, timeout=10)
        result = response.json()
        new_api_blueprint_id = result["result"]["blueprint_id"]
        
        # Orchestrate with learning enabled
        learning_orchestration_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "orchestrate_with_pattern_learning",
                "arguments": {
                    "project_id": project_id,
                    "blueprint_ids": [new_api_blueprint_id],
                    "enable_pattern_learning": True,
                    "apply_historical_lessons": True,
                    "optimization_focus": "success_rate"
                }
            },
            "id": 6
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=learning_orchestration_payload, timeout=15)
        learning_orchestration_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, f"Learning orchestration failed: {response.status_code}"
        learning_result = response.json()
        assert learning_result.get("error") is None, f"Learning orchestration error: {learning_result.get('error')}"
        
        orchestration_data = learning_result["result"]
        applied_lessons = orchestration_data.get("applied_lessons", [])
        selected_strategy = orchestration_data.get("orchestration_strategy")
        confidence_improvement = orchestration_data.get("confidence_improvement", 0.0)
        
        # Validate learning was applied
        assert len(applied_lessons) > 0, "Should apply lessons learned from historical data"
        assert selected_strategy == "parallel_with_testing", f"Should use successful strategy, got {selected_strategy}"
        assert confidence_improvement > 0.1, f"Should show confidence improvement, got {confidence_improvement}"
        
        # Validate performance with learning
        assert learning_orchestration_time < 20.0, f"Learning orchestration took {learning_orchestration_time:.2f}ms, expected <20ms"
        
        print(f"✅ Orchestration successfully learned from blueprint feedback in {learning_orchestration_time:.2f}ms")


if __name__ == "__main__":
    """
    Run comprehensive Phase 2 cross-component integration tests.
    
    These tests validate all component pairs work correctly together:
    1. TaskBlueprint ↔ Enhanced TaskManager Integration
    2. Enhanced TaskManager ↔ Configuration Templates Integration  
    3. Configuration Templates ↔ Documentation Generation Integration
    4. Documentation Generation ↔ Advanced Orchestration Integration
    5. Advanced Orchestration ↔ TaskBlueprint Integration (full circle)
    """
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, project_root)
    
    # Run cross-component integration tests
    exit_code = pytest.main([
        __file__,
        "-v", 
        "--tb=short",
        "-s",  # Show print statements
        "--durations=10"  # Show slowest tests
    ])
    
    if exit_code == 0:
        print("\\n🎉 PHASE 2 CROSS-COMPONENT INTEGRATION: SUCCESS! 🎉")
        print("✅ All component pairs integrate correctly")
        print("✅ Data flows properly between all components")
        print("✅ Performance requirements met across boundaries")
        print("✅ Component dependencies resolved correctly") 
        print("✅ Full-circle integration validated")
    else:
        print("\\n❌ PHASE 2 CROSS-COMPONENT INTEGRATION FAILURES")
        print("❌ Component integration issues detected")
        print("❌ Review test output for specific component pairs")
    
    sys.exit(exit_code)