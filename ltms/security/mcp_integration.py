"""
LTMC MCP Security Integration

Provides security validation decorators and middleware for MCP server integration.
Integrates ProjectIsolationManager and SecurePathValidator into MCP request flow.

Performance Target: <10ms total security overhead per request
Security Focus: Complete project isolation and path validation
Integration: Seamless integration with existing 28 MCP tools

This module provides the security layer that wraps around MCP tool execution
to enforce project boundaries and prevent security attacks.
"""

import os
import sys
import time
import logging
import functools
from typing import Dict, Any, Optional, Callable, Union
from pathlib import Path

# Add project root to path for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ltms.security.project_isolation import ProjectIsolationManager, SecurityError as IsolationSecurityError
from ltms.security.path_security import SecurePathValidator, SecurityError as PathSecurityError

logger = logging.getLogger(__name__)


class MCPSecurityError(Exception):
    """Raised when MCP security validation fails."""
    pass


class MCPSecurityManager:
    """
    MCP Security Manager for LTMC
    
    Provides unified security validation for all MCP tool operations:
    - Project isolation enforcement
    - Path security validation
    - Performance monitoring
    - Backward compatibility with existing tools
    
    Integration Pattern:
    1. Optional project_id parameter on all tools
    2. Security validation before tool execution
    3. Project-scoped resource access
    4. <10ms performance target maintained
    """
    
    def __init__(self, project_root: Union[str, Path], secure_root: Union[str, Path]):
        """
        Initialize MCP Security Manager.
        
        Args:
            project_root: Root directory for project operations
            secure_root: Root directory for secure operations
        """
        self.project_isolation = ProjectIsolationManager(project_root)
        self.path_validator = SecurePathValidator(secure_root)
        
        # Register default project for backward compatibility
        self._register_default_project()
        
        # Performance monitoring
        self.validation_stats = {
            "total_validations": 0,
            "security_failures": 0,
            "average_time_ms": 0.0,
            "max_time_ms": 0.0
        }
        
        logger.info("MCPSecurityManager initialized with project isolation and path validation")
    
    def _register_default_project(self):
        """Register the default project for backward compatibility."""
        default_config = {
            "name": "Default LTMC Project",
            "allowed_paths": [
                str(Path.cwd()),
                "/tmp/ltmc",
                str(Path.home() / "Projects" / "lmtc"),
                str(Path.home() / ".ltmc"),
            ],
            "database_prefix": "ltmc",
            "redis_namespace": "ltmc",
            "neo4j_label": "LTMC"
        }
        
        try:
            self.project_isolation.register_project("default", default_config)
            logger.info("Default project registered for backward compatibility")
        except Exception as e:
            logger.error(f"Failed to register default project: {e}")
    
    def validate_mcp_request(self, 
                           project_id: Optional[str], 
                           operation: str, 
                           file_path: Optional[str] = None,
                           user_input: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate MCP request for security compliance.
        
        Args:
            project_id: Project identifier (None = default project)
            operation: Operation being performed
            file_path: File path if applicable
            user_input: User input if applicable
            
        Returns:
            Validation result with security context
            
        Raises:
            MCPSecurityError: If validation fails
        """
        start_time = time.perf_counter()
        
        try:
            # Use default project if none specified (backward compatibility)
            if project_id is None:
                project_id = "default"
            
            # Project isolation validation
            if file_path:
                try:
                    self.project_isolation.validate_project_access(project_id, operation, file_path)
                except IsolationSecurityError as e:
                    raise MCPSecurityError(f"Project access denied: {e}")
            
            # Path security validation
            if file_path:
                try:
                    self.path_validator.validate_file_operation(file_path, operation, project_id)
                except PathSecurityError as e:
                    raise MCPSecurityError(f"Path security violation: {e}")
            
            # User input sanitization
            sanitized_input = None
            if user_input:
                try:
                    sanitized_input = self.path_validator.sanitize_user_input(user_input)
                except PathSecurityError as e:
                    raise MCPSecurityError(f"Input sanitization failed: {e}")
            
            # Generate project-scoped resources
            scoped_db_path = None
            scoped_redis_key = None
            
            if project_id != "default":
                # Only scope for non-default projects to maintain backward compatibility
                if file_path and file_path.endswith('.db'):
                    scoped_db_path = self.project_isolation.get_scoped_database_path(project_id, file_path)
                
                if operation.startswith('redis'):
                    scoped_redis_key = self.project_isolation.get_scoped_redis_key(project_id, "default")
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Update performance statistics
            self._update_performance_stats(execution_time, success=True)
            
            if execution_time > 10.0:
                logger.warning(f"Security validation exceeded 10ms: {execution_time:.2f}ms")
            
            return {
                "success": True,
                "project_id": project_id,
                "sanitized_input": sanitized_input,
                "scoped_db_path": scoped_db_path,
                "scoped_redis_key": scoped_redis_key,
                "execution_time_ms": execution_time
            }
            
        except MCPSecurityError:
            execution_time = (time.perf_counter() - start_time) * 1000
            self._update_performance_stats(execution_time, success=False)
            logger.warning(f"MCP security validation failed in {execution_time:.2f}ms")
            raise
    
    def _update_performance_stats(self, execution_time_ms: float, success: bool):
        """Update performance monitoring statistics."""
        self.validation_stats["total_validations"] += 1
        
        if not success:
            self.validation_stats["security_failures"] += 1
        
        # Update average time
        total_validations = self.validation_stats["total_validations"]
        current_avg = self.validation_stats["average_time_ms"]
        new_avg = ((current_avg * (total_validations - 1)) + execution_time_ms) / total_validations
        self.validation_stats["average_time_ms"] = new_avg
        
        # Update max time
        if execution_time_ms > self.validation_stats["max_time_ms"]:
            self.validation_stats["max_time_ms"] = execution_time_ms
    
    def get_security_context(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get security context for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Security context dictionary
        """
        if project_id is None:
            project_id = "default"
        
        project_config = self.project_isolation.get_project_config(project_id)
        
        return {
            "project_id": project_id,
            "project_exists": project_config is not None,
            "project_config": {
                "name": project_config.name if project_config else "Default",
                "redis_namespace": project_config.redis_namespace if project_config else "ltmc",
                "database_prefix": project_config.database_prefix if project_config else "ltmc"
            } if project_config else None,
            "performance_stats": self.validation_stats.copy(),
        }
    
    def register_project(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new project through the security manager.
        
        Args:
            project_id: Project identifier
            config: Project configuration
            
        Returns:
            Registration result
        """
        try:
            return self.project_isolation.register_project(project_id, config)
        except (IsolationSecurityError, Exception) as e:
            logger.error(f"Project registration failed: {e}")
            return {"success": False, "error": str(e)}


def secure_mcp_tool(operation: str = "read", 
                   validate_path: bool = True, 
                   sanitize_input: bool = True):
    """
    Decorator for securing MCP tools with project isolation.
    
    Args:
        operation: Operation type for validation
        validate_path: Whether to validate file paths
        sanitize_input: Whether to sanitize user inputs
        
    Returns:
        Decorated function with security validation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract project_id if present
            project_id = kwargs.pop('project_id', None)
            
            # Extract file paths for validation
            file_path = None
            if validate_path:
                # Common parameter names that might contain file paths
                path_params = ['file_name', 'file_path', 'path', 'db_path']
                for param in path_params:
                    if param in kwargs:
                        file_path = kwargs[param]
                        break
            
            # Extract user inputs for sanitization
            user_input = None
            if sanitize_input:
                # Common parameter names that contain user input
                input_params = ['content', 'query', 'title', 'description', 'input_prompt']
                for param in input_params:
                    if param in kwargs:
                        user_input = kwargs[param]
                        break
            
            # Get security manager (assuming it's available globally)
            security_manager = getattr(wrapper, '_security_manager', None)
            if security_manager is None:
                # Initialize security manager if not available
                project_root = Path.cwd()
                secure_root = project_root
                security_manager = MCPSecurityManager(project_root, secure_root)
                wrapper._security_manager = security_manager
            
            try:
                # Validate request
                validation_result = security_manager.validate_mcp_request(
                    project_id=project_id,
                    operation=operation,
                    file_path=file_path,
                    user_input=user_input
                )
                
                # Update kwargs with security context
                if validation_result.get('sanitized_input'):
                    # Update the original input parameter with sanitized version
                    for param in ['content', 'query', 'title', 'description', 'input_prompt']:
                        if param in kwargs:
                            kwargs[param] = validation_result['sanitized_input']
                            break
                
                if validation_result.get('scoped_db_path'):
                    # Update database path with scoped version
                    for param in ['db_path', 'file_path']:
                        if param in kwargs and kwargs[param].endswith('.db'):
                            kwargs[param] = validation_result['scoped_db_path']
                            break
                
                # Add security context to result
                result = func(*args, **kwargs)
                
                if isinstance(result, dict):
                    result['_security_context'] = {
                        "project_id": validation_result.get('project_id'),
                        "validation_time_ms": validation_result.get('execution_time_ms'),
                        "secure": True
                    }
                
                return result
                
            except MCPSecurityError as e:
                logger.error(f"Security validation failed for {func.__name__}: {e}")
                return {
                    "success": False,
                    "error": f"Security validation failed: {e}",
                    "_security_context": {
                        "secure": False,
                        "security_error": str(e)
                    }
                }
        
        return wrapper
    return decorator


# Global security manager instance for the MCP server
_global_security_manager: Optional[MCPSecurityManager] = None


def get_mcp_security_manager() -> MCPSecurityManager:
    """
    Get the global MCP security manager instance.
    
    Returns:
        MCPSecurityManager instance
    """
    global _global_security_manager
    
    if _global_security_manager is None:
        project_root = Path.cwd()
        secure_root = project_root
        _global_security_manager = MCPSecurityManager(project_root, secure_root)
    
    return _global_security_manager


def initialize_mcp_security(project_root: Union[str, Path], secure_root: Union[str, Path]):
    """
    Initialize the global MCP security manager.
    
    Args:
        project_root: Root directory for project operations
        secure_root: Root directory for secure operations
    """
    global _global_security_manager
    _global_security_manager = MCPSecurityManager(project_root, secure_root)
    logger.info("MCP Security Manager initialized globally")