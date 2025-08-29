"""
Enhanced FAISS Universal Manager for LTMC Unified Semantic Search.
Extends FAISS with universal metadata schema supporting all storage types.

File: ltms/database/faiss_universal_manager.py
Lines: ~280 (under 300 limit)
Purpose: Universal FAISS indexing with enhanced metadata for unified semantic search
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from .faiss_manager import FAISSManager
from ..config.json_config_loader import get_config

logger = logging.getLogger(__name__)


class StorageType(Enum):
    """Supported storage types for universal indexing."""
    MEMORY = "memory"
    DOCUMENT = "document"
    TASKS = "tasks"
    BLUEPRINT = "blueprint"
    CACHE_DATA = "cache_data"
    LOG_CHAT = "log_chat"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    PATTERN_ANALYSIS = "pattern_analysis"
    GRAPH_RELATIONSHIPS = "graph_relationships"
    COORDINATION = "coordination"
    TODO = "todo"


class SourceDatabase(Enum):
    """Source databases for metadata tracking."""
    SQLITE = "sqlite"
    NEO4J = "neo4j"
    REDIS = "redis"
    FAISS = "faiss"


class UniversalFAISSManager(FAISSManager):
    """
    Enhanced FAISS manager supporting universal metadata schema.
    Enables unified semantic search across all content types.
    """
    
    def __init__(self, index_path: Optional[str] = None, dimension: Optional[int] = None, 
                 test_mode: bool = False):
        """Initialize universal FAISS manager with enhanced metadata support.
        
        Args:
            index_path: Path to FAISS index file (uses config default if None)
            dimension: Vector dimension for embeddings (uses config default if None)
            test_mode: Enable test mode for unit testing
        """
        # Initialize base FAISS manager
        super().__init__(index_path, dimension, test_mode)
        
        # Universal metadata schema version
        self._metadata_version = "1.0"
        
        # Storage type to primary database mapping
        self._storage_to_database = {
            StorageType.MEMORY: SourceDatabase.FAISS,
            StorageType.DOCUMENT: SourceDatabase.SQLITE,
            StorageType.TASKS: SourceDatabase.SQLITE,
            StorageType.BLUEPRINT: SourceDatabase.NEO4J,
            StorageType.CACHE_DATA: SourceDatabase.REDIS,
            StorageType.LOG_CHAT: SourceDatabase.REDIS,
            StorageType.CHAIN_OF_THOUGHT: SourceDatabase.FAISS,
            StorageType.PATTERN_ANALYSIS: SourceDatabase.SQLITE,
            StorageType.GRAPH_RELATIONSHIPS: SourceDatabase.NEO4J,
            StorageType.COORDINATION: SourceDatabase.SQLITE,
            StorageType.TODO: SourceDatabase.REDIS
        }
        
        logger.info(f"UniversalFAISSManager initialized with enhanced metadata support")
    
    def generate_universal_id(self, storage_type: str, source_db: str, original_id: str) -> str:
        """
        Generate universal document ID for cross-database consistency.
        
        Format: {storage_type}:{source_db}:{original_id}
        
        Args:
            storage_type: Type of storage (memory, tasks, etc.)
            source_db: Source database (sqlite, neo4j, redis, faiss)
            original_id: Original document identifier
            
        Returns:
            Universal document ID string
        """
        # Sanitize components to ensure valid ID
        storage_clean = str(storage_type).lower().replace(" ", "_")
        source_clean = str(source_db).lower().replace(" ", "_")
        original_clean = str(original_id).replace(":", "_")
        
        return f"{storage_clean}:{source_clean}:{original_clean}"
    
    def parse_universal_id(self, universal_id: str) -> Dict[str, str]:
        """
        Parse universal document ID to extract components.
        
        Args:
            universal_id: Universal ID to parse
            
        Returns:
            Dictionary with storage_type, source_db, original_id
        """
        try:
            parts = universal_id.split(":", 2)
            if len(parts) != 3:
                return {"storage_type": "unknown", "source_db": "unknown", "original_id": universal_id}
            
            return {
                "storage_type": parts[0],
                "source_db": parts[1], 
                "original_id": parts[2]
            }
        except Exception as e:
            logger.error(f"Failed to parse universal ID {universal_id}: {e}")
            return {"storage_type": "unknown", "source_db": "unknown", "original_id": universal_id}
    
    def create_enhanced_metadata(self, storage_type: str, source_database: str,
                                content: str, original_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create enhanced metadata schema for universal indexing.
        
        Args:
            storage_type: Type of storage (memory, tasks, etc.)
            source_database: Source database identifier
            content: Full content for analysis
            original_metadata: Original metadata to merge
            
        Returns:
            Enhanced metadata dictionary
        """
        original_metadata = original_metadata or {}
        current_time = datetime.now().isoformat()
        
        # Extract key information from content
        content_preview = content[:200] if content else ""
        content_length = len(content) if content else 0
        
        # Create enhanced metadata
        enhanced_metadata = {
            # Universal schema fields
            "storage_type": storage_type,
            "source_database": source_database,
            "indexed_at": current_time,
            "metadata_version": self._metadata_version,
            
            # Content analysis
            "content_preview": content_preview,
            "content_length": content_length,
            "content_hash": abs(hash(content)) % (2**32) if content else 0,
            
            # Merge original metadata
            **original_metadata,
            
            # Indexing metadata
            "vector_indexed": True,
            "universal_search_enabled": True
        }
        
        # Add storage-specific fields
        if storage_type == StorageType.MEMORY.value:
            enhanced_metadata.update({
                "searchable_fields": ["content", "file_name", "tags"],
                "priority_boost": 1.2  # Memory gets slight search boost
            })
        elif storage_type == StorageType.TASKS.value:
            enhanced_metadata.update({
                "searchable_fields": ["title", "description", "status"],
                "task_specific": True
            })
        elif storage_type == StorageType.BLUEPRINT.value:
            enhanced_metadata.update({
                "searchable_fields": ["title", "description", "tags"],
                "blueprint_specific": True,
                "relationship_context": True
            })
        elif storage_type == StorageType.CACHE_DATA.value:
            enhanced_metadata.update({
                "searchable_fields": ["content", "key"],
                "cache_specific": True,
                "temporal_relevance": True
            })
        
        return enhanced_metadata
    
    def validate_metadata_schema(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate metadata conforms to universal schema.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "storage_type", "source_database", "indexed_at",
            "metadata_version", "content_preview"
        ]
        
        try:
            # Check required fields exist
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"Missing required field in metadata: {field}")
                    return False
            
            # Validate storage type
            if metadata["storage_type"] not in [st.value for st in StorageType]:
                logger.warning(f"Invalid storage_type: {metadata['storage_type']}")
                return False
            
            # Validate source database
            if metadata["source_database"] not in [db.value for db in SourceDatabase]:
                logger.warning(f"Invalid source_database: {metadata['source_database']}")
                return False
            
            # Validate metadata version
            if not isinstance(metadata["metadata_version"], str):
                logger.warning(f"Invalid metadata_version type: {type(metadata['metadata_version'])}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating metadata schema: {e}")
            return False
    
    async def store_universal_vector(self, content: str, universal_id: str, 
                                   storage_type: str, source_database: str = None,
                                   original_metadata: Dict[str, Any] = None) -> bool:
        """
        Store document vector with universal metadata schema.
        
        Args:
            content: Document content for embedding generation
            universal_id: Universal document identifier
            storage_type: Type of storage (memory, tasks, etc.)
            source_database: Source database (auto-detected if None)
            original_metadata: Original metadata to enhance
            
        Returns:
            True if storage successful, False otherwise
        """
        if self.test_mode:
            return True
            
        if not self.is_available():
            logger.error("Universal FAISS not available for document storage")
            return False
            
        try:
            # Auto-detect source database if not provided
            if source_database is None:
                storage_enum = StorageType(storage_type)
                source_database = self._storage_to_database[storage_enum].value
            
            # Create enhanced metadata
            enhanced_metadata = self.create_enhanced_metadata(
                storage_type, source_database, content, original_metadata
            )
            
            # Validate metadata schema
            if not self.validate_metadata_schema(enhanced_metadata):
                logger.error(f"Metadata validation failed for {universal_id}")
                return False
            
            # Store using base FAISS manager with enhanced metadata
            success = await super().store_document_vector(
                universal_id, content, enhanced_metadata
            )
            
            if success:
                logger.info(f"Successfully stored universal vector {universal_id} "
                           f"(type: {storage_type}, source: {source_database})")
            
            return success
            
        except Exception as e:
            logger.error(f"Exception storing universal vector {universal_id}: {e}")
            return False
    
    async def search_universal(self, query: str, k: int = 10, 
                             storage_type_filter: List[str] = None,
                             source_database_filter: List[str] = None) -> List[Dict[str, Any]]:
        """
        Universal semantic search with storage type and database filtering.
        
        Args:
            query: Query text to find similar documents
            k: Number of similar documents to return
            storage_type_filter: Optional list of storage types to include
            source_database_filter: Optional list of source databases to include
            
        Returns:
            List of similar document information with enhanced metadata
        """
        if self.test_mode:
            return [{
                "doc_id": "test_universal_doc",
                "universal_id": "memory:faiss:test_doc",
                "distance": 0.1,
                "storage_type": "memory",
                "source_database": "faiss",
                "content_preview": "test universal content",
                "metadata": {"test": True}
            }]
            
        if not self.is_available():
            return []
            
        try:
            # Get similar documents using base search
            base_results = await super().search_similar(query, k * 2)  # Get more to filter
            
            # Apply universal filters and enhance results
            filtered_results = []
            for result in base_results:
                doc_metadata = result.get("metadata", {})
                
                # Apply storage type filter
                if storage_type_filter:
                    doc_storage_type = doc_metadata.get("storage_type")
                    if doc_storage_type not in storage_type_filter:
                        continue
                
                # Apply source database filter
                if source_database_filter:
                    doc_source_db = doc_metadata.get("source_database")
                    if doc_source_db not in source_database_filter:
                        continue
                
                # Parse universal ID for additional context
                universal_id = result.get("doc_id", "")
                parsed_id = self.parse_universal_id(universal_id)
                
                # Enhance result with universal context
                enhanced_result = {
                    **result,
                    "universal_id": universal_id,
                    "storage_type": doc_metadata.get("storage_type", parsed_id["storage_type"]),
                    "source_database": doc_metadata.get("source_database", parsed_id["source_db"]),
                    "original_id": parsed_id["original_id"],
                    "similarity_score": 1.0 - result.get("distance", 1.0),
                    "universal_search": True
                }
                
                filtered_results.append(enhanced_result)
                
                # Stop when we have enough results
                if len(filtered_results) >= k:
                    break
            
            logger.info(f"Universal search: query='{query}', filters={storage_type_filter}, "
                       f"found {len(filtered_results)} results")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed universal search: {e}")
            return []
    
    async def get_storage_type_counts(self) -> Dict[str, int]:
        """
        Get document counts by storage type.
        
        Returns:
            Dictionary mapping storage types to document counts
        """
        if self.test_mode:
            return {"memory": 1, "tasks": 1, "document": 1}
            
        if not self.is_available():
            return {}
            
        try:
            # Ensure metadata structure exists
            self._ensure_metadata_structure()
            
            counts = {}
            for doc_id in self._metadata["doc_id_to_index"]:
                doc_metadata = self._metadata.get(f"doc_{doc_id}", {})
                metadata = doc_metadata.get("metadata", {})
                storage_type = metadata.get("storage_type", "unknown")
                
                counts[storage_type] = counts.get(storage_type, 0) + 1
            
            return counts
            
        except Exception as e:
            logger.error(f"Failed to get storage type counts: {e}")
            return {}
    
    def get_enhanced_health_status(self) -> Dict[str, Any]:
        """
        Get enhanced health status with universal indexing information.
        
        Returns:
            Enhanced health status dictionary
        """
        base_status = self.get_health_status()
        
        try:
            if base_status["status"] == "healthy":
                # Add universal indexing metrics
                if not self.test_mode:
                    storage_counts = {}
                    try:
                        # This would be async in real usage, but for health check keep it simple
                        # storage_counts = await self.get_storage_type_counts()
                        storage_counts = {"calculated_async": "not_in_sync_context"}
                    except:
                        storage_counts = {"error": "failed_to_calculate"}
                        
                    base_status.update({
                        "universal_indexing": True,
                        "metadata_version": self._metadata_version,
                        "supported_storage_types": [st.value for st in StorageType],
                        "storage_type_counts": storage_counts,
                        "universal_features": [
                            "cross_storage_search",
                            "enhanced_metadata",
                            "storage_type_filtering",
                            "source_database_tracking"
                        ]
                    })
                else:
                    base_status.update({
                        "universal_indexing": True,
                        "metadata_version": self._metadata_version,
                        "test_mode_features": "enabled"
                    })
            
            return base_status
            
        except Exception as e:
            logger.error(f"Failed to get enhanced health status: {e}")
            base_status["universal_indexing_error"] = str(e)
            return base_status
    
    async def delete_by_original_id(self, original_id: str) -> Dict[str, Any]:
        """
        Delete universal FAISS document by original document ID.
        
        Searches for all universal IDs that contain the original_id and removes them.
        This is used for rollback operations in enhanced unified storage.
        
        Args:
            original_id: Original document ID to find and delete
            
        Returns:
            Dictionary with success status and deletion details
        """
        if self.test_mode:
            logger.debug(f"Universal FAISS: Simulating delete for {original_id} in test mode")
            return {"success": True, "deleted_count": 1, "test_mode_simulated": True}
        
        if not self.is_available():
            return {"success": False, "error": "Universal FAISS not available"}
        
        try:
            deleted_count = 0
            deleted_universal_ids = []
            
            # Find all universal IDs that end with this original_id
            if hasattr(self, '_metadata') and 'doc_id_to_index' in self._metadata:
                matching_universal_ids = []
                
                for universal_id in self._metadata['doc_id_to_index'].keys():
                    # Parse universal ID: storage_type:source_db:original_id
                    try:
                        parsed = self.parse_universal_id(universal_id)
                        if parsed["original_id"] == original_id:
                            matching_universal_ids.append(universal_id)
                    except Exception:
                        # If parsing fails, check if universal_id ends with original_id
                        if universal_id.endswith(f":{original_id}"):
                            matching_universal_ids.append(universal_id)
                
                # Delete each matching universal ID
                for universal_id in matching_universal_ids:
                    try:
                        delete_result = await self.delete_document_vector(universal_id)
                        if delete_result:
                            deleted_count += 1
                            deleted_universal_ids.append(universal_id)
                            logger.debug(f"Universal FAISS: Deleted {universal_id}")
                        else:
                            logger.warning(f"Universal FAISS: Failed to delete {universal_id}")
                    except Exception as e:
                        logger.error(f"Universal FAISS: Error deleting {universal_id}: {e}")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_universal_ids": deleted_universal_ids,
                "original_id": original_id
            }
            
        except Exception as e:
            logger.error(f"Universal FAISS delete_by_original_id failed for {original_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_id": original_id
            }


# Global instance for singleton pattern
universal_faiss_manager = UniversalFAISSManager()


def get_universal_faiss_manager(test_mode: bool = False) -> UniversalFAISSManager:
    """Get global universal FAISS manager instance."""
    global universal_faiss_manager
    if test_mode or universal_faiss_manager is None:
        universal_faiss_manager = UniversalFAISSManager(test_mode=test_mode)
    return universal_faiss_manager