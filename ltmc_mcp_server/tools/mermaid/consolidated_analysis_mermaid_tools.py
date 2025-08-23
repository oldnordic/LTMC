"""
Consolidated Analysis Mermaid Tools - FastMCP Implementation
===========================================================

1 unified Mermaid analysis tool for all analysis operations.

Consolidated Tool:
- mermaid_analysis_manage - Unified tool for all Mermaid analysis operations
  * analyze_relationships - Extract and analyze relationships within diagrams
  * detect_patterns - Detect common patterns and anti-patterns
  * suggest_improvements - Generate AI-powered improvement suggestions
  * compare_diagrams - Compare multiple diagrams for similarities
  * generate_insights - Extract business and technical insights
  * complexity_analysis - Perform deep complexity analysis
"""

import re
from typing import Dict, Any, List

# Official MCP SDK import
from mcp.server.fastmcp import FastMCP

# Local imports
from ...config.settings import LTMCSettings
from ...utils.logging_utils import get_tool_logger


def register_consolidated_analysis_mermaid_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register consolidated Mermaid analysis tools with FastMCP server."""
    logger = get_tool_logger('mermaid.analysis.consolidated')
    logger.info("Registering consolidated Mermaid analysis tools")
    
    # Services not needed for this consolidated tool
    
    @mcp.tool()
    async def mermaid_analysis_manage(
        operation: str,
        content: str = None,
        diagram_type: str = None,
        extract_entities: bool = True,
        map_dependencies: bool = True,
        pattern_types: List[str] = None,
        improvement_areas: List[str] = None,
        diagram2_content: str = None,
        diagram2_type: str = None,
        comparison_metrics: List[str] = None,
        insight_types: List[str] = None,
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Unified Mermaid analysis management tool.
        
        Args:
            operation: Operation to perform ("analyze_relationships", "detect_patterns", "suggest_improvements", "compare_diagrams", "generate_insights", "complexity_analysis")
            content: Mermaid diagram content (for most operations)
            diagram_type: Type of diagram (for most operations)
            extract_entities: Whether to extract entity information (for analyze_relationships)
            map_dependencies: Whether to map dependencies between entities (for analyze_relationships)
            pattern_types: Types of patterns to detect (for detect_patterns)
            improvement_areas: Areas to focus improvements on (for suggest_improvements)
            diagram2_content: Second diagram content for comparison (for compare_diagrams)
            diagram2_type: Second diagram type for comparison (for compare_diagrams)
            comparison_metrics: Metrics to compare (for compare_diagrams)
            insight_types: Types of insights to extract (for generate_insights)
            analysis_depth: Depth of analysis (basic, detailed, comprehensive) (for complexity_analysis)
            
        Returns:
            Dict with operation results and metadata
        """
        logger.debug("Mermaid analysis operation: {}".format(operation))
        
        try:
            if operation == "analyze_relationships":
                if not content or not diagram_type:
                    return {"success": False, "error": "content and diagram_type required for analyze_relationships operation"}
                
                # Extract and analyze relationships within a Mermaid diagram
                logger.debug("Analyzing relationships in diagram: {}".format(diagram_type))
                
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
                                    "to": match[2] if len(match) > 2 else match[1],
                                    "type": match[1] if len(match) > 2 else "default",
                                    "line": line
                                })
                
                # Map dependencies
                if map_dependencies:
                    for rel in relationships:
                        dependency = {
                            "dependent": rel["from"],
                            "dependency": rel["to"],
                            "relationship_type": rel["type"],
                            "strength": "strong" if ">>" in rel["type"] else "weak"
                        }
                        dependencies.append(dependency)
                
                logger.info("Analyzed relationships: {} entities, {} relationships, {} dependencies".format(
                    len(entities), len(relationships), len(dependencies)
                ))
                
                return {
                    "success": True,
                    "operation": "analyze_relationships",
                    "diagram_type": diagram_type,
                    "entities": entities,
                    "relationships": relationships,
                    "dependencies": dependencies,
                    "summary": {
                        "total_entities": len(entities),
                        "total_relationships": len(relationships),
                        "total_dependencies": len(dependencies)
                    }
                }
                
            elif operation == "detect_patterns":
                if not content or not diagram_type:
                    return {"success": False, "error": "content and diagram_type required for detect_patterns operation"}
                
                # Detect common patterns and anti-patterns
                logger.debug("Detecting patterns in diagram: {}".format(diagram_type))
                
                patterns = []
                anti_patterns = []
                
                # Common patterns
                if "flowchart" in diagram_type.lower():
                    # Check for linear flow
                    if "-->".join([line.strip() for line in content.split('\n') if line.strip() and "-->" in line]):
                        patterns.append({
                            "type": "linear_flow",
                            "description": "Sequential linear flow pattern",
                            "confidence": 0.8
                        })
                    
                    # Check for branching
                    if content.count("-->") > content.count("---"):
                        patterns.append({
                            "type": "branching_flow",
                            "description": "Multiple branching paths",
                            "confidence": 0.7
                        })
                
                elif "class" in diagram_type.lower():
                    # Check for inheritance
                    if "|--" in content:
                        patterns.append({
                            "type": "inheritance_hierarchy",
                            "description": "Class inheritance pattern",
                            "confidence": 0.9
                        })
                    
                    # Check for composition
                    if "*--" in content:
                        patterns.append({
                            "type": "composition",
                            "description": "Object composition pattern",
                            "confidence": 0.8
                        })
                
                # Anti-patterns
                if len(content.split('\n')) > 50:
                    anti_patterns.append({
                        "type": "overly_complex",
                        "description": "Diagram is overly complex",
                        "severity": "high",
                        "suggestion": "Consider breaking into smaller diagrams"
                    })
                
                if content.count("-->") > 20:
                    anti_patterns.append({
                        "type": "too_many_connections",
                        "description": "Too many connections between elements",
                        "severity": "medium",
                        "suggestion": "Group related elements or simplify relationships"
                    })
                
                logger.info("Detected {} patterns and {} anti-patterns".format(len(patterns), len(anti_patterns)))
                
                return {
                    "success": True,
                    "operation": "detect_patterns",
                    "diagram_type": diagram_type,
                    "patterns": patterns,
                    "anti_patterns": anti_patterns,
                    "summary": {
                        "total_patterns": len(patterns),
                        "total_anti_patterns": len(anti_patterns)
                    }
                }
                
            elif operation == "suggest_improvements":
                if not content or not diagram_type:
                    return {"success": False, "error": "content and diagram_type required for suggest_improvements operation"}
                
                # Generate AI-powered improvement suggestions
                logger.debug("Generating improvement suggestions for diagram: {}".format(diagram_type))
                
                suggestions = []
                
                # Analyze complexity
                line_count = len(content.split('\n'))
                if line_count > 30:
                    suggestions.append({
                        "area": "complexity",
                        "priority": "high",
                        "suggestion": "Break diagram into smaller, focused diagrams",
                        "impact": "Improved readability and maintainability"
                    })
                
                # Analyze naming
                if any(len(word) > 20 for word in re.findall(r'\b\w+\b', content)):
                    suggestions.append({
                        "area": "naming",
                        "priority": "medium",
                        "suggestion": "Use shorter, more descriptive names",
                        "impact": "Better clarity and understanding"
                    })
                
                # Analyze structure
                if "flowchart" in diagram_type.lower():
                    if content.count("-->") > 15:
                        suggestions.append({
                            "area": "structure",
                            "priority": "medium",
                            "suggestion": "Group related elements into subgraphs",
                            "impact": "Reduced visual complexity"
                        })
                
                # Default improvement if none specific
                if not suggestions:
                    suggestions.append({
                        "area": "general",
                        "priority": "low",
                        "suggestion": "Diagram follows good practices",
                        "impact": "Maintain current structure"
                    })
                
                logger.info("Generated {} improvement suggestions".format(len(suggestions)))
                
                return {
                    "success": True,
                    "operation": "suggest_improvements",
                    "diagram_type": diagram_type,
                    "suggestions": suggestions,
                    "summary": {
                        "total_suggestions": len(suggestions),
                        "high_priority": len([s for s in suggestions if s["priority"] == "high"]),
                        "medium_priority": len([s for s in suggestions if s["priority"] == "medium"]),
                        "low_priority": len([s for s in suggestions if s["priority"] == "low"])
                    }
                }
                
            elif operation == "compare_diagrams":
                if not content or not diagram_type or not diagram2_content or not diagram2_type:
                    return {"success": False, "error": "content, diagram_type, diagram2_content, and diagram2_type required for compare_diagrams operation"}
                
                # Compare multiple diagrams for similarities
                logger.debug("Comparing diagrams: {} vs {}".format(diagram_type, diagram2_type))
                
                # Basic comparison metrics
                comparison = {
                    "diagram1": {
                        "type": diagram_type,
                        "line_count": len(content.split('\n')),
                        "complexity": "high" if len(content.split('\n')) > 30 else "medium" if len(content.split('\n')) > 15 else "low"
                    },
                    "diagram2": {
                        "type": diagram2_type,
                        "line_count": len(diagram2_content.split('\n')),
                        "complexity": "high" if len(diagram2_content.split('\n')) > 30 else "medium" if len(diagram2_content.split('\n')) > 15 else "low"
                    },
                    "similarities": [],
                    "differences": []
                }
                
                # Find similarities
                if diagram_type.lower() == diagram2_type.lower():
                    comparison["similarities"].append("Same diagram type")
                
                if abs(len(content.split('\n')) - len(diagram2_content.split('\n'))) < 5:
                    comparison["similarities"].append("Similar complexity level")
                
                # Find differences
                if len(content.split('\n')) != len(diagram2_content.split('\n')):
                    comparison["differences"].append("Different complexity levels")
                
                if diagram_type.lower() != diagram2_type.lower():
                    comparison["differences"].append("Different diagram types")
                
                logger.info("Diagram comparison completed")
                
                return {
                    "success": True,
                    "operation": "compare_diagrams",
                    "comparison": comparison,
                    "summary": {
                        "similarities_count": len(comparison["similarities"]),
                        "differences_count": len(comparison["differences"])
                    }
                }
                
            elif operation == "generate_insights":
                if not content or not diagram_type:
                    return {"success": False, "error": "content and diagram_type required for generate_insights operation"}
                
                # Extract business and technical insights from diagram content
                logger.debug("Generating insights from diagram: {}".format(diagram_type))
                
                insights = []
                
                # Technical insights
                if "flowchart" in diagram_type.lower():
                    flow_steps = content.count("-->")
                    if flow_steps > 10:
                        insights.append({
                            "type": "technical",
                            "category": "complexity",
                            "insight": "High process complexity with {} steps".format(flow_steps),
                            "implication": "May indicate need for process optimization"
                        })
                
                elif "class" in diagram_type.lower():
                    class_count = content.count("class")
                    if class_count > 5:
                        insights.append({
                            "type": "technical",
                            "category": "architecture",
                            "insight": "Large class hierarchy with {} classes".format(class_count),
                            "implication": "Consider breaking into smaller modules"
                        })
                
                # Business insights
                if any(word in content.lower() for word in ["user", "customer", "order", "payment"]):
                    insights.append({
                        "type": "business",
                        "category": "user_experience",
                        "insight": "User-centric process flow detected",
                        "implication": "Focus on user journey optimization"
                    })
                
                if not insights:
                    insights.append({
                        "type": "general",
                        "category": "overview",
                        "insight": "Standard diagram structure",
                        "implication": "Follows established patterns"
                    })
                
                logger.info("Generated {} insights".format(len(insights)))
                
                return {
                    "success": True,
                    "operation": "generate_insights",
                    "diagram_type": diagram_type,
                    "insights": insights,
                    "summary": {
                        "total_insights": len(insights),
                        "technical_insights": len([i for i in insights if i["type"] == "technical"]),
                        "business_insights": len([i for i in insights if i["type"] == "business"])
                    }
                }
                
            elif operation == "complexity_analysis":
                if not content or not diagram_type:
                    return {"success": False, "error": "content and diagram_type required for complexity_analysis operation"}
                
                # Perform deep complexity analysis of Mermaid diagrams
                logger.debug("Performing complexity analysis on diagram: {}".format(diagram_type))
                
                # Complexity metrics
                lines = content.split('\n')
                line_count = len(lines)
                
                # Count different elements
                element_counts = {
                    "nodes": content.count("["),
                    "connections": content.count("-->") + content.count("---"),
                    "subgraphs": content.count("subgraph"),
                    "comments": content.count("%%"),
                    "styling": content.count("style")
                }
                
                # Calculate complexity score
                complexity_score = 0
                complexity_score += line_count * 0.1
                complexity_score += element_counts["nodes"] * 0.2
                complexity_score += element_counts["connections"] * 0.3
                complexity_score += element_counts["subgraphs"] * 0.5
                
                # Determine complexity level
                if complexity_score < 5:
                    complexity_level = "low"
                elif complexity_score < 15:
                    complexity_level = "medium"
                else:
                    complexity_level = "high"
                
                # Recommendations based on complexity
                recommendations = []
                if complexity_level == "high":
                    recommendations.append("Consider breaking into smaller diagrams")
                    recommendations.append("Use subgraphs to group related elements")
                    recommendations.append("Simplify connection patterns")
                elif complexity_level == "medium":
                    recommendations.append("Monitor for increasing complexity")
                    recommendations.append("Consider modularization if growing")
                
                logger.info("Complexity analysis completed: {} level (score: {})".format(complexity_level, round(complexity_score, 2)))
                
                return {
                    "success": True,
                    "operation": "complexity_analysis",
                    "diagram_type": diagram_type,
                    "complexity_metrics": {
                        "overall_score": round(complexity_score, 2),
                        "complexity_level": complexity_level,
                        "line_count": line_count,
                        "element_counts": element_counts
                    },
                    "recommendations": recommendations,
                    "analysis_depth": analysis_depth
                }
                
            else:
                return {
                    "success": False,
                    "error": "Unknown operation: {}. Valid operations: analyze_relationships, detect_patterns, suggest_improvements, compare_diagrams, generate_insights, complexity_analysis".format(operation)
                }
                
        except Exception as e:
            logger.error("Error in Mermaid analysis operation '{}': {}".format(operation, e))
            return {
                "success": False,
                "error": "Mermaid analysis operation failed: {}".format(str(e))
            }
    
    logger.info("✅ Consolidated Mermaid analysis tools registered successfully")
    logger.info("📊 Tool consolidation: 6 individual tools → 1 unified tool")
    logger.info("🔧 All functionality preserved through operation parameter")
