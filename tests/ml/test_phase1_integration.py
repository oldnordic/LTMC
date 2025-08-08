"""Integration test for Phase 1 ML implementation."""

import pytest
import pytest_asyncio
import sqlite3
import tempfile
import os
from ltms.ml.semantic_memory_manager import SemanticMemoryManager
from ltms.ml.intelligent_context_retrieval import IntelligentContextRetrieval, RetrievalStrategy
from ltms.ml.enhanced_tools import MLEnhancedTools


class TestPhase1Integration:
    """Integration tests for complete Phase 1 ML implementation."""

    @pytest.fixture
    def production_like_db(self):
        """Create a production-like database with realistic data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        conn = sqlite3.connect(db_path)
        
        # Create schema
        conn.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY,
                file_name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS resource_chunks (
                id INTEGER PRIMARY KEY,
                resource_id INTEGER,
                content TEXT NOT NULL,
                vector_id INTEGER,
                FOREIGN KEY (resource_id) REFERENCES resources (id)
            )
        ''')
        
        # Insert realistic ML/AI content
        resources = [
            (1, 'ml_fundamentals.md', 'Machine learning fundamentals and algorithms'),
            (2, 'deep_learning_guide.md', 'Deep learning neural networks and architectures'),
            (3, 'nlp_techniques.md', 'Natural language processing methods and applications'),
            (4, 'computer_vision.md', 'Computer vision algorithms and image processing'),
            (5, 'reinforcement_learning.md', 'Reinforcement learning and decision making'),
            (6, 'data_preprocessing.md', 'Data cleaning and preprocessing techniques'),
            (7, 'model_evaluation.md', 'Model evaluation metrics and validation strategies'),
            (8, 'feature_engineering.md', 'Feature selection and engineering approaches'),
            (9, 'optimization_algorithms.md', 'Optimization algorithms for machine learning'),
            (10, 'ensemble_methods.md', 'Ensemble learning and model combination techniques')
        ]
        
        chunks = [
            (1, 1, 'Supervised learning algorithms learn from labeled training data to make predictions on new examples', 1),
            (2, 1, 'Unsupervised learning discovers hidden patterns and structures in unlabeled data', 2),
            (3, 1, 'Classification algorithms predict discrete categories while regression predicts continuous values', 3),
            (4, 2, 'Convolutional neural networks excel at processing grid-like data such as images', 4),
            (5, 2, 'Recurrent neural networks handle sequential data with memory of previous inputs', 5),
            (6, 2, 'Transformer architectures use attention mechanisms for parallel processing of sequences', 6),
            (7, 3, 'Tokenization breaks text into individual words or subword units for processing', 7),
            (8, 3, 'Word embeddings represent words as dense vectors capturing semantic relationships', 8),
            (9, 3, 'Named entity recognition identifies and classifies entities like persons and organizations', 9),
            (10, 4, 'Image classification assigns labels to entire images based on visual content', 10),
            (11, 4, 'Object detection locates and identifies multiple objects within a single image', 11),
            (12, 4, 'Semantic segmentation assigns class labels to each pixel in an image', 12),
            (13, 5, 'Q-learning learns optimal actions through trial and error in dynamic environments', 13),
            (14, 5, 'Policy gradient methods directly optimize the policy function for better performance', 14),
            (15, 5, 'Actor-critic algorithms combine value function estimation with policy optimization', 15),
            (16, 6, 'Data normalization scales features to have similar ranges for better model performance', 16),
            (17, 6, 'Missing value imputation fills in gaps using statistical methods or learned patterns', 17),
            (18, 6, 'Outlier detection identifies unusual data points that may indicate errors or anomalies', 18),
            (19, 7, 'Cross-validation splits data into training and validation sets to assess generalization', 19),
            (20, 7, 'Precision and recall measure the accuracy of positive predictions in classification tasks', 20),
            (21, 7, 'ROC curves visualize the trade-off between sensitivity and specificity at various thresholds', 21),
            (22, 8, 'Feature selection removes irrelevant or redundant features to improve model efficiency', 22),
            (23, 8, 'Principal component analysis reduces dimensionality while preserving important variance', 23),
            (24, 8, 'Feature scaling ensures all features contribute equally to distance-based algorithms', 24),
            (25, 9, 'Gradient descent iteratively adjusts parameters to minimize the loss function', 25),
            (26, 9, 'Adam optimizer combines momentum and adaptive learning rates for efficient convergence', 26),
            (27, 9, 'Learning rate scheduling adjusts the step size during training for better optimization', 27),
            (28, 10, 'Random forests combine multiple decision trees to reduce overfitting and improve accuracy', 28),
            (29, 10, 'Boosting algorithms sequentially train weak learners to correct previous mistakes', 29),
            (30, 10, 'Voting ensembles combine predictions from multiple models using majority vote or averaging', 30)
        ]
        
        for res in resources:
            conn.execute("INSERT INTO resources (id, file_name, content) VALUES (?, ?, ?)", res)
        
        for chunk in chunks:
            conn.execute("INSERT INTO resource_chunks (id, resource_id, content, vector_id) VALUES (?, ?, ?, ?)", chunk)
        
        conn.commit()
        conn.close()
        
        yield db_path
        os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_complete_ml_pipeline(self, production_like_db):
        """Test the complete ML pipeline from clustering to intelligent retrieval."""
        # Initialize all components
        semantic_manager = SemanticMemoryManager(production_like_db)
        await semantic_manager.initialize()
        
        context_retrieval = IntelligentContextRetrieval(production_like_db)
        await context_retrieval.initialize()
        
        ml_tools = MLEnhancedTools(production_like_db)
        await ml_tools.initialize()
        
        try:
            # Step 1: Build semantic clusters
            print("Building semantic clusters...")
            clusters = await semantic_manager.cluster_memories(min_cluster_size=3)
            print(f"Created {len(clusters)} clusters")
            
            assert len(clusters) > 0, "Should create at least one cluster with realistic data"
            
            # Step 2: Test intelligent context retrieval with different strategies
            print("Testing intelligent context retrieval...")
            
            # Semantic retrieval
            semantic_results = await context_retrieval.retrieve_context(
                query="deep learning neural networks",
                strategy=RetrievalStrategy.SEMANTIC,
                max_results=5
            )
            
            assert len(semantic_results) > 0, "Should find semantic matches"
            assert all(result.context_type == "semantic" for result in semantic_results)
            
            # Hybrid retrieval
            hybrid_results = await context_retrieval.retrieve_context(
                query="machine learning optimization",
                strategy=RetrievalStrategy.HYBRID,
                max_results=5
            )
            
            assert len(hybrid_results) > 0, "Should find hybrid matches"
            
            # Clustering-based retrieval
            cluster_results = await context_retrieval.retrieve_context(
                query="supervised learning algorithms",
                strategy=RetrievalStrategy.CLUSTERING,
                max_results=5
            )
            
            # Step 3: Test enhanced ML tools
            print("Testing enhanced ML tools...")
            
            # Enhanced retrieval with explanations
            enhanced_result = await ml_tools.enhanced_retrieve_memory(
                query="neural network architectures",
                strategy="hybrid",
                max_results=5,
                include_explanations=True,
                cluster_insights=True
            )
            
            assert enhanced_result['success'] is True
            assert enhanced_result['results_count'] > 0
            assert len(enhanced_result['explanations']) > 0
            assert enhanced_result['insights'] != {}
            
            # Related memory suggestions
            if enhanced_result['results']:
                first_memory_id = enhanced_result['results'][0]['chunk_id']
                suggestions_result = await ml_tools.enhanced_suggest_related(
                    memory_id=first_memory_id,
                    max_suggestions=3,
                    include_cluster_context=True
                )
                
                assert suggestions_result['success'] is True
                print(f"Found {suggestions_result['suggestions_count']} related memories")
            
            # Comprehensive memory analysis
            print("Running comprehensive memory analysis...")
            analysis_result = await ml_tools.enhanced_memory_analysis(
                analysis_type="full",
                rebuild_clusters=False,  # Use existing clusters
                min_cluster_size=3
            )
            
            assert analysis_result['success'] is True
            assert 'cluster_summaries' in analysis_result
            assert 'coherence_analysis' in analysis_result
            assert 'memory_statistics' in analysis_result
            
            # Validate memory statistics
            stats = analysis_result['memory_statistics']
            assert stats['total_resources'] == 10
            assert stats['total_chunks'] == 30
            assert stats['total_clusters'] > 0
            
            print(f"Analysis complete: {stats['total_clusters']} clusters, {stats['clustered_memories']} clustered memories")
            
            # Step 4: Test retrieval explanations
            print("Testing retrieval explanations...")
            if semantic_results:
                explanation = await context_retrieval.explain_retrieval(semantic_results[0])
                assert 'reasoning' in explanation
                assert 'confidence' in explanation
                assert 'factors' in explanation
                assert explanation['confidence'] > 0
            
            print("✅ Complete ML pipeline test successful!")
            
        finally:
            # Cleanup
            await semantic_manager.cleanup()
            await context_retrieval.cleanup()
            await ml_tools.cleanup()

    @pytest.mark.asyncio
    async def test_ml_performance_characteristics(self, production_like_db):
        """Test ML performance characteristics and edge cases."""
        ml_tools = MLEnhancedTools(production_like_db)
        await ml_tools.initialize()
        
        try:
            # Test with various query types
            test_queries = [
                "machine learning",  # General term
                "convolutional neural networks",  # Specific technique
                "data preprocessing methods",  # Process-oriented
                "optimization algorithms Adam",  # Specific algorithm
                "ensemble learning techniques"  # Category
            ]
            
            for query in test_queries:
                print(f"Testing query: '{query}'")
                
                # Test different strategies
                for strategy in ["semantic", "keyword", "hybrid", "clustering"]:
                    result = await ml_tools.enhanced_retrieve_memory(
                        query=query,
                        strategy=strategy,
                        max_results=3
                    )
                    
                    assert result['success'] is True
                    print(f"  {strategy}: {result['results_count']} results")
                    
                    # Validate result structure
                    for res in result['results']:
                        assert 'chunk_id' in res
                        assert 'relevance_score' in res
                        assert 0.0 <= res['relevance_score'] <= 1.0
                        assert res['context_type'] in ['semantic', 'keyword', 'hybrid', 'cluster']
            
            # Test diversity filtering
            print("Testing diversity filtering...")
            diverse_result = await ml_tools.enhanced_suggest_related(
                memory_id=1,
                max_suggestions=5,
                diversity_threshold=0.5
            )
            
            assert diverse_result['success'] is True
            if diverse_result['suggestions_count'] > 1:
                # Check that suggestions are reasonably diverse
                contents = [s['content'][:50] for s in diverse_result['suggestions']]
                print(f"Diverse suggestions: {contents}")
            
            print("✅ Performance characteristics test successful!")
            
        finally:
            await ml_tools.cleanup()

    @pytest.mark.asyncio
    async def test_error_resilience(self, production_like_db):
        """Test error resilience and edge cases."""
        ml_tools = MLEnhancedTools(production_like_db)
        await ml_tools.initialize()
        
        try:
            # Test with empty query
            empty_result = await ml_tools.enhanced_retrieve_memory(
                query="",
                strategy="semantic"
            )
            assert empty_result['success'] in [True, False]  # Should handle gracefully
            
            # Test with very long query
            long_query = " ".join(["machine learning"] * 100)
            long_result = await ml_tools.enhanced_retrieve_memory(
                query=long_query,
                strategy="semantic",
                max_results=3
            )
            assert long_result['success'] is True
            
            # Test with non-existent memory ID
            invalid_suggestion = await ml_tools.enhanced_suggest_related(
                memory_id=99999
            )
            # Should handle gracefully without crashing
            assert 'success' in invalid_suggestion
            
            # Test with invalid strategy
            invalid_strategy_result = await ml_tools.enhanced_retrieve_memory(
                query="test query",
                strategy="invalid_strategy"
            )
            # Should fallback to hybrid or handle gracefully
            assert invalid_strategy_result['success'] is True
            
            print("✅ Error resilience test successful!")
            
        finally:
            await ml_tools.cleanup()

    @pytest.mark.asyncio 
    async def test_concurrent_operations(self, production_like_db):
        """Test concurrent ML operations."""
        import asyncio
        
        ml_tools = MLEnhancedTools(production_like_db)
        await ml_tools.initialize()
        
        try:
            # Test concurrent retrievals
            async def concurrent_retrieval(query_suffix):
                return await ml_tools.enhanced_retrieve_memory(
                    query=f"machine learning {query_suffix}",
                    strategy="hybrid",
                    max_results=3
                )
            
            # Run multiple retrievals concurrently
            tasks = [
                concurrent_retrieval("algorithms"),
                concurrent_retrieval("optimization"),
                concurrent_retrieval("neural networks"),
                concurrent_retrieval("data preprocessing")
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(result['success'] for result in results)
            
            # All should return results
            total_results = sum(result['results_count'] for result in results)
            assert total_results > 0
            
            print(f"✅ Concurrent operations successful! Total results: {total_results}")
            
        finally:
            await ml_tools.cleanup()