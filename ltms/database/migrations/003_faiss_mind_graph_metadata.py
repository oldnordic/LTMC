"""
FAISS Mind Graph Metadata Enhancement
File: ltms/database/migrations/003_faiss_mind_graph_metadata.py
Purpose: Enhance FAISS metadata structure for Mind Graph integration
Status: Phase 1 - Real FAISS Implementation
"""

import pickle
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

class FAISSMindGraphMetadataMigration:
    """Real FAISS metadata migration for Mind Graph integration."""
    
    def __init__(self, faiss_index_path: str):
        """Initialize FAISS metadata migration.
        
        Args:
            faiss_index_path: Path to FAISS index file (without .metadata extension)
        """
        self.faiss_index_path = faiss_index_path
        self.metadata_path = f"{faiss_index_path}.metadata"
        self.backup_path = f"{faiss_index_path}.metadata.backup"
        self.migration_version = "003_faiss_mind_graph_metadata"
    
    def apply_migration(self) -> bool:
        """Apply FAISS metadata enhancement with real file operations.
        
        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            logger.info(f"Applying FAISS migration {self.migration_version}")
            
            # Check if metadata file exists
            if not os.path.exists(self.metadata_path):
                logger.error(f"FAISS metadata file not found: {self.metadata_path}")
                return False
            
            # Load current metadata
            current_metadata = self._load_current_metadata()
            if current_metadata is None:
                return False
            
            # Check if migration already applied
            if self._is_migration_applied(current_metadata):
                logger.info(f"FAISS migration {self.migration_version} already applied")
                return True
            
            # Create backup
            if not self._create_backup():
                return False
            
            # Enhance metadata structure
            enhanced_metadata = self._enhance_metadata_structure(current_metadata)
            
            # Save enhanced metadata
            if self._save_enhanced_metadata(enhanced_metadata):
                logger.info(f"FAISS migration {self.migration_version} applied successfully")
                return True
            else:
                # Restore from backup on failure
                self._restore_backup()
                return False
                
        except Exception as e:
            logger.error(f"FAISS migration failed: {e}")
            return False
    
    def _load_current_metadata(self) -> Optional[Dict[str, Any]]:
        """Load current FAISS metadata from pickle file."""
        try:
            with open(self.metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            logger.info("Loaded current FAISS metadata")
            return metadata
        except Exception as e:
            logger.error(f"Failed to load FAISS metadata: {e}")
            return None
    
    def _is_migration_applied(self, metadata: Dict[str, Any]) -> bool:
        """Check if migration is already applied."""
        return metadata.get('mind_graph_version') == self.migration_version
    
    def _create_backup(self) -> bool:
        """Create backup of current metadata file."""
        try:
            import shutil
            shutil.copy2(self.metadata_path, self.backup_path)
            logger.info(f"Created metadata backup: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def _restore_backup(self):
        """Restore metadata from backup."""
        try:
            import shutil
            shutil.copy2(self.backup_path, self.metadata_path)
            logger.info("Restored metadata from backup")
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
    
    def _enhance_metadata_structure(self, current_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata structure for Mind Graph integration."""
        enhanced_metadata = current_metadata.copy()
        
        # Add Mind Graph version tracking
        enhanced_metadata['mind_graph_version'] = self.migration_version
        enhanced_metadata['mind_graph_upgraded_at'] = datetime.now(timezone.utc).isoformat()
        
        # Enhance existing document metadata with Mind Graph fields
        for doc_key in enhanced_metadata.keys():
            if doc_key.startswith('doc_') and isinstance(enhanced_metadata[doc_key], dict):
                doc_metadata = enhanced_metadata[doc_key]
                
                # Add Mind Graph specific fields
                if 'metadata' not in doc_metadata:
                    doc_metadata['metadata'] = {}
                
                # Enhance metadata structure
                mind_graph_metadata = {
                    'mind_graph_nodes': [],  # Related Mind Graph node IDs
                    'reasoning_chain_id': None,  # Associated reasoning chain
                    'agent_id': None,  # Agent that created/modified this document
                    'context_tags': [],  # Semantic tags for better retrieval
                    'causal_links': [],  # Links to other documents in reasoning chain
                    'decision_context': None,  # Decision context when document was created
                    'change_tracking': {
                        'created_by_change_id': None,
                        'modified_by_change_ids': [],
                        'last_mind_graph_update': datetime.now(timezone.utc).isoformat()
                    }
                }
                
                # Merge with existing metadata, preserving original fields
                original_metadata = doc_metadata['metadata']
                doc_metadata['metadata'] = {**original_metadata, **mind_graph_metadata}
                
                logger.debug(f"Enhanced metadata for document: {doc_key}")
        
        # Add global Mind Graph statistics
        enhanced_metadata['mind_graph_stats'] = {
            'total_documents_enhanced': len([k for k in enhanced_metadata.keys() if k.startswith('doc_')]),
            'migration_applied_at': datetime.now(timezone.utc).isoformat(),
            'reasoning_chains_count': 0,  # Will be updated as chains are created
            'active_agents_count': 0,  # Will be updated as agents are tracked
            'total_causal_links': 0  # Will be updated as links are created
        }
        
        # Add Mind Graph query optimization data
        enhanced_metadata['mind_graph_query_optimization'] = {
            'semantic_clusters': {},  # For clustering related documents
            'reasoning_patterns': {},  # Common reasoning patterns
            'agent_patterns': {},  # Agent-specific document patterns
            'temporal_patterns': {}  # Time-based document patterns
        }
        
        logger.info(f"Enhanced {enhanced_metadata['mind_graph_stats']['total_documents_enhanced']} documents with Mind Graph metadata")
        
        return enhanced_metadata
    
    def _save_enhanced_metadata(self, enhanced_metadata: Dict[str, Any]) -> bool:
        """Save enhanced metadata to pickle file."""
        try:
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(enhanced_metadata, f)
            logger.info("Saved enhanced FAISS metadata")
            return True
        except Exception as e:
            logger.error(f"Failed to save enhanced metadata: {e}")
            return False
    
    def get_enhanced_document_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get enhanced metadata for specific document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Enhanced metadata dictionary or None
        """
        try:
            metadata = self._load_current_metadata()
            if metadata is None:
                return None
            
            doc_key = f"doc_{doc_id}"
            return metadata.get(doc_key, {}).get('metadata', {})
            
        except Exception as e:
            logger.error(f"Failed to get document metadata: {e}")
            return None
    
    def update_document_mind_graph_data(self, doc_id: str, 
                                       mind_graph_nodes: List[str] = None,
                                       reasoning_chain_id: str = None,
                                       agent_id: str = None,
                                       context_tags: List[str] = None,
                                       change_id: str = None) -> bool:
        """Update Mind Graph data for specific document.
        
        Args:
            doc_id: Document ID
            mind_graph_nodes: List of related Mind Graph node IDs
            reasoning_chain_id: Associated reasoning chain ID
            agent_id: Agent that modified this document
            context_tags: Semantic context tags
            change_id: Change ID that modified this document
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            metadata = self._load_current_metadata()
            if metadata is None:
                return False
            
            doc_key = f"doc_{doc_id}"
            if doc_key not in metadata:
                logger.error(f"Document not found in metadata: {doc_id}")
                return False
            
            doc_metadata = metadata[doc_key].get('metadata', {})
            
            # Update Mind Graph fields
            if mind_graph_nodes is not None:
                doc_metadata['mind_graph_nodes'] = mind_graph_nodes
            
            if reasoning_chain_id is not None:
                doc_metadata['reasoning_chain_id'] = reasoning_chain_id
            
            if agent_id is not None:
                doc_metadata['agent_id'] = agent_id
            
            if context_tags is not None:
                doc_metadata['context_tags'] = context_tags
            
            if change_id is not None:
                if 'change_tracking' not in doc_metadata:
                    doc_metadata['change_tracking'] = {'modified_by_change_ids': []}
                doc_metadata['change_tracking']['modified_by_change_ids'].append(change_id)
                doc_metadata['change_tracking']['last_mind_graph_update'] = datetime.now(timezone.utc).isoformat()
            
            # Save updated metadata
            return self._save_enhanced_metadata(metadata)
            
        except Exception as e:
            logger.error(f"Failed to update document Mind Graph data: {e}")
            return False


