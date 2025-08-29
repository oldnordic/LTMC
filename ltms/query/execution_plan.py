"""
LTMC Database Execution Plan Models
Real execution planning for federated database queries - NO PLACEHOLDERS

These models define the structure of database execution plans created by the
federation router for coordinating queries across multiple LTMC databases.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from .models import QueryType, DatabaseTarget


class OperationType(Enum):
    """Types of database operations in execution plans."""
    RETRIEVE = "retrieve"
    SEARCH = "search"
    VECTOR_SEARCH = "vector_search"
    GRAPH_QUERY = "graph_query"
    FILE_SEARCH = "file_search"
    CACHE_LOOKUP = "cache_lookup"
    AGGREGATE = "aggregate"
    JOIN = "join"


class ExecutionStrategy(Enum):
    """Execution strategies for database operations."""
    PARALLEL = "parallel"        # Operations run concurrently
    SEQUENTIAL = "sequential"    # Operations run in order
    CONDITIONAL = "conditional"  # Operations depend on previous results
    FALLBACK = "fallback"       # Alternative if primary fails


@dataclass
class DatabaseOperation:
    """Individual database operation in an execution plan."""
    database_target: DatabaseTarget
    operation_type: str
    parameters: Dict[str, Any]
    estimated_cost: float  # in milliseconds
    execution_strategy: ExecutionStrategy = ExecutionStrategy.PARALLEL
    priority: int = 1  # Higher priority operations execute first
    timeout_ms: int = 2000  # Operation timeout
    retry_count: int = 0  # Number of retries allowed
    
    def to_tool_call(self) -> Dict[str, Any]:
        """Convert database operation to LTMC tool call format."""
        if self.database_target == DatabaseTarget.SQLITE:
            return {
                "tool_name": "memory_action",
                "parameters": {
                    "action": "retrieve",
                    **self.parameters
                }
            }
        elif self.database_target == DatabaseTarget.FAISS:
            return {
                "tool_name": "memory_action", 
                "parameters": {
                    "action": "retrieve",
                    **self.parameters
                }
            }
        elif self.database_target == DatabaseTarget.FILESYSTEM:
            return {
                "tool_name": "unix_action",
                "parameters": {
                    "action": "find",
                    **self.parameters
                }
            }
        elif self.database_target == DatabaseTarget.NEO4J:
            return {
                "tool_name": "graph_action",
                "parameters": {
                    "action": "query",
                    **self.parameters
                }
            }
        elif self.database_target == DatabaseTarget.REDIS:
            return {
                "tool_name": "cache_action",
                "parameters": {
                    "action": "get",
                    **self.parameters
                }
            }
        else:
            raise ValueError(f"Unknown database target: {self.database_target}")
            
    def estimate_execution_time(self) -> float:
        """Get estimated execution time including overhead."""
        # Add small overhead for tool call dispatch
        return self.estimated_cost + 5.0  # 5ms overhead
        
    def is_compatible_for_parallel_execution(self, other: 'DatabaseOperation') -> bool:
        """Check if this operation can run in parallel with another."""
        # Operations on different databases can run in parallel
        if self.database_target != other.database_target:
            return True
            
        # Same database operations are compatible if they're read-only
        read_only_ops = {"retrieve", "search", "vector_search", "file_search", "cache_lookup"}
        return (self.operation_type in read_only_ops and 
                other.operation_type in read_only_ops)


@dataclass
class ExecutionPlan:
    """Complete execution plan for federated database query."""
    query_type: QueryType
    operations: List[DatabaseOperation]
    parallel_operations: List[DatabaseOperation] = field(default_factory=list)
    sequential_operations: List[DatabaseOperation] = field(default_factory=list)
    estimated_total_cost: float = 0.0
    is_optimized: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    optimization_notes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.parallel_operations and not self.sequential_operations:
            self._categorize_operations()
        if self.estimated_total_cost == 0.0:
            self.estimated_total_cost = self._calculate_total_cost()
            
    def _categorize_operations(self):
        """Categorize operations into parallel and sequential groups."""
        if not self.operations:
            return
            
        # Start with first operation
        remaining_operations = self.operations.copy()
        parallel_group = []
        sequential_group = []
        
        while remaining_operations:
            current_op = remaining_operations.pop(0)
            
            # Check if current operation can be parallel with existing parallel group
            can_be_parallel = True
            for parallel_op in parallel_group:
                if not current_op.is_compatible_for_parallel_execution(parallel_op):
                    can_be_parallel = False
                    break
                    
            if can_be_parallel and current_op.execution_strategy == ExecutionStrategy.PARALLEL:
                parallel_group.append(current_op)
            else:
                # Move current parallel group to sequential if it exists
                if parallel_group:
                    sequential_group.extend(parallel_group)
                    parallel_group = []
                sequential_group.append(current_op)
                
        # Add final parallel group to results
        self.parallel_operations = parallel_group
        self.sequential_operations = sequential_group
        
    def _calculate_total_cost(self) -> float:
        """Calculate total estimated cost considering parallelization."""
        if not self.operations:
            return 0.0
            
        parallel_cost = 0.0
        sequential_cost = 0.0
        
        # Parallel operations take the time of the slowest operation
        if self.parallel_operations:
            parallel_cost = max(op.estimated_cost for op in self.parallel_operations)
            
        # Sequential operations are additive
        if self.sequential_operations:
            sequential_cost = sum(op.estimated_cost for op in self.sequential_operations)
            
        # Add coordination overhead for multi-operation plans
        coordination_overhead = 0.0
        if len(self.operations) > 1:
            coordination_overhead = 10.0 * len(self.operations)  # 10ms per operation
            
        return parallel_cost + sequential_cost + coordination_overhead
        
    def get_critical_path_operations(self) -> List[DatabaseOperation]:
        """Get operations on the critical path (determine total execution time)."""
        critical_ops = []
        
        # Add the slowest parallel operation
        if self.parallel_operations:
            slowest_parallel = max(self.parallel_operations, key=lambda op: op.estimated_cost)
            critical_ops.append(slowest_parallel)
            
        # Add all sequential operations
        critical_ops.extend(self.sequential_operations)
        
        return critical_ops
        
    def optimize_for_performance(self) -> 'ExecutionPlan':
        """Create optimized version of execution plan."""
        if self.is_optimized:
            return self
            
        optimized_operations = []
        notes = []
        
        # Sort operations by estimated cost (fastest first for parallel execution)
        parallel_ops = sorted(
            [op for op in self.operations if op.execution_strategy == ExecutionStrategy.PARALLEL],
            key=lambda op: op.estimated_cost
        )
        
        sequential_ops = [op for op in self.operations 
                         if op.execution_strategy == ExecutionStrategy.SEQUENTIAL]
        
        optimized_operations.extend(parallel_ops)
        optimized_operations.extend(sequential_ops)
        
        # Apply optimizations
        for op in optimized_operations:
            # Optimize timeout based on estimated cost
            if op.estimated_cost < 100:
                op.timeout_ms = min(op.timeout_ms, 1000)  # Fast operations get shorter timeout
                notes.append(f"Reduced timeout for fast {op.operation_type} operation")
                
        return ExecutionPlan(
            query_type=self.query_type,
            operations=optimized_operations,
            estimated_total_cost=self._calculate_total_cost(),
            is_optimized=True,
            optimization_notes=notes
        )
        
    def to_tool_calls(self) -> List[Dict[str, Any]]:
        """Convert execution plan to list of LTMC tool calls."""
        tool_calls = []
        
        for operation in self.operations:
            try:
                tool_call = operation.to_tool_call()
                tool_calls.append(tool_call)
            except Exception as e:
                # Log error but continue with other operations
                continue
                
        return tool_calls
        
    def validate_plan(self) -> List[str]:
        """Validate execution plan and return list of issues."""
        issues = []
        
        if not self.operations:
            issues.append("Execution plan contains no operations")
            
        if self.estimated_total_cost <= 0:
            issues.append("Execution plan has invalid total cost estimate")
            
        # Check for unrealistic cost estimates
        if self.estimated_total_cost > 10000:  # 10 seconds
            issues.append(f"Execution plan cost too high: {self.estimated_total_cost}ms")
            
        # Validate individual operations
        for i, operation in enumerate(self.operations):
            if operation.estimated_cost <= 0:
                issues.append(f"Operation {i} has invalid cost estimate")
                
            if not operation.parameters:
                issues.append(f"Operation {i} has no parameters")
                
        return issues
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the execution plan."""
        metrics = {
            "total_operations": len(self.operations),
            "parallel_operations": len(self.parallel_operations),
            "sequential_operations": len(self.sequential_operations),
            "estimated_total_cost_ms": self.estimated_total_cost,
            "critical_path_cost_ms": sum(op.estimated_cost for op in self.get_critical_path_operations()),
            "parallelization_efficiency": 0.0,
            "database_targets": list(set(op.database_target.value for op in self.operations))
        }
        
        # Calculate parallelization efficiency
        if self.operations:
            total_sequential_cost = sum(op.estimated_cost for op in self.operations)
            if total_sequential_cost > 0:
                metrics["parallelization_efficiency"] = (
                    (total_sequential_cost - self.estimated_total_cost) / total_sequential_cost
                )
                
        return metrics


