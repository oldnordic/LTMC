"""
Configuration Template Service Tests

Tests for template loading, validation, inheritance, hot-reload functionality,
and integration with security system.

Performance Requirements:
- Configuration loading: <2ms
- Template validation: <5ms per template
- Hot-reload detection: <100ms

Security Requirements:
- All template operations use Phase 1 security validation
- Project-specific template isolation
- Sanitized template content and user inputs
"""

import os
import sys
import json
import time
import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ltms.services.config_template_service import (
    ConfigTemplateManager,
    ConfigTemplate,
    TemplateValidationError,
    TemplateLoadError,
    TemplateInheritanceError,
    ConfigurationCache
)
from ltms.security.mcp_integration import MCPSecurityManager, MCPSecurityError


class TestConfigTemplate:
    """Test ConfigTemplate model and data structure."""
    
    def test_config_template_creation(self):
        """Test ConfigTemplate can be created with valid data."""
        template_data = {
            "name": "test_template",
            "version": "1.0.0",
            "description": "Test template",
            "extends": "base_template",
            "environment": {
                "DB_PATH": "${PROJECT_ROOT}/data/test.db",
                "REDIS_PORT": "${REDIS_PORT:6379}"
            },
            "configuration": {
                "performance": {
                    "cache_size": 1000,
                    "timeout": "${TIMEOUT:30}"
                }
            },
            "validation_schema": {
                "type": "object",
                "properties": {
                    "performance": {
                        "type": "object",
                        "properties": {
                            "cache_size": {"type": "integer", "minimum": 100},
                            "timeout": {"type": "integer", "minimum": 1}
                        }
                    }
                }
            }
        }
        
        template = ConfigTemplate.from_dict(template_data)
        assert template.name == "test_template"
        assert template.version == "1.0.0"
        assert template.extends == "base_template"
        assert "DB_PATH" in template.environment
        assert template.validation_schema is not None
    
    def test_config_template_validation_error(self):
        """Test ConfigTemplate raises validation error for invalid data."""
        with pytest.raises(TemplateValidationError):
            ConfigTemplate.from_dict({})  # Missing required fields
        
        with pytest.raises(TemplateValidationError):
            ConfigTemplate.from_dict({"name": ""})  # Empty name
    
    def test_environment_variable_substitution(self):
        """Test environment variable substitution in templates."""
        template_data = {
            "name": "env_test",
            "version": "1.0.0",
            "environment": {
                "DB_PATH": "${PROJECT_ROOT}/test.db",
                "CACHE_SIZE": "${CACHE_SIZE:1000}",
                "DEBUG_MODE": "${DEBUG:false}"
            },
            "configuration": {}
        }
        
        template = ConfigTemplate.from_dict(template_data)
        
        # Mock environment variables
        with patch.dict(os.environ, {"PROJECT_ROOT": "/tmp", "DEBUG": "true"}):
            resolved = template.resolve_environment_variables()
            
            assert resolved["DB_PATH"] == "/tmp/test.db"
            assert resolved["CACHE_SIZE"] == "1000"  # Default value
            assert resolved["DEBUG_MODE"] == "true"   # From environment


class TestConfigurationCache:
    """Test ConfigurationCache for performance optimization."""
    
    def test_cache_creation(self):
        """Test ConfigurationCache can be created."""
        cache = ConfigurationCache(max_size=100, ttl_seconds=300)
        assert cache.max_size == 100
        assert cache.ttl_seconds == 300
        assert len(cache._cache) == 0
    
    def test_cache_get_set(self):
        """Test cache get and set operations."""
        cache = ConfigurationCache(max_size=10, ttl_seconds=60)
        
        # Test cache miss
        assert cache.get("test_key") is None
        
        # Test cache set and get
        test_data = {"config": "value"}
        cache.set("test_key", test_data)
        assert cache.get("test_key") == test_data
    
    def test_cache_expiry(self):
        """Test cache expiry based on TTL."""
        cache = ConfigurationCache(max_size=10, ttl_seconds=0.1)
        
        cache.set("test_key", {"data": "value"})
        assert cache.get("test_key") is not None
        
        # Wait for expiry
        time.sleep(0.2)
        assert cache.get("test_key") is None
    
    def test_cache_size_limit(self):
        """Test cache respects maximum size limit."""
        cache = ConfigurationCache(max_size=2, ttl_seconds=300)
        
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})
        cache.set("key3", {"data": "value3"})  # Should evict oldest
        
        # Should have only 2 items (LRU eviction)
        assert len(cache._cache) == 2
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None


class TestConfigTemplateManager:
    """Test ConfigTemplateManager service class."""
    
    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary directory for test templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            templates_dir.mkdir()
            yield templates_dir
    
    @pytest.fixture
    def sample_base_template(self, temp_templates_dir):
        """Create sample base template file."""
        base_template = {
            "name": "base_template",
            "version": "1.0.0",
            "description": "Base configuration template",
            "environment": {
                "LOG_LEVEL": "${LOG_LEVEL:INFO}",
                "REDIS_HOST": "${REDIS_HOST:localhost}"
            },
            "configuration": {
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(levelname)s - %(message)s"
                },
                "redis": {
                    "host": "localhost",
                    "port": 6379
                }
            },
            "validation_schema": {
                "type": "object",
                "properties": {
                    "logging": {"type": "object"},
                    "redis": {"type": "object"}
                }
            }
        }
        
        base_path = temp_templates_dir / "base_template.json"
        with open(base_path, 'w') as f:
            json.dump(base_template, f, indent=2)
        
        return base_path
    
    @pytest.fixture
    def sample_derived_template(self, temp_templates_dir):
        """Create sample derived template that extends base template."""
        derived_template = {
            "name": "high_performance",
            "version": "1.1.0",
            "description": "High performance configuration template",
            "extends": "base_template",
            "environment": {
                "CACHE_SIZE": "${CACHE_SIZE:10000}",
                "WORKER_THREADS": "${WORKER_THREADS:8}"
            },
            "configuration": {
                "performance": {
                    "cache_size": 10000,
                    "worker_threads": 8,
                    "enable_clustering": True
                },
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "connection_pool_size": 20
                }
            }
        }
        
        derived_path = temp_templates_dir / "high_performance.json"
        with open(derived_path, 'w') as f:
            json.dump(derived_template, f, indent=2)
        
        return derived_path
    
    @pytest.fixture
    def security_manager(self):
        """Create mock security manager for testing."""
        mock_security = Mock(spec=MCPSecurityManager)
        mock_security.validate_mcp_request.return_value = {
            "success": True,
            "project_id": "test_project",
            "sanitized_input": None,
            "scoped_db_path": None,
            "scoped_redis_key": None,
            "execution_time_ms": 1.0
        }
        return mock_security
    
    def test_template_manager_creation(self, temp_templates_dir, security_manager):
        """Test ConfigTemplateManager can be created."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        assert manager.templates_dir == temp_templates_dir
        assert manager.security_manager == security_manager
        assert isinstance(manager.cache, ConfigurationCache)
        assert isinstance(manager._file_watchers, dict)
    
    def test_load_single_template(self, temp_templates_dir, sample_base_template, security_manager):
        """Test loading a single template file."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        template = manager.load_template("base_template")
        
        assert template.name == "base_template"
        assert template.version == "1.0.0"
        assert "LOG_LEVEL" in template.environment
        assert "logging" in template.configuration
    
    def test_load_template_not_found(self, temp_templates_dir, security_manager):
        """Test loading non-existent template raises error."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        with pytest.raises(TemplateLoadError):
            manager.load_template("nonexistent_template")
    
    def test_template_inheritance(self, temp_templates_dir, sample_base_template, 
                                sample_derived_template, security_manager):
        """Test template inheritance and merging."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        derived_template = manager.load_template("high_performance")
        resolved_config = manager.resolve_template_inheritance(derived_template)
        
        # Should have base template configuration
        assert "logging" in resolved_config["configuration"]
        assert "redis" in resolved_config["configuration"]
        
        # Should have derived template additions
        assert "performance" in resolved_config["configuration"]
        
        # Redis configuration should be merged (derived overrides base)
        redis_config = resolved_config["configuration"]["redis"]
        assert redis_config["host"] == "localhost"
        assert redis_config["port"] == 6379
        assert redis_config["connection_pool_size"] == 20  # From derived template
    
    def test_circular_inheritance_detection(self, temp_templates_dir, security_manager):
        """Test detection of circular template inheritance."""
        # Create templates with circular inheritance
        template_a = {
            "name": "template_a",
            "version": "1.0.0",
            "extends": "template_b",
            "configuration": {}
        }
        
        template_b = {
            "name": "template_b", 
            "version": "1.0.0",
            "extends": "template_a",
            "configuration": {}
        }
        
        a_path = temp_templates_dir / "template_a.json"
        b_path = temp_templates_dir / "template_b.json"
        
        with open(a_path, 'w') as f:
            json.dump(template_a, f)
        with open(b_path, 'w') as f:
            json.dump(template_b, f)
        
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        template = manager.load_template("template_a")
        
        with pytest.raises(TemplateInheritanceError, match="Circular inheritance detected"):
            manager.resolve_template_inheritance(template)
    
    @pytest.mark.asyncio
    async def test_configuration_loading_performance(self, temp_templates_dir, 
                                                   sample_base_template, security_manager):
        """Test configuration loading meets <2ms performance requirement."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        # Pre-load template to ensure fair timing
        manager.load_template("base_template")
        
        # Time configuration generation
        start_time = time.perf_counter()
        config = await manager.generate_project_config(
            template_name="base_template",
            project_id="test_project",
            environment_overrides={}
        )
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        assert execution_time_ms < 2.0, f"Configuration loading took {execution_time_ms:.2f}ms, should be <2ms"
        assert config is not None
        assert "configuration" in config
        assert "logging" in config["configuration"]
    
    def test_template_validation_performance(self, temp_templates_dir, 
                                           sample_base_template, security_manager):
        """Test template validation meets <5ms performance requirement."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        template = manager.load_template("base_template")
        
        start_time = time.perf_counter()
        is_valid = manager.validate_template_schema(template, template.configuration)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        assert execution_time_ms < 5.0, f"Template validation took {execution_time_ms:.2f}ms, should be <5ms"
        assert is_valid is True
    
    def test_security_integration(self, temp_templates_dir, sample_base_template):
        """Test security integration with template operations."""
        # Mock security manager that raises security error
        mock_security = Mock(spec=MCPSecurityManager)
        mock_security.validate_mcp_request.side_effect = MCPSecurityError("Access denied")
        
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=mock_security
        )
        
        with pytest.raises(MCPSecurityError):
            manager.load_template_with_security("base_template", "test_project")
    
    def test_environment_override_application(self, temp_templates_dir, 
                                            sample_base_template, security_manager):
        """Test application of environment variable overrides."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        template = manager.load_template("base_template")
        
        overrides = {
            "LOG_LEVEL": "DEBUG",
            "REDIS_HOST": "redis-cluster.local"
        }
        
        resolved_config = manager.apply_environment_overrides(template, overrides)
        
        # Environment variables should be updated
        assert resolved_config["environment"]["LOG_LEVEL"] == "DEBUG"
        assert resolved_config["environment"]["REDIS_HOST"] == "redis-cluster.local"
    
    def test_invalid_template_schema(self, temp_templates_dir, security_manager):
        """Test handling of templates with invalid schema."""
        # Create template with invalid JSON schema
        invalid_template = {
            "name": "invalid_template",
            "version": "1.0.0", 
            "configuration": {
                "invalid_value": "not matching schema"
            },
            "validation_schema": {
                "type": "object",
                "properties": {
                    "required_field": {"type": "string"}
                },
                "required": ["required_field"]
            }
        }
        
        invalid_path = temp_templates_dir / "invalid_template.json"
        with open(invalid_path, 'w') as f:
            json.dump(invalid_template, f)
        
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        template = manager.load_template("invalid_template")
        
        # Should fail schema validation
        with pytest.raises(TemplateValidationError):
            manager.validate_template_schema(template, template.configuration)


class TestHotReloadFunctionality:
    """Test hot-reload functionality for configuration templates."""
    
    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary directory for test templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            templates_dir.mkdir()
            yield templates_dir
    
    @pytest.fixture 
    def security_manager(self):
        """Create mock security manager for testing."""
        mock_security = Mock(spec=MCPSecurityManager)
        mock_security.validate_mcp_request.return_value = {
            "success": True,
            "project_id": "test_project",
            "sanitized_input": None,
            "execution_time_ms": 1.0
        }
        return mock_security
    
    def test_file_watcher_setup(self, temp_templates_dir, security_manager):
        """Test file watcher is properly set up for template directory."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager,
            enable_hot_reload=True
        )
        
        # Should have file watcher for templates directory
        assert temp_templates_dir in manager._file_watchers
        watcher = manager._file_watchers[temp_templates_dir]
        assert watcher.is_alive()
    
    def test_template_change_detection(self, temp_templates_dir, security_manager):
        """Test detection of template file changes."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager,
            enable_hot_reload=True
        )
        
        # Create initial template
        template_data = {
            "name": "test_template",
            "version": "1.0.0",
            "configuration": {"value": "original"}
        }
        
        template_path = temp_templates_dir / "test_template.json"
        with open(template_path, 'w') as f:
            json.dump(template_data, f)
        
        # Load template into cache
        original_template = manager.load_template("test_template")
        assert original_template.configuration["value"] == "original"
        
        # Modify template file
        template_data["configuration"]["value"] = "modified"
        with open(template_path, 'w') as f:
            json.dump(template_data, f)
        
        # Wait for file system event processing
        time.sleep(0.2)
        
        # Template should be reloaded automatically
        modified_template = manager.load_template("test_template")
        assert modified_template.configuration["value"] == "modified"
    
    def test_hot_reload_performance(self, temp_templates_dir, security_manager):
        """Test hot-reload detection meets <100ms performance requirement."""
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager,
            enable_hot_reload=True
        )
        
        template_data = {
            "name": "perf_template",
            "version": "1.0.0",
            "configuration": {"timestamp": int(time.time())}
        }
        
        template_path = temp_templates_dir / "perf_template.json"
        with open(template_path, 'w') as f:
            json.dump(template_data, f)
        
        # Load initial template
        manager.load_template("perf_template")
        
        # Measure hot-reload time
        start_time = time.perf_counter()
        
        # Modify template
        template_data["configuration"]["timestamp"] = int(time.time()) + 1
        with open(template_path, 'w') as f:
            json.dump(template_data, f)
        
        # Wait for reload and measure
        time.sleep(0.05)  # Allow time for detection
        reloaded_template = manager.load_template("perf_template")
        
        end_time = time.perf_counter()
        
        reload_time_ms = (end_time - start_time) * 1000
        
        # Should detect and reload within 100ms
        assert reload_time_ms < 100.0, f"Hot-reload took {reload_time_ms:.2f}ms, should be <100ms"
        assert reloaded_template.configuration["timestamp"] == template_data["configuration"]["timestamp"]


class TestTemplateIntegrationEdgeCases:
    """Test edge cases and integration scenarios."""
    
    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary directory for test templates.""" 
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            templates_dir.mkdir()
            yield templates_dir
    
    @pytest.fixture
    def security_manager(self):
        """Create mock security manager for testing."""
        mock_security = Mock(spec=MCPSecurityManager)
        mock_security.validate_mcp_request.return_value = {
            "success": True,
            "project_id": "test_project", 
            "sanitized_input": None,
            "execution_time_ms": 1.0
        }
        return mock_security
    
    def test_deeply_nested_inheritance(self, temp_templates_dir, security_manager):
        """Test deeply nested template inheritance (3+ levels)."""
        # Create inheritance chain: level3 -> level2 -> level1 -> base
        templates = {
            "base": {
                "name": "base",
                "version": "1.0.0",
                "configuration": {"level": 0, "base_value": "base"}
            },
            "level1": {
                "name": "level1", 
                "version": "1.0.0",
                "extends": "base",
                "configuration": {"level": 1, "level1_value": "level1"}
            },
            "level2": {
                "name": "level2",
                "version": "1.0.0", 
                "extends": "level1",
                "configuration": {"level": 2, "level2_value": "level2"}
            },
            "level3": {
                "name": "level3",
                "version": "1.0.0",
                "extends": "level2", 
                "configuration": {"level": 3, "level3_value": "level3"}
            }
        }
        
        for name, data in templates.items():
            path = temp_templates_dir / f"{name}.json"
            with open(path, 'w') as f:
                json.dump(data, f)
        
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        level3_template = manager.load_template("level3")
        resolved_config = manager.resolve_template_inheritance(level3_template)
        
        config = resolved_config["configuration"]
        
        # Should have all values from inheritance chain
        assert config["base_value"] == "base"
        assert config["level1_value"] == "level1"
        assert config["level2_value"] == "level2"
        assert config["level3_value"] == "level3"
        assert config["level"] == 3  # Latest value wins
    
    def test_complex_environment_substitution(self, temp_templates_dir, security_manager):
        """Test complex environment variable substitution patterns."""
        template_data = {
            "name": "complex_env",
            "version": "1.0.0",
            "environment": {
                "BASE_DIR": "${PROJECT_ROOT}/app",
                "DATA_DIR": "${BASE_DIR}/data",
                "LOG_FILE": "${DATA_DIR}/logs/${SERVICE_NAME:ltmc}.log",
                "CONNECTION_STRING": "redis://${REDIS_HOST:localhost}:${REDIS_PORT:6379}/${REDIS_DB:0}"
            },
            "configuration": {}
        }
        
        template_path = temp_templates_dir / "complex_env.json"
        with open(template_path, 'w') as f:
            json.dump(template_data, f)
        
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        template = manager.load_template("complex_env")
        
        with patch.dict(os.environ, {
            "PROJECT_ROOT": "/opt/ltmc",
            "REDIS_HOST": "redis-cluster.local",
            "REDIS_DB": "5"
        }):
            resolved = template.resolve_environment_variables()
            
            assert resolved["BASE_DIR"] == "/opt/ltmc/app"
            assert resolved["DATA_DIR"] == "/opt/ltmc/app/data"
            assert resolved["LOG_FILE"] == "/opt/ltmc/app/data/logs/ltmc.log"
            assert resolved["CONNECTION_STRING"] == "redis://redis-cluster.local:6379/5"
    
    def test_template_with_malformed_json(self, temp_templates_dir, security_manager):
        """Test handling of malformed JSON template files."""
        malformed_path = temp_templates_dir / "malformed.json"
        with open(malformed_path, 'w') as f:
            f.write('{"name": "malformed", "invalid": json}')  # Invalid JSON
        
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        with pytest.raises(TemplateLoadError, match="JSON"):
            manager.load_template("malformed")
    
    def test_concurrent_template_access(self, temp_templates_dir, security_manager):
        """Test concurrent access to template loading and caching."""
        template_data = {
            "name": "concurrent_test",
            "version": "1.0.0",
            "configuration": {"value": "test"}
        }
        
        template_path = temp_templates_dir / "concurrent_test.json"
        with open(template_path, 'w') as f:
            json.dump(template_data, f)
        
        manager = ConfigTemplateManager(
            templates_dir=temp_templates_dir,
            security_manager=security_manager
        )
        
        # Simulate concurrent access
        import threading
        results = []
        errors = []
        
        def load_template():
            try:
                template = manager.load_template("concurrent_test")
                results.append(template.name)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=load_template) for _ in range(10)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(errors) == 0
        assert len(results) == 10
        assert all(name == "concurrent_test" for name in results)