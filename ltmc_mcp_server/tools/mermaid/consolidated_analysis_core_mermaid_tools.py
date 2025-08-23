"""
Consolidated Analysis Core Mermaid Tools - Unified Core Analysis & Pattern Detection
==================================================================================

Consolidated tool combining all 4 core analysis tools for Mermaid diagrams:
- analyze_relationships: Extract and analyze relationships
- detect_patterns: Pattern detection and recognition  
- suggest_improvements: AI-powered improvement suggestions
- compare_diagrams: Compare multiple diagrams for similarities

All functionality preserved through operation parameter.
"""

import re
from typing import Dict, Any, List
from collections import Counter

from mcp.server.fastmcp import FastMCP
from ltmc_mcp_server.config.settings import LTMCSettings
# Services imported for future extensibility
# from ltmc_mcp_server.services.mermaid_service import MermaidService
# from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_consolidated_analysis_core_mermaid_tools(
    mcp: FastMCP, settings: LTMCSettings
) -> None:
    """Register consolidated core analysis Mermaid tools with relationship mapping and pattern detection."""
    logger = get_tool_logger('consolidated_analysis_core_mermaid')
    logger.info("Registering consolidated core analysis Mermaid tools")
    
    # Initialize services
    # Note: Services initialized but not used in current implementation
    # Kept for future extensibility
    
    @mcp.tool()
    async def mermaid_core_analysis_manage(
        operation: str,
        content: str = None,
        diagram_type: str = None,
        extract_entities: bool = True,
        map_dependencies: bool = True,
        pattern_types: List[str] = None,
        improvement_areas: List[str] = None,
        diagram2_content: str = None,
        diagram2_type: str = None,
        comparison_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """
        Unified tool for all core Mermaid analysis operations.
        
        Args:
            operation: Operation to perform (analyze_relationships, detect_patterns, 
                       suggest_improvements, compare_diagrams)
            content: Mermaid diagram content (required for most operations)
            diagram_type: Type of diagram (required for most operations)
            extract_entities: Whether to extract entity information (for analyze_relationships)
            map_dependencies: Whether to map dependencies between entities (for analyze_relationships)
            pattern_types: Types of patterns to detect (for detect_patterns)
            improvement_areas: Areas to focus improvements on (for suggest_improvements)
            diagram2_content: Second diagram content (for compare_diagrams)
            diagram2_type: Second diagram type (for compare_diagrams)
            comparison_metrics: Metrics to compare (for compare_diagrams)
            
        Returns:
            Dict with operation results
        """
        
        if operation == "analyze_relationships":
            return await _analyze_relationships(content, diagram_type, extract_entities, map_dependencies)
        elif operation == "detect_patterns":
            return await _detect_patterns(content, diagram_type, pattern_types)
        elif operation == "suggest_improvements":
            return await _suggest_improvements(content, diagram_type, improvement_areas)
        elif operation == "compare_diagrams":
            return await _compare_diagrams(content, diagram_type, diagram2_content, diagram2_type, comparison_metrics)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Valid operations: analyze_relationships, detect_patterns, suggest_improvements, compare_diagrams"
            }
    
    async def _analyze_relationships(
        content: str,
        diagram_type: str,
        extract_entities: bool = True,
        map_dependencies: bool = True
    ) -> Dict[str, Any]:
        """Extract and analyze relationships within a Mermaid diagram."""
        try:
            if not content or not diagram_type:
                return {
                    "success": False,
                    "error": "Content and diagram_type are required"
                }
            
            # Parse diagram content
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            entities = []
            relationships = []
            dependencies = []
            
            # Entity extraction patterns
            entity_patterns = {
                'flowchart': r'(\w+)\[(.*?)\]',
                'class': r'class\s+(\w+)\s*\{',
                'sequence': r'participant\s+(\w+)',
                'state': r'(\w+)\s*:',
                'er': r'(\w+)\s*\{',
            }
            
            # Relationship patterns  
            relationship_patterns = {
                'flowchart': r'(\w+)\s*(-->|---)\s*(\w+)',
                'class': r'(\w+)\s*(--|\.\.|\<\|--|\*--)\s*(\w+)',
                'sequence': r'(\w+)->>(\w+)',
                'state': r'(\w+)\s*-->\s*(\w+)',
                'er': r'(\w+)\s*\|\|--\|\{\s*(\w+)'
            }
            
            dt_key = diagram_type.lower().replace('diagram', '').replace('chart', '')
            
            # Extract entities
            if extract_entities and dt_key in entity_patterns:
                pattern = entity_patterns[dt_key]
                for line in lines:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            entities.append({
                                "id": match[0],
                                "label": match[1] if len(match) > 1 else match[0],
                                "line": line
                            })
                        else:
                            entities.append({
                                "id": match,
                                "label": match,
                                "line": line
                            })
            
            # Extract relationships
            if dt_key in relationship_patterns:
                pattern = relationship_patterns[dt_key]
                for line in lines:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple) and len(match) >= 2:
                            relationships.append({
                                "from": match[0],
                                "to": match[1],
                                "type": match[2] if len(match) > 2 else "default",
                                "line": line
                            })
            
            # Map dependencies
            if map_dependencies:
                for rel in relationships:
                    dependencies.append({
                        "dependent": rel["from"],
                        "dependency": rel["to"],
                        "relationship_type": rel["type"]
                    })
            
            # Calculate metrics
            metrics = {
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "dependency_count": len(dependencies),
                "complexity_score": len(entities) + len(relationships) * 0.5,
                "connectivity_ratio": len(relationships) / max(len(entities), 1),
                "overall_health": "good" if len(entities) <= 15 and len(relationships) <= 30 else "needs_attention"
            }
            
            return {
                "success": True,
                "analysis": {
                    "entities": entities,
                    "relationships": relationships,
                    "dependencies": dependencies,
                    "metrics": metrics
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _detect_patterns(
        content: str,
        diagram_type: str,
        pattern_types: List[str] = None
    ) -> Dict[str, Any]:
        """Detect common patterns and anti-patterns in Mermaid diagrams."""
        try:
            if not content or not diagram_type:
                return {
                    "success": False,
                    "error": "Content and diagram_type are required"
                }
            
            patterns_detected = []
            anti_patterns = []
            recommendations = []
            
            # Analyze diagram structure
            analysis = await _analyze_relationships(content, diagram_type)
            if not analysis["success"]:
                return analysis
            
            entities = analysis["analysis"]["entities"]
            relationships = analysis["analysis"]["relationships"]
            metrics = analysis["analysis"]["metrics"]
            
            pattern_categories = pattern_types or ["structural", "design", "performance", "maintainability"]
            
            for category in pattern_categories:
                if category == "structural":
                    # Check for structural patterns
                    if len(entities) > 20:
                        patterns_detected.append({
                            "type": "large_diagram",
                            "description": f"Diagram contains {len(entities)} entities",
                            "severity": "medium",
                            "recommendation": "Consider breaking into smaller diagrams"
                        })
                    
                    # Check for hub-and-spoke pattern
                    connection_counts = Counter()
                    for rel in relationships:
                        connection_counts[rel["to"]] += 1
                        connection_counts[rel["from"]] += 1
                    
                    max_connections = max(connection_counts.values()) if connection_counts else 0
                    if max_connections > 5:
                        patterns_detected.append({
                            "type": "hub_and_spoke",
                            "description": f"Hub entity has {max_connections} connections",
                            "severity": "high",
                            "recommendation": "Review coupling and consider decomposition"
                        })
                
                elif category == "design":
                    # Check for design patterns
                    if diagram_type.lower() == "class":
                        # Inheritance depth
                        inheritance_chains = []
                        for rel in relationships:
                            if "inheritance" in rel["type"].lower():
                                inheritance_chains.append(rel)
                        
                        if len(inheritance_chains) > 3:
                            patterns_detected.append({
                                "type": "deep_inheritance",
                                "description": f"Deep inheritance chain with {len(inheritance_chains)} levels",
                                "severity": "medium",
                                "recommendation": "Consider composition over inheritance"
                            })
                
                elif category == "performance":
                    # Check for performance anti-patterns
                    if metrics["connectivity_ratio"] > 3:
                        anti_patterns.append({
                            "type": "high_coupling",
                            "description": f"High connectivity ratio: {metrics['connectivity_ratio']:.1f}",
                            "severity": "high",
                            "impact": "May cause performance issues and tight coupling"
                        })
                
                elif category == "maintainability":
                    # Check for maintainability issues
                    if metrics["complexity_score"] > 25:
                        anti_patterns.append({
                            "type": "high_complexity",
                            "description": f"High complexity score: {metrics['complexity_score']:.1f}",
                            "severity": "high",
                            "impact": "Difficult to maintain and understand"
                        })
            
            return {
                "success": True,
                "patterns": {
                    "detected": patterns_detected,
                    "anti_patterns": anti_patterns,
                    "recommendations": recommendations,
                    "overall_health": "good" if len(anti_patterns) < 2 else "needs_attention"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _suggest_improvements(
        content: str,
        diagram_type: str,
        improvement_areas: List[str] = None
    ) -> Dict[str, Any]:
        """Generate AI-powered suggestions for improving Mermaid diagrams."""
        try:
            if not content or not diagram_type:
                return {
                    "success": False,
                    "error": "Content and diagram_type are required"
                }
            
            suggestions = []
            priority_suggestions = []
            
            # Analyze current diagram
            analysis = await _analyze_relationships(content, diagram_type)
            if not analysis["success"]:
                return analysis
            
            entities = analysis["analysis"]["entities"]
            relationships = analysis["analysis"]["relationships"]
            metrics = analysis["analysis"]["metrics"]
            
            improvement_focus = improvement_areas or ["readability", "efficiency", "maintainability", "performance"]
            
            for area in improvement_focus:
                if area == "readability":
                    # Suggest readability improvements
                    if len(entities) > 15:
                        suggestions.append({
                            "area": "readability",
                            "suggestion": "Break diagram into smaller, focused diagrams",
                            "priority": "high",
                            "impact": "Improves understanding and reduces cognitive load",
                            "implementation": "Create separate diagrams for different concerns"
                        })
                    
                    # Check for long labels
                    long_labels = [e for e in entities if len(e["label"]) > 30]
                    if long_labels:
                        suggestions.append({
                            "area": "readability",
                            "suggestion": "Shorten entity labels for better readability",
                            "priority": "medium",
                            "impact": "Clearer visual representation",
                            "implementation": "Use concise, descriptive labels"
                        })
                
                elif area == "efficiency":
                    # Suggest efficiency improvements
                    if metrics["connectivity_ratio"] > 2.5:
                        suggestions.append({
                            "area": "efficiency",
                            "suggestion": "Reduce coupling between entities",
                            "priority": "high",
                            "impact": "Improves system performance and flexibility",
                            "implementation": "Review dependencies and remove unnecessary connections"
                        })
                
                elif area == "maintainability":
                    # Suggest maintainability improvements
                    if metrics["complexity_score"] > 20:
                        suggestions.append({
                            "area": "maintainability",
                            "suggestion": "Apply single responsibility principle",
                            "priority": "high",
                            "impact": "Easier to modify and extend",
                            "implementation": "Break complex entities into focused components"
                        })
                
                elif area == "performance":
                    # Suggest performance improvements
                    if len(relationships) > 50:
                        suggestions.append({
                            "area": "performance",
                            "suggestion": "Optimize relationship structure",
                            "priority": "medium",
                            "impact": "Better runtime performance",
                            "implementation": "Use intermediate entities to reduce direct connections"
                        })
            
            # Prioritize suggestions
            priority_suggestions = sorted(suggestions, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True)
            
            return {
                "success": True,
                "suggestions": {
                    "all": suggestions,
                    "prioritized": priority_suggestions,
                    "total_count": len(suggestions),
                    "high_priority_count": len([s for s in suggestions if s["priority"] == "high"])
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _compare_diagrams(
        diagram1_content: str,
        diagram1_type: str,
        diagram2_content: str,
        diagram2_type: str,
        comparison_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Compare two Mermaid diagrams for similarities and differences."""
        try:
            if not diagram1_content or not diagram1_type or not diagram2_content or not diagram2_type:
                return {
                    "success": False,
                    "error": "All diagram content and types are required"
                }
            
            comparison_results = {
                "similarities": [],
                "differences": [],
                "metrics_comparison": {},
                "overall_similarity": 0.0
            }
            
            # Analyze both diagrams
            analysis1 = await _analyze_relationships(diagram1_content, diagram1_type)
            analysis2 = await _analyze_relationships(diagram2_content, diagram2_type)
            
            if not analysis1["success"] or not analysis2["success"]:
                return {
                    "success": False,
                    "error": "Failed to analyze one or both diagrams"
                }
            
            entities1 = analysis1["analysis"]["entities"]
            relationships1 = analysis1["analysis"]["relationships"]
            metrics1 = analysis1["analysis"]["metrics"]
            
            entities2 = analysis2["analysis"]["entities"]
            relationships2 = analysis2["analysis"]["relationships"]
            metrics2 = analysis2["analysis"]["metrics"]
            
            comparison_focus = comparison_metrics or ["structure", "complexity", "entities", "relationships"]
            
            for metric in comparison_focus:
                if metric == "structure":
                    # Compare structural similarity
                    if diagram1_type.lower() == diagram2_type.lower():
                        comparison_results["similarities"].append({
                            "type": "structure",
                            "description": "Both diagrams use the same diagram type",
                            "similarity_score": 0.8
                        })
                    else:
                        comparison_results["differences"].append({
                            "type": "structure",
                            "description": f"Different diagram types: {diagram1_type} vs {diagram2_type}",
                            "difference_score": 0.6
                        })
                
                elif metric == "complexity":
                    # Compare complexity metrics
                    complexity_diff = abs(metrics1["complexity_score"] - metrics2["complexity_score"])
                    if complexity_diff < 5:
                        comparison_results["similarities"].append({
                            "type": "complexity",
                            "description": "Similar complexity levels",
                            "similarity_score": 0.9 - (complexity_diff / 10)
                        })
                    else:
                        comparison_results["differences"].append({
                            "type": "complexity",
                            "description": f"Complexity difference: {complexity_diff:.1f}",
                            "difference_score": min(complexity_diff / 20, 1.0)
                        })
                
                elif metric == "entities":
                    # Compare entity counts and types
                    entity_diff = abs(len(entities1) - len(entities2))
                    if entity_diff < 3:
                        comparison_results["similarities"].append({
                            "type": "entities",
                            "description": "Similar number of entities",
                            "similarity_score": 0.9 - (entity_diff / 10)
                        })
                    else:
                        comparison_results["differences"].append({
                            "type": "entities",
                            "description": f"Entity count difference: {entity_diff}",
                            "difference_score": min(entity_diff / 10, 1.0)
                        })
                
                elif metric == "relationships":
                    # Compare relationship patterns
                    rel_diff = abs(len(relationships1) - len(relationships2))
                    if rel_diff < 5:
                        comparison_results["similarities"].append({
                            "type": "relationships",
                            "description": "Similar relationship density",
                            "similarity_score": 0.9 - (rel_diff / 15)
                        })
                    else:
                        comparison_results["differences"].append({
                            "type": "relationships",
                            "description": f"Relationship count difference: {rel_diff}",
                            "difference_score": min(rel_diff / 15, 1.0)
                        })
            
            # Calculate overall similarity
            if comparison_results["similarities"]:
                avg_similarity = sum(s["similarity_score"] for s in comparison_results["similarities"]) / len(comparison_results["similarities"])
                comparison_results["overall_similarity"] = avg_similarity
            
            # Add metrics comparison
            comparison_results["metrics_comparison"] = {
                "diagram1": metrics1,
                "diagram2": metrics2,
                "differences": {
                    "complexity": metrics1["complexity_score"] - metrics2["complexity_score"],
                    "entities": len(entities1) - len(entities2),
                    "relationships": len(relationships1) - len(relationships2)
                }
            }
            
            return {
                "success": True,
                "comparison": comparison_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
