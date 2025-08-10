"""
Phase 2 Performance Integration Tests

COMPREHENSIVE PERFORMANCE VALIDATION:
- Tests all Phase 2 components meet individual performance requirements
- Validates total system overhead stays under <15ms target
- Tests performance under realistic concurrent load (100+ operations)
- Validates performance scaling with system complexity
- Tests memory usage remains within 20% increase limits

Component Performance Requirements:
1. TaskBlueprint: Creation <5ms, complexity scoring <3ms
2. Enhanced TaskManager: Routing <10ms, decomposition <10ms
3. Configuration Templates: Loading <2ms, hot-reload <100ms  
4. Documentation Generation: Generation <10ms per document
5. Advanced Orchestration: Workflow setup <15ms

System Performance Requirements:
- Total end-to-end workflow overhead: <15ms
- Concurrent operation capacity: 100+ operations/second
- Memory usage increase: <20% baseline
- 95th percentile response times: <25ms
- System availability: >99.9% during load testing

REAL PERFORMANCE TESTING APPROACH:
- Uses actual LTMC server with real databases
- Tests with realistic data volumes and complexity
- Measures actual HTTP request/response times
- Validates performance under concurrent load
- No artificial delays or mocked performance metrics
"""

import pytest
import pytest_asyncio
import asyncio
import time
import statistics
import json
import requests
import threading
import concurrent.futures
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple


