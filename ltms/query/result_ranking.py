"""
LTMC Result Ranking and Scoring
Advanced result ranking and scoring algorithms - NO PLACEHOLDERS

Provides intelligent ranking, scoring, and deduplication algorithms
for multi-database query results optimization.
"""

import hashlib
from typing import Dict, Any, List, Set, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class ResultRanker:
    """Advanced result ranking and scoring for LTMC multi-database responses."""
    
    def __init__(self):
        """Initialize result ranker with database weights and scoring algorithms."""
        # Database source weights for ranking
        self.database_weights = {
            "sqlite": 1.0,      # Metadata and structured data
            "faiss": 1.2,       # Vector similarity (higher relevance)
            "filesystem": 0.8,  # File system results (context dependent)
            "neo4j": 0.9,       # Graph relationships
            "redis": 0.7        # Cached data (potentially stale)
        }
        
        # Content similarity thresholds for deduplication
        self.similarity_thresholds = {
            "exact_match": 1.0,     # Identical content
            "high_similarity": 0.95, # Very similar content
            "medium_similarity": 0.85, # Similar content
            "low_similarity": 0.7   # Somewhat similar content
        }
        
        # Statistics tracking
        self.ranking_stats = defaultdict(int)
        
    def rank_results(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank results by relevance score and source weight."""
        if not items:
            return []
            
        self.ranking_stats["score_based"] += 1
        
        # Calculate composite score for each item
        for item in items:
            base_score = item.get("score", 0.0)
            source_weight = self.database_weights.get(item.get("source_database", ""), 0.5)
            
            # Composite score considers both relevance and source reliability
            composite_score = base_score * source_weight
            
            # Boost score for items with content
            content_length = len(item.get("content", ""))
            if content_length > 50:  # Substantial content
                composite_score *= 1.1
            elif content_length > 200:  # Rich content
                composite_score *= 1.2
                
            # Boost score for recent items (if timestamp available)
            if "timestamp" in item.get("metadata", {}):
                timestamp = item["metadata"]["timestamp"]
                if self._is_recent_timestamp(timestamp):
                    composite_score *= 1.05
                    
            item["composite_score"] = round(composite_score, 4)
            
        # Sort by composite score (descending)
        ranked_items = sorted(items, key=lambda x: x.get("composite_score", 0.0), reverse=True)
        
        # Add ranking position
        for i, item in enumerate(ranked_items):
            item["rank_position"] = i + 1
            
        return ranked_items
        
    def deduplicate_results(self, items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Deduplicate results based on content similarity."""
        if not items:
            return [], 0
            
        # Group items by content hash for exact duplicate removal
        hash_groups = defaultdict(list)
        for item in items:
            content_hash = item.get("content_hash", "")
            if not content_hash:
                content_hash = self.calculate_content_hash(item.get("content", ""))
                item["content_hash"] = content_hash
            hash_groups[content_hash].append(item)
            
        # Select best representative from each hash group
        deduplicated = []
        duplicates_removed = 0
        
        for hash_key, group_items in hash_groups.items():
            if len(group_items) == 1:
                deduplicated.append(group_items[0])
            else:
                # Multiple items with same hash - select highest scoring one
                best_item = max(group_items, key=lambda x: (
                    x.get("score", 0.0),
                    self.database_weights.get(x.get("source_database", ""), 0.5)
                ))
                # Add deduplication metadata
                best_item["metadata"]["duplicate_sources"] = [
                    item.get("source_database", "unknown") for item in group_items
                ]
                deduplicated.append(best_item)
                duplicates_removed += len(group_items) - 1
                
        return deduplicated, duplicates_removed
        
    def calculate_content_hash(self, content: str) -> str:
        """Calculate hash for content-based deduplication."""
        if not content:
            return ""
        # Normalize content before hashing
        normalized = content.strip().lower()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
        
    def calculate_relevance_boost(self, item: Dict[str, Any], query_terms: List[str]) -> float:
        """Calculate relevance boost based on query term matching."""
        content = item.get("content", "").lower()
        title = item.get("title", "").lower()
        
        boost_factor = 1.0
        
        # Boost for query terms in title (higher weight)
        title_matches = sum(1 for term in query_terms if term.lower() in title)
        if title_matches > 0:
            boost_factor += (title_matches / len(query_terms)) * 0.3
            
        # Boost for query terms in content
        content_matches = sum(1 for term in query_terms if term.lower() in content)
        if content_matches > 0:
            boost_factor += (content_matches / len(query_terms)) * 0.2
            
        return min(boost_factor, 2.0)  # Cap boost at 2x
        
    def _is_recent_timestamp(self, timestamp: str) -> bool:
        """Check if timestamp is recent (within last 24 hours)."""
        try:
            item_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(item_time.tzinfo)
            time_diff = current_time - item_time
            return time_diff.total_seconds() < 86400  # 24 hours
        except (ValueError, AttributeError):
            return False
            
    def apply_diversity_filter(self, ranked_items: List[Dict[str, Any]], 
                              max_per_source: int = 5) -> List[Dict[str, Any]]:
        """Apply diversity filter to ensure balanced representation across sources."""
        if not ranked_items:
            return []
            
        source_counts = defaultdict(int)
        filtered_items = []
        
        for item in ranked_items:
            source = item.get("source_database", "unknown")
            
            # Include item if source hasn't exceeded limit
            if source_counts[source] < max_per_source:
                filtered_items.append(item)
                source_counts[source] += 1
            else:
                # Add to metadata for potential inclusion in extended results
                if "diversity_filtered" not in item:
                    item["diversity_filtered"] = True
                    
        return filtered_items
        
    def calculate_result_confidence(self, item: Dict[str, Any]) -> float:
        """Calculate confidence score for individual result."""
        confidence = 0.5  # Base confidence
        
        # Source reliability contribution
        source = item.get("source_database", "")
        source_weight = self.database_weights.get(source, 0.5)
        confidence += source_weight * 0.3
        
        # Score contribution
        score = item.get("score", 0.0)
        if score > 0.8:
            confidence += 0.2
        elif score > 0.5:
            confidence += 0.1
            
        # Content quality contribution
        content_length = len(item.get("content", ""))
        if content_length > 100:
            confidence += 0.1
            
        # Metadata richness contribution
        metadata = item.get("metadata", {})
        if len(metadata) > 3:
            confidence += 0.05
            
        return min(round(confidence, 2), 1.0)
        
    def generate_ranking_explanation(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanation for why item received its ranking."""
        explanation = {
            "base_score": item.get("score", 0.0),
            "source_weight": self.database_weights.get(item.get("source_database", ""), 0.5),
            "composite_score": item.get("composite_score", 0.0),
            "rank_position": item.get("rank_position", 0),
            "confidence": self.calculate_result_confidence(item),
            "factors": []
        }
        
        # Identify ranking factors
        content_length = len(item.get("content", ""))
        if content_length > 200:
            explanation["factors"].append("rich_content")
        elif content_length > 50:
            explanation["factors"].append("substantial_content")
            
        source = item.get("source_database", "")
        if source in ["faiss", "sqlite"]:
            explanation["factors"].append("high_reliability_source")
            
        if item.get("score", 0.0) > 0.8:
            explanation["factors"].append("high_relevance_score")
            
        return explanation
        
    def get_ranking_statistics(self) -> Dict[str, Any]:
        """Get ranking algorithm usage statistics."""
        return {
            "ranking_algorithm_usage": dict(self.ranking_stats),
            "database_weights": self.database_weights,
            "similarity_thresholds": self.similarity_thresholds,
            "total_rankings_performed": sum(self.ranking_stats.values())
        }
        
    def reset_statistics(self):
        """Reset ranking statistics."""
        self.ranking_stats.clear()


class ResultProcessor:
    """Processes and standardizes results from different database sources."""
    
    def process_documents(self, documents: List[Dict[str, Any]], source_db: str) -> List[Dict[str, Any]]:
        """Process document results from memory operations."""
        processed = []
        for doc in documents:
            if isinstance(doc, dict):
                processed.append({
                    "type": "document",
                    "content": doc.get("content", ""),
                    "title": doc.get("title", doc.get("file_name", "Untitled")),
                    "score": float(doc.get("score", doc.get("similarity_score", 0.0))),
                    "source_database": source_db,
                    "metadata": doc.get("metadata", {}),
                    "content_hash": self._calculate_content_hash(doc.get("content", ""))
                })
        return processed
        
    def process_files(self, files: List[Dict[str, Any]], source_db: str) -> List[Dict[str, Any]]:
        """Process file results from filesystem operations."""
        processed = []
        for file_item in files:
            if isinstance(file_item, dict):
                content = file_item.get("content", file_item.get("path", ""))
                processed.append({
                    "type": "file",
                    "content": content,
                    "title": file_item.get("name", file_item.get("path", "Unknown file")),
                    "score": float(file_item.get("relevance", 0.5)),  # Default relevance
                    "source_database": source_db,
                    "metadata": file_item,
                    "content_hash": self._calculate_content_hash(content)
                })
        return processed
        
    def process_nodes(self, nodes: List[Dict[str, Any]], source_db: str) -> List[Dict[str, Any]]:
        """Process node results from graph operations."""
        processed = []
        for node in nodes:
            if isinstance(node, dict):
                content = node.get("properties", {}).get("content", str(node))
                processed.append({
                    "type": "node",
                    "content": content,
                    "title": node.get("label", node.get("name", "Graph node")),
                    "score": float(node.get("relevance", 0.6)),  # Default graph relevance
                    "source_database": source_db,
                    "metadata": node,
                    "content_hash": self._calculate_content_hash(content)
                })
        return processed
        
    def process_cache_data(self, cache_data: Any, source_db: str) -> List[Dict[str, Any]]:
        """Process cache data from cache operations."""
        processed = []
        if isinstance(cache_data, dict):
            for key, value in cache_data.items():
                content = str(value)
                processed.append({
                    "type": "cache_entry",
                    "content": content,
                    "title": f"Cache: {key}",
                    "score": 0.4,  # Lower score for cached data
                    "source_database": source_db,
                    "metadata": {"cache_key": key, "cache_value": value},
                    "content_hash": self._calculate_content_hash(content)
                })
        elif cache_data is not None:
            content = str(cache_data)
            processed.append({
                "type": "cache_entry",
                "content": content,
                "title": "Cache data",
                "score": 0.4,
                "source_database": source_db,
                "metadata": {"raw_cache_data": cache_data},
                "content_hash": self._calculate_content_hash(content)
            })
        return processed
        
    def process_generic_results(self, results: List[Any], source_db: str) -> List[Dict[str, Any]]:
        """Process generic result items."""
        processed = []
        for item in results:
            content = str(item)
            processed.append({
                "type": "generic",
                "content": content,
                "title": f"Result from {source_db}",
                "score": 0.5,  # Neutral score
                "source_database": source_db,
                "metadata": {"raw_item": item},
                "content_hash": self._calculate_content_hash(content)
            })
        return processed
        
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash for content-based deduplication."""
        if not content:
            return ""
        normalized = content.strip().lower()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()