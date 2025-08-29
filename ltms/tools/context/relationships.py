"""
Context relationship management utilities for LTMC.
Handles relationship mapping, context linking, and relationship analysis.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class RelationshipManager:
    """Manages context relationships and link analysis."""
    
    # Standard relationship types used in LTMC
    RELATIONSHIP_TYPES = {
        "related_to": "General relationship between entities",
        "depends_on": "Entity depends on another entity",
        "implements": "Entity implements another entity",
        "extends": "Entity extends another entity",
        "uses": "Entity uses another entity",
        "references": "Entity references another entity",
        "contains": "Entity contains another entity",
        "part_of": "Entity is part of another entity",
        "similar_to": "Entity is similar to another entity",
        "conflicts_with": "Entity conflicts with another entity"
    }
    
    def __init__(self):
        """Initialize relationship manager."""
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def normalize_relationship_type(self, relation_type: str) -> str:
        """
        Normalize relationship type to standard format.
        
        Args:
            relation_type: Raw relationship type
            
        Returns:
            str: Normalized relationship type
        """
        if not relation_type:
            return "related_to"
        
        normalized = relation_type.lower().strip().replace(" ", "_")
        
        # Map common variations to standard types
        type_mappings = {
            "relates_to": "related_to",
            "depends": "depends_on",
            "dependency": "depends_on",
            "require": "depends_on",
            "requires": "depends_on",
            "implement": "implements",
            "implementation": "implements",
            "extend": "extends",
            "extension": "extends",
            "use": "uses",
            "usage": "uses",
            "utilize": "uses",
            "reference": "references",
            "ref": "references",
            "contain": "contains",
            "include": "contains",
            "includes": "contains",
            "partof": "part_of",
            "component": "part_of",
            "similar": "similar_to",
            "like": "similar_to",
            "conflict": "conflicts_with",
            "contradict": "conflicts_with"
        }
        
        return type_mappings.get(normalized, normalized)
    
    def validate_relationship_type(self, relation_type: str) -> bool:
        """
        Validate if relationship type is supported.
        
        Args:
            relation_type: Relationship type to validate
            
        Returns:
            bool: True if valid relationship type
        """
        normalized = self.normalize_relationship_type(relation_type)
        return normalized in self.RELATIONSHIP_TYPES
    
    def get_relationship_strength(self, relation_type: str) -> int:
        """
        Get relationship strength score (1-10).
        
        Args:
            relation_type: Relationship type
            
        Returns:
            int: Strength score
        """
        strength_mapping = {
            "depends_on": 9,
            "implements": 8,
            "extends": 8,
            "part_of": 7,
            "contains": 7,
            "uses": 6,
            "references": 5,
            "similar_to": 4,
            "related_to": 3,
            "conflicts_with": 2
        }
        
        normalized = self.normalize_relationship_type(relation_type)
        return strength_mapping.get(normalized, 3)
    
    def is_bidirectional_relationship(self, relation_type: str) -> bool:
        """
        Check if relationship type is bidirectional.
        
        Args:
            relation_type: Relationship type
            
        Returns:
            bool: True if bidirectional
        """
        bidirectional_types = {
            "related_to",
            "similar_to", 
            "conflicts_with"
        }
        
        normalized = self.normalize_relationship_type(relation_type)
        return normalized in bidirectional_types
    
    def get_inverse_relationship(self, relation_type: str) -> Optional[str]:
        """
        Get the inverse of a relationship type if applicable.
        
        Args:
            relation_type: Original relationship type
            
        Returns:
            Optional[str]: Inverse relationship or None
        """
        inverse_mapping = {
            "depends_on": "required_by",
            "implements": "implemented_by", 
            "extends": "extended_by",
            "uses": "used_by",
            "references": "referenced_by",
            "contains": "part_of",
            "part_of": "contains"
        }
        
        normalized = self.normalize_relationship_type(relation_type)
        return inverse_mapping.get(normalized)
    
    def analyze_relationship_chain(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a chain of relationships for patterns and insights.
        
        Args:
            relationships: List of relationship dictionaries
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        if not relationships:
            return {
                "total_relationships": 0,
                "unique_entities": 0,
                "relationship_types": {},
                "strongest_connections": [],
                "potential_cycles": [],
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Analyze relationship patterns
        entities = set()
        type_counts = {}
        strength_scores = []
        connections = []
        
        for rel in relationships:
            source = rel.get("source_id", "")
            target = rel.get("target_id", "")
            rel_type = rel.get("relation_type", rel.get("relation", ""))
            
            if source and target:
                entities.add(source)
                entities.add(target)
                
                normalized_type = self.normalize_relationship_type(rel_type)
                type_counts[normalized_type] = type_counts.get(normalized_type, 0) + 1
                
                strength = self.get_relationship_strength(normalized_type)
                strength_scores.append(strength)
                
                connections.append({
                    "source": source,
                    "target": target,
                    "type": normalized_type,
                    "strength": strength
                })
        
        # Find strongest connections
        strongest_connections = sorted(
            connections,
            key=lambda x: x["strength"],
            reverse=True
        )[:5]  # Top 5 strongest
        
        # Detect potential cycles (simplified)
        potential_cycles = self._detect_simple_cycles(connections)
        
        return {
            "total_relationships": len(relationships),
            "unique_entities": len(entities),
            "relationship_types": type_counts,
            "average_strength": sum(strength_scores) / len(strength_scores) if strength_scores else 0,
            "strongest_connections": strongest_connections,
            "potential_cycles": potential_cycles,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _detect_simple_cycles(self, connections: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Detect simple cycles in relationship graph.
        
        Args:
            connections: List of connection dictionaries
            
        Returns:
            List[List[str]]: List of detected cycles
        """
        # Build adjacency list
        graph = {}
        for conn in connections:
            source = conn["source"]
            target = conn["target"]
            
            if source not in graph:
                graph[source] = []
            graph[source].append(target)
        
        # Find cycles using DFS (limited to prevent infinite loops)
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if len(path) > 10:  # Prevent deep recursion
                return
            
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if len(cycle) <= 6:  # Only short cycles
                    cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        # Check each node as potential cycle start
        for node in list(graph.keys())[:20]:  # Limit to prevent excessive computation
            if node not in visited:
                dfs(node, [])
        
        return cycles[:5]  # Return max 5 cycles
    
    def suggest_related_entities(self, entity_id: str, existing_relationships: List[Dict[str, Any]], 
                               similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Suggest potentially related entities based on patterns.
        
        Args:
            entity_id: Target entity ID
            existing_relationships: Current relationships
            similarity_threshold: Minimum similarity for suggestions
            
        Returns:
            List[Dict[str, Any]]: Suggested relationships
        """
        if not existing_relationships:
            return []
        
        # Extract patterns from existing relationships
        connected_entities = set()
        relationship_patterns = {}
        
        for rel in existing_relationships:
            source = rel.get("source_id", "")
            target = rel.get("target_id", "")
            rel_type = rel.get("relation_type", rel.get("relation", ""))
            
            if source == entity_id:
                connected_entities.add(target)
                relationship_patterns[target] = rel_type
            elif target == entity_id:
                connected_entities.add(source)
                # Use inverse relationship if available
                inverse = self.get_inverse_relationship(rel_type)
                relationship_patterns[source] = inverse or rel_type
        
        # Simple suggestion algorithm based on relationship transitivity
        suggestions = []
        
        # Suggest entities that are connected to our connected entities
        for connected_entity in list(connected_entities)[:10]:  # Limit processing
            for rel in existing_relationships:
                source = rel.get("source_id", "")
                target = rel.get("target_id", "")
                rel_type = rel.get("relation_type", rel.get("relation", ""))
                
                suggested_entity = None
                suggested_type = "related_to"
                
                if source == connected_entity and target not in connected_entities and target != entity_id:
                    suggested_entity = target
                    # Suggest similar relationship type
                    if connected_entity in relationship_patterns:
                        suggested_type = relationship_patterns[connected_entity]
                
                elif target == connected_entity and source not in connected_entities and source != entity_id:
                    suggested_entity = source
                    # Suggest inverse relationship
                    inverse = self.get_inverse_relationship(rel_type)
                    suggested_type = inverse or "related_to"
                
                if suggested_entity:
                    suggestions.append({
                        "entity_id": suggested_entity,
                        "suggested_relation": suggested_type,
                        "confidence": 0.6,  # Base confidence
                        "reason": f"Connected via {connected_entity}"
                    })
        
        # Remove duplicates and limit results
        seen = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            entity = suggestion["entity_id"]
            if entity not in seen:
                seen.add(entity)
                unique_suggestions.append(suggestion)
            
            if len(unique_suggestions) >= 5:
                break
        
        return unique_suggestions


# Global relationship manager instance
relationship_manager = RelationshipManager()