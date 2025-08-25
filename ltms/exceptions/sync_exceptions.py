"""
Custom exceptions for LTMC database synchronization.
Provides specific error types for atomic transaction management.

File: ltms/exceptions/sync_exceptions.py  
Lines: ~60 (under 300 limit)
Purpose: Exception handling for multi-database synchronization
"""

class SyncException(Exception):
    """Base exception for LTMC synchronization errors."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "SYNC_ERROR"

class AtomicTransactionException(SyncException):
    """
    Raised when atomic transaction fails across database systems.
    Contains details about which systems failed and transaction state.
    """
    
    def __init__(self, message: str, failed_systems: list = None, 
                 transaction_id: str = None, partial_success: dict = None):
        super().__init__(message, "ATOMIC_TRANSACTION_FAILED")
        self.failed_systems = failed_systems or []
        self.transaction_id = transaction_id
        self.partial_success = partial_success or {}

class ConsistencyValidationException(SyncException):
    """
    Raised when consistency validation fails between database systems.
    Indicates data inconsistency that requires immediate attention.
    """
    
    def __init__(self, message: str, inconsistent_systems: list = None, 
                 doc_id: str = None, consistency_report: dict = None):
        super().__init__(message, "CONSISTENCY_VALIDATION_FAILED")
        self.inconsistent_systems = inconsistent_systems or []
        self.doc_id = doc_id
        self.consistency_report = consistency_report or {}

class RollbackException(SyncException):
    """
    Raised when transaction rollback fails.
    Critical error indicating partial rollback state.
    """
    
    def __init__(self, message: str, partial_rollback_systems: list = None,
                 transaction_id: str = None, rollback_errors: dict = None):
        super().__init__(message, "ROLLBACK_FAILED")
        self.partial_rollback_systems = partial_rollback_systems or []
        self.transaction_id = transaction_id
        self.rollback_errors = rollback_errors or {}

class DatabaseConnectionException(SyncException):
    """
    Raised when database connection fails.
    Includes database type and connection details for debugging.
    """
    
    def __init__(self, message: str, database_type: str = None, 
                 connection_details: dict = None):
        super().__init__(message, "DATABASE_CONNECTION_FAILED")
        self.database_type = database_type
        self.connection_details = connection_details or {}

class PerformanceSLAException(SyncException):
    """
    Raised when operation exceeds performance SLA limits.
    Contains timing information for performance analysis.
    """
    
    def __init__(self, message: str, operation_time_ms: float = None, 
                 sla_limit_ms: float = None, operation_type: str = None):
        super().__init__(message, "PERFORMANCE_SLA_EXCEEDED")
        self.operation_time_ms = operation_time_ms
        self.sla_limit_ms = sla_limit_ms
        self.operation_type = operation_type