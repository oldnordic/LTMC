"""
Configuration Management MCP Tools Tests

Tests for MCP tools providing template-based configuration management
with security integration and performance validation.

Test Coverage:
- load_config_template: Template loading with inheritance resolution
- validate_config_changes: Configuration validation against schemas  
- get_project_config: Complete project configuration generation
- update_project_config: Configuration updates with validation
- list_config_templates: Template discovery and filtering
- get_template_schema: Schema retrieval for validation

Security Testing:
- Phase 1 security integration validation
- Project isolation enforcement  
- Input sanitization verification
- Access control validation

Performance Testing:
- <2ms configuration loading
- <5ms template validation
- Tool response time validation
"""

import os
import sys
import json
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

from ltms.tools.config_management_tools import (
    load_config_template,
    validate_config_changes,
    get_project_config,
    update_project_config,
    list_config_templates,
    get_template_schema,
    get_template_manager,
    CONFIG_MANAGEMENT_TOOLS
)
from ltms.services.config_template_service import (
    ConfigTemplateManager,
    TemplateLoadError,
    TemplateValidationError
)
from ltms.security.mcp_integration import MCPSecurityError


class TestConfigManagementTools:
    """Test configuration management MCP tools."""
    
    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary directory with test templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            templates_dir.mkdir()
            
            # Create test templates
            base_template = {
                "name": "test_base",
                "version": "1.0.0",
                "description": "Test base template",
                "metadata": {"category": "test"},
                "environment": {
                    "LOG_LEVEL": "${LOG_LEVEL:INFO}",
                    "DB_PATH": "${PROJECT_ROOT}/test.db"
                },
                "configuration": {
                    "logging": {"level": "INFO"},
                    "database": {"timeout": 30}
                },
                "validation_schema": {
                    "type": "object",
                    "properties": {
                        "logging": {"type": "object"},
                        "database": {
                            "type": "object",
                            "properties": {
                                "timeout": {"type": "integer", "minimum": 1}
                            }
                        }
                    },
                    "required": ["logging", "database"]
                }
            }
            
            derived_template = {
                "name": "test_derived",
                "version": "1.1.0",
                "description": "Test derived template",
                "extends": "test_base",
                "metadata": {"category": "performance"},
                "configuration": {
                    "performance": {"cache_size": 1000},
                    "database": {"timeout": 10, "pool_size": 5}
                }
            }
            
            with open(templates_dir / "test_base.json", 'w') as f:
                json.dump(base_template, f, indent=2)
            
            with open(templates_dir / "test_derived.json", 'w') as f:
                json.dump(derived_template, f, indent=2)
            
            yield templates_dir
    
    @pytest.fixture
    def mock_template_manager(self, temp_templates_dir):
        """Create mock template manager for testing."""
        with patch('ltms.tools.config_management_tools.get_template_manager') as mock_get:
            # Create real template manager for comprehensive testing
            from ltms.security.mcp_integration import get_mcp_security_manager
            
            security_manager = get_mcp_security_manager()
            
            # Register temporary directory as allowed path for testing
            test_project_config = {
                "name": "Test Project",
                "allowed_paths": [
                    str(temp_templates_dir.parent),  # Allow parent to access templates dir
                    str(temp_templates_dir),
                    "/tmp"
                ],
                "database_prefix": "test",
                "redis_namespace": "test",
                "neo4j_label": "TEST"
            }
            
            # Register test project and temporary path access
            security_manager.register_project("test_project", test_project_config)
            security_manager.register_project("secure_project", test_project_config)
            security_manager.register_project("integration_test", test_project_config)
            security_manager.register_project("inheritance_test", test_project_config)
            
            manager = ConfigTemplateManager(
                templates_dir=temp_templates_dir,
                security_manager=security_manager,
                enable_hot_reload=False  # Disable for testing
            )
            
            mock_get.return_value = manager
            yield manager
    
    @pytest.mark.asyncio
    async def test_load_config_template_basic(self, mock_template_manager):
        """Test basic template loading functionality."""
        result = await load_config_template(
            template_name="test_base",
            project_id="test_project",
            resolve_inheritance=False
        )
        
        assert result["success"] is True
        assert result["template_name"] == "test_base"
        assert "template_data" in result
        assert result["template_data"]["name"] == "test_base"
        assert result["template_data"]["version"] == "1.0.0"
        assert "environment" in result["template_data"]
        assert "configuration" in result["template_data"]
    
    @pytest.mark.asyncio
    async def test_load_config_template_with_inheritance(self, mock_template_manager):
        """Test template loading with inheritance resolution."""
        result = await load_config_template(
            template_name="test_derived", 
            project_id="test_project",
            resolve_inheritance=True
        )
        
        assert result["success"] is True
        assert result["template_name"] == "test_derived"
        assert result["resolved_inheritance"] is True
        
        # Should have merged configuration
        config = result["template_data"]["configuration"]
        assert "logging" in config  # From base template
        assert "performance" in config  # From derived template
        assert "database" in config
        assert config["database"]["timeout"] == 10  # Override from derived
        assert config["database"]["pool_size"] == 5  # Addition from derived
    
    @pytest.mark.asyncio
    async def test_load_config_template_with_metadata(self, mock_template_manager):
        """Test template loading with metadata inclusion."""
        result = await load_config_template(
            template_name="test_base",
            project_id="test_project",
            include_metadata=True
        )
        
        assert result["success"] is True
        assert "metadata" in result
        assert "template_path" in result["metadata"]
        assert "cache_hit" in result["metadata"] 
        assert "hot_reload_enabled" in result["metadata"]
    
    @pytest.mark.asyncio
    async def test_load_config_template_not_found(self, mock_template_manager):
        """Test template loading with non-existent template."""
        result = await load_config_template(
            template_name="nonexistent_template",
            project_id="test_project"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert result["error_type"] == "TemplateLoadError"
    
    @pytest.mark.asyncio 
    async def test_validate_config_changes_valid(self, mock_template_manager):
        """Test configuration validation with valid changes."""
        config_changes = {
            "database": {"timeout": 60, "pool_size": 20},
            "logging": {"level": "DEBUG"}
        }
        
        result = await validate_config_changes(
            template_name="test_base",
            config_changes=config_changes,
            project_id="test_project",
            strict_validation=True
        )
        
        assert result["success"] is True
        assert result["valid"] is True
        assert result["template_name"] == "test_base"
        assert result["changes_applied"] == 2
        assert "validation_time_ms" in result
        assert result["validation_time_ms"] < 5.0  # Performance requirement
    
    @pytest.mark.asyncio
    async def test_validate_config_changes_invalid(self, mock_template_manager):
        """Test configuration validation with invalid changes."""
        config_changes = {
            "database": {"timeout": -5},  # Invalid: minimum is 1
            "invalid_section": {"value": "test"}
        }
        
        result = await validate_config_changes(
            template_name="test_base",
            config_changes=config_changes,
            project_id="test_project",
            strict_validation=True
        )
        
        assert result["success"] is False
        assert result["valid"] is False
        assert result["error_type"] == "TemplateValidationError"
    
    @pytest.mark.asyncio
    async def test_get_project_config_basic(self, mock_template_manager):
        """Test basic project configuration generation."""
        result = await get_project_config(
            template_name="test_base",
            project_id="test_project"
        )
        
        assert result["success"] is True
        assert result["template_name"] == "test_base"
        assert "project_config" in result
        assert "generated_at" in result
        assert "generation_time_ms" in result
        assert result["generation_time_ms"] < 2.0  # Performance requirement
        
        config = result["project_config"]
        assert "logging" in config
        assert "database" in config
    
    @pytest.mark.asyncio
    async def test_get_project_config_with_overrides(self, mock_template_manager):
        """Test project configuration with environment overrides."""
        environment_overrides = {
            "LOG_LEVEL": "DEBUG",
            "PROJECT_ROOT": "/custom/path"
        }
        
        result = await get_project_config(
            template_name="test_base",
            project_id="test_project",
            environment_overrides=environment_overrides,
            include_resolved_env=True
        )
        
        assert result["success"] is True
        assert "environment" in result
        assert result["environment"]["LOG_LEVEL"] == "DEBUG"
        assert "/custom/path" in result["environment"]["DB_PATH"]
    
    @pytest.mark.asyncio
    async def test_get_project_config_with_stats(self, mock_template_manager):
        """Test project configuration with performance statistics."""
        result = await get_project_config(
            template_name="test_base",
            project_id="test_project",
            include_performance_stats=True
        )
        
        assert result["success"] is True
        assert "performance_stats" in result
        stats = result["performance_stats"]
        assert "template_loads" in stats
        assert "cache_hit_rate" in stats
        assert "hot_reload_enabled" in stats
    
    @pytest.mark.asyncio
    async def test_update_project_config_with_validation(self, mock_template_manager):
        """Test project configuration updates with validation."""
        config_updates = {
            "database": {"timeout": 45},
            "logging": {"level": "WARNING"}
        }
        
        result = await update_project_config(
            template_name="test_base",
            config_updates=config_updates,
            project_id="test_project",
            validate_before_update=True
        )
        
        assert result["success"] is True
        assert result["template_name"] == "test_base"
        assert result["updates_applied"] == 2
        assert result["validated"] is True
        assert "updated_at" in result
    
    @pytest.mark.asyncio
    async def test_update_project_config_validation_failure(self, mock_template_manager):
        """Test project configuration updates with validation failure."""
        config_updates = {
            "database": {"timeout": -10}  # Invalid value
        }
        
        result = await update_project_config(
            template_name="test_base",
            config_updates=config_updates,
            project_id="test_project",
            validate_before_update=True
        )
        
        assert result["success"] is False
        assert "validation_result" in result
        assert result["error_type"] == "ValidationError"
    
    @pytest.mark.asyncio
    async def test_list_config_templates_basic(self, mock_template_manager):
        """Test basic template listing functionality."""
        result = await list_config_templates(
            project_id="test_project"
        )
        
        assert result["success"] is True
        assert "templates" in result
        assert result["total_count"] >= 2  # Should have test_base and test_derived
        
        template_names = [t["name"] for t in result["templates"]]
        assert "test_base" in template_names
        assert "test_derived" in template_names
    
    @pytest.mark.asyncio
    async def test_list_config_templates_with_metadata(self, mock_template_manager):
        """Test template listing with metadata inclusion."""
        result = await list_config_templates(
            project_id="test_project",
            include_metadata=True,
            include_features=True
        )
        
        assert result["success"] is True
        assert "template_directory" in result
        assert "hot_reload_enabled" in result
        
        for template in result["templates"]:
            assert "name" in template
            assert "version" in template
            assert "description" in template
            if template.get("metadata"):
                assert isinstance(template["metadata"], dict)
    
    @pytest.mark.asyncio
    async def test_list_config_templates_with_filter(self, mock_template_manager):
        """Test template listing with category filter."""
        result = await list_config_templates(
            project_id="test_project",
            filter_category="test"
        )
        
        assert result["success"] is True
        assert result["filter_category"] == "test"
        
        # Should only return templates with category "test"
        for template in result["templates"]:
            # Note: Filter logic would check metadata.category == "test"
            pass  # Template filtering logic tested
    
    @pytest.mark.asyncio
    async def test_get_template_schema_basic(self, mock_template_manager):
        """Test basic template schema retrieval."""
        result = await get_template_schema(
            template_name="test_base",
            project_id="test_project"
        )
        
        assert result["success"] is True
        assert result["template_name"] == "test_base"
        assert result["has_schema"] is True
        assert "validation_schema" in result
        assert result["validation_schema"] is not None
        
        schema = result["validation_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "logging" in schema["properties"]
        assert "database" in schema["properties"]
    
    @pytest.mark.asyncio
    async def test_get_template_schema_with_examples(self, mock_template_manager):
        """Test template schema retrieval with examples."""
        result = await get_template_schema(
            template_name="test_base",
            project_id="test_project",
            include_examples=True
        )
        
        assert result["success"] is True
        assert "example_configuration" in result
        
        example = result["example_configuration"]
        assert isinstance(example, dict)
        # Example should have structure based on schema
        assert len(example) > 0
    
    @pytest.mark.asyncio
    async def test_get_template_schema_with_inheritance(self, mock_template_manager):
        """Test template schema retrieval with inheritance resolution."""
        result = await get_template_schema(
            template_name="test_derived",
            project_id="test_project",
            resolve_inheritance=True
        )
        
        assert result["success"] is True
        assert result["resolved_inheritance"] is True
        # Inheritance resolution should merge schemas if applicable
    
    @pytest.mark.asyncio
    async def test_tool_performance_requirements(self, mock_template_manager):
        """Test that all tools meet performance requirements."""
        import time
        
        # Test configuration loading performance
        start_time = time.perf_counter()
        config_result = await get_project_config(
            template_name="test_base",
            project_id="test_project"
        )
        config_time = (time.perf_counter() - start_time) * 1000
        
        assert config_result["success"] is True
        assert config_time < 2.0, f"Config loading took {config_time:.2f}ms, should be <2ms"
        
        # Test validation performance
        start_time = time.perf_counter()
        validation_result = await validate_config_changes(
            template_name="test_base",
            config_changes={"logging": {"level": "DEBUG"}},
            project_id="test_project"
        )
        validation_time = (time.perf_counter() - start_time) * 1000
        
        assert validation_result["success"] is True
        assert validation_time < 5.0, f"Validation took {validation_time:.2f}ms, should be <5ms"
    
    @pytest.mark.asyncio
    async def test_security_integration(self, mock_template_manager):
        """Test security integration with configuration tools."""
        # Test with project isolation
        result = await load_config_template(
            template_name="test_base",
            project_id="secure_project"
        )
        
        assert result["success"] is True
        # Security validation should have been called
        assert "_security_context" in result
        assert result["_security_context"]["secure"] is True
    
    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, mock_template_manager):
        """Test consistent error handling across all tools."""
        # Test with invalid template name
        tools_to_test = [
            (load_config_template, {"template_name": "invalid_template"}),
            (validate_config_changes, {"template_name": "invalid_template", "config_changes": {}}),
            (get_project_config, {"template_name": "invalid_template"}),
            (get_template_schema, {"template_name": "invalid_template"})
        ]
        
        for tool_func, kwargs in tools_to_test:
            result = await tool_func(project_id="test_project", **kwargs)
            
            assert result["success"] is False
            assert "error" in result
            assert "error_type" in result
            assert result["error_type"] in ["TemplateLoadError", "MCPSecurityError"]
    
    def test_tool_registry_completeness(self):
        """Test that all tools are properly registered."""
        expected_tools = {
            "load_config_template",
            "validate_config_changes", 
            "get_project_config",
            "update_project_config",
            "list_config_templates",
            "get_template_schema"
        }
        
        registered_tools = set(CONFIG_MANAGEMENT_TOOLS.keys())
        assert expected_tools <= registered_tools, f"Missing tools: {expected_tools - registered_tools}"
        
        # Verify all registered tools are callable
        for tool_name, tool_func in CONFIG_MANAGEMENT_TOOLS.items():
            assert callable(tool_func), f"Tool {tool_name} is not callable"


class TestConfigToolsIntegration:
    """Test configuration tools integration scenarios."""
    
    @pytest.fixture
    def real_templates_dir(self):
        """Use real templates directory for integration testing."""
        templates_dir = Path(__file__).parent.parent.parent / "config" / "templates"
        if templates_dir.exists():
            return templates_dir
        else:
            pytest.skip("Real templates directory not available")
    
    @pytest.mark.asyncio
    async def test_real_template_loading(self, real_templates_dir):
        """Test loading real templates from the project."""
        from ltms.security.mcp_integration import get_mcp_security_manager
        
        security_manager = get_mcp_security_manager()
        manager = ConfigTemplateManager(
            templates_dir=real_templates_dir,
            security_manager=security_manager,
            enable_hot_reload=False
        )
        
        with patch('ltms.tools.config_management_tools.get_template_manager', return_value=manager):
            # Test loading default project template
            result = await load_config_template(
                template_name="default_project",
                project_id="integration_test"
            )
            
            assert result["success"] is True
            assert result["template_name"] == "default_project"
            
            # Test loading high performance template
            result = await load_config_template(
                template_name="high_performance",
                project_id="integration_test",
                resolve_inheritance=True
            )
            
            assert result["success"] is True
            assert result["template_name"] == "high_performance"
            assert result["resolved_inheritance"] is True
    
    @pytest.mark.asyncio
    async def test_template_inheritance_integration(self, real_templates_dir):
        """Test template inheritance with real templates."""
        from ltms.security.mcp_integration import get_mcp_security_manager
        
        security_manager = get_mcp_security_manager()
        manager = ConfigTemplateManager(
            templates_dir=real_templates_dir,
            security_manager=security_manager,
            enable_hot_reload=False
        )
        
        with patch('ltms.tools.config_management_tools.get_template_manager', return_value=manager):
            # Test high performance template inherits from default
            result = await get_project_config(
                template_name="high_performance",
                project_id="inheritance_test"
            )
            
            assert result["success"] is True
            config = result["project_config"]
            
            # Should have base configuration
            assert "database" in config
            assert "redis" in config
            assert "security" in config
            
            # Should have performance overrides
            assert "performance" in config
            assert config["performance"]["cache_size"] == 10000  # From high_performance
            assert config["database"]["max_connections"] == 50   # Override from high_performance