@dataclass 
class SubQuery:
    """Sub-query for complex federated operations."""
    query_fragment: str
    target_databases: List[DatabaseTarget]
    operation_type: str
    parameters: Dict[str, Any]
    estimated_results: int = 0
    join_key: Optional[str] = None  # For joining results from multiple databases
    
    def to_database_operation(self, database: DatabaseTarget) -> DatabaseOperation:
        """Convert sub-query to database operation for specific database."""
        return DatabaseOperation(
            database_target=database,
            operation_type=self.operation_type,
            parameters={
                **self.parameters,
                "query": self.query_fragment
            },
            estimated_cost=self._estimate_cost_for_database(database)
        )
        
    def _estimate_cost_for_database(self, database: DatabaseTarget) -> float:
        """Estimate cost for this sub-query on specific database."""
        # Base costs from LTMC performance data
        base_costs = {
            DatabaseTarget.SQLITE: 50.0,      # Fast metadata queries
            DatabaseTarget.FAISS: 200.0,      # Vector similarity search
            DatabaseTarget.NEO4J: 300.0,      # Graph traversal
            DatabaseTarget.REDIS: 20.0,       # Cache lookup
            DatabaseTarget.FILESYSTEM: 150.0   # File system search
        }
        
        base_cost = base_costs.get(database, 100.0)
        
        # Adjust for query complexity
        complexity_factor = 1.0
        if len(self.query_fragment.split()) > 3:
            complexity_factor = 1.5
            
        return base_cost * complexity_factor


