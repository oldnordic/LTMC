"""
Consistency Scorer for documentation synchronization system.

This module implements the consistency scoring system that calculates detailed
consistency metrics between Neo4j blueprints and code structures. It provides:

- Weighted consistency scoring (<5ms target)
- Node-level consistency analysis
- Relationship consistency evaluation
- Detailed scoring breakdowns

Extracted from documentation_sync_service.py modularization.
"""

import time
import logging
from typing import Dict, List, Any, Union

# Import data models from sync_models
from ltms.services.sync_models import ConsistencyLevel

# Import supporting components
from ltms.models.blueprint_schemas import (
    BlueprintNode,
    FunctionNode,
    BlueprintRelationship,
    CodeStructure
)

logger = logging.getLogger(__name__)


class ConsistencyScorer:
    """Calculates consistency scores between blueprint and code structures."""
    
    def __init__(self):
        """Initialize consistency scorer."""
        self.scoring_weights = {
            "node_match": 0.4,
            "relationship_match": 0.2,
            "parameter_match": 0.2,
            "type_match": 0.1,
            "documentation_match": 0.1
        }
        
        self.consistency_thresholds = {
            ConsistencyLevel.HIGH: 0.90,
            ConsistencyLevel.MEDIUM: 0.70,
            ConsistencyLevel.LOW: 0.0
        }
    
    def calculate_consistency_score(
        self,
        blueprint_structure: CodeStructure,
        code_structure: Union[CodeStructure, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate consistency score between blueprint and code structures.
        
        Args:
            blueprint_structure: Blueprint structure from Neo4j
            code_structure: Code structure from AST analysis
            
        Returns:
            Dict with detailed consistency scoring results
        """
        start_time = time.perf_counter()
        
        try:
            # Handle code structure input formats
            if isinstance(code_structure, dict):
                code_nodes = code_structure.get("nodes", [])
                code_relationships = code_structure.get("relationships", [])
            else:
                code_nodes = [node.to_dict() for node in code_structure.nodes]
                code_relationships = [rel.to_dict() for rel in code_structure.relationships]
            
            # Calculate node consistency
            node_scores = self._calculate_node_consistency(
                blueprint_structure.nodes,
                code_nodes
            )
            
            # Calculate relationship consistency  
            rel_scores = self._calculate_relationship_consistency(
                blueprint_structure.relationships,
                code_relationships
            )
            
            # Calculate overall consistency score
            overall_score = (
                node_scores["score"] * self.scoring_weights["node_match"] +
                rel_scores["score"] * self.scoring_weights["relationship_match"] +
                node_scores["parameter_score"] * self.scoring_weights["parameter_match"] +
                node_scores["type_score"] * self.scoring_weights["type_match"] +
                node_scores["doc_score"] * self.scoring_weights["documentation_match"]
            )
            
            # Determine consistency level
            consistency_level = ConsistencyLevel.LOW
            for level, threshold in sorted(self.consistency_thresholds.items(), key=lambda x: x[1], reverse=True):
                if overall_score >= threshold:
                    consistency_level = level
                    break
            
            end_time = time.perf_counter()
            scoring_time_ms = (end_time - start_time) * 1000
            
            return {
                "success": True,
                "consistency_score": overall_score,
                "consistency_level": consistency_level.value,
                "node_consistency": node_scores["score"],
                "relationship_consistency": rel_scores["score"],
                "parameter_consistency": node_scores["parameter_score"],
                "type_consistency": node_scores["type_score"],
                "documentation_consistency": node_scores["doc_score"],
                "detailed_scores": {
                    "node_details": node_scores["details"],
                    "relationship_details": rel_scores["details"]
                },
                "scoring_time_ms": scoring_time_ms
            }
            
        except Exception as e:
            end_time = time.perf_counter()
            scoring_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Consistency scoring failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "scoring_time_ms": scoring_time_ms
            }
    
    def _calculate_node_consistency(
        self,
        blueprint_nodes: List[BlueprintNode],
        code_nodes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate consistency score for nodes."""
        if not blueprint_nodes and not code_nodes:
            return {
                "score": 1.0,
                "parameter_score": 1.0,
                "type_score": 1.0,
                "doc_score": 1.0,
                "details": []
            }
        
        if not blueprint_nodes or not code_nodes:
            return {
                "score": 0.0,
                "parameter_score": 0.0,
                "type_score": 0.0,
                "doc_score": 0.0,
                "details": []
            }
        
        # Build lookup maps
        blueprint_map = {node.name: node for node in blueprint_nodes}
        code_map = {node.get("name"): node for node in code_nodes}
        
        total_nodes = len(blueprint_map)
        matching_nodes = 0
        parameter_matches = 0
        type_matches = 0
        doc_matches = 0
        details = []
        
        for name, blueprint_node in blueprint_map.items():
            node_detail = {"name": name, "blueprint_type": blueprint_node.node_type.value}
            
            if name in code_map:
                code_node = code_map[name]
                node_detail["found_in_code"] = True
                node_detail["code_type"] = code_node.get("type", "unknown")
                
                # Check type match
                blueprint_type = blueprint_node.node_type.value.lower()
                code_type = code_node.get("type", "").lower()
                
                if blueprint_type == code_type:
                    matching_nodes += 1
                    type_matches += 1
                    node_detail["type_match"] = True
                else:
                    node_detail["type_match"] = False
                
                # Check parameters for functions
                if isinstance(blueprint_node, FunctionNode):
                    blueprint_params = blueprint_node.parameters or []
                    code_params = code_node.get("parameters", [])
                    
                    if self._compare_parameters(blueprint_params, code_params):
                        parameter_matches += 1
                        node_detail["parameter_match"] = True
                    else:
                        node_detail["parameter_match"] = False
                
                # Check documentation
                if blueprint_node.docstring and code_node.get("docstring"):
                    doc_matches += 1
                    node_detail["doc_match"] = True
                else:
                    node_detail["doc_match"] = False
            else:
                node_detail["found_in_code"] = False
                node_detail["type_match"] = False
                node_detail["parameter_match"] = False
                node_detail["doc_match"] = False
            
            details.append(node_detail)
        
        # Calculate scores
        node_score = matching_nodes / total_nodes if total_nodes > 0 else 0.0
        param_score = parameter_matches / total_nodes if total_nodes > 0 else 0.0
        type_score = type_matches / total_nodes if total_nodes > 0 else 0.0
        doc_score = doc_matches / total_nodes if total_nodes > 0 else 0.0
        
        return {
            "score": node_score,
            "parameter_score": param_score,
            "type_score": type_score,
            "doc_score": doc_score,
            "details": details
        }
    
    def _calculate_relationship_consistency(
        self,
        blueprint_relationships: List[BlueprintRelationship],
        code_relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate consistency score for relationships."""
        # Simplified relationship scoring
        blueprint_count = len(blueprint_relationships)
        code_count = len(code_relationships)
        
        if blueprint_count == 0 and code_count == 0:
            score = 1.0
        elif blueprint_count == 0 or code_count == 0:
            score = 0.0
        else:
            # Simple count-based scoring (could be enhanced)
            score = min(code_count, blueprint_count) / max(code_count, blueprint_count)
        
        return {
            "score": score,
            "details": {
                "blueprint_relationships": blueprint_count,
                "code_relationships": code_count,
                "relationship_ratio": score
            }
        }
    
    def _compare_parameters(
        self,
        blueprint_params: List[Dict[str, Any]],
        code_params: List[Dict[str, Any]]
    ) -> bool:
        """Compare function parameters for consistency."""
        if len(blueprint_params) != len(code_params):
            return False
        
        # Simple name-based comparison
        blueprint_names = set(param.get("name", "") for param in blueprint_params)
        code_names = set(param.get("name", "") for param in code_params)
        
        return blueprint_names == code_names