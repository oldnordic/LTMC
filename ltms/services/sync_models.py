"""
Data models and exceptions for documentation synchronization system.

This module contains all the core data structures used across the documentation
sync system, including:

- Exception classes for error handling
- Enums for event types and states
- Data classes for structured data
- Type definitions and constants

Extracted from documentation_sync_service.py modularization.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import supporting components
from ltms.models.blueprint_schemas import ConsistencyLevel


# ===== EXCEPTION CLASSES =====

class DocumentationSyncError(Exception):
    """Base exception for documentation synchronization errors."""
    pass


class SyncConflictError(DocumentationSyncError):
    """Exception raised when synchronization conflicts occur."""
    
    def __init__(self, message: str, conflict_type: str = None, file_path: str = None):
        super().__init__(message)
        self.conflict_type = conflict_type
        self.file_path = file_path


class ValidationFailureError(DocumentationSyncError):
    """Exception raised when validation operations fail."""
    pass


# ===== ENUMS =====

class ChangeEventType(Enum):
    """Types of change events for monitoring."""
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    BLUEPRINT_UPDATED = "blueprint_updated"
    BLUEPRINT_DELETED = "blueprint_deleted"


# ===== DATA CLASSES =====

@dataclass
class ChangeEvent:
    """Represents a change event for synchronization."""
    event_type: ChangeEventType
    file_path: str
    project_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    change_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ConsistencyResult:
    """Results of consistency validation."""
    success: bool
    consistency_score: float
    consistency_level: ConsistencyLevel
    validation_time_ms: float
    node_consistency: float = 0.0
    relationship_consistency: float = 0.0
    inconsistencies: List[Dict[str, Any]] = field(default_factory=list)
    total_nodes: int = 0
    matching_nodes: int = 0
    error_message: Optional[str] = None


@dataclass
class SyncResult:
    """Results of synchronization operations."""
    success: bool
    sync_time_ms: float
    files_processed: int = 0
    documentation_updated: bool = False
    blueprint_nodes_synced: int = 0
    blueprint_relationships_synced: int = 0
    consistency_score: float = 0.0
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None