"""Semantic Memory Manager for advanced memory operations with clustering."""

import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from dataclasses import dataclass
import logging
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from ltms.services.embedding_service import create_embedding_model, encode_texts


@dataclass
class MemoryCluster:
    """Represents a cluster of semantically similar memories."""
    cluster_id: int
    centroid: np.ndarray
    member_ids: List[int]
    coherence_score: float
    topic_keywords: List[str]
    
    def similarity_to(self, other: 'MemoryCluster') -> float:
        """Calculate similarity between this cluster and another."""
        return float(cosine_similarity(
            self.centroid.reshape(1, -1),
            other.centroid.reshape(1, -1)
        )[0, 0])


class SemanticMemoryManager:
    """Advanced semantic memory management with clustering and intelligent retrieval."""
    
    def __init__(
        self, 
        db_path: str,
        embedding_model_name: str = 'all-MiniLM-L6-v2',
        clustering_algorithm: str = 'hdbscan'
    ):
        """Initialize the Semantic Memory Manager.
        
        Args:
            db_path: Path to SQLite database
            embedding_model_name: Name of embedding model to use
            clustering_algorithm: Clustering algorithm ('hdbscan' or 'kmeans')
        """
        self.db_path = db_path
        self.embedding_model_name = embedding_model_name
        self.clustering_algorithm = clustering_algorithm
        self.embedding_model: Optional[SentenceTransformer] = None
        self.clusters: Dict[int, MemoryCluster] = {}
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize the semantic memory manager.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Load embedding model
            self.embedding_model = create_embedding_model(self.embedding_model_name)
            self.is_initialized = True
            self.logger.info(f"SemanticMemoryManager initialized with {self.embedding_model_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize SemanticMemoryManager: {e}")
            self.is_initialized = False
            return False
    
    async def cluster_memories(
        self, 
        min_cluster_size: int = 3,
        min_samples: int = 2
    ) -> Dict[int, MemoryCluster]:
        """Cluster memories based on semantic similarity.
        
        Args:
            min_cluster_size: Minimum cluster size for HDBSCAN
            min_samples: Minimum samples for HDBSCAN
            
        Returns:
            Dictionary of cluster_id -> MemoryCluster
        """
        if not self.is_initialized:
            raise RuntimeError("SemanticMemoryManager not initialized")
        
        try:
            # Fetch all memory chunks with embeddings
            chunks_data = await self._fetch_chunks_with_content()
            
            if len(chunks_data) < min_cluster_size:
                self.logger.warning(f"Not enough chunks ({len(chunks_data)}) for clustering")
                return {}
            
            # Generate embeddings for chunks
            contents = [chunk['content'] for chunk in chunks_data]
            embeddings = encode_texts(self.embedding_model, contents)
            
            # Perform clustering
            if self.clustering_algorithm == 'hdbscan':
                clusterer = HDBSCAN(
                    min_cluster_size=min_cluster_size,
                    min_samples=min_samples,
                    metric='cosine'
                )
                cluster_labels = clusterer.fit_predict(embeddings)
            else:
                raise ValueError(f"Unsupported clustering algorithm: {self.clustering_algorithm}")
            
            # Create cluster objects
            clusters = {}
            unique_labels = np.unique(cluster_labels)
            
            for label in unique_labels:
                if label == -1:  # Noise points in HDBSCAN
                    continue
                
                # Safely convert label to integer
                try:
                    cluster_id = int(label) if np.isscalar(label) and np.isreal(label) else hash(str(label)) % 1000000
                except (ValueError, TypeError, OverflowError):
                    # Fallback: use hash of string representation
                    cluster_id = abs(hash(str(label))) % 1000000
                
                # Find members of this cluster
                cluster_mask = cluster_labels == label
                member_indices = np.where(cluster_mask)[0]
                member_ids = [chunks_data[i]['chunk_id'] for i in member_indices]
                
                # Calculate centroid
                cluster_embeddings = embeddings[cluster_mask]
                centroid = np.mean(cluster_embeddings, axis=0)
                
                # Calculate coherence score (average intra-cluster similarity)
                coherence_score = float(np.mean(
                    cosine_similarity(cluster_embeddings)
                ))
                
                # Extract topic keywords (simplified - use most frequent words)
                cluster_contents = [chunks_data[i]['content'] for i in member_indices]
                topic_keywords = await self._extract_topic_keywords(cluster_contents)
                
                cluster = MemoryCluster(
                    cluster_id=cluster_id,
                    centroid=centroid,
                    member_ids=member_ids,
                    coherence_score=coherence_score,
                    topic_keywords=topic_keywords
                )
                
                clusters[cluster_id] = cluster
            
            self.clusters = clusters
            self.logger.info(f"Created {len(clusters)} memory clusters")
            return clusters
            
        except Exception as e:
            self.logger.error(f"Error clustering memories: {e}")
            return {}
    
    async def find_similar_clusters(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """Find clusters most similar to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top similar clusters to return
            
        Returns:
            List of tuples (cluster_id, similarity_score)
        """
        if not self.clusters:
            return []
        
        similarities = []
        query_embedding = query_embedding.reshape(1, -1)
        
        for cluster_id, cluster in self.clusters.items():
            similarity = float(cosine_similarity(
                query_embedding,
                cluster.centroid.reshape(1, -1)
            )[0, 0])
            similarities.append((cluster_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    async def get_cluster_memories(self, cluster_id: int) -> List[Dict[str, Any]]:
        """Get all memories belonging to a specific cluster.
        
        Args:
            cluster_id: ID of the cluster
            
        Returns:
            List of memory dictionaries
        """
        if cluster_id not in self.clusters:
            return []
        
        cluster = self.clusters[cluster_id]
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get chunk details for cluster members
            placeholders = ','.join(['?'] * len(cluster.member_ids))
            query = f"""
                SELECT rc.id as chunk_id, rc.chunk_text as content, 0 as chunk_index, 
                       r.file_name, r.created_at
                FROM ResourceChunks rc
                JOIN Resources r ON rc.resource_id = r.id
                WHERE rc.id IN ({placeholders})
                ORDER BY r.created_at DESC, rc.id
            """
            
            cursor.execute(query, cluster.member_ids)
            memories = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return memories
            
        except Exception as e:
            self.logger.error(f"Error fetching cluster memories: {e}")
            return []
    
    async def update_pattern_weights(
        self, 
        successful_patterns: List[str], 
        weight_multiplier: float = 1.2
    ):
        """Update pattern weights based on successful usage.
        
        Args:
            successful_patterns: List of successful semantic patterns
            weight_multiplier: Multiplier for successful patterns
        """
        try:
            # This would update the internal weighting for semantic patterns
            # For now, just log the intent
            self.logger.info(f"Updating weights for {len(successful_patterns)} successful patterns with multiplier {weight_multiplier}")
            
            # In a full implementation, this would:
            # 1. Store pattern success rates in database
            # 2. Adjust embedding weights or similarity thresholds
            # 3. Update clustering parameters based on successful patterns
            
        except Exception as e:
            self.logger.error(f"Failed to update pattern weights: {e}")
    
    async def get_usage_patterns(self) -> Dict[str, Any]:
        """Get usage patterns for sharing with other components.
        
        Returns:
            Dictionary containing usage patterns and statistics
        """
        try:
            patterns = {
                "total_clusters": len(self.clusters),
                "cluster_coherence_scores": [c.coherence_score for c in self.clusters.values()],
                "cluster_sizes": [len(c.member_ids) for c in self.clusters.values()],
                "top_topics": [],
                "usage_statistics": {
                    "initialized": self.is_initialized,
                    "clustering_algorithm": self.clustering_algorithm,
                    "embedding_model": self.embedding_model_name
                }
            }
            
            # Extract top topics from all clusters
            all_keywords = []
            for cluster in self.clusters.values():
                all_keywords.extend(cluster.topic_keywords)
            
            # Count keyword frequency
            keyword_counts = {}
            for keyword in all_keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            # Get top 10 keywords
            patterns["top_topics"] = sorted(
                keyword_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to get usage patterns: {e}")
            return {"error": str(e)}
    
    async def _fetch_chunks_with_content(self) -> List[Dict[str, Any]]:
        """Fetch all memory chunks with their content."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT id as chunk_id, chunk_text as content, 0 as chunk_index, resource_id
                FROM ResourceChunks
                WHERE LENGTH(chunk_text) > 10
                ORDER BY id
            """
            
            cursor.execute(query)
            chunks = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error fetching chunks: {e}")
            return []
    
    async def _extract_topic_keywords(self, contents: List[str]) -> List[str]:
        """Extract topic keywords from cluster contents.
        
        Args:
            contents: List of text contents from cluster
            
        Returns:
            List of topic keywords
        """
        try:
            # Simplified keyword extraction
            # In a full implementation, this would use more sophisticated NLP
            
            import re
            from collections import Counter
            
            # Combine all contents
            combined_text = " ".join(contents).lower()
            
            # Extract words (simple tokenization)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', combined_text)
            
            # Remove common stop words
            stop_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
                'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 
                'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 
                'will', 'would', 'could', 'should', 'may', 'might', 'must',
                'this', 'that', 'these', 'those', 'a', 'an'
            }
            
            # Filter and count
            filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
            word_counts = Counter(filtered_words)
            
            # Return top 5 keywords
            return [word for word, count in word_counts.most_common(5)]
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the semantic memory manager.
        
        Returns:
            Dictionary containing health status and metrics
        """
        try:
            health_status = {
                "healthy": self.is_initialized,
                "performance_score": 0.0,
                "component_name": "SemanticMemoryManager",
                "metrics": {
                    "initialized": self.is_initialized,
                    "clusters_count": len(self.clusters),
                    "embedding_model": self.embedding_model_name,
                    "clustering_algorithm": self.clustering_algorithm
                }
            }
            
            if self.is_initialized:
                # Calculate performance score based on cluster quality
                if self.clusters:
                    avg_coherence = sum(c.coherence_score for c in self.clusters.values()) / len(self.clusters)
                    health_status["performance_score"] = min(1.0, max(0.0, avg_coherence))
                else:
                    health_status["performance_score"] = 0.8  # Good but no clusters yet
                    
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "performance_score": 0.0,
                "error": str(e)
            }
    
    async def get_insights(self) -> Dict[str, Any]:
        """Get insights about semantic memory performance.
        
        Returns:
            Dictionary containing insights and recommendations
        """
        try:
            insights = {
                "status": "active" if self.is_initialized else "inactive",
                "cluster_analysis": {
                    "total_clusters": len(self.clusters),
                    "average_cluster_size": 0,
                    "average_coherence": 0.0,
                    "most_coherent_cluster": None
                },
                "recommendations": [],
                "performance_trends": []
            }
            
            if self.clusters:
                cluster_sizes = [len(c.member_ids) for c in self.clusters.values()]
                coherence_scores = [c.coherence_score for c in self.clusters.values()]
                
                insights["cluster_analysis"]["average_cluster_size"] = sum(cluster_sizes) / len(cluster_sizes)
                insights["cluster_analysis"]["average_coherence"] = sum(coherence_scores) / len(coherence_scores)
                
                # Find most coherent cluster
                best_cluster = max(self.clusters.values(), key=lambda c: c.coherence_score)
                insights["cluster_analysis"]["most_coherent_cluster"] = {
                    "cluster_id": best_cluster.cluster_id,
                    "coherence_score": best_cluster.coherence_score,
                    "topic_keywords": best_cluster.topic_keywords,
                    "member_count": len(best_cluster.member_ids)
                }
                
                # Generate recommendations
                if insights["cluster_analysis"]["average_coherence"] < 0.7:
                    insights["recommendations"].append("Consider adjusting clustering parameters for better coherence")
                
                if insights["cluster_analysis"]["average_cluster_size"] < 3:
                    insights["recommendations"].append("Cluster sizes are small - consider lowering min_cluster_size")
                
                if len(self.clusters) > 50:
                    insights["recommendations"].append("Many clusters detected - consider increasing min_cluster_size")
            
            else:
                insights["recommendations"].append("No clusters found - run cluster_memories() to analyze data")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to get insights: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            self.clusters.clear()
            self.embedding_model = None
            self.is_initialized = False
            self.logger.info("SemanticMemoryManager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")