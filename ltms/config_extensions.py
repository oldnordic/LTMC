"""
Configuration Extensions for Template Management

Extends the existing configuration system to support template-based configuration
management with hot-reload and inheritance capabilities.

This module integrates the ConfigTemplateManager with the existing Config class
to provide backward compatibility while adding new template features.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ltms.config import Config
from ltms.services.config_template_service import (
    ConfigTemplateManager,
    ConfigTemplate,
    TemplateLoadError
)
from ltms.security.mcp_integration import get_mcp_security_manager

logger = logging.getLogger(__name__)


class EnhancedConfig(Config):
    """
    Enhanced Configuration class with template management support.
    
    Extends the base Config class with template-based configuration loading,
    environment variable resolution, and hot-reload capabilities.
    """
    
    _template_manager: Optional[ConfigTemplateManager] = None
    _active_template: Optional[str] = None
    
    @classmethod
    def initialize_template_manager(cls, templates_dir: Optional[Path] = None, enable_hot_reload: bool = True):
        """
        Initialize configuration template manager.
        
        Args:
            templates_dir: Directory containing template files
            enable_hot_reload: Enable hot-reload functionality
        """
        if cls._template_manager is not None:
            return  # Already initialized
        
        if templates_dir is None:
            # Use default templates directory
            templates_dir = Path(__file__).parent.parent / "config" / "templates"
        
        # Get security manager
        security_manager = get_mcp_security_manager()
        
        # Initialize template manager
        cls._template_manager = ConfigTemplateManager(
            templates_dir=templates_dir,
            security_manager=security_manager,
            redis_service=None,  # Will be connected later if needed
            enable_hot_reload=enable_hot_reload,
            cache_ttl_seconds=300
        )
        
        logger.info(f"Template manager initialized: {templates_dir}")
    
    @classmethod
    def load_from_template(cls, template_name: str, project_id: Optional[str] = None, 
                          environment_overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Load configuration from template with inheritance and environment resolution.
        
        Args:
            template_name: Name of template to load
            project_id: Project identifier for security context
            environment_overrides: Environment variable overrides
            
        Returns:
            Complete configuration dictionary
            
        Raises:
            TemplateLoadError: If template cannot be loaded
        """
        if cls._template_manager is None:
            cls.initialize_template_manager()
        
        try:
            # Load template with security validation
            template = cls._template_manager.load_template_with_security(template_name, project_id)
            
            # Resolve inheritance chain
            resolved_config = cls._template_manager.resolve_template_inheritance(template)
            
            # Apply environment overrides
            if environment_overrides:
                resolved_config = cls._template_manager.apply_environment_overrides(
                    ConfigTemplate.from_dict(resolved_config), 
                    environment_overrides
                )
            
            # Resolve environment variables
            template_obj = ConfigTemplate.from_dict(resolved_config)
            resolved_env = template_obj.resolve_environment_variables(environment_overrides)
            
            # Validate configuration against schema
            if template_obj.validation_schema:
                cls._template_manager.validate_template_schema(template_obj, resolved_config['configuration'])
            
            cls._active_template = template_name
            logger.info(f"Configuration loaded from template: {template_name}")
            
            return {
                'template_name': template_name,
                'configuration': resolved_config['configuration'],
                'environment': resolved_env,
                'metadata': resolved_config.get('metadata', {}),
                'features': resolved_config.get('features', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to load configuration from template {template_name}: {e}")
            raise TemplateLoadError(f"Template loading failed: {e}")
    
    @classmethod
    def apply_template_config(cls, template_name: str, project_id: Optional[str] = None,
                             environment_overrides: Optional[Dict[str, str]] = None):
        """
        Apply template configuration to the current Config class.
        
        This updates the class attributes with values from the template,
        providing backward compatibility with existing code.
        
        Args:
            template_name: Name of template to apply
            project_id: Project identifier for security context
            environment_overrides: Environment variable overrides
        """
        config_data = cls.load_from_template(template_name, project_id, environment_overrides)
        
        # Apply template configuration to class attributes
        template_config = config_data['configuration']
        template_env = config_data['environment']
        
        # Update database configuration
        if 'database' in template_config:
            db_config = template_config['database']
            if 'connection_timeout' in db_config:
                # Note: Would need to add these attributes to base Config class
                pass
        
        # Update environment variables with resolved values
        for key, value in template_env.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
        
        logger.info(f"Template configuration applied: {template_name}")
    
    @classmethod
    def get_active_template(cls) -> Optional[str]:
        """Get the currently active template name."""
        return cls._active_template
    
    @classmethod
    def reload_template(cls, project_id: Optional[str] = None):
        """Reload the currently active template."""
        if cls._active_template:
            cls.apply_template_config(cls._active_template, project_id)
            logger.info(f"Template reloaded: {cls._active_template}")
    
    @classmethod
    def get_template_manager(cls) -> Optional[ConfigTemplateManager]:
        """Get the template manager instance."""
        return cls._template_manager
    
    @classmethod
    def cleanup_template_manager(cls):
        """Cleanup template manager resources."""
        if cls._template_manager:
            cls._template_manager.cleanup()
            cls._template_manager = None
            cls._active_template = None
            logger.info("Template manager cleaned up")


# Initialize enhanced configuration on import for backward compatibility
enhanced_config = EnhancedConfig()

# Export commonly used functions for convenience
def load_project_config(template_name: str, project_id: Optional[str] = None, 
                       environment_overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Convenience function to load project configuration from template.
    
    Args:
        template_name: Name of template to load
        project_id: Project identifier for security context
        environment_overrides: Environment variable overrides
        
    Returns:
        Complete configuration dictionary
    """
    return EnhancedConfig.load_from_template(template_name, project_id, environment_overrides)


def apply_project_template(template_name: str, project_id: Optional[str] = None,
                          environment_overrides: Optional[Dict[str, str]] = None):
    """
    Convenience function to apply template configuration.
    
    Args:
        template_name: Name of template to apply
        project_id: Project identifier for security context
        environment_overrides: Environment variable overrides
    """
    EnhancedConfig.apply_template_config(template_name, project_id, environment_overrides)


def get_template_manager() -> Optional[ConfigTemplateManager]:
    """Get the global template manager instance."""
    return EnhancedConfig.get_template_manager()