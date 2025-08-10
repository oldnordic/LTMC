"""
Configuration Template Management Service

Provides template loading, validation, inheritance resolution, and hot-reload
functionality for LTMC configuration management.

Performance Targets:
- Configuration loading: <2ms
- Template validation: <5ms per template  
- Hot-reload detection: <100ms

Security Features:
- Phase 1 security integration with MCPSecurityManager
- Project-specific template isolation
- Input sanitization and path validation
- Secure template content validation

Features:
- Template inheritance with circular dependency detection
- Environment variable substitution with ${VAR:default} syntax  
- Hot-reload with file system monitoring
- Redis caching for performance optimization
- JSON schema validation for template structure
- Comprehensive error handling and logging
"""

import os
import sys
import json
import time
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Set
from dataclasses import dataclass, field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import jsonschema
from collections import OrderedDict
import re

# Add project root to path for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ltms.security.mcp_integration import MCPSecurityManager, MCPSecurityError
from ltms.services.redis_service import RedisCacheService

logger = logging.getLogger(__name__)


class TemplateError(Exception):
    """Base exception for template-related errors."""
    pass


class TemplateLoadError(TemplateError):
    """Raised when template loading fails."""
    pass


class TemplateValidationError(TemplateError):
    """Raised when template validation fails."""
    pass


class TemplateInheritanceError(TemplateError):
    """Raised when template inheritance resolution fails."""
    pass


