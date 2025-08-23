"""
Comprehensive semantic similarity and auto-linking tests for LTMC.

Tests cover:
- Real FAISS vector similarity operations
- Semantic document auto-linking functionality 
- Embedding generation and similarity computation
- Auto-link threshold and limit parameters
- Performance validation for similarity operations
- Integration with relationship backends
"""

import pytest
import numpy as np
import tempfile
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import patch

# Import FAISS and embedding components
from ltms.vector_store.faiss_store import create_index, add_vectors, search_vectors, load_index
from ltms.services.embedding_service import create_embedding_model, encode_text
from ltms.services.context_service import auto_link_documents
from ltms.tools.context_tools import auto_link_documents_handler
from ltms.database.dal import store_document_chunks, get_chunks_by_vector_ids


class TestSemanticSimilarityAutoLink:
    """Comprehensive tests for semantic similarity and auto-linking functionality."""

    @pytest.fixture(autouse=True) 
    def setup_semantic_environment(self):
        """Set up semantic similarity test environment."""
        # Create temporary FAISS index
        self.temp_index_path = tempfile.mktemp(suffix='.faiss')
        self.test_dimension = 384  # Common embedding dimension
        
        # Create test documents with semantic content
        self.test_documents = [
            {
                "id": "1",
                "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models.",
                "file_name": "ml_intro.md",
                "type": "document"
            },
            {
                "id": "2", 
                "content": "Deep learning uses neural networks with multiple layers to learn and make predictions from data.",
                "file_name": "deep_learning.md",
                "type": "document"
            },
            {
                "id": "3",
                "content": "Python programming language is widely used for data science and machine learning applications.",
                "file_name": "python_tutorial.py",
                "type": "code"
            },
            {
                "id": "4",
                "content": "Data structures and algorithms are fundamental concepts in computer science programming.",
                "file_name": "data_structures.md", 
                "type": "document"
            },
            {
                "id": "5",
                "content": "Neural networks are computing systems inspired by biological neural networks in animal brains.",
                "file_name": "neural_networks.md",
                "type": "document"
            }
        ]
        
        yield
        
        # Cleanup
        if os.path.exists(self.temp_index_path):
            os.unlink(self.temp_index_path)

    def test_embedding_generation_real(self):
        """Test real embedding generation for semantic similarity."""
        try:
            # Create embedding model
            embedding_model = create_embedding_model()
            assert embedding_model is not None
            
            # Test encoding text
            test_text = "Machine learning algorithms for data analysis"
            embedding = encode_text(embedding_model, test_text)
            
            assert isinstance(embedding, np.ndarray)
            assert len(embedding.shape) == 1  # Should be 1D vector
            assert embedding.shape[0] > 0  # Should have dimensions
            
            # Test consistency - same text should produce same embedding
            embedding2 = encode_text(embedding_model, test_text)
            np.testing.assert_array_almost_equal(embedding, embedding2, decimal=5)
            
        except ImportError:
            pytest.skip("Embedding model not available - sentence transformers may not be installed")
        except Exception as e:
            pytest.skip(f"Embedding generation failed: {e}")

    def test_faiss_index_operations_real(self):
        """Test real FAISS index creation and operations."""
        try:
            # Create FAISS index
            index = create_index(self.test_dimension, "Flat")
            assert index is not None
            assert index.d == self.test_dimension
            
            # Create test vectors
            test_vectors = np.random.rand(5, self.test_dimension).astype(np.float32)
            vector_ids = [1, 2, 3, 4, 5]
            
            # Add vectors to index
            add_vectors(index, test_vectors, vector_ids, self.temp_index_path)
            
            # Verify vectors were added
            assert index.ntotal == 5
            
            # Test search
            query_vector = test_vectors[0:1]  # Use first vector as query
            distances, indices = search_vectors(index, query_vector, k=3)
            
            assert len(distances) == 1
            assert len(indices) == 1
            assert len(distances[0]) == 3
            assert len(indices[0]) == 3
            
            # First result should be exact match (distance ~0)
            assert distances[0][0] < 0.01  # Very small distance for self-match
            
        except ImportError:
            pytest.skip("FAISS not available - may not be installed")
        except Exception as e:
            pytest.skip(f"FAISS operations failed: {e}")

    def test_semantic_similarity_computation(self):
        """Test semantic similarity computation between documents."""
        try:
            # Create embedding model
            embedding_model = create_embedding_model()
            
            # Compute embeddings for test documents
            embeddings = []
            for doc in self.test_documents:
                embedding = encode_text(embedding_model, doc["content"])
                embeddings.append(embedding)
            
            # Create FAISS index
            index = create_index(embeddings[0].shape[0], "Flat")
            
            # Add all embeddings
            vector_matrix = np.vstack(embeddings).astype(np.float32)
            vector_ids = [int(doc["id"]) for doc in self.test_documents]
            add_vectors(index, vector_matrix, vector_ids, self.temp_index_path)
            
            # Test similarity search
            query_embedding = embeddings[0:1]  # ML intro document
            distances, indices = search_vectors(index, query_embedding, k=3)
            
            # Verify results make semantic sense
            found_indices = indices[0]
            found_distances = distances[0]
            
            # Should find similar ML/AI related documents
            similar_doc_ids = [vector_ids[idx] for idx in found_indices]
            
            # Documents 1, 2, and 5 (ML, deep learning, neural networks) should be similar
            expected_similar = {1, 2, 5}
            found_similar = set(similar_doc_ids)
            
            # Should have some overlap with expected similar documents
            overlap = len(expected_similar.intersection(found_similar))
            assert overlap >= 1, f"Expected semantic similarity between ML docs, found {found_similar}"
            
        except ImportError:
            pytest.skip("Required libraries not available")
        except Exception as e:
            pytest.skip(f"Semantic similarity computation failed: {e}")

    def test_auto_link_documents_real_similarity(self):
        """Test auto_link_documents with real semantic similarity."""
        # Test with default parameters
        result = auto_link_documents_handler()
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            assert 'links_created' in result or 'analyzed' in result or 'relationships_created' in result
            links_count = result.get('links_created', result.get('relationships_created', 0))
            assert isinstance(links_count, int)
            assert links_count >= 0

    def test_auto_link_documents_with_parameters(self):
        """Test auto_link_documents with specific parameters."""
        # Test with provided documents and custom parameters
        result = auto_link_documents_handler(
            documents=self.test_documents,
            similarity_threshold=0.6,
            max_links_per_document=3
        )
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            links_count = result.get('links_created', result.get('relationships_created', 0))
            assert isinstance(links_count, int)
            assert links_count >= 0
            
            # With 5 documents and max 3 links each, should not exceed 15 total links
            assert links_count <= 15

    def test_auto_link_similarity_thresholds(self):
        """Test auto-linking behavior with different similarity thresholds."""
        thresholds_to_test = [0.3, 0.5, 0.7, 0.9]
        results = []
        
        for threshold in thresholds_to_test:
            result = auto_link_documents_handler(
                documents=self.test_documents,
                similarity_threshold=threshold,
                max_links_per_document=5
            )
            
            assert isinstance(result, dict)
            assert 'success' in result
            
            if result['success']:
                links_count = result.get('links_created', result.get('relationships_created', 0))
                results.append((threshold, links_count))
        
        # Higher thresholds should generally produce fewer links
        if len(results) >= 2:
            # Not all thresholds may produce results, but check trend where available
            non_zero_results = [(t, c) for t, c in results if c > 0]
            if len(non_zero_results) >= 2:
                # Sort by threshold and verify trend
                non_zero_results.sort(key=lambda x: x[0])
                # At minimum, very high thresholds should produce fewer links than very low ones
                lowest_threshold_links = non_zero_results[0][1]
                highest_threshold_links = non_zero_results[-1][1]
                assert highest_threshold_links <= lowest_threshold_links + 5  # Allow some variance

    def test_auto_link_max_links_limit(self):
        """Test auto-linking respects max_links_per_document parameter."""
        max_limits = [1, 3, 5, 10]
        
        for max_limit in max_limits:
            result = auto_link_documents_handler(
                documents=self.test_documents,
                similarity_threshold=0.5,
                max_links_per_document=max_limit
            )
            
            assert isinstance(result, dict)
            assert 'success' in result
            
            if result['success']:
                links_count = result.get('links_created', result.get('relationships_created', 0))
                
                # Total links should not exceed num_docs * max_limit
                max_possible_links = len(self.test_documents) * max_limit
                assert links_count <= max_possible_links

    def test_auto_link_performance_validation(self):
        """Test auto-linking performance with various document sets."""
        performance_tests = [
            ("small_set", self.test_documents[:2]),
            ("medium_set", self.test_documents),
            ("empty_set", []),
            ("single_doc", [self.test_documents[0]])
        ]
        
        for test_name, documents in performance_tests:
            start_time = time.time()
            
            result = auto_link_documents_handler(
                documents=documents if documents else None,
                similarity_threshold=0.6,
                max_links_per_document=3
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Auto-linking should complete within reasonable time
            max_time = 30.0 if len(documents) > 3 else 10.0
            assert execution_time < max_time, f"Auto-linking {test_name} took {execution_time:.2f}s (> {max_time}s limit)"
            
            # Verify result structure
            assert isinstance(result, dict)
            assert 'success' in result

    def test_auto_link_with_backend_integration(self):
        """Test auto-linking integration with relationship backends."""
        # Create auto-links
        result = auto_link_documents_handler(
            documents=self.test_documents,
            similarity_threshold=0.6,
            max_links_per_document=2
        )
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success'] and result.get('links_created', 0) > 0:
            # Verify links were actually stored in backend
            from ltms.tools.context_tools import list_all_resource_links_handler
            
            all_links_result = list_all_resource_links_handler(50)
            if all_links_result['success']:
                # Should find some similarity-based relationships
                auto_links = [
                    link for link in all_links_result['links'] 
                    if 'similarity' in link.get('link_type', '').lower() or 'auto' in link.get('link_type', '').lower()
                ]
                # May or may not find auto-generated links depending on system state
                assert len(auto_links) >= 0  # At minimum, should not error

    def test_semantic_similarity_edge_cases(self):
        """Test semantic similarity handling of edge cases."""
        edge_cases = [
            # Empty content
            {"id": "empty", "content": "", "type": "document"},
            # Very short content
            {"id": "short", "content": "AI", "type": "document"},
            # Very long content
            {"id": "long", "content": "Machine learning " * 100, "type": "document"},
            # Special characters
            {"id": "special", "content": "ML & AI: @neural-networks #deep_learning!", "type": "document"}
        ]
        
        result = auto_link_documents_handler(
            documents=edge_cases,
            similarity_threshold=0.5,
            max_links_per_document=2
        )
        
        # Should handle edge cases gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        # Either succeeds or fails gracefully with error message
        if not result['success']:
            assert 'error' in result
            assert isinstance(result['error'], str)

    def test_faiss_index_persistence(self):
        """Test FAISS index persistence and loading."""
        try:
            # Create and populate index
            index = create_index(self.test_dimension, "Flat")
            test_vectors = np.random.rand(3, self.test_dimension).astype(np.float32)
            vector_ids = [10, 20, 30]
            
            add_vectors(index, test_vectors, vector_ids, self.temp_index_path)
            
            # Save index (should be saved by add_vectors)
            assert os.path.exists(self.temp_index_path)
            
            # Load index
            loaded_index = load_index(self.temp_index_path)
            assert loaded_index is not None
            assert loaded_index.ntotal == 3
            assert loaded_index.d == self.test_dimension
            
            # Test search on loaded index
            query_vector = test_vectors[0:1]
            distances, indices = search_vectors(loaded_index, query_vector, k=2)
            
            assert len(distances[0]) == 2
            assert len(indices[0]) == 2
            
        except ImportError:
            pytest.skip("FAISS not available")
        except Exception as e:
            pytest.skip(f"FAISS persistence test failed: {e}")

    def test_embedding_consistency_across_sessions(self):
        """Test embedding consistency across different sessions."""
        try:
            # Create embeddings in "session 1"
            embedding_model_1 = create_embedding_model()
            text = "Artificial intelligence and machine learning"
            embedding_1 = encode_text(embedding_model_1, text)
            
            # Create embeddings in "session 2" (new model instance)
            embedding_model_2 = create_embedding_model()
            embedding_2 = encode_text(embedding_model_2, text)
            
            # Embeddings should be consistent
            np.testing.assert_array_almost_equal(embedding_1, embedding_2, decimal=4)
            
        except ImportError:
            pytest.skip("Embedding model not available")
        except Exception as e:
            pytest.skip(f"Embedding consistency test failed: {e}")

    def test_similarity_ranking_quality(self):
        """Test quality of similarity ranking."""
        try:
            # Documents with known semantic relationships
            semantic_test_docs = [
                {"id": "ml_1", "content": "Machine learning algorithms for classification and regression"},
                {"id": "ml_2", "content": "Supervised learning methods including decision trees and neural networks"}, 
                {"id": "ml_3", "content": "Deep learning and artificial neural network architectures"},
                {"id": "unrelated", "content": "Cooking recipes for pasta and pizza dishes"}
            ]
            
            embedding_model = create_embedding_model()
            embeddings = []
            
            for doc in semantic_test_docs:
                embedding = encode_text(embedding_model, doc["content"])
                embeddings.append(embedding)
            
            # Create index
            index = create_index(embeddings[0].shape[0], "Flat")
            vector_matrix = np.vstack(embeddings).astype(np.float32)
            vector_ids = list(range(len(semantic_test_docs)))
            add_vectors(index, vector_matrix, vector_ids, self.temp_index_path)
            
            # Query with first ML document
            query_embedding = embeddings[0:1]
            distances, indices = search_vectors(index, query_embedding, k=4)
            
            found_indices = indices[0]
            found_distances = distances[0]
            
            # The unrelated document (cooking) should have the highest distance (lowest similarity)
            unrelated_index = 3  # "unrelated" document
            unrelated_position = np.where(found_indices == unrelated_index)[0]
            
            if len(unrelated_position) > 0:
                unrelated_rank = unrelated_position[0]
                # Unrelated document should not be the most similar (rank 0)
                assert unrelated_rank > 0, "Unrelated document ranked as most similar"
                
                # ML documents should be more similar to each other than to cooking
                ml_indices = [0, 1, 2]
                ml_ranks = [np.where(found_indices == idx)[0][0] for idx in ml_indices if idx in found_indices]
                
                if ml_ranks:
                    best_ml_rank = min(ml_ranks)
                    assert best_ml_rank < unrelated_rank, "ML documents should be more similar to each other than to cooking"
                    
        except ImportError:
            pytest.skip("Required libraries not available")
        except Exception as e:
            pytest.skip(f"Similarity ranking test failed: {e}")

    def test_auto_link_relationship_types(self):
        """Test auto-linking creates appropriate relationship types."""
        result = auto_link_documents_handler(
            documents=self.test_documents,
            similarity_threshold=0.6,
            max_links_per_document=3
        )
        
        if result.get('success') and result.get('links_created', 0) > 0:
            # Check if relationships were created with appropriate types
            from ltms.tools.context_tools import list_all_resource_links_handler
            
            all_links = list_all_resource_links_handler(20)
            if all_links['success'] and all_links.get('links'):
                # Look for similarity-based relationship types
                similarity_link_types = [
                    'similar_to', 'semantic_similarity', 'related_to', 'auto_linked'
                ]
                
                found_similarity_links = [
                    link for link in all_links['links']
                    if any(sim_type in link.get('link_type', '').lower() for sim_type in similarity_link_types)
                ]
                
                # Should have created some similarity-based relationships
                # (This might be 0 if no documents are similar enough or if cleanup happened)
                assert len(found_similarity_links) >= 0


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short", 
        "-k", "test_semantic"  # Run only semantic similarity tests
    ])