"""
Consolidated Analysis Intelligence Mermaid Tools - Unified AI Insights & Advanced Analytics
=========================================================================================

Consolidated tool combining all 4 intelligence analysis tools for Mermaid diagrams:
- generate_insights: Extract business insights from diagrams
- diagram_complexity_analysis: Deep complexity analysis
- trend_analysis: Analyze diagram usage trends
- intelligent_assistant: AI assistant for diagram creation

All functionality preserved through operation parameter.
"""

import json
from typing import Dict, Any, List
from collections import Counter

from mcp.server.fastmcp import FastMCP
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.mermaid_service import MermaidService
from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_consolidated_analysis_intelligence_mermaid_tools(
    mcp: FastMCP, settings: LTMCSettings
) -> None:
    """Register consolidated intelligence analysis Mermaid tools with AI capabilities."""
    logger = get_tool_logger('consolidated_analysis_intelligence_mermaid')
    logger.info("Registering consolidated intelligence analysis Mermaid tools")
    
    # Initialize services
    mermaid_service = MermaidService(settings)
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def mermaid_intelligence_manage(
        operation: str,
        content: str = None,
        diagram_type: str = None,
        insight_types: List[str] = None,
        complexity_metrics: List[str] = None,
        trend_period: str = None,
        trend_filters: Dict[str, Any] = None,
        assistant_query: str = None,
        assistant_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Unified tool for all intelligence analysis Mermaid operations.
        
        Args:
            operation: Operation to perform (generate_insights, diagram_complexity_analysis,
                       trend_analysis, intelligent_assistant)
            content: Mermaid diagram content
            diagram_type: Type of diagram
            insight_types: Types of insights to extract
            complexity_metrics: Metrics for complexity analysis
            trend_period: Time period for trend analysis
            trend_filters: Filters for trend analysis
            assistant_query: Query for AI assistant
            assistant_context: Context for AI assistant
            
        Returns:
            Dict with operation results
        """
        
        if operation == "generate_insights":
            return await _generate_insights(content, diagram_type, insight_types)
        elif operation == "diagram_complexity_analysis":
            return await _diagram_complexity_analysis(content, diagram_type, complexity_metrics)
        elif operation == "trend_analysis":
            return await _trend_analysis(trend_period, trend_filters)
        elif operation == "intelligent_assistant":
            return await _intelligent_assistant(assistant_query, assistant_context)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Valid operations: generate_insights, diagram_complexity_analysis, trend_analysis, intelligent_assistant"
            }
    
    async def _generate_insights(
        content: str,
        diagram_type: str,
        insight_types: List[str] = None
    ) -> Dict[str, Any]:
        """Extract business and technical insights from diagram content."""
        try:
            if not content or not diagram_type:
                return {
                    "success": False,
                    "error": "Content and diagram_type are required"
                }
            
            insights = []
            business_insights = []
            technical_insights = []
            
            # Analyze diagram structure using core analysis
            from .consolidated_analysis_core_mermaid_tools import mermaid_core_analysis_manage
            analysis = await mermaid_core_analysis_manage(
                operation="analyze_relationships",
                content=content,
                diagram_type=diagram_type
            )
            
            if not analysis["success"]:
                return analysis
            
            entities = analysis["analysis"]["entities"]
            relationships = analysis["analysis"]["relationships"] 
            metrics = analysis["analysis"]["metrics"]
            
            insight_categories = insight_types or ["business", "technical", "architectural", "process"]
            
            for category in insight_categories:
                if category == "business":
                    # Business process insights
                    if diagram_type.lower() == "flowchart":
                        decision_nodes = [e for e in entities if "decision" in e["label"].lower() or "?" in e["label"]]
                        if decision_nodes:
                            business_insights.append({
                                "type": "decision_points",
                                "insight": f"Process contains {len(decision_nodes)} decision points",
                                "impact": "Decision complexity may affect process efficiency",
                                "nodes": [d["id"] for d in decision_nodes]
                            })
                    
                    # Process bottlenecks
                    connection_counts = Counter()
                    for rel in relationships:
                        connection_counts[rel["to"]] += 1
                    
                    bottlenecks = [entity for entity, count in connection_counts.items() if count > 3]
                    if bottlenecks:
                        business_insights.append({
                            "type": "potential_bottlenecks",
                            "insight": f"Identified {len(bottlenecks)} potential process bottlenecks",
                            "impact": "These nodes may cause delays or resource constraints",
                            "nodes": bottlenecks
                        })
                
                elif category == "technical":
                    # Technical complexity insights
                    if metrics["complexity_score"] > 15:
                        technical_insights.append({
                            "type": "high_complexity",
                            "insight": f"System complexity score: {metrics['complexity_score']:.1f}",
                            "impact": "May indicate maintenance challenges",
                            "recommendation": "Consider breaking into smaller components"
                        })
                    
                    # Coupling analysis
                    if metrics["connectivity_ratio"] > 2.5:
                        technical_insights.append({
                            "type": "high_coupling",
                            "insight": f"High connectivity ratio: {metrics['connectivity_ratio']:.1f}",
                            "impact": "Tight coupling may reduce flexibility",
                            "recommendation": "Review dependencies and reduce coupling"
                        })
                
                elif category == "architectural":
                    # Architectural patterns
                    if diagram_type.lower() == "class":
                        inheritance_count = sum(1 for rel in relationships if "inheritance" in rel["type"].lower())
                        if inheritance_count > 5:
                            technical_insights.append({
                                "type": "inheritance_heavy",
                                "insight": f"High inheritance usage: {inheritance_count} relationships",
                                "impact": "May indicate design issues",
                                "recommendation": "Consider composition over inheritance"
                            })
                
                elif category == "process":
                    # Process flow insights
                    if diagram_type.lower() == "flowchart":
                        start_nodes = [e for e in entities if "start" in e["label"].lower()]
                        end_nodes = [e for e in entities if "end" in e["label"].lower()]
                        
                        if len(start_nodes) > 1:
                            business_insights.append({
                                "type": "multiple_entry_points",
                                "insight": f"Multiple start points: {len(start_nodes)}",
                                "impact": "Process may have unclear entry",
                                "recommendation": "Consolidate to single entry point"
                            })
                        
                        if len(end_nodes) > 1:
                            business_insights.append({
                                "type": "multiple_exit_points",
                                "insight": f"Multiple end points: {len(end_nodes)}",
                                "impact": "Process may have unclear completion",
                                "recommendation": "Define clear completion criteria"
                            })
            
            # Combine all insights
            insights = business_insights + technical_insights
            
            return {
                "success": True,
                "insights": {
                    "business": business_insights,
                    "technical": technical_insights,
                    "all": insights,
                    "total_count": len(insights)
                },
                "diagram_analysis": {
                    "entities": len(entities),
                    "relationships": len(relationships),
                    "complexity_score": metrics["complexity_score"]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _diagram_complexity_analysis(
        content: str,
        diagram_type: str,
        complexity_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Perform deep complexity analysis of Mermaid diagrams."""
        try:
            if not content or not diagram_type:
                return {
                    "success": False,
                    "error": "Content and diagram_type are required"
                }
            
            # Get detailed analysis
            from .consolidated_analysis_core_mermaid_tools import mermaid_core_analysis_manage
            analysis = await mermaid_core_analysis_manage(
                operation="analyze_relationships",
                content=content,
                diagram_type=diagram_type
            )
            
            if not analysis["success"]:
                return analysis
            
            entities = analysis["analysis"]["entities"]
            relationships = analysis["analysis"]["relationships"]
            metrics = analysis["analysis"]["metrics"]
            
            # Deep complexity metrics
            complexity_analysis = {
                "structural_complexity": {
                    "node_count": len(entities),
                    "edge_count": len(relationships),
                    "density": len(relationships) / max(len(entities), 1),
                    "connectivity": len(relationships) / max(len(entities) * (len(entities) - 1) / 2, 1)
                },
                "cognitive_complexity": {
                    "label_length_avg": sum(len(e.get("label", "")) for e in entities) / max(len(entities), 1),
                    "long_labels": [e for e in entities if len(e.get("label", "")) > 30],
                    "decision_points": sum(1 for e in entities if "?" in e.get("label", "")),
                    "nested_levels": _calculate_nesting_levels(content)
                },
                "maintainability": {
                    "complexity_score": metrics["complexity_score"],
                    "coupling_score": metrics["connectivity_ratio"],
                    "cohesion_score": _calculate_cohesion_score(entities, relationships),
                    "maintainability_index": max(0, 100 - metrics["complexity_score"] * 2)
                }
            }
            
            # Calculate advanced metrics
            complexity_analysis["advanced_metrics"] = {
                "cyclomatic_complexity": len(relationships) - len(entities) + 2,
                "halstead_metrics": _calculate_halstead_metrics(content),
                "cognitive_weight": _calculate_cognitive_weight(entities, relationships)
            }
            
            # Complexity recommendations
            recommendations = []
            if complexity_analysis["structural_complexity"]["density"] > 2.0:
                recommendations.append({
                    "type": "reduce_density",
                    "description": "High relationship density detected",
                    "impact": "May cause visual clutter and confusion",
                    "suggestion": "Consider grouping related entities or breaking into sub-diagrams"
                })
            
            if complexity_analysis["maintainability"]["maintainability_index"] < 50:
                recommendations.append({
                    "type": "improve_maintainability",
                    "description": "Low maintainability score detected",
                    "impact": "Difficult to modify and extend",
                    "suggestion": "Break complex entities into smaller, focused components"
                })
            
            return {
                "success": True,
                "complexity_analysis": complexity_analysis,
                "recommendations": recommendations,
                "overall_complexity": "high" if complexity_analysis["maintainability"]["maintainability_index"] < 50 else "medium" if complexity_analysis["maintainability"]["maintainability_index"] < 75 else "low"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _trend_analysis(
        trend_period: str = None,
        trend_filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze diagram usage trends and patterns."""
        try:
            trend_period = trend_period or "30d"
            trend_filters = trend_filters or {}
            
            # Get diagram resources from database
            resources = await db_service.get_resources_by_type("mermaid_diagram")
            
            # Analyze trends
            trend_data = {
                "period": trend_period,
                "total_diagrams": len(resources),
                "diagram_types": {},
                "creation_trends": {},
                "usage_patterns": {},
                "popular_tags": []
            }
            
            # Analyze diagram types
            type_counts = Counter()
            tag_counts = Counter()
            
            for resource in resources:
                try:
                    diagram_data = json.loads(resource["content"])
                    diagram_type = diagram_data.get("diagram_type", "unknown")
                    type_counts[diagram_type] += 1
                    
                    # Count tags
                    for tag in diagram_data.get("tags", []):
                        tag_counts[tag] += 1
                        
                except (json.JSONDecodeError, KeyError):
                    continue
            
            trend_data["diagram_types"] = dict(type_counts)
            trend_data["popular_tags"] = [tag for tag, count in tag_counts.most_common(10)]
            
            # Time-based analysis
            if trend_period == "7d":
                trend_data["creation_trends"] = {"daily": _analyze_daily_trends(resources, 7)}
            elif trend_period == "30d":
                trend_data["creation_trends"] = {"weekly": _analyze_weekly_trends(resources, 4)}
            elif trend_period == "90d":
                trend_data["creation_trends"] = {"monthly": _analyze_monthly_trends(resources, 3)}
            
            return {
                "success": True,
                "trend_analysis": trend_data,
                "insights": _generate_trend_insights(trend_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _intelligent_assistant(
        assistant_query: str,
        assistant_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """AI assistant for diagram creation and optimization."""
        try:
            if not assistant_query:
                return {
                    "success": False,
                    "error": "Assistant query is required"
                }
            
            context = assistant_context or {}
            
            # Analyze query intent
            query_analysis = _analyze_query_intent(assistant_query)
            
            # Generate response based on intent
            if query_analysis["intent"] == "create_diagram":
                response = await _assist_diagram_creation(assistant_query, context)
            elif query_analysis["intent"] == "optimize_diagram":
                response = await _assist_diagram_optimization(assistant_query, context)
            elif query_analysis["intent"] == "explain_diagram":
                response = await _assist_diagram_explanation(assistant_query, context)
            else:
                response = await _assist_general_help(assistant_query, context)
            
            return {
                "success": True,
                "assistant_response": response,
                "query_analysis": query_analysis,
                "context_used": context
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper functions for complexity analysis
    def _calculate_nesting_levels(content: str) -> int:
        """Calculate nesting levels in diagram content."""
        max_level = 0
        current_level = 0
        
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('{'):
                current_level += 1
                max_level = max(max_level, current_level)
            elif stripped.startswith('}'):
                current_level = max(0, current_level - 1)
        
        return max_level
    
    def _calculate_cohesion_score(entities: List[Dict], relationships: List[Dict]) -> float:
        """Calculate cohesion score for entities."""
        if not entities:
            return 0.0
        
        # Simple cohesion based on relationship density within entity groups
        total_possible_relationships = len(entities) * (len(entities) - 1) / 2
        if total_possible_relationships == 0:
            return 1.0
        
        actual_relationships = len(relationships)
        return min(1.0, actual_relationships / total_possible_relationships)
    
    def _calculate_halstead_metrics(content: str) -> Dict[str, float]:
        """Calculate Halstead complexity metrics."""
        # Simplified implementation
        lines = content.split('\n')
        operators = sum(1 for line in lines if any(op in line for op in ['-->', '---', '--', '..']))
        operands = sum(1 for line in lines if '[' in line and ']' in line)
        
        return {
            "operators": operators,
            "operands": operands,
            "vocabulary": operators + operands,
            "length": operators + operands
        }
    
    def _calculate_cognitive_weight(entities: List[Dict], relationships: List[Dict]) -> float:
        """Calculate cognitive weight of diagram."""
        base_weight = len(entities) * 1.0 + len(relationships) * 0.5
        
        # Adjust for complexity factors
        for entity in entities:
            if len(entity.get("label", "")) > 30:
                base_weight += 0.5  # Long labels increase cognitive load
        
        return base_weight
    
    # Helper functions for trend analysis
    def _analyze_daily_trends(resources: List[Dict], days: int) -> Dict[str, int]:
        """Analyze daily creation trends."""
        # Simplified implementation
        return {"recent": len(resources), "period": f"{days} days"}
    
    def _analyze_weekly_trends(resources: List[Dict], weeks: int) -> Dict[str, int]:
        """Analyze weekly creation trends."""
        # Simplified implementation
        return {"recent": len(resources), "period": f"{weeks} weeks"}
    
    def _analyze_monthly_trends(resources: List[Dict], months: int) -> Dict[str, int]:
        """Analyze monthly creation trends."""
        # Simplified implementation
        return {"recent": len(resources), "period": f"{months} months"}
    
    def _generate_trend_insights(trend_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from trend data."""
        insights = []
        
        if trend_data["total_diagrams"] > 100:
            insights.append({
                "type": "high_usage",
                "description": "High diagram creation activity",
                "recommendation": "Consider implementing diagram templates and standards"
            })
        
        if len(trend_data["diagram_types"]) > 5:
            insights.append({
                "type": "diverse_usage",
                "description": "Diverse diagram types in use",
                "recommendation": "Standardize on most effective diagram types"
            })
        
        return insights
    
    # Helper functions for intelligent assistant
    def _analyze_query_intent(query: str) -> Dict[str, Any]:
        """Analyze the intent of an assistant query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["create", "make", "generate", "new"]):
            intent = "create_diagram"
        elif any(word in query_lower for word in ["optimize", "improve", "better", "fix"]):
            intent = "optimize_diagram"
        elif any(word in query_lower for word in ["explain", "what", "how", "why"]):
            intent = "explain_diagram"
        else:
            intent = "general_help"
        
        return {
            "intent": intent,
            "confidence": 0.8,
            "keywords": [word for word in query_lower.split() if len(word) > 3]
        }
    
    async def _assist_diagram_creation(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assist with diagram creation."""
        return {
            "type": "creation_assistance",
            "suggestions": [
                "Start with a clear title and purpose",
                "Identify the main entities or components",
                "Define relationships between entities",
                "Use consistent naming conventions",
                "Keep the diagram focused and readable"
            ],
            "template_suggestion": "Consider using a flowchart template for process diagrams",
            "next_steps": "Define your diagram type and main components"
        }
    
    async def _assist_diagram_optimization(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assist with diagram optimization."""
        return {
            "type": "optimization_assistance",
            "suggestions": [
                "Reduce the number of entities if over 20",
                "Simplify complex relationships",
                "Use clear, concise labels",
                "Group related elements together",
                "Consider breaking into smaller diagrams"
            ],
            "tools": "Use the diagram_optimization operation for specific recommendations",
            "next_steps": "Analyze your current diagram for optimization opportunities"
        }
    
    async def _assist_diagram_explanation(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assist with diagram explanation."""
        return {
            "type": "explanation_assistance",
            "suggestions": [
                "Start with the overall purpose and context",
                "Explain the main components and their roles",
                "Describe key relationships and dependencies",
                "Highlight important decision points or flows",
                "Provide examples of how the diagram applies"
            ],
            "tools": "Use the generate_insights operation for detailed analysis",
            "next_steps": "Focus on the main message you want to convey"
        }
    
    async def _assist_general_help(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general help and guidance."""
        return {
            "type": "general_assistance",
            "suggestions": [
                "I can help you create, optimize, and analyze Mermaid diagrams",
                "Use specific operations like generate_insights or diagram_optimization",
                "Provide diagram content and type for detailed analysis",
                "Ask about specific diagram types or use cases"
            ],
            "available_operations": [
                "generate_insights", "diagram_complexity_analysis", 
                "trend_analysis", "intelligent_assistant"
            ],
            "next_steps": "Specify what type of diagram help you need"
        }
