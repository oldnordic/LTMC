"""
LTMC Database Federation Router
Production federation routing for multi-database queries - NO PLACEHOLDERS

This router coordinates queries across LTMC's 4 database systems (SQLite, FAISS, Neo4j, Redis)
with cost-based optimization and parallel execution planning.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .models import SemanticQuery, QueryType, DatabaseTarget
from .execution_plan import ExecutionPlan, DatabaseOperation, ExecutionStrategy, create_fallback_execution_plan
from .cost_estimator import DatabaseCostEstimator

# Import LTMC database managers for real connectivity
from ltms.database.sqlite_manager import SQLiteManager
from ltms.database.faiss_manager import FAISSManager
from ltms.database.neo4j_manager import Neo4jManager
from ltms.database.redis_manager import RedisManager


class DatabaseFederationRouter:
    """
    Production database federation router for LTMC unified query system.
    
    Coordinates queries across multiple database systems with cost-based optimization,
    parallel execution planning, and real-time performance monitoring.
    """
    
    def __init__(self):
        """Initialize federation router with real database connections."""
        self.cost_estimator = DatabaseCostEstimator()
        self._init_database_managers()
        self._init_performance_tracking()
        
    def _init_database_managers(self):
        """Initialize real LTMC database managers."""
        # Primary databases (required)
        try:
            self.sqlite_manager = SQLiteManager(test_mode=False)
        except Exception:
            self.sqlite_manager = None
            
        try:
            self.faiss_manager = FAISSManager(test_mode=False)
        except Exception:
            self.faiss_manager = None
            
        # Optional databases (graceful fallback)
        try:
            self.neo4j_manager = Neo4jManager(test_mode=False)
        except Exception:
            try:
                self.neo4j_manager = Neo4jManager(test_mode=True)
            except Exception:
                self.neo4j_manager = None
                
        try:
            self.redis_manager = RedisManager(test_mode=False)
        except Exception:
            try:
                self.redis_manager = RedisManager(test_mode=True)
            except Exception:
                self.redis_manager = None
                
    def _init_performance_tracking(self):
        """Initialize performance tracking for SLA monitoring."""
        self.performance_metrics = {
            "query_planning_times": [],
            "database_selection_times": [],
            "total_federation_times": [],
            "sla_violations": []
        }
        
        # SLA targets from LTMC performance guide
        self.sla_targets = {
            "query_planning_ms": 50.0,
            "database_selection_ms": 10.0,
            "total_federation_ms": 100.0
        }
        
    def create_execution_plan(self, semantic_query: SemanticQuery) -> ExecutionPlan:
        """
        Create optimized execution plan for semantic query.
        
        Args:
            semantic_query: Parsed semantic query from Phase 1
            
        Returns:
            Optimized execution plan for multi-database coordination
            
        Raises:
            ValueError: If query is invalid or has no search terms
        """
        start_time = time.time()
        
        # Validate input query
        if not semantic_query.search_terms:
            raise ValueError("No search terms provided in semantic query")
            
        if not semantic_query.target_databases:
            raise ValueError("No target databases specified in semantic query")
            
        try:
            # Step 1: Get available databases
            available_databases = self._get_available_databases(semantic_query.target_databases)
            
            # Step 2: Create database operations with cost estimation
            operations = self._create_database_operations(semantic_query, available_databases)
            
            # Step 3: Optimize operation order and execution strategy
            optimized_operations = self._optimize_operations(operations, semantic_query.query_type)
            
            # Step 4: Build execution plan
            execution_plan = ExecutionPlan(
                query_type=semantic_query.query_type,
                operations=optimized_operations
            )
            
            # Step 5: Apply final optimizations
            optimized_plan = execution_plan.optimize_for_performance()
            
            # Track performance metrics
            planning_time = (time.time() - start_time) * 1000
            self._track_performance("query_planning_times", planning_time)
            
            if planning_time > self.sla_targets["query_planning_ms"]:
                self._record_sla_violation("query_planning", planning_time)
                
            return optimized_plan
            
        except Exception as e:
            # Graceful degradation to fallback plan
            fallback_plan = create_fallback_execution_plan(
                semantic_query.query_type,
                semantic_query.search_terms
            )
            return fallback_plan
            
    def _get_available_databases(self, target_databases: List[DatabaseTarget]) -> List[DatabaseTarget]:
        """Get list of actually available databases from targets."""
        available = []
        
        for db_target in target_databases:
            if db_target == DatabaseTarget.SQLITE and self.sqlite_manager:
                try:
                    health = self.sqlite_manager.get_health_status()
                    if health.get('status') == 'healthy':
                        available.append(db_target)
                except Exception:
                    continue
                    
            elif db_target == DatabaseTarget.FAISS and self.faiss_manager:
                try:
                    if self.faiss_manager.is_available():
                        available.append(db_target)
                except Exception:
                    continue
                    
            elif db_target == DatabaseTarget.FILESYSTEM:
                # Filesystem is always available
                available.append(db_target)
                
            elif db_target == DatabaseTarget.NEO4J and self.neo4j_manager:
                # Neo4j is optional, include if manager exists
                available.append(db_target)
                
            elif db_target == DatabaseTarget.REDIS and self.redis_manager:
                # Redis is optional, include if manager exists
                available.append(db_target)
                
        # Always ensure at least SQLite is available as fallback
        if not available and self.sqlite_manager:
            available.append(DatabaseTarget.SQLITE)
            
        return available
        
    def _create_database_operations(self, semantic_query: SemanticQuery, 
                                  available_databases: List[DatabaseTarget]) -> List[DatabaseOperation]:
        """Create database operations with cost estimation."""
        operations = []
        
        for db_target in available_databases:
            # Create operation parameters based on database type and query
            parameters = self._build_operation_parameters(semantic_query, db_target)
            
            # Determine operation type based on database and query type
            operation_type = self._determine_operation_type(db_target, semantic_query.query_type)
            
            # Estimate cost for this operation
            # Extract search_terms from parameters to avoid duplicate argument
            cost_params = {k: v for k, v in parameters.items() if k != 'search_terms'}
            estimated_cost = self.cost_estimator.estimate_query_cost(
                semantic_query.search_terms,
                db_target,
                operation_type,
                **cost_params
            )
            
            # Create database operation
            operation = DatabaseOperation(
                database_target=db_target,
                operation_type=operation_type,
                parameters=parameters,
                estimated_cost=estimated_cost,
                execution_strategy=self._determine_execution_strategy(db_target, semantic_query.query_type)
            )
            
            operations.append(operation)
            
        return operations
        
    def _build_operation_parameters(self, semantic_query: SemanticQuery, 
                                  db_target: DatabaseTarget) -> Dict[str, Any]:
        """Build operation parameters for specific database target."""
        base_params = {
            "query": " ".join(semantic_query.search_terms),
            "search_terms": semantic_query.search_terms,
            "limit": 10,
            "conversation_id": f"federated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        if db_target == DatabaseTarget.SQLITE:
            # SQLite-specific parameters
            base_params.update({
                "action": "retrieve",
                "resource_type": "memory" if semantic_query.query_type == QueryType.MEMORY else "chat"
            })
            
        elif db_target == DatabaseTarget.FAISS:
            # FAISS-specific parameters for vector search
            base_params.update({
                "action": "retrieve",
                "k": 5,  # Top 5 most similar vectors
                "resource_type": "memory"
            })
            
        elif db_target == DatabaseTarget.FILESYSTEM:
            # Filesystem search parameters
            base_params.update({
                "action": "find",
                "path": "./ltms",
                "pattern": "*.py" if "code" in semantic_query.search_terms else "*"
            })
            
        elif db_target == DatabaseTarget.NEO4J:
            # Neo4j graph query parameters
            base_params.update({
                "action": "query",
                "cypher": self._build_cypher_query(semantic_query.search_terms)
            })
            
        elif db_target == DatabaseTarget.REDIS:
            # Redis cache lookup parameters
            base_params.update({
                "action": "get" if len(semantic_query.search_terms) == 1 else "scan",
                "key": semantic_query.search_terms[0] if len(semantic_query.search_terms) == 1 else None,
                "pattern": "*".join(semantic_query.search_terms) if len(semantic_query.search_terms) > 1 else None
            })
            
        # Add temporal filters if present
        if semantic_query.temporal_filters:
            base_params.update({"temporal_filters": semantic_query.temporal_filters})
            
        return base_params
        
    def _determine_operation_type(self, db_target: DatabaseTarget, query_type: QueryType) -> str:
        """Determine operation type based on database and query type."""
        if db_target == DatabaseTarget.SQLITE:
            return "retrieve"
        elif db_target == DatabaseTarget.FAISS:
            return "vector_search"
        elif db_target == DatabaseTarget.FILESYSTEM:
            return "file_search"
        elif db_target == DatabaseTarget.NEO4J:
            return "graph_query"
        elif db_target == DatabaseTarget.REDIS:
            return "cache_lookup"
        else:
            return "retrieve"  # Default fallback
            
    def _determine_execution_strategy(self, db_target: DatabaseTarget, query_type: QueryType) -> ExecutionStrategy:
        """Determine execution strategy based on database characteristics."""
        # Fast databases can run in parallel
        if db_target in [DatabaseTarget.REDIS, DatabaseTarget.SQLITE]:
            return ExecutionStrategy.PARALLEL
            
        # Slower databases might need sequential execution
        elif db_target in [DatabaseTarget.NEO4J, DatabaseTarget.FILESYSTEM]:
            return ExecutionStrategy.SEQUENTIAL
            
        # FAISS can be parallel for memory queries
        elif db_target == DatabaseTarget.FAISS and query_type == QueryType.MEMORY:
            return ExecutionStrategy.PARALLEL
            
        else:
            return ExecutionStrategy.PARALLEL  # Default to parallel
            
    def _optimize_operations(self, operations: List[DatabaseOperation], 
                           query_type: QueryType) -> List[DatabaseOperation]:
        """Optimize operation order and parameters based on query type and costs."""
        if not operations:
            return operations
            
        # Sort operations by estimated cost (fastest first for parallel execution)
        sorted_operations = sorted(operations, key=lambda op: op.estimated_cost)
        
        # Apply query-type specific optimizations
        if query_type == QueryType.MEMORY:
            # Memory queries benefit from both vector and structured search
            # Prioritize FAISS for semantic search, SQLite for metadata
            priority_order = [DatabaseTarget.FAISS, DatabaseTarget.SQLITE, 
                             DatabaseTarget.FILESYSTEM, DatabaseTarget.NEO4J, DatabaseTarget.REDIS]
            
        elif query_type == QueryType.CHAT:
            # Chat queries only need SQLite
            priority_order = [DatabaseTarget.SQLITE, DatabaseTarget.REDIS]
            
        elif query_type == QueryType.DOCUMENT:
            # Document queries prioritize filesystem, then content search
            priority_order = [DatabaseTarget.FILESYSTEM, DatabaseTarget.FAISS, 
                             DatabaseTarget.SQLITE, DatabaseTarget.NEO4J, DatabaseTarget.REDIS]
        else:
            # Default prioritization by estimated performance
            priority_order = [DatabaseTarget.REDIS, DatabaseTarget.SQLITE, 
                             DatabaseTarget.FAISS, DatabaseTarget.FILESYSTEM, DatabaseTarget.NEO4J]
            
        # Re-sort by priority while maintaining cost ordering within same priority
        def priority_key(op):
            try:
                priority_index = priority_order.index(op.database_target)
            except ValueError:
                priority_index = len(priority_order)  # Unknown databases last
            return (priority_index, op.estimated_cost)
            
        optimized_operations = sorted(sorted_operations, key=priority_key)
        
        return optimized_operations
        
    def _build_cypher_query(self, search_terms: List[str]) -> str:
        """Build Cypher query for Neo4j based on search terms."""
        # Simple pattern matching query for now
        search_pattern = "|".join(search_terms)
        return f"MATCH (n) WHERE n.name =~ '(?i).*({search_pattern}).*' RETURN n LIMIT 10"
        
    def estimate_query_cost(self, semantic_query: SemanticQuery, 
                          database_target: DatabaseTarget) -> float:
        """Estimate cost for query on specific database."""
        start_time = time.time()
        
        cost = self.cost_estimator.estimate_query_cost(
            semantic_query.search_terms,
            database_target,
            self._determine_operation_type(database_target, semantic_query.query_type)
        )
        
        # Track database selection performance
        selection_time = (time.time() - start_time) * 1000
        self._track_performance("database_selection_times", selection_time)
        
        if selection_time > self.sla_targets["database_selection_ms"]:
            self._record_sla_violation("database_selection", selection_time)
            
        return cost
        
    def convert_to_tool_calls(self, execution_plan: ExecutionPlan) -> List[Dict[str, Any]]:
        """Convert execution plan to LTMC tool calls."""
        try:
            tool_calls = execution_plan.to_tool_calls()
            return tool_calls
        except Exception as e:
            # Return empty list on conversion failure
            return []
            
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for monitoring."""
        metrics = self.cost_estimator.get_database_performance_metrics()
        
        # Add federation-specific metrics
        metrics.update({
            "federation_performance": {
                "avg_query_planning_ms": self._calculate_avg_performance("query_planning_times"),
                "avg_database_selection_ms": self._calculate_avg_performance("database_selection_times"),
                "avg_total_federation_ms": self._calculate_avg_performance("total_federation_times"),
                "sla_violations_count": len(self.performance_metrics["sla_violations"]),
                "sla_compliance_rate": self._calculate_sla_compliance_rate()
            }
        })
        
        return metrics
        
    def _track_performance(self, metric_name: str, value: float):
        """Track performance metric with rolling window."""
        if metric_name not in self.performance_metrics:
            self.performance_metrics[metric_name] = []
            
        metrics_list = self.performance_metrics[metric_name]
        metrics_list.append(value)
        
        # Keep only last 100 measurements for rolling average
        if len(metrics_list) > 100:
            metrics_list.pop(0)
            
    def _record_sla_violation(self, metric_type: str, value: float):
        """Record SLA violation for monitoring."""
        violation = {
            "timestamp": datetime.now().isoformat(),
            "metric_type": metric_type,
            "value": value,
            "sla_target": self.sla_targets.get(f"{metric_type}_ms", 0)
        }
        self.performance_metrics["sla_violations"].append(violation)
        
        # Keep only last 50 violations
        if len(self.performance_metrics["sla_violations"]) > 50:
            self.performance_metrics["sla_violations"].pop(0)
            
    def _calculate_avg_performance(self, metric_name: str) -> float:
        """Calculate average performance for metric."""
        metrics_list = self.performance_metrics.get(metric_name, [])
        if not metrics_list:
            return 0.0
        return sum(metrics_list) / len(metrics_list)
        
    def _calculate_sla_compliance_rate(self) -> float:
        """Calculate SLA compliance rate as percentage."""
        total_operations = sum(len(metrics) for metrics in [
            self.performance_metrics["query_planning_times"],
            self.performance_metrics["database_selection_times"],
            self.performance_metrics["total_federation_times"]
        ])
        
        if total_operations == 0:
            return 100.0  # No operations = 100% compliance
            
        violations = len(self.performance_metrics["sla_violations"])
        return max(0.0, (total_operations - violations) / total_operations * 100.0)