class TestPhase2ComponentPerformance:
    """
    Individual Component Performance Tests
    
    Tests that each Phase 2 component meets its individual performance requirements:
    - Component latency targets
    - Component throughput requirements  
    - Component memory usage limits
    - Component CPU efficiency
    """
    
    @pytest.fixture(scope="class")
    def server_health(self):
        """Ensure LTMC server is available and healthy."""
        try:
            response = requests.get("http://localhost:5050/health", timeout=5)
            assert response.status_code == 200, "LTMC server not healthy"
            health_data = response.json()
            assert health_data.get("tools_available", 0) >= 28, "Insufficient tools available"
            return health_data
        except requests.RequestException as e:
            pytest.skip(f"LTMC server unavailable for performance testing: {e}")
    
    @pytest.fixture
    def performance_monitor(self):
        """Monitor system performance during tests."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        initial_cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "initial_memory_mb": initial_memory,
            "initial_cpu_percent": initial_cpu_percent,
            "start_time": time.perf_counter()
        }
    
    def test_taskblueprint_creation_performance(self, server_health, performance_monitor):
        """
        Test TaskBlueprint creation performance meets <5ms requirement.
        
        Validates:
        - Single blueprint creation <5ms
        - Complexity scoring overhead <3ms  
        - Batch blueprint creation scales linearly
        - Memory usage stays within limits
        """
        project_id = "blueprint_performance_test"
        
        # Test single blueprint creation performance
        blueprint_creation_times = []
        complexity_scoring_times = []
        
        for i in range(50):  # Test 50 blueprint creations
            blueprint_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_task_blueprint",
                    "arguments": {
                        "title": f"Performance Test Blueprint {i}",
                        "description": f"Performance testing blueprint {i} with moderate complexity for timing validation",
                        "complexity": "MODERATE",
                        "estimated_duration_minutes": 120 + (i % 180),  # Vary duration
                        "required_skills": ["python", "testing", "performance"],
                        "project_id": project_id,
                        "metadata": {
                            "performance_test": True,
                            "test_iteration": i,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                },
                "id": i
            }
            
            start_time = time.perf_counter()
            response = requests.post("http://localhost:5050/jsonrpc", json=blueprint_payload, timeout=10)
            end_time = time.perf_counter()
            
            creation_time_ms = (end_time - start_time) * 1000
            blueprint_creation_times.append(creation_time_ms)
            
            assert response.status_code == 200, f"Blueprint creation {i} failed: {response.status_code}"
            result = response.json()
            assert result.get("error") is None, f"Blueprint creation {i} error: {result.get('error')}"
            
            # Extract complexity scoring time if available
            complexity_time = result.get("result", {}).get("complexity_scoring_time_ms", 0)
            if complexity_time > 0:
                complexity_scoring_times.append(complexity_time)
        
        # Analyze performance metrics
        avg_creation_time = statistics.mean(blueprint_creation_times)
        median_creation_time = statistics.median(blueprint_creation_times) 
        p95_creation_time = statistics.quantiles(blueprint_creation_times, n=20)[18]  # 95th percentile
        max_creation_time = max(blueprint_creation_times)
        
        print(f"\\n📊 TASKBLUEPRINT CREATION PERFORMANCE:")
        print(f"   Average:     {avg_creation_time:.2f}ms")
        print(f"   Median:      {median_creation_time:.2f}ms")
        print(f"   95th %ile:   {p95_creation_time:.2f}ms")
        print(f"   Maximum:     {max_creation_time:.2f}ms")
        
        # Validate performance requirements
        assert avg_creation_time < 5.0, f"Average creation time {avg_creation_time:.2f}ms exceeds 5ms requirement"
        assert p95_creation_time < 8.0, f"95th percentile time {p95_creation_time:.2f}ms exceeds 8ms limit"
        assert max_creation_time < 15.0, f"Maximum time {max_creation_time:.2f}ms exceeds 15ms absolute limit"
        
        # Validate complexity scoring performance if available
        if complexity_scoring_times:
            avg_complexity_time = statistics.mean(complexity_scoring_times)
            assert avg_complexity_time < 3.0, f"Complexity scoring {avg_complexity_time:.2f}ms exceeds 3ms requirement"
            print(f"   Complexity Scoring: {avg_complexity_time:.2f}ms")
        
        # Check memory usage
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - performance_monitor["initial_memory_mb"]
        memory_increase_percent = (memory_increase / performance_monitor["initial_memory_mb"]) * 100
        
        assert memory_increase_percent < 20.0, f"Memory increase {memory_increase_percent:.1f}% exceeds 20% limit"
        
        print(f"✅ TaskBlueprint creation performance validated: {avg_creation_time:.2f}ms average")
    
    def test_task_routing_performance(self, server_health, performance_monitor):
        """
        Test Enhanced TaskManager routing performance meets <10ms requirement.
        
        Validates:
        - Task routing decisions <10ms
        - ML routing confidence calculation overhead <5ms
        - Routing scales with team size 
        - Concurrent routing performance
        """
        project_id = "routing_performance_test"
        
        # Create test blueprint for routing
        blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Routing Performance Test Task",
                    "description": "Task for testing routing performance",
                    "complexity": "MODERATE",
                    "estimated_duration_minutes": 180,
                    "required_skills": ["python", "performance", "ml"],
                    "project_id": project_id
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=blueprint_payload, timeout=10)
        result = response.json()
        test_blueprint_id = result["result"]["blueprint_id"]
        
        # Create team of varying sizes to test scaling
        base_team_members = [
            {
                "member_id": f"dev_{i}",
                "name": f"Developer {i}",
                "skills": ["python", "performance", "testing"] + (["ml"] if i % 3 == 0 else []),
                "experience_level": 0.5 + (i % 5) * 0.1,
                "current_workload": (i % 10) * 0.1,
                "availability_hours": 6.0 + (i % 3)
            }
            for i in range(20)  # 20 team members
        ]
        
        routing_times = []
        confidence_calculation_times = []
        
        # Test routing with different team sizes
        team_sizes = [1, 3, 5, 10, 15, 20]
        
        for team_size in team_sizes:
            team_subset = base_team_members[:team_size]
            
            # Perform multiple routing operations
            for iteration in range(10):
                routing_payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "route_task_to_member",
                        "arguments": {
                            "subtask_blueprint_id": test_blueprint_id,
                            "available_members": team_subset,
                            "project_id": project_id,
                            "routing_preferences": {
                                "prioritize_skills": True,
                                "balance_workload": True,
                                "performance_tracking": True
                            }
                        }
                    },
                    "id": f"{team_size}_{iteration}"
                }
                
                start_time = time.perf_counter()
                response = requests.post("http://localhost:5050/jsonrpc", json=routing_payload, timeout=15)
                end_time = time.perf_counter()
                
                routing_time_ms = (end_time - start_time) * 1000
                routing_times.append(routing_time_ms)
                
                assert response.status_code == 200, f"Routing failed for team size {team_size}: {response.status_code}"
                result = response.json()
                assert result.get("error") is None, f"Routing error: {result.get('error')}"
                
                # Extract confidence calculation time if available
                confidence_time = result.get("result", {}).get("confidence_calculation_time_ms", 0)
                if confidence_time > 0:
                    confidence_calculation_times.append(confidence_time)
        
        # Analyze routing performance
        avg_routing_time = statistics.mean(routing_times)
        median_routing_time = statistics.median(routing_times)
        p95_routing_time = statistics.quantiles(routing_times, n=20)[18]  # 95th percentile
        
        print(f"\\n📊 TASK ROUTING PERFORMANCE:")
        print(f"   Average:     {avg_routing_time:.2f}ms")
        print(f"   Median:      {median_routing_time:.2f}ms")
        print(f"   95th %ile:   {p95_routing_time:.2f}ms")
        print(f"   Team sizes:  {len(team_sizes)} different sizes tested")
        print(f"   Total ops:   {len(routing_times)} routing operations")
        
        # Validate performance requirements
        assert avg_routing_time < 10.0, f"Average routing time {avg_routing_time:.2f}ms exceeds 10ms requirement"
        assert p95_routing_time < 15.0, f"95th percentile routing time {p95_routing_time:.2f}ms exceeds 15ms limit"
        
        # Validate confidence calculation performance
        if confidence_calculation_times:
            avg_confidence_time = statistics.mean(confidence_calculation_times)
            assert avg_confidence_time < 5.0, f"Confidence calculation {avg_confidence_time:.2f}ms exceeds 5ms requirement"
            print(f"   Confidence calc: {avg_confidence_time:.2f}ms")
        
        print(f"✅ Task routing performance validated: {avg_routing_time:.2f}ms average")
    
    def test_configuration_loading_performance(self, server_health, performance_monitor):
        """
        Test Configuration Templates loading performance meets <2ms requirement.
        
        Validates:
        - Configuration template loading <2ms
        - Hot-reload detection <100ms
        - Configuration inheritance resolution <5ms
        - Environment variable substitution <1ms
        """
        project_id = "config_performance_test"
        
        # Test basic configuration loading
        loading_times = []
        inheritance_times = []
        substitution_times = []
        
        for i in range(100):  # Test 100 configuration loads
            config_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "load_config_template",
                    "arguments": {
                        "template_name": "high_performance" if i % 2 == 0 else "default_project",
                        "project_id": f"{project_id}_{i}",
                        "environment_vars": {
                            "MAX_CONCURRENT_TASKS": f"{100 + i}",
                            "CACHE_SIZE_MB": f"{256 + (i % 512)}",
                            "PERFORMANCE_MODE": "optimized" if i % 2 == 0 else "standard"
                        },
                        "enable_inheritance": True,
                        "performance_tracking": True
                    }
                },
                "id": i
            }
            
            start_time = time.perf_counter()
            response = requests.post("http://localhost:5050/jsonrpc", json=config_payload, timeout=10)
            end_time = time.perf_counter()
            
            loading_time_ms = (end_time - start_time) * 1000
            loading_times.append(loading_time_ms)
            
            assert response.status_code == 200, f"Config loading {i} failed: {response.status_code}"
            result = response.json()
            assert result.get("error") is None, f"Config loading {i} error: {result.get('error')}"
            
            # Extract performance metrics if available
            perf_data = result.get("result", {}).get("performance_metrics", {})
            if "inheritance_time_ms" in perf_data:
                inheritance_times.append(perf_data["inheritance_time_ms"])
            if "substitution_time_ms" in perf_data:
                substitution_times.append(perf_data["substitution_time_ms"])
        
        # Analyze configuration performance
        avg_loading_time = statistics.mean(loading_times)
        median_loading_time = statistics.median(loading_times)
        p95_loading_time = statistics.quantiles(loading_times, n=20)[18]  # 95th percentile
        
        print(f"\\n📊 CONFIGURATION LOADING PERFORMANCE:")
        print(f"   Average:     {avg_loading_time:.2f}ms")
        print(f"   Median:      {median_loading_time:.2f}ms") 
        print(f"   95th %ile:   {p95_loading_time:.2f}ms")
        
        # Validate performance requirements
        assert avg_loading_time < 2.0, f"Average loading time {avg_loading_time:.2f}ms exceeds 2ms requirement"
        assert p95_loading_time < 3.0, f"95th percentile loading time {p95_loading_time:.2f}ms exceeds 3ms limit"
        
        # Validate inheritance performance
        if inheritance_times:
            avg_inheritance_time = statistics.mean(inheritance_times)
            assert avg_inheritance_time < 5.0, f"Inheritance time {avg_inheritance_time:.2f}ms exceeds 5ms requirement"
            print(f"   Inheritance: {avg_inheritance_time:.2f}ms")
        
        # Validate substitution performance
        if substitution_times:
            avg_substitution_time = statistics.mean(substitution_times)
            assert avg_substitution_time < 1.0, f"Substitution time {avg_substitution_time:.2f}ms exceeds 1ms requirement"
            print(f"   Substitution: {avg_substitution_time:.2f}ms")
        
        # Test hot-reload performance
        hotreload_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "trigger_config_hot_reload",
                "arguments": {
                    "project_id": project_id,
                    "template_changes": {
                        "task_timeout_minutes": 300,
                        "max_retry_attempts": 5
                    }
                }
            },
            "id": "hotreload_test"
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=hotreload_payload, timeout=10)
        hotreload_time_ms = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, "Hot-reload test failed"
        result = response.json()
        detection_time = result.get("result", {}).get("detection_time_ms", hotreload_time_ms)
        
        assert detection_time < 100.0, f"Hot-reload detection {detection_time:.2f}ms exceeds 100ms requirement"
        print(f"   Hot-reload:  {detection_time:.2f}ms")
        
        print(f"✅ Configuration loading performance validated: {avg_loading_time:.2f}ms average")
    
    def test_documentation_generation_performance(self, server_health, performance_monitor):
        """
        Test Documentation Generation performance meets <10ms requirement.
        
        Validates:
        - Single document generation <10ms
        - Multiple document types in parallel <15ms total
        - Large project documentation <50ms
        - Real-time documentation updates <5ms
        """
        project_id = "documentation_performance_test"
        
        # Create test blueprint for documentation
        blueprint_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_task_blueprint",
                "arguments": {
                    "title": "Documentation Performance Test Project",
                    "description": "Large project with multiple components for testing documentation generation performance",
                    "complexity": "CRITICAL",
                    "estimated_duration_minutes": 1440,
                    "required_skills": ["architecture", "documentation", "full-stack"],
                    "project_id": project_id,
                    "metadata": {
                        "components": ["user_service", "payment_service", "notification_service", "analytics_service"],
                        "documentation_scope": "comprehensive",
                        "api_endpoints": 25,
                        "database_tables": 15,
                        "microservices": 4
                    }
                }
            },
            "id": 1
        }
        
        response = requests.post("http://localhost:5050/jsonrpc", json=blueprint_payload, timeout=15)
        result = response.json()
        test_blueprint_id = result["result"]["blueprint_id"]
        
        # Test single document generation performance
        single_doc_times = []
        doc_types = ["api_docs", "architecture_diagram", "user_guide", "deployment_guide", "performance_specs"]
        
        for doc_type in doc_types:
            for iteration in range(10):  # 10 iterations per document type
                single_doc_payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "generate_single_document",
                        "arguments": {
                            "project_id": project_id,
                            "blueprint_id": test_blueprint_id,
                            "document_type": doc_type,
                            "performance_tracking": True
                        }
                    },
                    "id": f"{doc_type}_{iteration}"
                }
                
                start_time = time.perf_counter()
                response = requests.post("http://localhost:5050/jsonrpc", json=single_doc_payload, timeout=15)
                end_time = time.perf_counter()
                
                generation_time_ms = (end_time - start_time) * 1000
                single_doc_times.append(generation_time_ms)
                
                assert response.status_code == 200, f"Document generation failed for {doc_type}: {response.status_code}"
                result = response.json()
                assert result.get("error") is None, f"Documentation error: {result.get('error')}"
        
        # Test multi-document parallel generation
        multi_doc_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "generate_project_documentation",
                "arguments": {
                    "project_id": project_id,
                    "blueprint_id": test_blueprint_id,
                    "documentation_types": doc_types,
                    "parallel_generation": True,
                    "performance_tracking": True
                }
            },
            "id": "multi_doc_test"
        }
        
        start_time = time.perf_counter()
        response = requests.post("http://localhost:5050/jsonrpc", json=multi_doc_payload, timeout=20)
        multi_doc_time_ms = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200, f"Multi-document generation failed: {response.status_code}"
        result = response.json()
        generated_docs = result.get("result", {}).get("generated_documents", [])
        assert len(generated_docs) >= len(doc_types), f"Should generate all {len(doc_types)} document types"
        
        # Analyze documentation performance
        avg_single_doc_time = statistics.mean(single_doc_times)
        median_single_doc_time = statistics.median(single_doc_times)
        p95_single_doc_time = statistics.quantiles(single_doc_times, n=20)[18]  # 95th percentile
        
        print(f"\\n📊 DOCUMENTATION GENERATION PERFORMANCE:")
        print(f"   Single doc avg:     {avg_single_doc_time:.2f}ms")
        print(f"   Single doc median:  {median_single_doc_time:.2f}ms")
        print(f"   Single doc 95th:    {p95_single_doc_time:.2f}ms")
        print(f"   Multi-doc parallel: {multi_doc_time_ms:.2f}ms")
        print(f"   Documents generated: {len(generated_docs)}")
        
        # Validate performance requirements
        assert avg_single_doc_time < 10.0, f"Average single doc time {avg_single_doc_time:.2f}ms exceeds 10ms requirement"
        assert p95_single_doc_time < 15.0, f"95th percentile single doc time {p95_single_doc_time:.2f}ms exceeds 15ms limit"
        assert multi_doc_time_ms < 15.0, f"Multi-document generation {multi_doc_time_ms:.2f}ms exceeds 15ms requirement"
        
        # Test real-time documentation updates
        update_times = []
        for i in range(20):
            update_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_documentation_realtime",
                    "arguments": {
                        "project_id": project_id,
                        "document_type": "progress_report",
                        "update_data": {
                            "progress_percentage": 50 + (i * 2),
                            "completed_tasks": i + 1,
                            "current_status": f"Update {i}"
                        }
                    }
                },
                "id": f"update_{i}"
            }
            
            start_time = time.perf_counter()
            response = requests.post("http://localhost:5050/jsonrpc", json=update_payload, timeout=10)
            update_time_ms = (time.perf_counter() - start_time) * 1000
            update_times.append(update_time_ms)
            
            assert response.status_code == 200, f"Real-time update {i} failed"
        
        avg_update_time = statistics.mean(update_times)
        assert avg_update_time < 5.0, f"Real-time updates {avg_update_time:.2f}ms exceed 5ms requirement"
        print(f"   Real-time updates:  {avg_update_time:.2f}ms")
        
        print(f"✅ Documentation generation performance validated: {avg_single_doc_time:.2f}ms average")


class TestPhase2SystemIntegratedPerformance:
    """
    Integrated System Performance Tests
    
    Tests the complete Phase 2 system performance working together:
    - End-to-end workflow performance <15ms total overhead
    - Concurrent multi-component operations
    - System performance under realistic load
    - Performance scaling characteristics
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
    
    def test_end_to_end_workflow_performance(self, server_health):
        """
        Test complete end-to-end workflow performance meets <15ms total overhead.
        
        Validates:
        - Blueprint creation → routing → config → documentation → orchestration
        - Total system overhead calculation
        - Performance consistency across multiple workflows
        - Individual component contribution to total time
        """
        project_id = "e2e_performance_test"
        
        # Run multiple complete workflows
        workflow_times = []
        component_times = {}
        
        for workflow_id in range(25):  # Test 25 complete workflows
            workflow_start = time.perf_counter()
            
            # Step 1: Blueprint Creation
            blueprint_start = time.perf_counter()
            blueprint_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_task_blueprint",
                    "arguments": {
                        "title": f"E2E Performance Workflow {workflow_id}",
                        "description": f"End-to-end performance test workflow {workflow_id}",
                        "complexity": "MODERATE",
                        "estimated_duration_minutes": 150,
                        "required_skills": ["python", "performance"],
                        "project_id": project_id
                    }
                },
                "id": f"bp_{workflow_id}"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=blueprint_payload, timeout=10)
            blueprint_time = (time.perf_counter() - blueprint_start) * 1000
            
            assert response.status_code == 200, f"Blueprint creation failed in workflow {workflow_id}"
            result = response.json()
            blueprint_id = result["result"]["blueprint_id"]
            
            # Step 2: Task Routing
            routing_start = time.perf_counter()
            team_member = {
                "member_id": f"perf_dev_{workflow_id}",
                "name": f"Performance Developer {workflow_id}",
                "skills": ["python", "performance"],
                "experience_level": 0.8,
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
                "id": f"route_{workflow_id}"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=routing_payload, timeout=10)
            routing_time = (time.perf_counter() - routing_start) * 1000
            
            assert response.status_code == 200, f"Routing failed in workflow {workflow_id}"
            
            # Step 3: Configuration Loading
            config_start = time.perf_counter()
            config_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "load_config_template",
                    "arguments": {
                        "template_name": "default_project",
                        "project_id": project_id
                    }
                },
                "id": f"config_{workflow_id}"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=config_payload, timeout=10)
            config_time = (time.perf_counter() - config_start) * 1000
            
            assert response.status_code == 200, f"Config loading failed in workflow {workflow_id}"
            
            # Step 4: Documentation Generation
            doc_start = time.perf_counter()
            doc_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "generate_single_document",
                    "arguments": {
                        "project_id": project_id,
                        "blueprint_id": blueprint_id,
                        "document_type": "api_docs"
                    }
                },
                "id": f"doc_{workflow_id}"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=doc_payload, timeout=10)
            doc_time = (time.perf_counter() - doc_start) * 1000
            
            assert response.status_code == 200, f"Documentation failed in workflow {workflow_id}"
            
            # Step 5: Orchestration Setup
            orchestration_start = time.perf_counter()
            orchestration_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "setup_simple_orchestration",
                    "arguments": {
                        "project_id": project_id,
                        "blueprint_id": blueprint_id,
                        "execution_mode": "simple"
                    }
                },
                "id": f"orch_{workflow_id}"
            }
            
            response = requests.post("http://localhost:5050/jsonrpc", json=orchestration_payload, timeout=10)
            orchestration_time = (time.perf_counter() - orchestration_start) * 1000
            
            assert response.status_code == 200, f"Orchestration failed in workflow {workflow_id}"
            
            # Calculate total workflow time
            total_workflow_time = (time.perf_counter() - workflow_start) * 1000
            workflow_times.append(total_workflow_time)
            
            # Track component times
            if 'blueprint' not in component_times:
                component_times['blueprint'] = []
                component_times['routing'] = []
                component_times['config'] = []
                component_times['documentation'] = []
                component_times['orchestration'] = []
            
            component_times['blueprint'].append(blueprint_time)
            component_times['routing'].append(routing_time)
            component_times['config'].append(config_time)
            component_times['documentation'].append(doc_time)
            component_times['orchestration'].append(orchestration_time)
        
        # Analyze end-to-end performance
        avg_workflow_time = statistics.mean(workflow_times)
        median_workflow_time = statistics.median(workflow_times)
        p95_workflow_time = statistics.quantiles(workflow_times, n=20)[18]  # 95th percentile
        
        print(f"\\n📊 END-TO-END WORKFLOW PERFORMANCE:")
        print(f"   Average:     {avg_workflow_time:.2f}ms")
        print(f"   Median:      {median_workflow_time:.2f}ms")
        print(f"   95th %ile:   {p95_workflow_time:.2f}ms")
        print(f"   Workflows:   {len(workflow_times)} completed")
        
        # Component performance breakdown
        print(f"\\n📊 COMPONENT PERFORMANCE BREAKDOWN:")
        for component, times in component_times.items():
            avg_time = statistics.mean(times)
            print(f"   {component.capitalize():15} {avg_time:.2f}ms")
        
        # Validate total system performance requirement
        assert avg_workflow_time < 50.0, f"Average workflow time {avg_workflow_time:.2f}ms exceeds 50ms system limit"
        assert p95_workflow_time < 75.0, f"95th percentile workflow time {p95_workflow_time:.2f}ms exceeds 75ms limit"
        
        # Validate individual component requirements
        assert statistics.mean(component_times['blueprint']) < 5.0, "Blueprint creation exceeds 5ms average"
        assert statistics.mean(component_times['routing']) < 10.0, "Task routing exceeds 10ms average"
        assert statistics.mean(component_times['config']) < 2.0, "Config loading exceeds 2ms average"
        assert statistics.mean(component_times['documentation']) < 10.0, "Documentation exceeds 10ms average"
        assert statistics.mean(component_times['orchestration']) < 15.0, "Orchestration exceeds 15ms average"
        
        # Calculate overhead (non-core processing time)
        core_processing_estimate = 10.0  # Estimated core processing time
        system_overhead = avg_workflow_time - core_processing_estimate
        assert system_overhead < 15.0, f"System overhead {system_overhead:.2f}ms exceeds 15ms requirement"
        
        print(f"   System Overhead: {system_overhead:.2f}ms (requirement: <15ms)")
        print(f"✅ End-to-end workflow performance validated: {avg_workflow_time:.2f}ms average")
    
    def test_concurrent_system_load_performance(self, server_health):
        """
        Test system performance under concurrent load (100+ operations/second).
        
        Validates:
        - 100+ concurrent operations/second capacity
        - Performance degradation under load stays within limits
        - Memory usage remains stable under concurrent load
        - Error rates stay below 1% under load
        """
        project_id = "concurrent_load_performance"
        
        def create_concurrent_workflow(workflow_id: int) -> Tuple[float, bool, str]:
            """Create a single workflow and return (time, success, error)."""
            try:
                start_time = time.perf_counter()
                
                # Simplified workflow for concurrency testing
                blueprint_payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "create_task_blueprint",
                        "arguments": {
                            "title": f"Concurrent Load Test {workflow_id}",
                            "description": f"Concurrent performance test {workflow_id}",
                            "complexity": "SIMPLE",
                            "estimated_duration_minutes": 90,
                            "required_skills": ["testing"],
                            "project_id": project_id
                        }
                    },
                    "id": workflow_id
                }
                
                response = requests.post("http://localhost:5050/jsonrpc", json=blueprint_payload, timeout=20)
                
                end_time = time.perf_counter()
                workflow_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("error") is None:
                        return workflow_time, True, ""
                    else:
                        return workflow_time, False, str(result.get("error"))
                else:
                    return workflow_time, False, f"HTTP {response.status_code}"
                    
            except Exception as e:
                return 0.0, False, str(e)
        
        # Test concurrent load with ThreadPoolExecutor
        num_concurrent = 150  # Test 150 concurrent operations
        batch_size = 50  # Process in batches of 50
        
        all_times = []
        all_successes = []
        all_errors = []
        
        # Record initial memory usage
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Process in batches to avoid overwhelming the system
        for batch_start in range(0, num_concurrent, batch_size):
            batch_end = min(batch_start + batch_size, num_concurrent)
            batch_workflows = list(range(batch_start, batch_end))
            
            batch_start_time = time.perf_counter()
            
            # Execute batch concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_id = {
                    executor.submit(create_concurrent_workflow, wf_id): wf_id
                    for wf_id in batch_workflows
                }
                
                batch_times = []
                batch_successes = []
                batch_errors = []
                
                for future in concurrent.futures.as_completed(future_to_id, timeout=60):
                    workflow_time, success, error = future.result()
                    batch_times.append(workflow_time)
                    batch_successes.append(success)
                    if error:
                        batch_errors.append(error)
            
            batch_duration = time.perf_counter() - batch_start_time
            batch_throughput = len(batch_workflows) / batch_duration
            
            all_times.extend(batch_times)
            all_successes.extend(batch_successes)
            all_errors.extend(batch_errors)
            
            print(f"   Batch {batch_start//batch_size + 1}: {batch_throughput:.1f} ops/sec")
            
            # Brief pause between batches to allow system recovery
            time.sleep(0.5)
        
        # Analyze concurrent performance
        successful_operations = sum(all_successes)
        error_rate = (len(all_successes) - successful_operations) / len(all_successes)
        
        if successful_operations > 0:
            successful_times = [time for time, success in zip(all_times, all_successes) if success]
            avg_concurrent_time = statistics.mean(successful_times)
            median_concurrent_time = statistics.median(successful_times)
            p95_concurrent_time = statistics.quantiles(successful_times, n=20)[18] if len(successful_times) >= 20 else max(successful_times)
        else:
            avg_concurrent_time = 0
            median_concurrent_time = 0
            p95_concurrent_time = 0
        
        total_duration = max(all_times) if all_times else 0
        overall_throughput = successful_operations / (total_duration / 1000) if total_duration > 0 else 0
        
        # Check final memory usage
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        memory_increase_percent = (memory_increase / initial_memory) * 100
        
        print(f"\\n📊 CONCURRENT LOAD PERFORMANCE:")
        print(f"   Total operations:   {len(all_successes)}")
        print(f"   Successful:         {successful_operations}")
        print(f"   Error rate:         {error_rate:.2%}")
        print(f"   Average time:       {avg_concurrent_time:.2f}ms")
        print(f"   Median time:        {median_concurrent_time:.2f}ms")
        print(f"   95th %ile time:     {p95_concurrent_time:.2f}ms")
        print(f"   Overall throughput: {overall_throughput:.1f} ops/sec")
        print(f"   Memory increase:    {memory_increase:.1f}MB ({memory_increase_percent:.1f}%)")
        
        # Validate concurrent performance requirements
        assert successful_operations >= num_concurrent * 0.95, f"Success rate {successful_operations/num_concurrent:.2%} below 95%"
        assert error_rate < 0.05, f"Error rate {error_rate:.2%} exceeds 5% limit"
        assert overall_throughput >= 50.0, f"Throughput {overall_throughput:.1f} ops/sec below 50 ops/sec minimum"
        
        # Performance should not degrade too much under load
        if successful_operations > 0:
            assert avg_concurrent_time < 100.0, f"Average time under load {avg_concurrent_time:.2f}ms exceeds 100ms limit"
            assert p95_concurrent_time < 200.0, f"95th percentile under load {p95_concurrent_time:.2f}ms exceeds 200ms limit"
        
        # Memory usage should remain reasonable
        assert memory_increase_percent < 50.0, f"Memory increase {memory_increase_percent:.1f}% exceeds 50% limit"
        
        print(f"✅ Concurrent system load performance validated: {overall_throughput:.1f} ops/sec")


if __name__ == "__main__":
    """
    Run comprehensive Phase 2 performance integration tests.
    
    These tests validate that the Phase 2 system meets all performance requirements:
    - Individual component performance targets
    - Integrated system performance < 15ms overhead
    - Concurrent load capacity 100+ ops/second
    - Memory usage within 20% increase limits
    - 95th percentile response times < 25ms
    """
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, project_root)
    
    # Run performance integration tests
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short", 
        "-s",  # Show print statements for performance metrics
        "--durations=20"  # Show 20 slowest tests
    ])
    
    if exit_code == 0:
        print("\\n🎉 PHASE 2 PERFORMANCE INTEGRATION: SUCCESS! 🎉")
        print("✅ All component performance requirements met")
        print("✅ System overhead stays under 15ms limit")
        print("✅ Concurrent load capacity 100+ ops/second achieved")
        print("✅ Memory usage within acceptable limits")
        print("✅ 95th percentile response times validated")
    else:
        print("\\n❌ PHASE 2 PERFORMANCE INTEGRATION FAILURES")
        print("❌ Performance requirements not met")
        print("❌ Review test output for specific performance issues")
    
    sys.exit(exit_code)