# Utility functions for execution plan management

def merge_execution_plans(plans: List[ExecutionPlan]) -> ExecutionPlan:
    """Merge multiple execution plans into single optimized plan."""
    if not plans:
        raise ValueError("Cannot merge empty list of execution plans")
        
    if len(plans) == 1:
        return plans[0].optimize_for_performance()
        
    # Combine all operations
    all_operations = []
    all_notes = []
    
    for plan in plans:
        all_operations.extend(plan.operations)
        all_notes.extend(plan.optimization_notes)
        
    # Use query type from first plan
    merged_plan = ExecutionPlan(
        query_type=plans[0].query_type,
        operations=all_operations,
        optimization_notes=all_notes
    )
    
    return merged_plan.optimize_for_performance()


def create_fallback_execution_plan(query_type: QueryType, search_terms: List[str]) -> ExecutionPlan:
    """Create simple fallback execution plan when optimization fails."""
    # Default to SQLite-only query as fallback
    operation = DatabaseOperation(
        database_target=DatabaseTarget.SQLITE,
        operation_type="retrieve",
        parameters={
            "action": "retrieve",
            "query": " ".join(search_terms),
            "limit": 10,
            "conversation_id": f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        },
        estimated_cost=50.0,  # Fast SQLite query
        execution_strategy=ExecutionStrategy.SEQUENTIAL
    )
    
    return ExecutionPlan(
        query_type=query_type,
        operations=[operation],
        optimization_notes=["Fallback plan - single database query"]
    )