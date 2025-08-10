"""
LTMC Project Data Models

Phase 1 project isolation data structures and validation schemas.
Defines project configuration, security constraints, and multi-tenant data models.

TDD Implementation: Models designed to satisfy test requirements for project isolation.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    PENDING = "pending"


class ProjectPermission(str, Enum):
    """Project permission levels."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class ProjectIsolationLevel(str, Enum):
    """Project isolation security levels."""
    STRICT = "strict"      # Complete isolation, no cross-project access
    MODERATE = "moderate"  # Limited cross-project access with validation
    RELAXED = "relaxed"    # Minimal isolation for development


class ProjectConfigModel(BaseModel):
    """
    Project configuration model for multi-tenant isolation.
    
    Defines all security constraints and operational parameters for a project.
    """
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    # Security isolation settings
    allowed_paths: List[str] = Field(..., min_items=1)
    database_prefix: str = Field(..., min_length=1, max_length=50)
    redis_namespace: str = Field(..., min_length=1, max_length=100)
    neo4j_label: str = Field(..., min_length=1, max_length=50)
    
    # Resource constraints
    max_file_size: int = Field(default=100 * 1024 * 1024, gt=0)  # 100MB default
    max_storage_size: int = Field(default=1024 * 1024 * 1024, gt=0)  # 1GB default
    max_memory_usage: int = Field(default=512 * 1024 * 1024, gt=0)  # 512MB default
    
    # File operation constraints
    allowed_extensions: Optional[List[str]] = Field(default=None)
    blocked_extensions: Optional[List[str]] = Field(default_factory=lambda: [
        '.exe', '.bat', '.cmd', '.sh', '.dll', '.so'
    ])
    
    # Security settings
    isolation_level: ProjectIsolationLevel = Field(default=ProjectIsolationLevel.STRICT)
    allow_cross_project_reads: bool = Field(default=False)
    require_path_validation: bool = Field(default=True)
    enable_audit_logging: bool = Field(default=True)
    
    # Operational settings
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Contact and ownership
    owner_id: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=200)
    
    @validator('allowed_paths')
    def validate_allowed_paths(cls, v):
        """Validate allowed paths for security."""
        for path in v:
            # Check for path traversal attempts
            if '..' in path or path.startswith('/'):
                raise ValueError(f"Invalid path detected: {path}")
            # Ensure reasonable path length
            if len(path) > 500:
                raise ValueError(f"Path too long: {path}")
        return v
    
    @validator('database_prefix', 'redis_namespace', 'neo4j_label')
    def validate_identifiers(cls, v):
        """Validate database identifiers for security."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Identifier contains invalid characters: {v}")
        return v
    
    @validator('allowed_extensions', 'blocked_extensions')
    def validate_extensions(cls, v):
        """Validate file extensions."""
        if v is None:
            return v
        for ext in v:
            if not ext.startswith('.') or len(ext) < 2:
                raise ValueError(f"Invalid extension format: {ext}")
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class ProjectSecurityConstraints(BaseModel):
    """
    Project security constraints and validation rules.
    
    Defines specific security policies and enforcement rules for a project.
    """
    project_id: str = Field(..., min_length=1, max_length=100)
    
    # Path validation rules
    max_path_length: int = Field(default=4096, gt=0)
    max_path_depth: int = Field(default=100, gt=0)
    forbidden_path_patterns: List[str] = Field(default_factory=lambda: [
        r'\.\.[\\/]', r'__import__', r'eval\s*\(', r'/etc/', r'/root/'
    ])
    
    # Input validation rules
    max_input_length: int = Field(default=10000, gt=0)
    sanitization_rules: Dict[str, str] = Field(default_factory=lambda: {
        'remove_html': r'<[^>]*>',
        'remove_scripts': r'<script[^>]*>.*?</script>',
        'remove_dangerous_chars': r'[<>:"|?*\x00-\x1f\x7f-\x9f]'
    })
    
    # Operation limits
    max_concurrent_operations: int = Field(default=10, gt=0)
    operation_timeout_seconds: int = Field(default=30, gt=0)
    
    # Security monitoring
    enable_intrusion_detection: bool = Field(default=True)
    log_failed_attempts: bool = Field(default=True)
    alert_threshold: int = Field(default=5, gt=0)  # Failed attempts before alert
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class ProjectUsageMetrics(BaseModel):
    """
    Project usage metrics and performance tracking.
    
    Tracks resource usage, performance metrics, and operational statistics.
    """
    project_id: str = Field(..., min_length=1, max_length=100)
    
    # Storage metrics
    current_storage_bytes: int = Field(default=0, ge=0)
    total_files: int = Field(default=0, ge=0)
    
    # Operation metrics
    total_operations: int = Field(default=0, ge=0)
    failed_operations: int = Field(default=0, ge=0)
    
    # Performance metrics
    avg_response_time_ms: float = Field(default=0.0, ge=0.0)
    max_response_time_ms: float = Field(default=0.0, ge=0.0)
    
    # Security metrics
    security_violations: int = Field(default=0, ge=0)
    blocked_attempts: int = Field(default=0, ge=0)
    
    # Timestamps
    last_activity: Optional[datetime] = Field(default=None)
    metrics_updated: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_success_rate(self) -> float:
        """Calculate operation success rate."""
        if self.total_operations == 0:
            return 1.0
        return (self.total_operations - self.failed_operations) / self.total_operations
    
    def is_under_limits(self, config: ProjectConfigModel) -> bool:
        """Check if project is operating within configured limits."""
        return (
            self.current_storage_bytes <= config.max_storage_size and
            self.avg_response_time_ms <= 10.0  # 10ms performance target
        )
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class ProjectRegistrationRequest(BaseModel):
    """
    Request model for project registration.
    
    Used for API endpoints that create new project isolations.
    """
    project_id: str = Field(..., min_length=1, max_length=100)
    config: ProjectConfigModel = Field(...)
    constraints: Optional[ProjectSecurityConstraints] = Field(default=None)
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Project ID contains invalid characters: {v}")
        return v
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class ProjectRegistrationResponse(BaseModel):
    """
    Response model for project registration.
    
    Returned by API endpoints after successful project creation.
    """
    success: bool = Field(...)
    project_id: str = Field(...)
    message: str = Field(...)
    execution_time_ms: float = Field(..., ge=0.0)
    
    # Optional detailed information
    allocated_resources: Optional[Dict[str, Any]] = Field(default=None)
    security_summary: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class ProjectAccessRequest(BaseModel):
    """
    Request model for project access validation.
    
    Used by security middleware to validate operations.
    """
    project_id: str = Field(..., min_length=1, max_length=100)
    operation: ProjectPermission = Field(...)
    resource_path: str = Field(..., min_length=1)
    user_id: Optional[str] = Field(default=None)
    
    # Additional context
    client_ip: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class ProjectAccessResponse(BaseModel):
    """
    Response model for project access validation.
    
    Returned by security validation middleware.
    """
    allowed: bool = Field(...)
    project_id: str = Field(...)
    reason: Optional[str] = Field(default=None)
    execution_time_ms: float = Field(..., ge=0.0)
    
    # Security context
    security_level: ProjectIsolationLevel = Field(...)
    risk_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True