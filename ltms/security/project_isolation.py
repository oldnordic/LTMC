"""
LTMC Project Isolation Manager

Implements multi-project isolation for secure multi-tenant operation.
Prevents cross-project data access and provides scoped database/Redis operations.

Performance Target: <5ms for all project validation operations
Security Focus: Complete project boundary enforcement

TDD Implementation: This module was implemented to satisfy failing tests that define
the exact security behavior required for Phase 1 multi-project isolation.
"""

import os
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import hashlib
import logging

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


class ProjectConfigError(Exception):
    """Raised when project configuration is invalid."""
    pass


@dataclass
class ProjectConfig:
    """Project configuration data structure."""
    name: str
    allowed_paths: List[str]
    database_prefix: str
    redis_namespace: str
    neo4j_label: str
    max_file_size: int = 100 * 1024 * 1024  # 100MB default
    allowed_extensions: Optional[List[str]] = None


class ProjectIsolationManager:
    """
    Project Isolation Manager for LTMC Multi-Tenant Security
    
    Provides complete project boundary enforcement:
    - Validates project access permissions
    - Scopes database paths per project
    - Creates Redis namespaces for isolation
    - Prevents path traversal and cross-project access
    
    Performance: All operations complete in <5ms for high-throughput usage.
    """
    
    def __init__(self, project_root: Union[str, Path]):
        """
        Initialize ProjectIsolationManager.
        
        Args:
            project_root: Root directory for all project operations
        """
        self.project_root = Path(project_root).resolve()
        self.projects: Dict[str, ProjectConfig] = {}
        self.default_project = "default"
        
        # Precompiled regex patterns for performance
        self._path_traversal_pattern = re.compile(r'\.\.[\\/]|[\\/]\.\.[\\/]|[\\/]\.\.$')
        self._dangerous_chars = re.compile(r'[<>:"|?*\x00-\x1f\x7f-\x9f]')
        
        # Security constraints
        self._max_path_length = 4096
        self._max_project_name_length = 100
        
        logger.info(f"ProjectIsolationManager initialized with root: {self.project_root}")
    
    def register_project(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new project with validation.
        
        Args:
            project_id: Unique project identifier
            config: Project configuration dictionary
            
        Returns:
            Dict with success status and details
            
        Raises:
            ProjectConfigError: If configuration is invalid
            SecurityError: If project_id is unsafe
        """
        start_time = time.perf_counter()
        
        try:
            # Validate project_id
            if not project_id or len(project_id) > self._max_project_name_length:
                raise ProjectConfigError(f"Invalid project_id length: {len(project_id)}")
            
            if not re.match(r'^[a-zA-Z0-9_-]+$', project_id):
                raise SecurityError(f"Project ID contains unsafe characters: {project_id}")
            
            # Validate required configuration fields
            required_fields = ['name', 'allowed_paths', 'database_prefix', 'redis_namespace', 'neo4j_label']
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                raise ProjectConfigError(f"Missing required configuration fields: {missing_fields}")
            
            # Validate allowed_paths for security
            for path in config['allowed_paths']:
                if self._path_traversal_pattern.search(path):
                    raise SecurityError(f"Path traversal detected in allowed_paths: {path}")
                
                if len(path) > self._max_path_length:
                    raise SecurityError(f"Path exceeds maximum length: {path}")
            
            # Create ProjectConfig instance
            project_config = ProjectConfig(
                name=config['name'],
                allowed_paths=config['allowed_paths'],
                database_prefix=config['database_prefix'],
                redis_namespace=config['redis_namespace'],
                neo4j_label=config['neo4j_label'],
                max_file_size=config.get('max_file_size', 100 * 1024 * 1024),
                allowed_extensions=config.get('allowed_extensions')
            )
            
            # Store configuration
            self.projects[project_id] = project_config
            
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.info(f"Project {project_id} registered in {execution_time:.2f}ms")
            
            return {
                "success": True,
                "project_id": project_id,
                "execution_time_ms": execution_time
            }
            
        except (ProjectConfigError, SecurityError) as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Project registration failed for {project_id}: {e}")
            raise
    
    def validate_project_access(self, project_id: str, operation: str, file_path: str) -> bool:
        """
        Validate project access for a specific file operation.
        
        Args:
            project_id: Project attempting the operation
            operation: Type of operation (read, write, execute)
            file_path: Path being accessed
            
        Returns:
            True if access is allowed
            
        Raises:
            SecurityError: If access is denied for security reasons
            
        Performance: Completes in <5ms for all validation checks
        """
        start_time = time.perf_counter()
        
        try:
            # Check if project exists and is authorized
            if project_id not in self.projects:
                raise SecurityError(f"Project '{project_id}' is not authorized")
            
            project_config = self.projects[project_id]
            
            # Normalize and validate path
            normalized_path = self._normalize_path(file_path)
            
            # Check for path traversal attacks
            if self._path_traversal_pattern.search(normalized_path):
                raise SecurityError(f"Path traversal detected: {file_path}")
            
            # Check path length
            if len(normalized_path) > self._max_path_length:
                raise SecurityError(f"Path exceeds maximum length: {file_path}")
            
            # Check if path is within allowed paths for this project
            path_allowed = False
            for allowed_path in project_config.allowed_paths:
                if normalized_path.startswith(allowed_path) or normalized_path.startswith(f"{allowed_path}/"):
                    path_allowed = True
                    break
            
            if not path_allowed:
                raise SecurityError(f"Path '{file_path}' is not allowed for project '{project_id}'")
            
            # Additional validation for absolute paths (system directories)
            if os.path.isabs(normalized_path):
                system_dirs = ['/etc/', '/root/', '/proc/', '/sys/', '/dev/', '/var/log/', '/usr/lib/python']
                for system_dir in system_dirs:
                    if normalized_path.startswith(system_dir):
                        raise SecurityError(f"System directory access denied: {file_path}")
            
            execution_time = (time.perf_counter() - start_time) * 1000
            if execution_time > 5.0:
                logger.warning(f"Project validation exceeded 5ms: {execution_time:.2f}ms")
            
            return True
            
        except SecurityError:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Project access denied for {project_id}: {file_path} ({execution_time:.2f}ms)")
            raise
    
    def get_scoped_database_path(self, project_id: str, base_path: str) -> str:
        """
        Generate project-scoped database path.
        
        Args:
            project_id: Project identifier
            base_path: Base database path
            
        Returns:
            Project-scoped database path
            
        Raises:
            SecurityError: If project is not authorized
        """
        start_time = time.perf_counter()
        
        if project_id not in self.projects:
            raise SecurityError(f"Project '{project_id}' is not authorized")
        
        project_config = self.projects[project_id]
        
        # Create scoped path using project prefix
        base_name = Path(base_path).stem
        extension = Path(base_path).suffix
        parent_dir = Path(base_path).parent
        
        scoped_path = parent_dir / f"{project_config.database_prefix}_{base_name}{extension}"
        
        execution_time = (time.perf_counter() - start_time) * 1000
        logger.debug(f"Database path scoped in {execution_time:.2f}ms: {scoped_path}")
        
        return str(scoped_path)
    
    def get_scoped_redis_key(self, project_id: str, key: str) -> str:
        """
        Generate project-namespaced Redis key.
        
        Args:
            project_id: Project identifier
            key: Original Redis key
            
        Returns:
            Project-namespaced Redis key
            
        Raises:
            SecurityError: If project is not authorized
        """
        start_time = time.perf_counter()
        
        if project_id not in self.projects:
            raise SecurityError(f"Project '{project_id}' is not authorized")
        
        project_config = self.projects[project_id]
        
        # Create namespaced key
        namespaced_key = f"{project_config.redis_namespace}:{key}"
        
        execution_time = (time.perf_counter() - start_time) * 1000
        logger.debug(f"Redis key namespaced in {execution_time:.2f}ms: {namespaced_key}")
        
        return namespaced_key
    
    def get_project_config(self, project_id: str) -> Optional[ProjectConfig]:
        """
        Get project configuration.
        
        Args:
            project_id: Project identifier
            
        Returns:
            ProjectConfig if project exists, None otherwise
        """
        return self.projects.get(project_id)
    
    def list_projects(self) -> List[str]:
        """
        List all registered project IDs.
        
        Returns:
            List of project IDs
        """
        return list(self.projects.keys())
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for security validation.
        
        Args:
            path: Input path
            
        Returns:
            Normalized path
        """
        # Remove dangerous characters
        cleaned = self._dangerous_chars.sub('', path)
        
        # Normalize separators
        normalized = cleaned.replace('\\', '/')
        
        # Remove duplicate slashes
        normalized = re.sub(r'/+', '/', normalized)
        
        # Remove trailing slash
        if normalized.endswith('/') and len(normalized) > 1:
            normalized = normalized[:-1]
        
        return normalized
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for monitoring.
        
        Returns:
            Performance metrics dictionary
        """
        return {
            "total_projects": len(self.projects),
            "project_root": str(self.project_root),
            "max_path_length": self._max_path_length,
            "max_project_name_length": self._max_project_name_length
        }