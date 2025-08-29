"""
Circuit Breaker Pattern Implementation for LTMC Optional Databases.
Provides fault tolerance and prevents cascading failures for Neo4j and Redis.

File: ltms/database/circuit_breaker.py
Lines: ~290 (under 300 limit)
Purpose: Circuit breaker pattern for optional database resilience
"""
import asyncio
import time
import logging
from typing import Callable, Any, Dict, Optional
from enum import Enum
from dataclasses import dataclass, field

from ltms.sync.sync_models import CircuitBreakerState, DatabaseType

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerMetrics:
    """Metrics tracking for circuit breaker operations."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_operations: int = 0
    
    def record_success(self):
        """Record a successful operation."""
        self.success_count += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success_time = time.time()
        self.total_operations += 1
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = time.time()
        self.total_operations += 1
    
    def reset(self):
        """Reset failure counters."""
        self.consecutive_failures = 0
        self.consecutive_successes = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for database operations.
    
    Implements three states:
    - CLOSED: Normal operation, failures are tracked
    - OPEN: Circuit open, operations fail fast
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(self, 
                 name: str,
                 failure_threshold: int = 3,
                 recovery_timeout: int = 30,
                 success_threshold: int = 2):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker identifier
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying recovery
            success_threshold: Consecutive successes needed to close circuit
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized - "
                   f"failure_threshold={failure_threshold}, "
                   f"recovery_timeout={recovery_timeout}s")
    
    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute operation through circuit breaker.
        
        Args:
            operation: Async callable to execute
            *args, **kwargs: Arguments for the operation
            
        Returns:
            Operation result
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
            Original exception: When operation fails and circuit allows it
        """
        async with self._lock:
            # Check if circuit should transition states
            await self._check_state_transition()
            
            # Handle different circuit states
            if self.state == CircuitBreakerState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN - operation blocked"
                )
            
            try:
                # Execute the operation
                start_time = time.time()
                result = await operation(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record success
                self.metrics.record_success()
                
                # Handle HALF_OPEN state - check if we should close circuit
                if self.state == CircuitBreakerState.HALF_OPEN:
                    if self.metrics.consecutive_successes >= self.success_threshold:
                        self._close_circuit()
                        logger.info(f"Circuit breaker '{self.name}' CLOSED after recovery - "
                                  f"{self.metrics.consecutive_successes} consecutive successes")
                
                logger.debug(f"Circuit breaker '{self.name}' operation succeeded in {execution_time:.3f}s")
                return result
                
            except Exception as e:
                # Record failure
                self.metrics.record_failure()
                
                # Check if we should open the circuit
                if (self.state == CircuitBreakerState.CLOSED and 
                    self.metrics.consecutive_failures >= self.failure_threshold):
                    self._open_circuit()
                    logger.warning(f"Circuit breaker '{self.name}' OPENED after "
                                 f"{self.metrics.consecutive_failures} consecutive failures")
                
                # In HALF_OPEN state, return to OPEN on any failure
                elif self.state == CircuitBreakerState.HALF_OPEN:
                    self._open_circuit()
                    logger.warning(f"Circuit breaker '{self.name}' returned to OPEN during recovery test")
                
                logger.debug(f"Circuit breaker '{self.name}' operation failed: {e}")
                raise e
    
    async def _check_state_transition(self):
        """Check if circuit breaker should transition to HALF_OPEN."""
        if (self.state == CircuitBreakerState.OPEN and 
            self.metrics.last_failure_time is not None):
            
            time_since_failure = time.time() - self.metrics.last_failure_time
            
            if time_since_failure >= self.recovery_timeout:
                self._half_open_circuit()
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN for recovery test")
    
    def _open_circuit(self):
        """Transition circuit to OPEN state."""
        self.state = CircuitBreakerState.OPEN
    
    def _close_circuit(self):
        """Transition circuit to CLOSED state."""
        self.state = CircuitBreakerState.CLOSED
        self.metrics.reset()
    
    def _half_open_circuit(self):
        """Transition circuit to HALF_OPEN state."""
        self.state = CircuitBreakerState.HALF_OPEN
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of circuit breaker."""
        return {
            "name": self.name,
            "state": self.state.value,
            "metrics": {
                "failure_count": self.metrics.failure_count,
                "success_count": self.metrics.success_count,
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "total_operations": self.metrics.total_operations,
                "last_failure_time": self.metrics.last_failure_time,
                "last_success_time": self.metrics.last_success_time
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "success_threshold": self.success_threshold
            },
            "time_until_recovery_test": self._get_time_until_recovery() if self.state == CircuitBreakerState.OPEN else None
        }
    
    def _get_time_until_recovery(self) -> Optional[float]:
        """Get seconds until recovery test (when OPEN)."""
        if (self.state == CircuitBreakerState.OPEN and 
            self.metrics.last_failure_time is not None):
            elapsed = time.time() - self.metrics.last_failure_time
            remaining = max(0, self.recovery_timeout - elapsed)
            return remaining
        return None
    
    def force_open(self):
        """Force circuit to OPEN state (for testing)."""
        self.state = CircuitBreakerState.OPEN
        self.metrics.record_failure()
        logger.warning(f"Circuit breaker '{self.name}' forced to OPEN state")
    
    def force_close(self):
        """Force circuit to CLOSED state (for testing)."""
        self.state = CircuitBreakerState.CLOSED
        self.metrics.reset()
        logger.info(f"Circuit breaker '{self.name}' forced to CLOSED state")


class CircuitBreakerManager:
    """Manages circuit breakers for optional databases."""
    
    def __init__(self):
        """Initialize circuit breaker manager."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        logger.info("Circuit breaker manager initialized")
    
    def create_circuit_breaker(self, 
                             database_type: DatabaseType,
                             failure_threshold: int = 3,
                             recovery_timeout: int = 30,
                             success_threshold: int = 2) -> CircuitBreaker:
        """
        Create circuit breaker for a database.
        
        Args:
            database_type: Database type
            failure_threshold: Failures before opening circuit
            recovery_timeout: Recovery timeout in seconds
            success_threshold: Successes needed to close circuit
            
        Returns:
            Circuit breaker instance
        """
        name = database_type.value
        circuit_breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold
        )
        
        self.circuit_breakers[name] = circuit_breaker
        logger.info(f"Created circuit breaker for {name}")
        return circuit_breaker
    
    def get_circuit_breaker(self, database_type: DatabaseType) -> Optional[CircuitBreaker]:
        """Get circuit breaker for database type."""
        return self.circuit_breakers.get(database_type.value)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return {
            name: cb.get_status() 
            for name, cb in self.circuit_breakers.items()
        }
    
    async def execute_with_circuit_breaker(self, 
                                         database_type: DatabaseType, 
                                         operation: Callable,
                                         *args, **kwargs) -> Any:
        """
        Execute operation with circuit breaker protection.
        
        Args:
            database_type: Database type
            operation: Operation to execute
            *args, **kwargs: Operation arguments
            
        Returns:
            Operation result or None if circuit is open
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
        """
        circuit_breaker = self.get_circuit_breaker(database_type)
        
        if circuit_breaker:
            return await circuit_breaker.call(operation, *args, **kwargs)
        else:
            # No circuit breaker configured, execute directly
            return await operation(*args, **kwargs)


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass