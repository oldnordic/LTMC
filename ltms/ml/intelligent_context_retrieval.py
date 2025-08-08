"""Intelligent Context Retrieval for smart context selection and relevance scoring."""

import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from dataclasses import dataclass
from enum import Enum
import logging
import re
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from ltms.ml.semantic_memory_manager import SemanticMemoryManager
from ltms.services.embedding_service import create_embedding_model, encode_text


class RetrievalStrategy(Enum):
    """Enum for different retrieval strategies."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    CLUSTERING = "clustering"
    HYBRID = "hybrid"


@dataclass
class ContextCandidate:
    """Represents a candidate context with relevance scoring."""
    chunk_id: int
    content: str
    relevance_score: float
    retrieval_strategy: RetrievalStrategy
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate relevance score."""
        self.relevance_score = max(0.0, min(1.0, self.relevance_score))


@dataclass
class RetrievalResult:
    """Results from intelligent context retrieval."""
    query: str
    candidates: List[ContextCandidate]
    total_retrieved: int
    retrieval_time: float
    strategy_used: RetrievalStrategy
    
    @property
    def top_candidate(self) -> Optional[ContextCandidate]:
        """Get the top-scoring candidate."""
        return self.candidates[0] if self.candidates else None
    
    @property
    def average_relevance(self) -> float:
        """Calculate average relevance score."""
        if not self.candidates:
            return 0.0
        return sum(c.relevance_score for c in self.candidates) / len(self.candidates)


class IntelligentContextRetrieval:
    """Advanced context retrieval with multiple strategies and relevance scoring."""
    
    def __init__(
        self,
        db_path: str,
        embedding_model_name: str = 'all-MiniLM-L6-v2',
        default_strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    ):
        """Initialize the intelligent context retrieval system.
        
        Args:
            db_path: Path to SQLite database
            embedding_model_name: Name of embedding model to use
            default_strategy: Default retrieval strategy
        """
        self.db_path = db_path
        self.embedding_model_name = embedding_model_name
        self.default_strategy = default_strategy
        self.embedding_model: Optional[SentenceTransformer] = None
        self.semantic_manager: Optional[SemanticMemoryManager] = None
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)
        
        # Strategy weights for hybrid approach
        self.strategy_weights = {
            RetrievalStrategy.SEMANTIC: 0.6,
            RetrievalStrategy.KEYWORD: 0.3,
            RetrievalStrategy.CLUSTERING: 0.1
        }
    
    async def initialize(self) -> bool:
        """Initialize the intelligent context retrieval system.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Initialize embedding model
            self.embedding_model = create_embedding_model(self.embedding_model_name)
            
            # Initialize semantic memory manager
            self.semantic_manager = SemanticMemoryManager(
                db_path=self.db_path,
                embedding_model_name=self.embedding_model_name
            )
            semantic_init_success = await self.semantic_manager.initialize()
            
            if not semantic_init_success:
                self.logger.warning("SemanticMemoryManager initialization failed, continuing with limited functionality")
            
            self.is_initialized = True
            self.logger.info("IntelligentContextRetrieval initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize IntelligentContextRetrieval: {e}")
            self.is_initialized = False
            return False
    
    async def retrieve_context(
        self,
        query: str,
        max_results: int = 10,
        strategy: Optional[RetrievalStrategy] = None,
        min_relevance: float = 0.3
    ) -> RetrievalResult:
        """Retrieve relevant context using intelligent strategies.
        
        Args:
            query: Query text
            max_results: Maximum number of results to return
            strategy: Specific strategy to use (None for default)
            min_relevance: Minimum relevance score threshold
            
        Returns:
            RetrievalResult with ranked context candidates
        """
        if not self.is_initialized:
            raise RuntimeError("IntelligentContextRetrieval not initialized")
        
        import time
        start_time = time.time()
        
        strategy = strategy or self.default_strategy
        
        try:
            if strategy == RetrievalStrategy.SEMANTIC:
                candidates = await self._semantic_retrieval(query, max_results, min_relevance)
            elif strategy == RetrievalStrategy.KEYWORD:
                candidates = await self._keyword_retrieval(query, max_results, min_relevance)
            elif strategy == RetrievalStrategy.CLUSTERING:
                candidates = await self._clustering_retrieval(query, max_results, min_relevance)
            elif strategy == RetrievalStrategy.HYBRID:
                candidates = await self._hybrid_retrieval(query, max_results, min_relevance)
            else:
                raise ValueError(f"Unknown retrieval strategy: {strategy}")
            
            retrieval_time = time.time() - start_time
            
            result = RetrievalResult(
                query=query,
                candidates=candidates,
                total_retrieved=len(candidates),
                retrieval_time=retrieval_time,
                strategy_used=strategy
            )
            
            self.logger.info(f"Retrieved {len(candidates)} contexts in {retrieval_time:.3f}s using {strategy.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during context retrieval: {e}")
            return RetrievalResult(
                query=query,
                candidates=[],
                total_retrieved=0,
                retrieval_time=time.time() - start_time,
                strategy_used=strategy
            )
    
    async def _semantic_retrieval(
        self,
        query: str,
        max_results: int,
        min_relevance: float
    ) -> List[ContextCandidate]:
        """Perform semantic similarity-based retrieval."""
        try:
            # Generate query embedding
            query_embedding = encode_text(self.embedding_model, query)
            
            # Get all chunks with their embeddings
            chunks_data = await self._get_chunks_with_embeddings()
            
            if not chunks_data:
                return []
            
            candidates = []
            
            for chunk in chunks_data:
                if chunk.get('embedding') is not None:
                    # Calculate semantic similarity
                    similarity = float(cosine_similarity(
                        query_embedding.reshape(1, -1),
                        chunk['embedding'].reshape(1, -1)
                    )[0, 0])
                    
                    if similarity >= min_relevance:
                        candidate = ContextCandidate(
                            chunk_id=chunk['chunk_id'],
                            content=chunk['content'],
                            relevance_score=similarity,
                            retrieval_strategy=RetrievalStrategy.SEMANTIC,
                            metadata={
                                'file_name': chunk.get('file_name', ''),
                                'chunk_index': chunk.get('chunk_index', 0),
                                'semantic_similarity': similarity
                            }
                        )
                        candidates.append(candidate)
            
            # Sort by relevance score
            candidates.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return candidates[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error in semantic retrieval: {e}")
            return []
    
    async def _keyword_retrieval(
        self,
        query: str,
        max_results: int,
        min_relevance: float
    ) -> List[ContextCandidate]:
        """Perform keyword-based retrieval with TF-IDF scoring."""
        try:
            # Extract keywords from query
            query_keywords = self._extract_keywords(query)
            
            if not query_keywords:
                return []
            
            # Get all chunks
            chunks_data = await self._get_all_chunks()
            
            candidates = []
            
            for chunk in chunks_data:
                # Calculate keyword relevance score
                relevance_score = self._calculate_keyword_relevance(
                    query_keywords,
                    chunk['content']
                )
                
                if relevance_score >= min_relevance:
                    candidate = ContextCandidate(
                        chunk_id=chunk['chunk_id'],
                        content=chunk['content'],
                        relevance_score=relevance_score,
                        retrieval_strategy=RetrievalStrategy.KEYWORD,
                        metadata={
                            'file_name': chunk.get('file_name', ''),
                            'chunk_index': chunk.get('chunk_index', 0),
                            'keyword_matches': query_keywords,
                            'keyword_score': relevance_score
                        }
                    )
                    candidates.append(candidate)
            
            # Sort by relevance score
            candidates.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return candidates[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error in keyword retrieval: {e}")
            return []
    
    async def _clustering_retrieval(
        self,
        query: str,
        max_results: int,
        min_relevance: float
    ) -> List[ContextCandidate]:
        """Perform cluster-based retrieval using semantic clusters."""
        try:
            if not self.semantic_manager or not self.semantic_manager.is_initialized:
                self.logger.warning("Semantic manager not available for clustering retrieval")
                return []
            
            # Generate query embedding
            query_embedding = encode_text(self.embedding_model, query)
            
            # Find similar clusters
            similar_clusters = await self.semantic_manager.find_similar_clusters(
                query_embedding, top_k=5
            )
            
            if not similar_clusters:
                return []
            
            candidates = []
            
            # Get memories from top similar clusters
            for cluster_id, cluster_similarity in similar_clusters:
                if cluster_similarity >= min_relevance:
                    cluster_memories = await self.semantic_manager.get_cluster_memories(cluster_id)
                    
                    for memory in cluster_memories:
                        candidate = ContextCandidate(
                            chunk_id=memory['chunk_id'],
                            content=memory['content'],
                            relevance_score=cluster_similarity * 0.8,  # Slight discount for cluster-based
                            retrieval_strategy=RetrievalStrategy.CLUSTERING,
                            metadata={
                                'file_name': memory.get('file_name', ''),
                                'chunk_index': memory.get('chunk_index', 0),
                                'cluster_id': cluster_id,
                                'cluster_similarity': cluster_similarity
                            }
                        )
                        candidates.append(candidate)
                        
                        if len(candidates) >= max_results:
                            break
                
                if len(candidates) >= max_results:
                    break
            
            # Sort by relevance score
            candidates.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return candidates[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error in clustering retrieval: {e}")
            return []
    
    async def _hybrid_retrieval(
        self,
        query: str,
        max_results: int,
        min_relevance: float
    ) -> List[ContextCandidate]:
        """Perform hybrid retrieval combining multiple strategies."""
        try:
            # Get results from each strategy
            semantic_results = await self._semantic_retrieval(query, max_results, min_relevance * 0.8)
            keyword_results = await self._keyword_retrieval(query, max_results, min_relevance * 0.7)
            clustering_results = await self._clustering_retrieval(query, max_results, min_relevance * 0.6)
            
            # Combine and deduplicate results
            combined_candidates = {}
            
            # Add semantic results with weight
            for candidate in semantic_results:
                weighted_score = candidate.relevance_score * self.strategy_weights[RetrievalStrategy.SEMANTIC]
                combined_candidates[candidate.chunk_id] = ContextCandidate(
                    chunk_id=candidate.chunk_id,
                    content=candidate.content,
                    relevance_score=weighted_score,
                    retrieval_strategy=RetrievalStrategy.HYBRID,
                    metadata={
                        **candidate.metadata,
                        'hybrid_components': ['semantic'],
                        'semantic_weight': self.strategy_weights[RetrievalStrategy.SEMANTIC]
                    }
                )
            
            # Add keyword results with weight
            for candidate in keyword_results:
                weighted_score = candidate.relevance_score * self.strategy_weights[RetrievalStrategy.KEYWORD]
                
                if candidate.chunk_id in combined_candidates:
                    # Combine scores
                    existing = combined_candidates[candidate.chunk_id]
                    existing.relevance_score += weighted_score
                    existing.metadata['hybrid_components'].append('keyword')
                    existing.metadata['keyword_weight'] = self.strategy_weights[RetrievalStrategy.KEYWORD]
                else:
                    combined_candidates[candidate.chunk_id] = ContextCandidate(
                        chunk_id=candidate.chunk_id,
                        content=candidate.content,
                        relevance_score=weighted_score,
                        retrieval_strategy=RetrievalStrategy.HYBRID,
                        metadata={
                            **candidate.metadata,
                            'hybrid_components': ['keyword'],
                            'keyword_weight': self.strategy_weights[RetrievalStrategy.KEYWORD]
                        }
                    )
            
            # Add clustering results with weight
            for candidate in clustering_results:
                weighted_score = candidate.relevance_score * self.strategy_weights[RetrievalStrategy.CLUSTERING]
                
                if candidate.chunk_id in combined_candidates:
                    # Combine scores
                    existing = combined_candidates[candidate.chunk_id]
                    existing.relevance_score += weighted_score
                    existing.metadata['hybrid_components'].append('clustering')
                    existing.metadata['clustering_weight'] = self.strategy_weights[RetrievalStrategy.CLUSTERING]
                else:
                    combined_candidates[candidate.chunk_id] = ContextCandidate(
                        chunk_id=candidate.chunk_id,
                        content=candidate.content,
                        relevance_score=weighted_score,
                        retrieval_strategy=RetrievalStrategy.HYBRID,
                        metadata={
                            **candidate.metadata,
                            'hybrid_components': ['clustering'],
                            'clustering_weight': self.strategy_weights[RetrievalStrategy.CLUSTERING]
                        }
                    )
            
            # Filter by minimum relevance and sort
            final_candidates = [
                candidate for candidate in combined_candidates.values()
                if candidate.relevance_score >= min_relevance
            ]
            
            final_candidates.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return final_candidates[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error in hybrid retrieval: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        try:
            # Simple keyword extraction
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            
            # Remove common stop words
            stop_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
                'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'could', 'should', 'may', 'might', 'must',
                'this', 'that', 'these', 'those'
            }
            
            keywords = [word for word in words if word not in stop_words and len(word) > 3]
            return list(set(keywords))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _calculate_keyword_relevance(self, query_keywords: List[str], content: str) -> float:
        """Calculate keyword-based relevance score."""
        try:
            content_lower = content.lower()
            matches = 0
            total_keyword_frequency = 0
            
            for keyword in query_keywords:
                if keyword in content_lower:
                    matches += 1
                    # Count frequency of keyword in content
                    frequency = content_lower.count(keyword)
                    total_keyword_frequency += frequency
            
            if not query_keywords:
                return 0.0
            
            # Calculate relevance as combination of match ratio and frequency
            match_ratio = matches / len(query_keywords)
            frequency_factor = min(1.0, total_keyword_frequency / 10.0)  # Cap at 1.0
            
            return (match_ratio * 0.7) + (frequency_factor * 0.3)
            
        except Exception as e:
            self.logger.error(f"Error calculating keyword relevance: {e}")
            return 0.0
    
    async def _get_chunks_with_embeddings(self) -> List[Dict[str, Any]]:
        """Get all chunks with their embeddings."""
        try:
            # This would ideally load pre-computed embeddings from database
            # For now, compute embeddings on-demand
            chunks = await self._get_all_chunks()
            
            for chunk in chunks:
                try:
                    embedding = encode_text(self.embedding_model, chunk['content'])
                    chunk['embedding'] = embedding
                except Exception as e:
                    self.logger.warning(f"Failed to generate embedding for chunk {chunk['chunk_id']}: {e}")
                    chunk['embedding'] = None
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error getting chunks with embeddings: {e}")
            return []
    
    async def _get_all_chunks(self) -> List[Dict[str, Any]]:
        """Get all chunks from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT rc.chunk_id, rc.content, rc.chunk_index,
                       r.file_name, r.created_at
                FROM resource_chunks rc
                JOIN resources r ON rc.resource_id = r.resource_id
                WHERE LENGTH(rc.content) > 10
                ORDER BY r.created_at DESC, rc.chunk_index
            """
            
            cursor.execute(query)
            chunks = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error fetching chunks: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check.
        
        Returns:
            Dictionary containing health status and metrics
        """
        try:
            health_status = {
                "healthy": self.is_initialized,
                "performance_score": 0.0,
                "component_name": "IntelligentContextRetrieval",
                "metrics": {
                    "initialized": self.is_initialized,
                    "embedding_model": self.embedding_model_name,
                    "default_strategy": self.default_strategy.value,
                    "semantic_manager_available": self.semantic_manager is not None and self.semantic_manager.is_initialized
                }
            }
            
            if self.is_initialized:
                # Test retrieval performance
                try:
                    test_result = await self.retrieve_context("test query", max_results=1)
                    health_status["performance_score"] = 0.9 if test_result.total_retrieved > 0 else 0.7
                except:
                    health_status["performance_score"] = 0.6  # Partial functionality
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "performance_score": 0.0,
                "error": str(e)
            }
    
    async def get_insights(self) -> Dict[str, Any]:
        """Get insights about context retrieval performance.
        
        Returns:
            Dictionary containing insights and recommendations
        """
        try:
            insights = {
                "status": "active" if self.is_initialized else "inactive",
                "component_name": "IntelligentContextRetrieval",
                "retrieval_strategies": {
                    "available": [s.value for s in RetrievalStrategy],
                    "default": self.default_strategy.value,
                    "weights": {k.value: v for k, v in self.strategy_weights.items()}
                },
                "recommendations": [],
                "performance_metrics": {}
            }
            
            if self.is_initialized:
                insights["recommendations"].append("System is operational and ready for context retrieval")
                
                if not self.semantic_manager or not self.semantic_manager.is_initialized:
                    insights["recommendations"].append("Semantic manager unavailable - clustering retrieval disabled")
                
                # Test basic retrieval
                try:
                    test_result = await self.retrieve_context("test", max_results=1)
                    insights["performance_metrics"]["test_retrieval_time"] = test_result.retrieval_time
                    insights["performance_metrics"]["test_results_found"] = test_result.total_retrieved
                except Exception as e:
                    insights["recommendations"].append(f"Retrieval test failed: {str(e)}")
            else:
                insights["recommendations"].append("Component needs initialization")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to get insights: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.semantic_manager:
                await self.semantic_manager.cleanup()
            
            self.embedding_model = None
            self.semantic_manager = None
            self.is_initialized = False
            self.logger.info("IntelligentContextRetrieval cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")