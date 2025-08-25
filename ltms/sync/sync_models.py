"""
Data models for LTMC database synchronization.
Defines structures for atomic transactions and consistency validation.

File: ltms/sync/sync_models.py
Lines: ~290 (under 300 limit)  
Purpose: Data structures for multi-database coordination
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class DatabaseType(Enum):
    """Enumeration of database types in LTMC system."""
    SQLITE = "sqlite"
    NEO4J = "neo4j"
    FAISS = "faiss"
    REDIS = "redis"

class TransactionStatus(Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"

class OperationType(Enum):
    """Database operation types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RETRIEVE = "retrieve"

@dataclass
class DocumentData:
    """
    Document data structure for synchronization across all databases.
    Contains all necessary information for atomic operations.
    """
    id: str
    content: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    conversation_id: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        current_time = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = current_time
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "conversation_id": self.conversation_id
        }

@dataclass
class TransactionOperation:
    """Single operation within an atomic transaction."""
    operation_id: str
    operation_type: OperationType
    database_type: DatabaseType
    document_data: DocumentData
    status: TransactionStatus = TransactionStatus.PENDING
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def mark_started(self):
        """Mark operation as started."""
        self.started_at = datetime.now()
        self.status = TransactionStatus.IN_PROGRESS
    
    def mark_completed(self, success: bool, error_message: str = None):
        """Mark operation as completed."""
        self.completed_at = datetime.now()
        if success:
            self.status = TransactionStatus.COMMITTED
        else:
            self.status = TransactionStatus.FAILED
            self.error_message = error_message
        
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.execution_time_ms = delta.total_seconds() * 1000

@dataclass
class AtomicTransaction:
    """
    Atomic transaction across multiple databases.
    Ensures all-or-nothing execution with rollback capability.
    """
    transaction_id: str
    operations: List[TransactionOperation] = field(default_factory=list)
    status: TransactionStatus = TransactionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_execution_time_ms: Optional[float] = None
    rollback_attempted: bool = False
    rollback_successful: bool = False
    
    def add_operation(self, operation: TransactionOperation):
        """Add operation to transaction."""
        self.operations.append(operation)
    
    def get_operations_by_database(self, db_type: DatabaseType) -> List[TransactionOperation]:
        """Get all operations for specific database type."""
        return [op for op in self.operations if op.database_type == db_type]
    
    def get_failed_operations(self) -> List[TransactionOperation]:
        """Get all failed operations."""
        return [op for op in self.operations if op.status == TransactionStatus.FAILED]
    
    def get_successful_operations(self) -> List[TransactionOperation]:
        """Get all successful operations."""
        return [op for op in self.operations if op.status == TransactionStatus.COMMITTED]
    
    def mark_started(self):
        """Mark transaction as started."""
        self.started_at = datetime.now()
        self.status = TransactionStatus.IN_PROGRESS
    
    def mark_completed(self, success: bool):
        """Mark transaction as completed."""
        self.completed_at = datetime.now()
        if success:
            self.status = TransactionStatus.COMMITTED
        else:
            self.status = TransactionStatus.FAILED
        
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.total_execution_time_ms = delta.total_seconds() * 1000
    
    def mark_rollback_attempted(self, successful: bool):
        """Mark rollback attempt."""
        self.rollback_attempted = True
        self.rollback_successful = successful
        if successful:
            self.status = TransactionStatus.ROLLED_BACK

@dataclass
class ConsistencyReport:
    """
    Consistency validation report across all databases.
    Provides detailed analysis of data consistency state.
    """
    doc_id: str
    is_consistent: bool = False
    sqlite_consistent: bool = False
    neo4j_consistent: bool = False
    faiss_consistent: bool = False
    redis_consistent: bool = False
    validation_timestamp: Optional[str] = None
    inconsistencies: List[str] = field(default_factory=list)
    database_states: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize validation timestamp and compute overall consistency."""
        if self.validation_timestamp is None:
            self.validation_timestamp = datetime.now().isoformat()
        
        # Update overall consistency based on individual systems
        self.is_consistent = all([
            self.sqlite_consistent,
            self.neo4j_consistent,
            self.faiss_consistent,
            self.redis_consistent
        ])
    
    def add_inconsistency(self, description: str, database_type: str = None):
        """Add inconsistency to report."""
        if database_type:
            description = f"[{database_type}] {description}"
        self.inconsistencies.append(description)
        self.is_consistent = False
    
    def set_database_state(self, database_type: DatabaseType, state: Dict[str, Any]):
        """Set database state information."""
        self.database_states[database_type.value] = state

@dataclass
class SyncResult:
    """
    Result of synchronization operation with comprehensive details.
    Used for operation feedback and debugging.
    """
    success: bool
    doc_id: Optional[str] = None
    transaction_id: Optional[str] = None
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    affected_databases: List[DatabaseType] = field(default_factory=list)
    consistency_report: Optional[ConsistencyReport] = None
    operation_details: Dict[str, Any] = field(default_factory=dict)
    
    def add_operation_detail(self, key: str, value: Any):
        """Add operation detail to result."""
        self.operation_details[key] = value
    
    def set_error(self, error_message: str, error_code: str = None):
        """Set error information."""
        self.success = False
        self.error_message = error_message
        if error_code:
            self.add_operation_detail("error_code", error_code)

@dataclass
class RecoveryResult:
    """
    Result of data recovery operation.
    Contains details about recovery success and any issues encountered.
    """
    success: bool
    recovered_documents: int = 0
    failed_documents: int = 0
    backup_source: Optional[str] = None
    recovery_timestamp: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    recovery_details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize recovery timestamp."""
        if self.recovery_timestamp is None:
            self.recovery_timestamp = datetime.now().isoformat()
    
    def add_error(self, error_message: str):
        """Add error to recovery result."""
        self.errors.append(error_message)
        self.success = False
    
    def add_recovery_detail(self, key: str, value: Any):
        """Add recovery detail."""
        self.recovery_details[key] = value

@dataclass
class PerformanceMetrics:
    """
    Performance metrics for synchronization operations.
    Used for SLA validation and performance monitoring.
    """
    operation_type: str
    execution_time_ms: float
    sla_limit_ms: float
    database_breakdown: Dict[DatabaseType, float] = field(default_factory=dict)
    meets_sla: bool = field(init=False)
    
    def __post_init__(self):
        """Calculate SLA compliance."""
        self.meets_sla = self.execution_time_ms <= self.sla_limit_ms
    
    def add_database_timing(self, database_type: DatabaseType, timing_ms: float):
        """Add timing for specific database operation."""
        self.database_breakdown[database_type] = timing_ms