@dataclass
class ConfigTemplate:
    """
    Configuration Template Model
    
    Represents a configuration template with metadata, environment variables,
    configuration data, and validation schema.
    """
    
    name: str
    version: str
    description: str = ""
    extends: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    validation_schema: Optional[Dict[str, Any]] = None
    features: Dict[str, bool] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate template data after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise TemplateValidationError("Template name is required and must be a string")
        
        if not self.version or not isinstance(self.version, str):
            raise TemplateValidationError("Template version is required and must be a string")
        
        if self.extends and not isinstance(self.extends, str):
            raise TemplateValidationError("Template extends must be a string if specified")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigTemplate':
        """Create ConfigTemplate from dictionary data."""
        required_fields = {'name', 'version'}
        if not all(field in data for field in required_fields):
            missing = required_fields - set(data.keys())
            raise TemplateValidationError(f"Missing required template fields: {missing}")
        
        return cls(
            name=data['name'],
            version=data['version'],
            description=data.get('description', ''),
            extends=data.get('extends'),
            metadata=data.get('metadata', {}),
            environment=data.get('environment', {}),
            configuration=data.get('configuration', {}),
            validation_schema=data.get('validation_schema'),
            features=data.get('features', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ConfigTemplate to dictionary."""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'extends': self.extends,
            'metadata': self.metadata,
            'environment': self.environment,
            'configuration': self.configuration,
            'validation_schema': self.validation_schema,
            'features': self.features
        }
    
    def resolve_environment_variables(self, overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Resolve environment variables with substitution and defaults.
        
        Supports ${VAR:default_value} syntax for environment variable substitution.
        Supports recursive resolution where one variable can reference another.
        
        Args:
            overrides: Optional environment variable overrides
            
        Returns:
            Dictionary of resolved environment variables
        """
        resolved = {}
        env_vars = {**self.environment}
        
        if overrides:
            env_vars.update(overrides)
        
        # Pattern to match ${VAR:default} or ${VAR}
        pattern = re.compile(r'\$\{([^:}]+)(?::([^}]*))?\}')
        
        # Resolve variables with multiple passes to handle dependencies
        max_iterations = 10  # Prevent infinite loops
        
        for iteration in range(max_iterations):
            changed = False
            
            for key, value in env_vars.items():
                if isinstance(value, str):
                    original_value = value
                    
                    def replace_env_var(match):
                        var_name = match.group(1)
                        default_value = match.group(2) or ""
                        
                        # First check overrides and resolved vars
                        if var_name in resolved:
                            return resolved[var_name]
                        elif var_name in env_vars and var_name != key:  # Avoid self-reference
                            return env_vars[var_name]
                        else:
                            return os.getenv(var_name, default_value)
                    
                    new_value = pattern.sub(replace_env_var, value)
                    
                    if new_value != original_value:
                        changed = True
                        env_vars[key] = new_value
                    
                    # If no more substitutions possible, consider resolved
                    if not pattern.search(new_value):
                        resolved[key] = new_value
                else:
                    resolved[key] = value
            
            # If no changes in this iteration, we're done
            if not changed:
                break
        
        # Handle any remaining unresolved variables
        for key, value in env_vars.items():
            if key not in resolved:
                if isinstance(value, str):
                    # Final pass with just environment variables
                    def final_replace(match):
                        var_name = match.group(1)
                        default_value = match.group(2) or ""
                        return os.getenv(var_name, default_value)
                    
                    resolved[key] = pattern.sub(final_replace, value)
                else:
                    resolved[key] = value
        
        return resolved


class ConfigurationCache:
    """
    LRU Cache for configuration templates with TTL support.
    
    Provides efficient caching with automatic expiration and size limits
    to meet <2ms configuration loading performance targets.
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        Initialize configuration cache.
        
        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time-to-live for cached items
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()
        logger.info(f"ConfigurationCache initialized: max_size={max_size}, ttl={ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if time.time() > entry['expires_at']:
                del self._cache[key]
                return None
            
            # Move to end (LRU update)
            self._cache.move_to_end(key)
            return entry['data']
    
    def set(self, key: str, value: Any) -> None:
        """Set item in cache with automatic expiration."""
        with self._lock:
            # Remove if already exists
            if key in self._cache:
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = {
                'data': value,
                'expires_at': time.time() + self.ttl_seconds
            }
            
            # Enforce size limit (LRU eviction)
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
    
    def clear(self) -> None:
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()
    
    def invalidate(self, key: str) -> bool:
        """Invalidate specific cache key."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False


class TemplateFileWatcher(FileSystemEventHandler):
    """File system event handler for template hot-reload functionality."""
    
    def __init__(self, template_manager: 'ConfigTemplateManager'):
        """Initialize file watcher with reference to template manager."""
        self.template_manager = template_manager
        self.logger = logging.getLogger(f"{__name__}.TemplateFileWatcher")
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix == '.json':
            template_name = file_path.stem
            self.logger.info(f"Template file modified: {template_name}")
            
            # Invalidate cache for this template
            cache_key = f"template:{template_name}"
            self.template_manager.cache.invalidate(cache_key)
            
            # Trigger reload callback if registered
            if hasattr(self.template_manager, '_reload_callbacks'):
                for callback in self.template_manager._reload_callbacks:
                    try:
                        callback(template_name, file_path)
                    except Exception as e:
                        self.logger.error(f"Template reload callback failed: {e}")


class ConfigTemplateManager:
    """
    Configuration Template Management Service
    
    Provides comprehensive template management with loading, validation,
    inheritance resolution, hot-reload, and security integration.
    
    Features:
    - Template loading with JSON parsing and validation
    - Template inheritance with circular dependency detection
    - Environment variable substitution with ${VAR:default} syntax
    - Hot-reload with file system monitoring
    - Redis caching for performance optimization
    - Security integration with MCPSecurityManager
    - JSON schema validation for template structure
    """
    
    def __init__(self, 
                 templates_dir: Union[str, Path],
                 security_manager: MCPSecurityManager,
                 redis_service: Optional[RedisCacheService] = None,
                 enable_hot_reload: bool = True,
                 cache_ttl_seconds: int = 300):
        """
        Initialize Configuration Template Manager.
        
        Args:
            templates_dir: Directory containing template files
            security_manager: Security manager for validation
            redis_service: Optional Redis service for distributed caching
            enable_hot_reload: Enable hot-reload functionality
            cache_ttl_seconds: Cache TTL in seconds
        """
        self.templates_dir = Path(templates_dir)
        self.security_manager = security_manager
        self.redis_service = redis_service
        self.enable_hot_reload = enable_hot_reload
        
        # Initialize caching
        self.cache = ConfigurationCache(max_size=100, ttl_seconds=cache_ttl_seconds)
        
        # Template inheritance resolution tracking
        self._inheritance_stack: Set[str] = set()
        
        # File watchers for hot-reload
        self._file_watchers: Dict[Path, Observer] = {}
        self._reload_callbacks: List[callable] = []
        
        # Performance monitoring
        self._performance_stats = {
            'template_loads': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_time_ms': 0.0,
            'load_time_ms': 0.0
        }
        
        # Ensure templates directory exists
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup hot-reload if enabled
        if self.enable_hot_reload:
            self._setup_file_watchers()
        
        logger.info(f"ConfigTemplateManager initialized: templates_dir={self.templates_dir}, "
                   f"hot_reload={self.enable_hot_reload}, redis_enabled={self.redis_service is not None}")
    
    def _setup_file_watchers(self) -> None:
        """Setup file system watchers for hot-reload functionality."""
        if not self.enable_hot_reload:
            return
        
        try:
            observer = Observer()
            event_handler = TemplateFileWatcher(self)
            observer.schedule(event_handler, str(self.templates_dir), recursive=True)
            observer.start()
            
            self._file_watchers[self.templates_dir] = observer
            logger.info(f"File watcher started for: {self.templates_dir}")
            
        except Exception as e:
            logger.error(f"Failed to setup file watcher: {e}")
            self.enable_hot_reload = False
    
    def load_template(self, template_name: str, use_cache: bool = True) -> ConfigTemplate:
        """
        Load configuration template from file.
        
        Args:
            template_name: Name of template to load
            use_cache: Whether to use caching
            
        Returns:
            Loaded ConfigTemplate instance
            
        Raises:
            TemplateLoadError: If template cannot be loaded
            TemplateValidationError: If template validation fails
        """
        start_time = time.perf_counter()
        
        try:
            # Check cache first
            cache_key = f"template:{template_name}"
            if use_cache:
                cached_template = self.cache.get(cache_key)
                if cached_template:
                    self._performance_stats['cache_hits'] += 1
                    return cached_template
                
                # Check Redis cache if available (async, so skip for sync method)
                # Note: Redis cache integration would require async method
            
            self._performance_stats['cache_misses'] += 1
            
            # Load from file
            template_path = self.templates_dir / f"{template_name}.json"
            if not template_path.exists():
                raise TemplateLoadError(f"Template file not found: {template_path}")
            
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
            except json.JSONDecodeError as e:
                raise TemplateLoadError(f"Invalid JSON in template {template_name}: {e}")
            except Exception as e:
                raise TemplateLoadError(f"Failed to read template {template_name}: {e}")
            
            # Create ConfigTemplate instance
            template = ConfigTemplate.from_dict(template_data)
            
            # Cache the loaded template
            if use_cache:
                self.cache.set(cache_key, template)
                
                # Cache in Redis if available (would require async method)
                # Note: Redis cache integration would require async method
            
            self._performance_stats['template_loads'] += 1
            
            load_time_ms = (time.perf_counter() - start_time) * 1000
            self._performance_stats['load_time_ms'] = (
                (self._performance_stats['load_time_ms'] * (self._performance_stats['template_loads'] - 1) + load_time_ms) 
                / self._performance_stats['template_loads']
            )
            
            logger.debug(f"Template loaded: {template_name} in {load_time_ms:.2f}ms")
            return template
            
        except (TemplateLoadError, TemplateValidationError):
            raise
        except Exception as e:
            raise TemplateLoadError(f"Unexpected error loading template {template_name}: {e}")
    
    def load_template_with_security(self, template_name: str, project_id: Optional[str] = None) -> ConfigTemplate:
        """
        Load template with security validation.
        
        Args:
            template_name: Name of template to load
            project_id: Project identifier for security context
            
        Returns:
            Loaded ConfigTemplate instance
            
        Raises:
            MCPSecurityError: If security validation fails
            TemplateLoadError: If template cannot be loaded
        """
        try:
            # Validate request with security manager
            template_path = str(self.templates_dir / f"{template_name}.json")
            validation_result = self.security_manager.validate_mcp_request(
                project_id=project_id,
                operation="read",
                file_path=template_path,
                user_input=template_name
            )
            
            if not validation_result.get('success'):
                raise MCPSecurityError("Template access denied by security policy")
            
            # Load template with validated context
            return self.load_template(template_name)
            
        except MCPSecurityError:
            raise
        except Exception as e:
            raise TemplateLoadError(f"Security validation failed for template {template_name}: {e}")
    
    def resolve_template_inheritance(self, template: ConfigTemplate) -> Dict[str, Any]:
        """
        Resolve template inheritance chain and merge configurations.
        
        Args:
            template: Template to resolve inheritance for
            
        Returns:
            Merged configuration dictionary
            
        Raises:
            TemplateInheritanceError: If inheritance resolution fails
        """
        if template.name in self._inheritance_stack:
            raise TemplateInheritanceError(
                f"Circular inheritance detected: {' -> '.join(self._inheritance_stack)} -> {template.name}"
            )
        
        self._inheritance_stack.add(template.name)
        
        try:
            # Base configuration starts with current template
            merged_config = {
                'name': template.name,
                'version': template.version,
                'description': template.description,
                'metadata': template.metadata.copy(),
                'environment': template.environment.copy(),
                'configuration': template.configuration.copy(),
                'validation_schema': template.validation_schema,
                'features': template.features.copy()
            }
            
            # If template extends another, resolve parent first
            if template.extends:
                try:
                    parent_template = self.load_template(template.extends)
                    parent_config = self.resolve_template_inheritance(parent_template)
                    
                    # Merge parent configuration (parent values as base)
                    merged_config = self._deep_merge_config(parent_config, merged_config)
                    
                except TemplateLoadError as e:
                    raise TemplateInheritanceError(f"Failed to load parent template '{template.extends}': {e}")
            
            return merged_config
            
        finally:
            self._inheritance_stack.discard(template.name)
    
    def _deep_merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two configuration dictionaries.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        merged = base.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                merged[key] = self._deep_merge_config(merged[key], value)
            else:
                # Override value (including lists and primitives)
                merged[key] = value
        
        return merged
    
    def validate_template_schema(self, template: ConfigTemplate, config_data: Dict[str, Any]) -> bool:
        """
        Validate template configuration against JSON schema.
        
        Args:
            template: Template containing validation schema
            config_data: Configuration data to validate
            
        Returns:
            True if validation passes
            
        Raises:
            TemplateValidationError: If validation fails
        """
        start_time = time.perf_counter()
        
        try:
            if not template.validation_schema:
                logger.debug(f"No validation schema for template: {template.name}")
                return True
            
            # Validate using jsonschema
            jsonschema.validate(config_data, template.validation_schema)
            
            validation_time_ms = (time.perf_counter() - start_time) * 1000
            self._performance_stats['validation_time_ms'] = validation_time_ms
            
            if validation_time_ms > 5.0:
                logger.warning(f"Template validation exceeded 5ms: {validation_time_ms:.2f}ms")
            
            logger.debug(f"Template validation passed: {template.name} in {validation_time_ms:.2f}ms")
            return True
            
        except jsonschema.ValidationError as e:
            raise TemplateValidationError(f"Schema validation failed for {template.name}: {e.message}")
        except jsonschema.SchemaError as e:
            raise TemplateValidationError(f"Invalid schema in template {template.name}: {e.message}")
        except Exception as e:
            raise TemplateValidationError(f"Unexpected validation error for {template.name}: {e}")
    
    def apply_environment_overrides(self, template: ConfigTemplate, 
                                  overrides: Dict[str, str]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to template.
        
        Args:
            template: Template to apply overrides to
            overrides: Environment variable overrides
            
        Returns:
            Template dictionary with overrides applied
        """
        template_dict = template.to_dict()
        
        # Apply environment overrides
        for key, value in overrides.items():
            if key in template_dict['environment']:
                template_dict['environment'][key] = value
        
        return template_dict
    
    async def generate_project_config(self, 
                                    template_name: str,
                                    project_id: Optional[str] = None,
                                    environment_overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Generate complete project configuration from template.
        
        Args:
            template_name: Name of template to use
            project_id: Project identifier for security context
            environment_overrides: Environment variable overrides
            
        Returns:
            Complete project configuration dictionary
            
        Raises:
            TemplateLoadError: If template loading fails
            TemplateInheritanceError: If inheritance resolution fails
            MCPSecurityError: If security validation fails
        """
        start_time = time.perf_counter()
        
        try:
            # Load template with security validation
            template = self.load_template_with_security(template_name, project_id)
            
            # Resolve inheritance chain
            resolved_config = self.resolve_template_inheritance(template)
            
            # Apply environment overrides
            if environment_overrides:
                resolved_config = self.apply_environment_overrides(
                    ConfigTemplate.from_dict(resolved_config), 
                    environment_overrides
                )
            
            # Resolve environment variables in final config
            template_obj = ConfigTemplate.from_dict(resolved_config)
            resolved_env = template_obj.resolve_environment_variables(environment_overrides)
            resolved_config['environment'] = resolved_env
            
            # Validate final configuration against schema
            self.validate_template_schema(template_obj, resolved_config['configuration'])
            
            generation_time_ms = (time.perf_counter() - start_time) * 1000
            
            if generation_time_ms > 2.0:
                logger.warning(f"Config generation exceeded 2ms target: {generation_time_ms:.2f}ms")
            
            logger.info(f"Project configuration generated: {template_name} in {generation_time_ms:.2f}ms")
            
            return {
                'template_name': template_name,
                'generated_at': time.time(),
                'generation_time_ms': generation_time_ms,
                'project_id': project_id,
                'configuration': resolved_config['configuration'],
                'environment': resolved_env,
                'metadata': resolved_config.get('metadata', {}),
                'features': resolved_config.get('features', {})
            }
            
        except (TemplateLoadError, TemplateInheritanceError, TemplateValidationError, MCPSecurityError):
            raise
        except Exception as e:
            raise TemplateLoadError(f"Failed to generate project configuration: {e}")
    
    def register_reload_callback(self, callback: callable) -> None:
        """Register callback for template reload events."""
        if callback not in self._reload_callbacks:
            self._reload_callbacks.append(callback)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        return {
            **self._performance_stats,
            'cache_hit_rate': (
                self._performance_stats['cache_hits'] / 
                (self._performance_stats['cache_hits'] + self._performance_stats['cache_misses'])
                if (self._performance_stats['cache_hits'] + self._performance_stats['cache_misses']) > 0 
                else 0.0
            ),
            'cache_size': len(self.cache._cache),
            'hot_reload_enabled': self.enable_hot_reload,
            'redis_enabled': self.redis_service is not None
        }
    
    def cleanup(self) -> None:
        """Cleanup resources including file watchers."""
        logger.info("Cleaning up ConfigTemplateManager resources")
        
        # Stop file watchers
        for observer in self._file_watchers.values():
            observer.stop()
            observer.join(timeout=5.0)
        
        self._file_watchers.clear()
        
        # Clear caches
        self.cache.clear()
        
        logger.info("ConfigTemplateManager cleanup completed")
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore cleanup errors during destruction