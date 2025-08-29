"""
LTMC Unified Query API
Main API interface for natural language queries across all databases
Integrates with MCP tools system - NO MOCKS, NO PLACEHOLDERS

This module provides the primary interface for:
- Natural language query processing
- Multi-database query coordination
- Result aggregation and ranking
- Integration with LTMC MCP tools
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

# Import core components
from .natural_language_interface import UnifiedQueryInterface
from .unified_query_coordinator import UnifiedQueryCoordinator, QueryStrategy
from .models import QueryType, DatabaseTarget

# Import for MCP integration
import logging

logger = logging.getLogger(__name__)


class UnifiedQueryAPI:
    """
    Main API class for unified natural language queries.
    
    This class provides the high-level interface used by MCP tools
    and other LTMC components to execute natural language queries
    across all databases.
    """
    
    def __init__(self, test_mode: bool = False):
        """Initialize the unified query API."""
        self.test_mode = test_mode
        self.interface = UnifiedQueryInterface(test_mode=test_mode)
        self.coordinator = UnifiedQueryCoordinator(test_mode=test_mode)
        
        # Track API usage statistics
        self.api_stats = {
            "total_requests": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_response_time_ms": 0.0,
            "query_types": {}
        }
        
        logger.info(f"UnifiedQueryAPI initialized (test_mode={test_mode})")
    
    async def query(self, 
                   natural_query: str,
                   limit: int = 10,
                   strategy: str = "hybrid",
                   use_cache: bool = True,
                   include_metadata: bool = True) -> Dict[str, Any]:
        """
        Execute a natural language query across all LTMC databases.
        
        Args:
            natural_query: Natural language query string
                Examples:
                - "Find yesterday's chat about database architecture"
                - "Search memories related to modularization"
                - "Show me all documents mentioning Redis"
            limit: Maximum number of results to return (default: 10)
            strategy: Query execution strategy (parallel|sequential|hybrid|selective)
            use_cache: Whether to use cached results (default: True)
            include_metadata: Include detailed metadata in response (default: True)
            
        Returns:
            Dict containing:
            - success: Whether query executed successfully
            - results: List of matched results from all databases
            - query_analysis: Parsed query information
            - metadata: Execution metadata (if include_metadata=True)
            - error: Error message (if failed)
        """
        start_time = time.time()
        self.api_stats["total_requests"] += 1
        
        try:
            # Validate inputs
            if not natural_query or not natural_query.strip():
                raise ValueError("Query cannot be empty")
                
            if limit < 1 or limit > 100:
                raise ValueError("Limit must be between 1 and 100")
                
            # Parse strategy
            query_strategy = self._parse_strategy(strategy)
            
            # Execute query using coordinator
            result = await self.coordinator.execute_unified_query(
                query=natural_query,
                limit=limit,
                strategy=query_strategy
            )
            
            # Post-process results
            processed_result = self._process_results(
                result, 
                include_metadata=include_metadata,
                execution_time=time.time() - start_time
            )
            
            # Update statistics
            self._update_stats(success=True, execution_time=time.time() - start_time)
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.api_stats["failed_queries"] += 1
            
            return {
                "success": False,
                "error": str(e),
                "query": natural_query,
                "results": [],
                "metadata": {
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "error_type": type(e).__name__
                }
            }
    
    async def query_database(self,
                            natural_query: str,
                            database: str,
                            limit: int = 10) -> Dict[str, Any]:
        """
        Query a specific database using natural language.
        
        Args:
            natural_query: Natural language query
            database: Target database (sqlite|faiss|neo4j|redis)
            limit: Maximum results
            
        Returns:
            Query results from specified database
        """
        try:
            # Parse database target
            db_target = self._parse_database_target(database)
            
            # Use interface for single-database query
            result = await self.interface.query_specific_database(
                natural_query=natural_query,
                database=db_target,
                limit=limit
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "database": database,
                "query": natural_query,
                "results": []
            }
    
    async def search_memories(self, 
                             topic: str,
                             time_filter: Optional[str] = None,
                             limit: int = 10) -> Dict[str, Any]:
        """
        Search memories by topic with optional time filtering.
        
        Args:
            topic: Topic or keywords to search for
            time_filter: Temporal filter (yesterday|today|recent|last_week|last_month)
            limit: Maximum results
            
        Returns:
            Memory search results
        """
        # Build natural language query
        query_parts = [f"Search memories about {topic}"]
        if time_filter:
            query_parts.append(f"from {time_filter}")
            
        natural_query = " ".join(query_parts)
        
        # Execute with memory-optimized strategy
        return await self.query(
            natural_query=natural_query,
            limit=limit,
            strategy="hybrid"
        )
    
    async def find_related_documents(self,
                                    reference: str,
                                    relationship_type: Optional[str] = None,
                                    limit: int = 10) -> Dict[str, Any]:
        """
        Find documents related to a reference document or topic.
        
        Args:
            reference: Reference document ID or topic
            relationship_type: Type of relationship to follow
            limit: Maximum results
            
        Returns:
            Related documents with relationship information
        """
        # Build query for relationship traversal
        if relationship_type:
            natural_query = f"Find documents {relationship_type} to {reference}"
        else:
            natural_query = f"Find documents related to {reference}"
            
        # Execute with graph-optimized strategy
        result = await self.query(
            natural_query=natural_query,
            limit=limit,
            strategy="selective"  # Focus on Neo4j
        )
        
        # Enhance with relationship details
        if result["success"] and result["results"]:
            for item in result["results"]:
                item["relationship_to_reference"] = reference
                
        return result
    
    async def semantic_search(self,
                             query_text: str,
                             similarity_threshold: float = 0.7,
                             limit: int = 10) -> Dict[str, Any]:
        """
        Perform semantic similarity search using embeddings.
        
        Args:
            query_text: Text to search for similar content
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum results
            
        Returns:
            Semantically similar documents with scores
        """
        # Execute semantic search
        result = await self.query(
            natural_query=f"Find similar content to: {query_text}",
            limit=limit * 2,  # Get extra for filtering
            strategy="selective"  # Focus on FAISS
        )
        
        # Filter by similarity threshold
        if result["success"] and result["results"]:
            filtered_results = []
            for item in result["results"]:
                if "similarity_score" in item and item["similarity_score"] >= similarity_threshold:
                    filtered_results.append(item)
                    
            result["results"] = filtered_results[:limit]
            result["metadata"]["similarity_threshold"] = similarity_threshold
            
        return result
    
    async def get_recent_activity(self,
                                 hours: int = 24,
                                 activity_type: Optional[str] = None,
                                 limit: int = 20) -> Dict[str, Any]:
        """
        Get recent activity across all databases.
        
        Args:
            hours: Number of hours to look back
            activity_type: Filter by activity type (chat|memory|document)
            limit: Maximum results
            
        Returns:
            Recent activity sorted by timestamp
        """
        # Build temporal query
        if hours <= 24:
            time_filter = "recent"
        elif hours <= 48:
            time_filter = "yesterday"
        elif hours <= 168:
            time_filter = "last week"
        else:
            time_filter = "last month"
            
        query_parts = ["Show"]
        if activity_type:
            query_parts.append(f"{activity_type} activity")
        else:
            query_parts.append("all activity")
        query_parts.append(f"from {time_filter}")
        
        natural_query = " ".join(query_parts)
        
        # Execute with cache priority
        result = await self.query(
            natural_query=natural_query,
            limit=limit,
            strategy="hybrid",
            use_cache=True
        )
        
        # Sort by timestamp if available
        if result["success"] and result["results"]:
            result["results"] = sorted(
                result["results"],
                key=lambda x: x.get("timestamp", x.get("created_at", "")),
                reverse=True
            )
            
        return result
    
    def _parse_strategy(self, strategy: str) -> QueryStrategy:
        """Parse strategy string to enum."""
        strategy_map = {
            "parallel": QueryStrategy.PARALLEL,
            "sequential": QueryStrategy.SEQUENTIAL,
            "hybrid": QueryStrategy.HYBRID,
            "selective": QueryStrategy.SELECTIVE,
            "cached": QueryStrategy.CACHED
        }
        
        return strategy_map.get(strategy.lower(), QueryStrategy.HYBRID)
    
    def _parse_database_target(self, database: str) -> DatabaseTarget:
        """Parse database string to enum."""
        database_map = {
            "sqlite": DatabaseTarget.SQLITE,
            "faiss": DatabaseTarget.FAISS,
            "neo4j": DatabaseTarget.NEO4J,
            "redis": DatabaseTarget.REDIS,
            "filesystem": DatabaseTarget.FILESYSTEM
        }
        
        if database.lower() not in database_map:
            raise ValueError(f"Unknown database: {database}")
            
        return database_map[database.lower()]
    
    def _process_results(self, result: Dict[str, Any], 
                        include_metadata: bool,
                        execution_time: float) -> Dict[str, Any]:
        """Process and format query results."""
        processed = {
            "success": result.get("success", False),
            "results": result.get("results", []),
            "query_analysis": result.get("query", {})
        }
        
        # Add metadata if requested
        if include_metadata:
            processed["metadata"] = result.get("metadata", {})
            processed["metadata"]["api_execution_time_ms"] = execution_time * 1000
            
        # Clean up internal fields from results
        for item in processed["results"]:
            # Remove internal fields starting with underscore
            keys_to_remove = [k for k in item.keys() if k.startswith("_")]
            for key in keys_to_remove:
                if key != "_relevance_score":  # Keep relevance score
                    item.pop(key, None)
                    
        return processed
    
    def _update_stats(self, success: bool, execution_time: float):
        """Update API statistics."""
        if success:
            self.api_stats["successful_queries"] += 1
        else:
            self.api_stats["failed_queries"] += 1
            
        # Update average response time
        total = self.api_stats["total_requests"]
        avg = self.api_stats["average_response_time_ms"]
        self.api_stats["average_response_time_ms"] = (
            (avg * (total - 1) + execution_time * 1000) / total
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return {
            **self.api_stats,
            "coordinator_metrics": self.coordinator.get_metrics() if self.coordinator else {}
        }


# Global API instance for singleton pattern
_api_instance: Optional[UnifiedQueryAPI] = None


def get_unified_query_api(test_mode: bool = False) -> UnifiedQueryAPI:
    """
    Get or create the global UnifiedQueryAPI instance.
    
    Args:
        test_mode: Whether to initialize in test mode
        
    Returns:
        UnifiedQueryAPI singleton instance
    """
    global _api_instance
    
    if _api_instance is None:
        _api_instance = UnifiedQueryAPI(test_mode=test_mode)
        
    return _api_instance


# Main entry point for MCP tool integration
async def unified_query_action(query: str, **params) -> Dict[str, Any]:
    """
    Execute unified natural language query across all LTMC databases.
    
    This function is designed to be called from the MCP tools system
    and provides the main entry point for natural language queries.
    
    Args:
        query: Natural language query string
        **params: Additional parameters:
            - limit: Maximum results (default: 10)
            - strategy: Execution strategy (default: "hybrid")
            - use_cache: Use cached results (default: True)
            - database: Query specific database only (optional)
            
    Returns:
        Query results with metadata
        
    Examples:
        >>> await unified_query_action("Find yesterday's chat about databases")
        >>> await unified_query_action("Search memories related to Python", limit=5)
        >>> await unified_query_action("Show recent documents", strategy="parallel")
    """
    api = get_unified_query_api()
    
    # Extract parameters
    limit = params.get("limit", 10)
    strategy = params.get("strategy", "hybrid")
    use_cache = params.get("use_cache", True)
    database = params.get("database")
    
    # Route to specific database if requested
    if database:
        return await api.query_database(query, database, limit)
    
    # Execute unified query
    return await api.query(
        natural_query=query,
        limit=limit,
        strategy=strategy,
        use_cache=use_cache,
        include_metadata=True
    )


# Specialized query functions for common use cases
async def search_ltmc_memories(topic: str, **params) -> Dict[str, Any]:
    """Search LTMC memories by topic."""
    api = get_unified_query_api()
    return await api.search_memories(
        topic=topic,
        time_filter=params.get("time_filter"),
        limit=params.get("limit", 10)
    )


async def find_similar_content(text: str, **params) -> Dict[str, Any]:
    """Find semantically similar content."""
    api = get_unified_query_api()
    return await api.semantic_search(
        query_text=text,
        similarity_threshold=params.get("threshold", 0.7),
        limit=params.get("limit", 10)
    )


async def get_recent_ltmc_activity(**params) -> Dict[str, Any]:
    """Get recent LTMC activity."""
    api = get_unified_query_api()
    return await api.get_recent_activity(
        hours=params.get("hours", 24),
        activity_type=params.get("type"),
        limit=params.get("limit", 20)
    )