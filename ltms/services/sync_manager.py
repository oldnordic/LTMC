"""
Documentation Sync Manager - Main orchestration component.

This module implements the main DocumentationSyncManager class that orchestrates
all documentation synchronization operations by utilizing the modularized components:

- DualSourceValidator: Blueprint vs code validation
- ChangeDetectionEngine: Real-time change monitoring  
- ConsistencyScorer: Detailed consistency metrics
- SyncModels: Data structures and exceptions

This maintains the original API while providing a clean, modular implementation.

Extracted from documentation_sync_service.py modularization.
"""

import time
import logging
from typing import Dict, Any, Optional, List

# Import modularized components
from ltms.services.sync_models import (
    SyncResult, 
    ConsistencyResult,
    ValidationFailureError
)
from ltms.services.dual_source_validator import DualSourceValidator
from ltms.services.change_detection_engine import ChangeDetectionEngine
from ltms.services.consistency_scorer import ConsistencyScorer

# Import supporting components
from ltms.database.neo4j_store import Neo4jGraphStore, get_neo4j_graph_store
from ltms.services.documentation_generator import DocumentationGenerator
from ltms.services.code_analyzer import CodeAnalyzer

logger = logging.getLogger(__name__)


class DocumentationSyncManager:
    """Main manager for documentation synchronization operations."""
    
    def __init__(
        self,
        neo4j_store: Neo4jGraphStore = None,
        documentation_generator: DocumentationGenerator = None
    ):
        """
        Initialize documentation sync manager.
        
        Args:
            neo4j_store: Neo4j graph store instance
            documentation_generator: Documentation generator instance
        """
        self.neo4j_store = neo4j_store or self._get_neo4j_store()
        self.documentation_generator = documentation_generator or self._get_documentation_generator()
        
        # Initialize modularized components
        self.dual_source_validator = DualSourceValidator(self.neo4j_store)
        self.change_detector = ChangeDetectionEngine()
        self.consistency_scorer = ConsistencyScorer()
        
        self._sync_status = {}
        self._real_time_monitoring = {}
    
    async def sync_documentation_with_code(
        self,
        file_path: str,
        project_id: str,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize documentation with code changes.
        
        Args:
            file_path: Path to code file to sync
            project_id: Project identifier
            force_update: Force update even if no changes detected
            
        Returns:
            Dict with synchronization results
        """
        start_time = time.perf_counter()
        
        try:
            # Validate inputs
            self._validate_sync_inputs(file_path, project_id)
            
            warnings = []
            blueprint_nodes_synced = 0
            blueprint_relationships_synced = 0
            documentation_updated = False
            consistency_score = 0.0
            
            # Check if Neo4j is available
            if not self.neo4j_store or not self.neo4j_store.is_available():
                warnings.append("neo4j_unavailable")
                logger.warning("Neo4j not available for synchronization")
            
            # Analyze current code structure
            code_analyzer = CodeAnalyzer()
            current_structure = code_analyzer.analyze_file(file_path, project_id)
            
            # If Neo4j is available, sync with blueprints
            if self.neo4j_store and self.neo4j_store.is_available():
                # Get existing blueprint structure (simplified)
                blueprint_result = await self._get_blueprint_structure(file_path, project_id)
                
                if blueprint_result["success"]:
                    blueprint_structure = blueprint_result["structure"]
                    
                    # Validate consistency using modularized validator
                    comparison = await self.dual_source_validator.compare_structures(
                        blueprint_structure,
                        file_path,
                        project_id
                    )
                    
                    if comparison["success"]:
                        consistency_score = comparison["consistency_score"]
                        
                        # Update blueprints if needed
                        if consistency_score < 0.90 or force_update:
                            update_result = await self._update_blueprint_from_code(
                                current_structure,
                                project_id
                            )
                            
                            if update_result["success"]:
                                blueprint_nodes_synced = update_result.get("nodes_updated", 0)
                                blueprint_relationships_synced = update_result.get("relationships_updated", 0)
            
            # Update documentation
            doc_result = await self._update_documentation_from_structure(
                current_structure,
                project_id
            )
            
            if doc_result["success"]:
                documentation_updated = True
            
            end_time = time.perf_counter()
            sync_time_ms = (end_time - start_time) * 1000
            
            return SyncResult(
                success=True,
                sync_time_ms=sync_time_ms,
                files_processed=1,
                documentation_updated=documentation_updated,
                blueprint_nodes_synced=blueprint_nodes_synced,
                blueprint_relationships_synced=blueprint_relationships_synced,
                consistency_score=consistency_score,
                warnings=warnings
            ).__dict__
            
        except Exception as e:
            end_time = time.perf_counter()
            sync_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Documentation sync failed for {file_path}: {e}")
            return SyncResult(
                success=False,
                sync_time_ms=sync_time_ms,
                files_processed=0,
                error_message=str(e)
            ).__dict__
    
    async def validate_documentation_consistency(
        self,
        file_path: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Validate consistency between documentation and code.
        
        Args:
            file_path: Path to Python file to validate
            project_id: Project identifier for isolation
            
        Returns:
            Dict with consistency validation results
        """
        start_time = time.perf_counter()
        
        try:
            # Get blueprint structure
            blueprint_result = await self._get_blueprint_structure(file_path, project_id)
            
            if not blueprint_result["success"]:
                return {
                    "success": False,
                    "error": f"Could not retrieve blueprint: {blueprint_result.get('error', 'unknown error')}"
                }
            
            blueprint_structure = blueprint_result["structure"]
            
            # Use modularized validator for consistency check
            comparison = await self.dual_source_validator.compare_structures(
                blueprint_structure,
                file_path,
                project_id
            )
            
            end_time = time.perf_counter()
            validation_time_ms = (end_time - start_time) * 1000
            
            if comparison["success"]:
                return ConsistencyResult(
                    success=True,
                    consistency_score=comparison["consistency_score"],
                    consistency_level=comparison["consistency_level"],
                    validation_time_ms=validation_time_ms,
                    total_nodes=comparison["total_nodes"],
                    matching_nodes=comparison["matching_nodes"],
                    inconsistencies=comparison["inconsistencies"]
                ).__dict__
            else:
                return ConsistencyResult(
                    success=False,
                    consistency_score=0.0,
                    consistency_level="LOW",
                    validation_time_ms=validation_time_ms,
                    error_message=comparison.get("error", "Validation failed")
                ).__dict__
            
        except Exception as e:
            end_time = time.perf_counter()
            validation_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Consistency validation failed: {e}")
            return ConsistencyResult(
                success=False,
                consistency_score=0.0,
                consistency_level="LOW",
                validation_time_ms=validation_time_ms,
                error_message=str(e)
            ).__dict__
    
    async def start_real_time_documentation_sync(
        self,
        file_paths: List[str],
        project_id: str,
        sync_interval_ms: int = 100
    ) -> Dict[str, Any]:
        """
        Start real-time documentation synchronization monitoring.
        
        Args:
            file_paths: List of file paths to monitor
            project_id: Project identifier for isolation
            sync_interval_ms: Monitoring interval in milliseconds
            
        Returns:
            Dict with sync monitoring status
        """
        try:
            # Start monitoring using modularized change detector
            for file_path in file_paths:
                self.change_detector.start_monitoring(file_path)
            
            # Register sync callback
            def sync_callback(file_path: str, change_type: str):
                logger.info(f"Real-time sync triggered: {file_path} ({change_type})")
                # In a full implementation, this would trigger async sync
            
            self.change_detector.register_sync_callback(sync_callback)
            
            self._real_time_monitoring[project_id] = {
                "file_paths": file_paths,
                "sync_interval_ms": sync_interval_ms,
                "monitoring": True,
                "started_at": time.time()
            }
            
            return {
                "success": True,
                "monitoring_active": True,
                "monitored_files": len(file_paths),
                "sync_interval_ms": sync_interval_ms,
                "project_id": project_id
            }
            
        except Exception as e:
            logger.error(f"Failed to start real-time sync: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    def _validate_sync_inputs(self, file_path: str, project_id: str):
        """Validate synchronization inputs."""
        if not file_path or not project_id:
            raise ValidationFailureError("file_path and project_id are required")
    
    def _get_neo4j_store(self) -> Optional[Neo4jGraphStore]:
        """Get Neo4j store instance."""
        try:
            return get_neo4j_graph_store()
        except Exception as e:
            logger.warning(f"Could not initialize Neo4j store: {e}")
            return None
    
    def _get_documentation_generator(self) -> Optional[DocumentationGenerator]:
        """Get documentation generator instance."""
        try:
            return DocumentationGenerator()
        except Exception as e:
            logger.warning(f"Could not initialize documentation generator: {e}")
            return None
    
    async def _get_blueprint_structure(self, file_path: str, project_id: str) -> Dict[str, Any]:
        """Get blueprint structure from Neo4j using real queries."""
        try:
            if not self.neo4j_store or not self.neo4j_store.is_available():
                return {"success": False, "error": "Neo4j store not available"}
            
            # Query Neo4j for nodes related to this file and project
            node_query = """
            MATCH (n)
            WHERE n.project_id = $project_id 
            AND (n.file_path = $file_path OR n.source_path = $file_path)
            RETURN n.name as name, 
                   n.node_id as node_id,
                   labels(n) as labels, 
                   n.docstring as docstring,
                   n.parameters as parameters,
                   n.return_type as return_type,
                   n.base_classes as base_classes,
                   n.file_path as file_path,
                   n.line_number as line_number
            """
            
            # Query for relationships
            rel_query = """
            MATCH (source)-[r]->(target)
            WHERE source.project_id = $project_id 
            AND target.project_id = $project_id
            AND (source.file_path = $file_path OR target.file_path = $file_path)
            RETURN source.name as source_name, 
                   target.name as target_name,
                   type(r) as rel_type,
                   r.type as rel_subtype
            """
            
            query_params = {"project_id": project_id, "file_path": file_path}
            
            # Execute queries using Neo4j store
            import asyncio
            
            node_results = await asyncio.get_event_loop().run_in_executor(
                None,
                self.neo4j_store.execute_read_query,
                node_query,
                query_params
            )
            
            rel_results = await asyncio.get_event_loop().run_in_executor(
                None,
                self.neo4j_store.execute_read_query,
                rel_query,
                query_params
            )
            
            # Convert results to CodeStructure
            from ltms.models.blueprint_schemas import (
                CodeStructure, BlueprintNode, FunctionNode, ClassNode, ModuleNode,
                BlueprintNodeType, BlueprintRelationship, RelationshipType
            )
            
            nodes = []
            if node_results:
                for record in node_results:
                    # Determine node type from labels
                    node_type = BlueprintNodeType.MODULE  # Default
                    if 'Function' in record.get('labels', []):
                        node_type = BlueprintNodeType.FUNCTION
                    elif 'Class' in record.get('labels', []):
                        node_type = BlueprintNodeType.CLASS
                    elif 'Module' in record.get('labels', []):
                        node_type = BlueprintNodeType.MODULE
                    
                    # Create appropriate node type
                    if node_type == BlueprintNodeType.FUNCTION:
                        node = FunctionNode(
                            node_id=record.get('node_id', record['name']),
                            name=record['name'],
                            project_id=project_id,
                            docstring=record.get('docstring'),
                            parameters=eval(record.get('parameters', '[]')) if record.get('parameters') else [],
                            return_type=record.get('return_type'),
                            file_path=record.get('file_path'),
                            line_number=record.get('line_number')
                        )
                    elif node_type == BlueprintNodeType.CLASS:
                        node = ClassNode(
                            node_id=record.get('node_id', record['name']),
                            name=record['name'],
                            project_id=project_id,
                            docstring=record.get('docstring'),
                            base_classes=eval(record.get('base_classes', '[]')) if record.get('base_classes') else [],
                            file_path=record.get('file_path'),
                            line_number=record.get('line_number')
                        )
                    else:
                        node = ModuleNode(
                            node_id=record.get('node_id', record['name']),
                            name=record['name'],
                            project_id=project_id,
                            docstring=record.get('docstring'),
                            file_path=record.get('file_path')
                        )
                    
                    nodes.append(node)
            
            # Convert relationships
            relationships = []
            if rel_results:
                for record in rel_results:
                    try:
                        rel_type = RelationshipType(record.get('rel_subtype', record['rel_type']))
                    except ValueError:
                        rel_type = RelationshipType.DEPENDS_ON  # Default fallback
                    
                    relationship = BlueprintRelationship(
                        source_id=record['source_name'],
                        target_id=record['target_name'],
                        relationship_type=rel_type,
                        project_id=project_id
                    )
                    relationships.append(relationship)
            
            # Create CodeStructure
            structure = CodeStructure(
                file_path=file_path,
                project_id=project_id,
                nodes=nodes,
                relationships=relationships
            )
            
            return {
                "success": True,
                "structure": structure,
                "nodes_found": len(nodes),
                "relationships_found": len(relationships)
            }
            
        except Exception as e:
            logger.error(f"Failed to get blueprint structure: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_blueprint_from_code(self, code_structure, project_id: str) -> Dict[str, Any]:
        """Update Neo4j blueprints from code structure using real Neo4j operations."""
        try:
            if not self.neo4j_store or not self.neo4j_store.is_available():
                return {"success": False, "error": "Neo4j store not available"}
            
            from ltms.models.blueprint_schemas import BlueprintNodeType
            import asyncio
            
            nodes_updated = 0
            relationships_updated = 0
            
            # Update each node in the code structure
            for node in code_structure.nodes:
                node_query = ""
                node_params = {
                    "project_id": project_id,
                    "node_name": node.name,
                    "node_id": getattr(node, 'node_id', f"{node.name}_{project_id}")
                }
                
                # Create different queries based on node type
                if node.node_type == BlueprintNodeType.MODULE:
                    node_query = """
                    MERGE (n:Module {name: $node_name, project_id: $project_id})
                    ON CREATE SET n.created_at = datetime(), n.node_id = $node_id
                    ON MATCH SET n.updated_at = datetime()
                    SET n.docstring = $docstring, n.file_path = $file_path
                    RETURN n
                    """
                    node_params.update({
                        "docstring": getattr(node, 'docstring', ''),
                        "file_path": getattr(node, 'file_path', '')
                    })
                    
                elif node.node_type == BlueprintNodeType.FUNCTION:
                    node_query = """
                    MERGE (n:Function {name: $node_name, project_id: $project_id})
                    ON CREATE SET n.created_at = datetime(), n.node_id = $node_id
                    ON MATCH SET n.updated_at = datetime()
                    SET n.docstring = $docstring, n.parameters = $parameters, n.return_type = $return_type, 
                        n.file_path = $file_path, n.line_number = $line_number, n.is_async = $is_async
                    RETURN n
                    """
                    node_params.update({
                        "docstring": getattr(node, 'docstring', ''),
                        "parameters": str(getattr(node, 'parameters', [])),
                        "return_type": getattr(node, 'return_type', ''),
                        "file_path": getattr(node, 'file_path', ''),
                        "line_number": getattr(node, 'line_number', 0),
                        "is_async": getattr(node, 'is_async', False)
                    })
                    
                elif node.node_type == BlueprintNodeType.CLASS:
                    node_query = """
                    MERGE (n:Class {name: $node_name, project_id: $project_id})
                    ON CREATE SET n.created_at = datetime(), n.node_id = $node_id
                    ON MATCH SET n.updated_at = datetime()
                    SET n.docstring = $docstring, n.base_classes = $base_classes,
                        n.file_path = $file_path, n.line_number = $line_number
                    RETURN n
                    """
                    node_params.update({
                        "docstring": getattr(node, 'docstring', ''),
                        "base_classes": str(getattr(node, 'base_classes', [])),
                        "file_path": getattr(node, 'file_path', ''),
                        "line_number": getattr(node, 'line_number', 0)
                    })
                
                # Execute node update query
                if node_query:
                    node_result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.neo4j_store.execute_write_query,
                        node_query,
                        node_params
                    )
                    
                    if node_result:
                        nodes_updated += 1
            
            # Update relationships
            for relationship in code_structure.relationships:
                rel_query = """
                MATCH (source {name: $source_name, project_id: $project_id})
                MATCH (target {name: $target_name, project_id: $project_id})
                MERGE (source)-[r:RELATES_TO {type: $rel_type}]->(target)
                ON CREATE SET r.created_at = datetime()
                ON MATCH SET r.updated_at = datetime()
                RETURN r
                """
                
                rel_params = {
                    "source_name": relationship.source_id,
                    "target_name": relationship.target_id,
                    "project_id": project_id,
                    "rel_type": str(relationship.relationship_type.value) if hasattr(relationship.relationship_type, 'value') else str(relationship.relationship_type)
                }
                
                rel_result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.neo4j_store.execute_write_query,
                    rel_query,
                    rel_params
                )
                
                if rel_result:
                    relationships_updated += 1
            
            return {
                "success": True,
                "nodes_updated": nodes_updated,
                "relationships_updated": relationships_updated,
                "total_nodes_processed": len(code_structure.nodes),
                "total_relationships_processed": len(code_structure.relationships)
            }
            
        except Exception as e:
            logger.error(f"Failed to update blueprint from code: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_documentation_from_structure(self, code_structure, project_id: str) -> Dict[str, Any]:
        """Update documentation from code structure using real documentation generation."""
        try:
            from ltms.services.real_documentation_generator import generate_documentation_from_file
            import os
            import asyncio
            from pathlib import Path
            
            # Extract file path from code structure (the file being analyzed)
            documented_files = []
            total_functions = 0
            total_classes = 0
            total_bytes = 0
            
            # Generate documentation for the analyzed file
            source_file = code_structure.file_path
            if source_file and os.path.exists(source_file):
                # Generate output file path
                output_dir = f"docs/ltmc_generated/{project_id}"
                os.makedirs(output_dir, exist_ok=True)
                
                file_name = Path(source_file).stem
                output_file = f"{output_dir}/{file_name}_api.md"
                
                # Run documentation generation in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    generate_documentation_from_file,
                    source_file,
                    output_file,
                    project_id
                )
                
                if result.get("success"):
                    documented_files.append(output_file)
                    total_functions += result.get("functions_documented", 0)
                    total_classes += result.get("classes_documented", 0)
                    total_bytes += result.get("bytes_written", 0)
                    
                    # Also create a summary file with structure information
                    summary_file = f"{output_dir}/{file_name}_structure.md"
                    structure_content = f"# Code Structure Analysis for {Path(source_file).name}\n\n"
                    structure_content += f"**Project ID**: {project_id}\n"
                    structure_content += f"**Analysis Date**: {asyncio.get_event_loop().time()}\n\n"
                    
                    if code_structure.nodes:
                        structure_content += f"## Nodes Found: {len(code_structure.nodes)}\n\n"
                        for node in code_structure.nodes:
                            structure_content += f"- **{node.name}** ({node.node_type.value})\n"
                            if hasattr(node, 'docstring') and node.docstring:
                                structure_content += f"  - {node.docstring[:100]}...\n"
                    
                    if code_structure.relationships:
                        structure_content += f"\n## Relationships Found: {len(code_structure.relationships)}\n\n"
                        for rel in code_structure.relationships:
                            structure_content += f"- {rel.source_id} → {rel.target_id} ({rel.relationship_type})\n"
                    
                    # Write structure summary
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        f.write(structure_content)
                    
                    documented_files.append(summary_file)
                    total_bytes += len(structure_content.encode('utf-8'))
                else:
                    return {"success": False, "error": f"Documentation generation failed: {result.get('error', 'unknown error')}"}
            else:
                return {"success": False, "error": f"Source file not found or invalid: {source_file}"}
            
            return {
                "success": True,
                "sections_updated": ["api_docs", "structure_analysis"],
                "documented_files": documented_files,
                "total_functions_documented": total_functions,
                "total_classes_documented": total_classes,
                "total_bytes_written": total_bytes,
                "output_directory": output_dir
            }
            
        except Exception as e:
            logger.error(f"Failed to update documentation from structure: {e}")
            return {"success": False, "error": str(e)}


# Global instance management
_sync_manager: Optional[DocumentationSyncManager] = None


async def get_documentation_sync_manager() -> DocumentationSyncManager:
    """Get or create documentation sync manager instance."""
    global _sync_manager
    if not _sync_manager:
        _sync_manager = DocumentationSyncManager()
    return _sync_manager