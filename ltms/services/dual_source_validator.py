"""
Dual-Source Validator for documentation synchronization system.

This module implements the dual-source validation system that ensures consistency
between Neo4j blueprints and actual code structures. It provides:

- Structure comparison between blueprints and code
- Node-level consistency validation
- Relationship validation
- Performance-optimized validation (<10ms target)

Extracted from documentation_sync_service.py modularization.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import data models from sync_models
from ltms.services.sync_models import ValidationFailureError

# Import supporting components
from ltms.models.blueprint_schemas import (
    BlueprintNode,
    FunctionNode,
    ClassNode,
    CodeStructure,
    ConsistencyLevel
)

from ltms.database.neo4j_store import Neo4jGraphStore
from ltms.tools.blueprint_tools import CodeAnalyzer

logger = logging.getLogger(__name__)


class DualSourceValidator:
    """Validates consistency between Neo4j blueprints and actual code."""
    
    def __init__(self, neo4j_store: Neo4jGraphStore = None):
        """
        Initialize dual-source validator.
        
        Args:
            neo4j_store: Neo4j graph store instance
        """
        self.neo4j_store = neo4j_store
        self.code_analyzer = CodeAnalyzer()
        self._validation_cache = {}
    
    async def compare_structures(
        self,
        blueprint_structure: CodeStructure,
        file_path: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Compare blueprint structure with actual code structure.
        
        Args:
            blueprint_structure: Blueprint structure from Neo4j
            file_path: Path to code file for comparison
            project_id: Project identifier for isolation
            
        Returns:
            Dict with comparison results and consistency score
        """
        start_time = time.perf_counter()
        
        try:
            # Validate inputs
            if not blueprint_structure or not file_path or not project_id:
                raise ValidationFailureError("blueprint_structure, file_path, and project_id are required")
            
            # Validate file exists and is readable
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise ValidationFailureError(f"File not found: {file_path}")
            
            if not file_path.endswith('.py'):
                raise ValidationFailureError(f"Only Python files supported: {file_path}")
            
            # Analyze current code structure
            current_structure = self.code_analyzer.analyze_file(file_path, project_id)
            
            # Compare structures
            comparison = self._compare_code_structures(blueprint_structure, current_structure)
            
            end_time = time.perf_counter()
            validation_time_ms = (end_time - start_time) * 1000
            
            return {
                "success": True,
                "consistency_score": comparison["consistency_score"],
                "consistency_level": comparison["consistency_level"],
                "total_nodes": comparison["total_nodes"],
                "matching_nodes": comparison["matching_nodes"],
                "inconsistencies": comparison["inconsistencies"],
                "node_details": comparison["node_details"],
                "relationship_details": comparison["relationship_details"],
                "validation_time_ms": validation_time_ms
            }
            
        except Exception as e:
            end_time = time.perf_counter()
            validation_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Structure comparison failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "validation_time_ms": validation_time_ms
            }
    
    def _compare_code_structures(
        self,
        blueprint_structure: CodeStructure,
        current_structure: CodeStructure
    ) -> Dict[str, Any]:
        """Compare two code structures and calculate consistency."""
        # Build lookup maps
        blueprint_nodes = {node.name: node for node in blueprint_structure.nodes}
        current_nodes = {node.name: node for node in current_structure.nodes}
        
        total_nodes = len(blueprint_nodes)
        matching_nodes = 0
        inconsistencies = []
        node_details = []
        
        # Compare nodes
        for name, blueprint_node in blueprint_nodes.items():
            if name in current_nodes:
                current_node = current_nodes[name]
                node_consistency = self._validate_node_consistency(blueprint_node, current_node)
                
                if node_consistency["is_consistent"]:
                    matching_nodes += 1
                else:
                    inconsistencies.append({
                        "type": "node_mismatch",
                        "node_name": name,
                        "differences": node_consistency["differences"]
                    })
                
                node_details.append({
                    "name": name,
                    "type": blueprint_node.node_type.value,
                    "consistent": node_consistency["is_consistent"],
                    "score": node_consistency["score"],
                    "differences": node_consistency["differences"]
                })
            else:
                inconsistencies.append({
                    "type": "missing_from_code",
                    "node_name": name,
                    "node_type": blueprint_node.node_type.value
                })
                node_details.append({
                    "name": name,
                    "type": blueprint_node.node_type.value,
                    "consistent": False,
                    "score": 0.0,
                    "differences": ["node_missing_from_code"]
                })
        
        # Check for nodes in current code but not in blueprint
        for name, current_node in current_nodes.items():
            if name not in blueprint_nodes:
                inconsistencies.append({
                    "type": "missing_from_blueprint",
                    "node_name": name,
                    "node_type": current_node.node_type.value
                })
                node_details.append({
                    "name": name,
                    "type": current_node.node_type.value,
                    "consistent": False,
                    "score": 0.0,
                    "differences": ["node_missing_from_blueprint"]
                })
        
        # Calculate consistency score
        if total_nodes == 0:
            consistency_score = 1.0
        else:
            consistency_score = matching_nodes / total_nodes
        
        # Determine consistency level
        if consistency_score >= 0.90:
            consistency_level = ConsistencyLevel.HIGH
        elif consistency_score >= 0.70:
            consistency_level = ConsistencyLevel.MEDIUM
        else:
            consistency_level = ConsistencyLevel.LOW
        
        # Compare relationships (simplified)
        blueprint_rels = len(blueprint_structure.relationships)
        current_rels = len(current_structure.relationships)
        rel_consistency = 1.0 if blueprint_rels == current_rels else 0.8
        
        return {
            "consistency_score": consistency_score,
            "consistency_level": consistency_level.value,
            "total_nodes": total_nodes,
            "matching_nodes": matching_nodes,
            "inconsistencies": inconsistencies,
            "node_details": node_details,
            "relationship_details": {
                "blueprint_relationships": blueprint_rels,
                "current_relationships": current_rels,
                "relationship_consistency": rel_consistency
            }
        }
    
    def _validate_node_consistency(
        self,
        blueprint_node: BlueprintNode,
        current_node: BlueprintNode
    ) -> Dict[str, Any]:
        """Validate consistency between two nodes."""
        differences = []
        score = 1.0
        
        # Compare basic properties
        if blueprint_node.node_type != current_node.node_type:
            differences.append(f"node_type: {blueprint_node.node_type} vs {current_node.node_type}")
            score -= 0.3
        
        # For function nodes, compare parameters and return types
        if isinstance(blueprint_node, FunctionNode) and isinstance(current_node, FunctionNode):
            if blueprint_node.parameters != current_node.parameters:
                differences.append(f"parameters: {blueprint_node.parameters} vs {current_node.parameters}")
                score -= 0.2
            
            if blueprint_node.return_type != current_node.return_type:
                differences.append(f"return_type: {blueprint_node.return_type} vs {current_node.return_type}")
                score -= 0.1
            
            if blueprint_node.is_async != current_node.is_async:
                differences.append(f"is_async: {blueprint_node.is_async} vs {current_node.is_async}")
                score -= 0.1
        
        # For class nodes, compare methods and base classes
        elif isinstance(blueprint_node, ClassNode) and isinstance(current_node, ClassNode):
            if blueprint_node.methods != current_node.methods:
                differences.append(f"methods: {blueprint_node.methods} vs {current_node.methods}")
                score -= 0.2
            
            if blueprint_node.base_classes != current_node.base_classes:
                differences.append(f"base_classes: {blueprint_node.base_classes} vs {current_node.base_classes}")
                score -= 0.1
        
        score = max(score, 0.0)  # Ensure score doesn't go negative
        is_consistent = score >= 0.8 and len(differences) == 0
        
        return {
            "is_consistent": is_consistent,
            "score": score,
            "differences": differences
        }