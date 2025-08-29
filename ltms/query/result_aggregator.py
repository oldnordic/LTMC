"""
LTMC Result Aggregator
Real result merging and ranking from multiple databases - NO PLACEHOLDERS

Aggregates, deduplicates, and ranks results from multiple database operations
with intelligent scoring, source attribution, and performance optimization.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime
from collections import defaultdict

from .result_ranking import ResultRanker, ResultProcessor


class ResultAggregator:
    """
    Production result aggregator for LTMC multi-database responses.
    
    Merges results from multiple database sources with intelligent deduplication,
    relevance scoring, and source attribution for optimal user experience.
    
    Design Philosophy:
    - Content-based deduplication: Hash-based duplicate detection
    - Source-aware ranking: Consider database-specific relevance
    - Metadata preservation: Maintain source database information
    - Performance optimization: Efficient merging algorithms
    """
    
    def __init__(self):
        """Initialize result aggregator with modular ranking components."""
        # Use modular components for ranking and processing
        self.ranker = ResultRanker()
        self.processor = ResultProcessor()
        
        # Statistics tracking
        self.aggregation_stats = {
            "total_aggregations": 0,
            "total_results_processed": 0,
            "total_duplicates_removed": 0,
            "average_deduplication_ratio": 0.0,
            "average_aggregation_time_ms": 0.0,
            "results_by_source": defaultdict(int),
            "ranking_algorithm_usage": defaultdict(int)
        }
        
    def aggregate_results(self, operation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from multiple database operations.
        
        Args:
            operation_results: List of standardized operation results
            
        Returns:
            Aggregated and ranked results with metadata
        """
        if not operation_results:
            return {
                "results": [],
                "aggregation_metadata": {
                    "raw_result_count": 0,
                    "final_result_count": 0,
                    "deduplication_ratio": 0.0,
                    "ranking_algorithm": "none",
                    "sources_processed": []
                }
            }
            
        start_time = datetime.now()
        self.aggregation_stats["total_aggregations"] += 1
        
        # Step 1: Extract and normalize results from all operations
        all_items, source_metadata = self._extract_all_result_items(operation_results)
        raw_count = len(all_items)
        self.aggregation_stats["total_results_processed"] += raw_count
        
        # Step 2: Deduplicate results using modular ranker
        deduplicated_items, duplicates_removed = self.ranker.deduplicate_results(all_items)
        final_count = len(deduplicated_items)
        self.aggregation_stats["total_duplicates_removed"] += duplicates_removed
        
        # Step 3: Rank results using modular ranker
        ranked_results = self.ranker.rank_results(deduplicated_items)
        
        # Step 4: Build aggregation metadata
        aggregation_time = (datetime.now() - start_time).total_seconds() * 1000
        deduplication_ratio = duplicates_removed / raw_count if raw_count > 0 else 0.0
        
        metadata = self._build_aggregation_metadata(
            raw_count, final_count, deduplication_ratio,
            source_metadata, aggregation_time
        )
        
        # Step 5: Update statistics
        self._update_aggregation_statistics(deduplication_ratio, aggregation_time)
        
        return {
            "results": ranked_results,
            "aggregation_metadata": metadata
        }
        
    def _extract_all_result_items(self, operation_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Extract all individual result items from operation results."""
        all_items = []
        source_metadata = {
            "sources_processed": [],
            "items_per_source": {},
            "errors_encountered": [],
            "successful_operations": 0
        }
        
        for op_result in operation_results:
            source_db = op_result.get("source_database", "unknown")
            source_metadata["sources_processed"].append(source_db)
            
            if not op_result.get("success", False):
                source_metadata["errors_encountered"].append({
                    "source": source_db,
                    "error": op_result.get("error", "Unknown error")
                })
                continue
                
            source_metadata["successful_operations"] += 1
            
            # Extract items from different result formats
            items_from_source = []
            
            # Use modular processor for different result types
            if "documents" in op_result:
                items_from_source.extend(self.processor.process_documents(op_result["documents"], source_db))
            if "files" in op_result:
                items_from_source.extend(self.processor.process_files(op_result["files"], source_db))
            if "nodes" in op_result:
                items_from_source.extend(self.processor.process_nodes(op_result["nodes"], source_db))
            if "cache_data" in op_result:
                items_from_source.extend(self.processor.process_cache_data(op_result["cache_data"], source_db))
            if "results" in op_result and isinstance(op_result["results"], list):
                items_from_source.extend(self.processor.process_generic_results(op_result["results"], source_db))
                
            # Update statistics
            source_metadata["items_per_source"][source_db] = len(items_from_source)
            self.aggregation_stats["results_by_source"][source_db] += len(items_from_source)
            all_items.extend(items_from_source)
            
        return all_items, source_metadata
        
        
    def _build_aggregation_metadata(self, raw_count: int, final_count: int,
                                  deduplication_ratio: float, source_metadata: Dict[str, Any],
                                  aggregation_time: float) -> Dict[str, Any]:
        """Build comprehensive aggregation metadata."""
        return {
            "raw_result_count": raw_count,
            "final_result_count": final_count,
            "deduplication_ratio": round(deduplication_ratio, 3),
            "duplicates_removed": raw_count - final_count,
            "ranking_algorithm": "score_based",
            "aggregation_time_ms": round(aggregation_time, 2),
            "sources_processed": source_metadata["sources_processed"],
            "items_per_source": source_metadata["items_per_source"],
            "successful_operations": source_metadata["successful_operations"],
            "errors_encountered": source_metadata["errors_encountered"],
            "database_weights_used": self.ranker.database_weights,
            "aggregation_timestamp": datetime.now().isoformat()
        }
        
    def _update_aggregation_statistics(self, deduplication_ratio: float, aggregation_time: float):
        """Update aggregation statistics for monitoring."""
        # Update average deduplication ratio
        total_agg = self.aggregation_stats["total_aggregations"]
        current_avg_dedup = self.aggregation_stats["average_deduplication_ratio"]
        new_avg_dedup = ((current_avg_dedup * (total_agg - 1)) + deduplication_ratio) / total_agg
        self.aggregation_stats["average_deduplication_ratio"] = round(new_avg_dedup, 4)
        
        # Update average aggregation time
        current_avg_time = self.aggregation_stats["average_aggregation_time_ms"]
        new_avg_time = ((current_avg_time * (total_agg - 1)) + aggregation_time) / total_agg
        self.aggregation_stats["average_aggregation_time_ms"] = round(new_avg_time, 2)
        
    def get_aggregation_statistics(self) -> Dict[str, Any]:
        """Get aggregation statistics for monitoring."""
        stats = self.aggregation_stats.copy()
        
        # Convert defaultdict to regular dict for JSON serialization
        stats["results_by_source"] = dict(stats["results_by_source"])
        stats["ranking_algorithm_usage"] = dict(stats["ranking_algorithm_usage"])
        
        return stats
        
    def reset_statistics(self):
        """Reset aggregation statistics."""
        for key in self.aggregation_stats:
            if isinstance(self.aggregation_stats[key], (int, float)):
                self.aggregation_stats[key] = 0 if isinstance(self.aggregation_stats[key], int) else 0.0
            elif isinstance(self.aggregation_stats[key], defaultdict):
                self.aggregation_stats[key] = defaultdict(int)