def apply_faiss_mind_graph_migration(faiss_index_path: str) -> bool:
    """Apply FAISS Mind Graph metadata migration.
    
    Args:
        faiss_index_path: Path to FAISS index file
        
    Returns:
        bool: True if successful, False otherwise
    """
    migration = FAISSMindGraphMetadataMigration(faiss_index_path)
    return migration.apply_migration()


def test_faiss_migration(faiss_index_path: str) -> bool:
    """Test FAISS metadata migration."""
    try:
        migration = FAISSMindGraphMetadataMigration(faiss_index_path)
        
        # Load enhanced metadata
        metadata = migration._load_current_metadata()
        if metadata is None:
            print("❌ Could not load FAISS metadata")
            return False
        
        # Check if migration was applied
        if metadata.get('mind_graph_version') == migration.migration_version:
            print("✅ FAISS migration successfully applied")
            
            # Check enhanced structure
            stats = metadata.get('mind_graph_stats', {})
            documents_enhanced = stats.get('total_documents_enhanced', 0)
            print(f"✅ Enhanced {documents_enhanced} documents with Mind Graph metadata")
            
            # Test document metadata enhancement
            doc_keys = [k for k in metadata.keys() if k.startswith('doc_')]
            if doc_keys:
                sample_doc = metadata[doc_keys[0]]
                doc_metadata = sample_doc.get('metadata', {})
                
                # Check for Mind Graph fields
                required_fields = ['mind_graph_nodes', 'reasoning_chain_id', 'agent_id', 'context_tags']
                missing_fields = [f for f in required_fields if f not in doc_metadata]
                
                if not missing_fields:
                    print("✅ Document metadata enhancement successful")
                    return True
                else:
                    print(f"❌ Missing Mind Graph fields: {missing_fields}")
                    return False
            else:
                print("⚠️  No documents found to test enhancement")
                return True  # Migration applied but no documents to enhance
        else:
            print("❌ FAISS migration not properly applied")
            return False
            
    except Exception as e:
        print(f"❌ FAISS migration test failed: {e}")
        return False


if __name__ == "__main__":
    import os
    
    data_dir = os.environ.get('LTMC_DATA_DIR', '/home/feanor/Projects/Data')
    faiss_index_path = os.path.join(data_dir, 'faiss_index')
    
    print(f"Testing FAISS Mind Graph metadata migration on {faiss_index_path}")
    
    if apply_faiss_mind_graph_migration(faiss_index_path):
        print("✅ FAISS migration applied successfully")
        
        # Test the migration
        if test_faiss_migration(faiss_index_path):
            print("✅ FAISS migration test passed")
        else:
            print("❌ FAISS migration test failed")
    else:
        print("❌ FAISS migration failed")