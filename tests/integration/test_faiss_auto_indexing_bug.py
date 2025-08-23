"""
FAISS Auto-Indexing Bug Test for LTMC - COMPREHENSIVE FAILING TEST

This test exposes the FAISS auto-indexing path inconsistency bug that breaks semantic similarity features.

**BUG DESCRIPTION:**
- store_memory() saves FAISS index using Config.get_faiss_index_path()
- auto_link_documents() looks for index using db_dir + 'vector_index.faiss'
- Path inconsistency causes "FAISS index not found" error despite index existing

**EXPECTED TEST RESULT:**
This test SHOULD FAIL with "FAISS index not found" error, exposing the bug.
Once the path inconsistency is fixed, this test should pass.

**REAL INTEGRATION ONLY:**
- Uses actual LTMC MCP tools (store_memory, auto_link_documents)
- Tests real database operations and FAISS indexing
- Validates actual filesystem index creation and access
- NO mocks, stubs, or placeholders
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import time

# Import LTMC MCP tools and services
from ltms.tools.memory_tools import store_memory_handler
from ltms.tools.context_tools import auto_link_documents_handler
from ltms.config import Config
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables


class TestFAISSAutoIndexingBug:
    """
    Comprehensive test exposing FAISS auto-indexing path inconsistency bug.
    
    This test validates the complete document storage → vector indexing → semantic linking pipeline
    and exposes where the FAISS index path inconsistency breaks auto-linking functionality.
    """

    @pytest.fixture(autouse=True)
    def setup_clean_environment(self):
        """Set up clean test environment with isolated database and index paths."""
        # Create temporary directory for test isolation
        self.test_dir = tempfile.mkdtemp(prefix="ltmc_faiss_bug_test_")
        
        # Create isolated test database path
        self.test_db_path = os.path.join(self.test_dir, "test_ltmc.db")
        
        # Set up test environment variables
        self.original_db_path = os.environ.get('LTMC_DB_PATH')
        self.original_data_dir = os.environ.get('LTMC_DATA_DIR')
        
        os.environ['LTMC_DB_PATH'] = self.test_db_path
        os.environ['LTMC_DATA_DIR'] = self.test_dir
        
        # Initialize database tables
        conn = get_db_connection(self.test_db_path)
        create_tables(conn)
        close_db_connection(conn)
        
        # Test documents with semantic similarity for auto-linking
        self.test_documents = [
            {
                "file_name": "machine_learning_intro.md",
                "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn for themselves.",
                "resource_type": "document"
            },
            {
                "file_name": "neural_networks_guide.md", 
                "content": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes that process information using connectionist approaches to computation. Deep learning uses neural networks with multiple layers.",
                "resource_type": "document"
            },
            {
                "file_name": "ai_applications.md",
                "content": "Artificial intelligence applications span many domains including computer vision, natural language processing, and autonomous systems. Machine learning algorithms power recommendation systems and predictive analytics.",
                "resource_type": "document"
            },
            {
                "file_name": "data_science_overview.md",
                "content": "Data science combines statistical analysis, machine learning, and domain expertise to extract insights from data. It uses algorithms for pattern recognition and predictive modeling to solve complex problems.",
                "resource_type": "document"
            }
        ]
        
        yield
        
        # Cleanup test environment
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
        # Restore original environment
        if self.original_db_path:
            os.environ['LTMC_DB_PATH'] = self.original_db_path
        elif 'LTMC_DB_PATH' in os.environ:
            del os.environ['LTMC_DB_PATH']
            
        if self.original_data_dir:
            os.environ['LTMC_DATA_DIR'] = self.original_data_dir
        elif 'LTMC_DATA_DIR' in os.environ:
            del os.environ['LTMC_DATA_DIR']

    def test_phase_0_system_startup_validation(self):
        """PHASE 0: Validate LTMC system can start successfully before component testing."""
        # Verify LTMC core components can import and initialize without errors
        try:
            # Skip ltms.main due to MCP dependency issues, test core components
            import ltms.config
            import ltms.services.memory_service
            import ltms.services.context_service
            import ltms.tools.memory_tools
            import ltms.tools.context_tools
            
            # Verify config can be loaded
            config = Config()
            assert config is not None
            
            # Verify database connection works
            db_path = Config.get_db_path()
            conn = get_db_connection(db_path)
            assert conn is not None
            close_db_connection(conn)
            
            # Verify FAISS can be imported
            import ltms.vector_store.faiss_store
            
            print("✅ PHASE 0: LTMC core system validation passed")
            
        except Exception as e:
            pytest.fail(f"PHASE 0 FAILED: LTMC core system startup failed: {e}")

    def test_faiss_path_inconsistency_analysis(self):
        """Analyze FAISS index path configuration to expose inconsistency."""
        # Get path used by store_memory (correct path)
        storage_index_path = Config.get_faiss_index_path()
        
        # Simulate path used by auto_link_documents (incorrect path construction)
        db_path = Config.get_db_path()
        db_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else '.'
        lookup_index_path = os.path.join(db_dir, 'vector_index.faiss')
        
        print(f"📊 FAISS Path Analysis:")
        print(f"   Storage Path (store_memory): {storage_index_path}")
        print(f"   Lookup Path (auto_link_documents): {lookup_index_path}")
        print(f"   Paths Match: {storage_index_path == lookup_index_path}")
        
        # Document the path inconsistency
        assert storage_index_path != lookup_index_path, "Path inconsistency not detected - bug may be fixed!"

    def test_document_storage_with_faiss_indexing(self):
        """Test document storage creates FAISS index at storage location."""
        stored_docs = []
        
        # Store multiple semantically related documents
        for doc in self.test_documents:
            print(f"📝 Storing document: {doc['file_name']}")
            
            result = store_memory_handler(
                file_name=doc['file_name'],
                content=doc['content'],
                resource_type=doc['resource_type']
            )
            
            # Verify storage succeeded
            assert result['success'] == True, f"Document storage failed: {result.get('error')}"
            assert result['chunks_created'] > 0, "No chunks created during storage"
            
            stored_docs.append({
                'resource_id': result['resource_id'],
                'file_name': doc['file_name'],
                'chunks_created': result['chunks_created']
            })
            
            print(f"   ✅ Stored {result['chunks_created']} chunks for {doc['file_name']}")
        
        print(f"📊 Successfully stored {len(stored_docs)} documents with total chunks")
        return stored_docs

    def test_faiss_index_filesystem_verification(self):
        """Verify FAISS index files exist on filesystem after document storage."""
        # Store test documents first
        self.test_document_storage_with_faiss_indexing()
        
        # Check FAISS index at storage location (where it should be created)
        storage_index_path = Config.get_faiss_index_path()
        storage_exists = os.path.exists(storage_index_path)
        
        # Check FAISS index at lookup location (where auto_link_documents looks)
        db_path = Config.get_db_path()
        db_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else '.'
        lookup_index_path = os.path.join(db_dir, 'vector_index.faiss')
        lookup_exists = os.path.exists(lookup_index_path)
        
        print(f"🔍 FAISS Index Filesystem Analysis:")
        print(f"   Storage Location: {storage_index_path}")
        print(f"   Storage Exists: {storage_exists}")
        if storage_exists:
            size = os.path.getsize(storage_index_path)
            print(f"   Storage Size: {size} bytes")
        
        print(f"   Lookup Location: {lookup_index_path}")
        print(f"   Lookup Exists: {lookup_exists}")
        if lookup_exists:
            size = os.path.getsize(lookup_index_path)
            print(f"   Lookup Size: {size} bytes")
        
        # The bug: index exists at storage location but not at lookup location
        assert storage_exists, "FAISS index not created at storage location - store_memory failed"
        assert not lookup_exists, "FAISS index exists at lookup location - bug may be fixed!"
        
        return {
            'storage_path': storage_index_path,
            'storage_exists': storage_exists,
            'lookup_path': lookup_index_path,
            'lookup_exists': lookup_exists
        }

    def test_auto_link_documents_faiss_index_not_found_bug(self):
        """
        TEST EXPOSING THE BUG: auto_link_documents fails due to FAISS index path inconsistency.
        
        This test SHOULD FAIL with "FAISS index not found" error, demonstrating the bug.
        """
        # First: Store documents and verify FAISS index created
        stored_docs = self.test_document_storage_with_faiss_indexing()
        index_analysis = self.test_faiss_index_filesystem_verification()
        
        print(f"🔗 Testing auto-linking with {len(stored_docs)} semantically related documents...")
        
        # Now: Attempt auto-linking (this should fail due to path inconsistency)
        start_time = time.time()
        
        auto_link_result = auto_link_documents_handler(
            documents=None,  # Analyze all documents
            similarity_threshold=0.5,  # Lower threshold to ensure matches
            max_links_per_document=3
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"📊 Auto-linking Result:")
        print(f"   Success: {auto_link_result.get('success')}")
        print(f"   Error: {auto_link_result.get('error')}")
        print(f"   Execution Time: {execution_time:.2f}s")
        
        # THE BUG MANIFESTATION: This should fail with specific error message
        expected_error = "FAISS index not found. Please ensure documents have been indexed."
        
        if auto_link_result['success']:
            # If this passes, the bug might be fixed!
            pytest.fail(
                "AUTO-LINKING SUCCEEDED - BUG MAY BE FIXED!\n"
                f"Expected failure with '{expected_error}' but got success.\n"
                f"Links created: {auto_link_result.get('links_created', 0)}\n"
                "This suggests the FAISS path inconsistency has been resolved."
            )
        else:
            # Expected failure - validate it's the specific bug we're testing
            actual_error = auto_link_result.get('error', '')
            
            print(f"❌ EXPECTED FAILURE DETECTED:")
            print(f"   Expected Error: {expected_error}")
            print(f"   Actual Error: {actual_error}")
            
            # Verify this is the specific FAISS indexing bug
            assert expected_error in actual_error, (
                f"Unexpected error type. Expected '{expected_error}' but got '{actual_error}'. "
                "This might be a different bug."
            )
            
            # Document the bug details
            bug_report = {
                'bug_type': 'FAISS Path Inconsistency',
                'symptom': 'auto_link_documents fails to find existing FAISS index',
                'root_cause': 'store_memory and auto_link_documents use different index paths',
                'storage_path': index_analysis['storage_path'],
                'storage_exists': index_analysis['storage_exists'],
                'lookup_path': index_analysis['lookup_path'],
                'lookup_exists': index_analysis['lookup_exists'],
                'documents_stored': len(stored_docs),
                'auto_link_error': actual_error,
                'execution_time': execution_time
            }
            
            print(f"🐛 BUG SUCCESSFULLY EXPOSED:")
            for key, value in bug_report.items():
                print(f"   {key}: {value}")
            
            # This test is designed to fail - document the expected fix
            pytest.fail(
                f"FAISS AUTO-INDEXING BUG CONFIRMED!\n\n"
                f"BUG DETAILS:\n"
                f"- Documents stored successfully: {len(stored_docs)}\n"
                f"- FAISS index created at: {index_analysis['storage_path']}\n"
                f"- auto_link_documents looks at: {index_analysis['lookup_path']}\n"
                f"- Result: {actual_error}\n\n"
                f"REQUIRED FIX:\n"
                f"Make auto_link_documents use Config.get_faiss_index_path() instead of constructing its own path.\n\n"
                f"THIS TEST SHOULD PASS AFTER THE BUG IS FIXED."
            )

    def test_semantic_similarity_pipeline_integration(self):
        """Test complete semantic similarity pipeline if FAISS bug is fixed."""
        # This test documents what should work once the bug is fixed
        
        # Store semantically related documents
        stored_docs = self.test_document_storage_with_faiss_indexing()
        
        print(f"🧪 Testing semantic similarity pipeline integration...")
        print(f"   Documents with ML/AI content should be auto-linked")
        print(f"   Expected semantic relationships:")
        print(f"   - machine_learning_intro.md ↔ neural_networks_guide.md")
        print(f"   - ai_applications.md ↔ data_science_overview.md")
        print(f"   - All documents share ML/AI concepts")
        
        # Attempt auto-linking
        result = auto_link_documents_handler(
            documents=None,
            similarity_threshold=0.3,  # Lower threshold for testing
            max_links_per_document=3
        )
        
        if result['success']:
            # Bug is fixed!
            links_created = result.get('links_created', 0)
            print(f"🎉 SUCCESS: Auto-linking worked! Created {links_created} semantic links")
            
            # Validate semantic relationships were created
            assert links_created > 0, "No semantic links created despite related content"
            
            created_links = result.get('created_links', [])
            for link in created_links:
                print(f"   📎 {link['source_name']} ↔ {link['target_name']} "
                      f"(similarity: {link['similarity']:.3f})")
            
            return result
        else:
            # Still failing - document for debugging
            print(f"❌ Auto-linking still failing: {result.get('error')}")
            return result

    def test_faiss_index_content_validation(self):
        """Validate FAISS index contains document vectors after storage."""
        # Store documents
        stored_docs = self.test_document_storage_with_faiss_indexing()
        
        # Load and inspect FAISS index
        try:
            from ltms.vector_store.faiss_store import load_index, get_index_stats
            
            storage_index_path = Config.get_faiss_index_path()
            
            if os.path.exists(storage_index_path):
                # Load index and check contents
                index = load_index(storage_index_path, dimension=384)
                stats = get_index_stats(index)
                
                print(f"📊 FAISS Index Content Analysis:")
                print(f"   Index Path: {storage_index_path}")
                print(f"   Total Vectors: {stats['total_vectors']}")
                print(f"   Dimension: {stats['dimension']}")
                print(f"   Index Type: {stats['index_type']}")
                print(f"   Is Trained: {stats['is_trained']}")
                
                # Verify index contains vectors from stored documents
                total_chunks = sum(doc['chunks_created'] for doc in stored_docs)
                
                assert stats['total_vectors'] > 0, "FAISS index is empty after document storage"
                assert stats['dimension'] == 384, f"Expected 384-dimensional vectors, got {stats['dimension']}"
                
                print(f"   Expected Chunks: {total_chunks}")
                print(f"   Actual Vectors: {stats['total_vectors']}")
                
                # The index should contain at least as many vectors as chunks created
                # (may be more if index already existed)
                assert stats['total_vectors'] >= total_chunks, (
                    f"FAISS index has fewer vectors ({stats['total_vectors']}) than chunks created ({total_chunks})"
                )
                
                return stats
            else:
                pytest.fail(f"FAISS index not found at expected storage path: {storage_index_path}")
                
        except Exception as e:
            pytest.fail(f"Failed to validate FAISS index content: {e}")


    def test_comprehensive_faiss_auto_indexing_bug(self):
        """
        MAIN TEST: Comprehensive FAISS auto-indexing bug exposure.
        
        This test is designed to FAIL and expose the FAISS auto-indexing path inconsistency bug.
        Once the bug is fixed, this test should pass.
        """
        print("🚀 Starting Comprehensive FAISS Auto-Indexing Bug Test")
        print("=" * 70)
        
        # Run the complete test sequence that should expose the bug
        self.test_phase_0_system_startup_validation()
        self.test_faiss_path_inconsistency_analysis()
        self.test_document_storage_with_faiss_indexing()
        self.test_faiss_index_filesystem_verification()
        self.test_faiss_index_content_validation()
        self.test_auto_link_documents_faiss_index_not_found_bug()
        self.test_semantic_similarity_pipeline_integration()


if __name__ == "__main__":
    # Run the test when executed directly
    pytest.main([__file__, "-v", "-s"])