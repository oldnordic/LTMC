#!/usr/bin/env python3
"""
FAISS Index Synchronization Fix
Resolves the critical issue where FAISS index has fewer vectors than metadata indicates
"""

import sys
import os
import asyncio
import pickle
import numpy as np
from pathlib import Path

# Add LTMC to Python path
sys.path.insert(0, '/home/feanor/Projects/ltmc')

from ltms.database.faiss_manager import FAISSManager
from ltms.services.embedding_service import EmbeddingService
from ltms.config.json_config_loader import get_config
import faiss

async def fix_faiss_synchronization():
    print("=== FAISS SYNCHRONIZATION FIX ===")
    
    # Initialize config and services
    config = get_config()
    faiss_index_path = config.get_faiss_index_path()
    metadata_path = f"{faiss_index_path}.metadata"
    
    print(f"FAISS index path: {faiss_index_path}")
    print(f"Metadata path: {metadata_path}")
    
    # Load current metadata
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    
    doc_id_to_index = metadata.get('doc_id_to_index', {})
    print(f"Documents in metadata: {len(doc_id_to_index)}")
    
    # Load current index
    current_index = faiss.read_index(faiss_index_path)
    print(f"Vectors in current index: {current_index.ntotal}")
    
    # Find the gap
    max_metadata_index = max(doc_id_to_index.values()) if doc_id_to_index else -1
    print(f"Highest metadata index: {max_metadata_index}")
    print(f"Index gap: {max_metadata_index + 1 - current_index.ntotal} vectors missing")
    
    if max_metadata_index + 1 > current_index.ntotal:
        print("\n❌ SYNCHRONIZATION ISSUE CONFIRMED")
        print("Need to rebuild vectors for missing documents...")
        
        # Initialize FAISS manager for embedding generation
        temp_faiss_mgr = FAISSManager(test_mode=False)
        
        # Create new index with correct dimension
        dimension = 384  # all-MiniLM-L6-v2 dimension
        new_index = faiss.IndexFlatIP(dimension)
        
        # Rebuild all vectors from metadata
        print("\nRebuilding FAISS index from metadata...")
        
        # Sort documents by their index to maintain order
        sorted_docs = sorted(doc_id_to_index.items(), key=lambda x: x[1])
        
        vectors_to_add = []
        index_to_doc_id = {}
        
        for doc_id, expected_index in sorted_docs:
            doc_metadata_key = f"doc_{doc_id}"
            if doc_metadata_key in metadata:
                doc_info = metadata[doc_metadata_key]
                content = doc_info.get('content_preview', '')
                
                if content:
                    # Generate embedding using FAISS manager method
                    embedding = temp_faiss_mgr._generate_embedding(content)
                    vectors_to_add.append(embedding)
                    index_to_doc_id[len(vectors_to_add) - 1] = doc_id
                    
                    if len(vectors_to_add) % 100 == 0:
                        print(f"  Processed {len(vectors_to_add)} documents...")
        
        # Add all vectors to new index
        if vectors_to_add:
            vectors_array = np.array(vectors_to_add, dtype=np.float32)
            new_index.add(vectors_array)
            print(f"✅ Added {len(vectors_to_add)} vectors to new index")
        
        # Update metadata with correct mapping
        metadata['index_to_doc_id'] = index_to_doc_id
        
        # Save new index and metadata
        backup_index_path = f"{faiss_index_path}.backup"
        backup_metadata_path = f"{metadata_path}.backup"
        
        # Create backups
        os.rename(faiss_index_path, backup_index_path)
        os.rename(metadata_path, backup_metadata_path)
        
        # Save new files
        faiss.write_index(new_index, faiss_index_path)
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"✅ FAISS index rebuilt successfully")
        print(f"   New index vectors: {new_index.ntotal}")
        print(f"   Backup saved: {backup_index_path}")
        
        # Test the fix
        print("\n=== TESTING THE FIX ===")
        faiss_mgr = FAISSManager(test_mode=False)
        
        # Test search for our problematic document
        results = await faiss_mgr.search_similar_with_conversation_filter(
            'golden spiral fusion', k=5, conversation_id='unified_search_integration_test'
        )
        
        print(f"Test search results: {len(results)}")
        if results:
            for i, result in enumerate(results, 1):
                doc_id = result.get('doc_id', 'unknown')
                distance = result.get('distance', 1.0)
                conv_id = result.get('metadata', {}).get('conversation_id', 'none')
                print(f"  {i}. {doc_id} - conv: {conv_id} - distance: {distance:.4f}")
            
            print("🎉 FAISS SYNCHRONIZATION FIX SUCCESSFUL!")
        else:
            print("❌ Fix did not resolve the search issue")
    else:
        print("✅ No synchronization issue found")
    
    return True

if __name__ == "__main__":
    asyncio.run(fix_faiss_synchronization())