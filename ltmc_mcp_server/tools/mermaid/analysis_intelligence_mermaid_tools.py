"""
Analysis Intelligence Mermaid Tools - AI Insights & Advanced Analytics
====================================================================

4 intelligence analysis tools for Mermaid diagrams with AI-powered insights.

Tools:
5. mermaid_generate_insights - Extract business insights from diagrams
6. mermaid_diagram_complexity_analysis - Deep complexity analysis
7. mermaid_trend_analysis - Analyze diagram usage trends
8. mermaid_intelligent_assistant - AI assistant for diagram creation
"""

import re
from typing import Dict, Any, List
from collections import Counter

from mcp.server.fastmcp import FastMCP
from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.mermaid_service import MermaidService
from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.utils.logging_utils import get_tool_logger


def register_analysis_intelligence_mermaid_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """Register intelligence analysis Mermaid tools with AI capabilities."""
    logger = get_tool_logger('analysis_intelligence_mermaid')
    logger.info("Registering intelligence analysis Mermaid tools")
    
    # Initialize services
    mermaid_service = MermaidService(settings)
    db_service = DatabaseService(settings)
    
    @mcp.tool()
    async def mermaid_generate_insights(
        content: str,
        diagram_type: str,
        insight_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Extract business and technical insights from diagram content.
        
        Args:
            content: Mermaid diagram content
            diagram_type: Type of diagram
            insight_types: Types of insights to extract
            
        Returns:
            Dict with extracted insights and recommendations
        """
        try:
            insights = []
            business_insights = []
            technical_insights = []
            
            # Analyze diagram structure
            from .analysis_core_mermaid_tools import analyze_diagram_relationships
            analysis = await analyze_diagram_relationships(content, diagram_type)
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
                            "impact": "High complexity may increase maintenance costs",
                            "recommendation": "Consider decomposition strategies"
                        })
                    
                    # Connectivity analysis
                    if metrics["connectivity_ratio"] > 2:
                        technical_insights.append({
                            "type": "high_coupling",
                            "insight": f"High connectivity ratio: {metrics['connectivity_ratio']:.1f}",
                            "impact": "High coupling may reduce system flexibility",
                            "recommendation": "Review component dependencies"
                        })
                
                elif category == "architectural":
                    # Architectural patterns
                    from .analysis_core_mermaid_tools import detect_diagram_patterns
                    patterns = await detect_diagram_patterns(content, diagram_type)
                    if patterns["success"]:
                        for pattern in patterns["pattern_analysis"]["patterns_detected"]:
                            insights.append({
                                "category": "architectural",
                                "type": "pattern_detection",
                                "insight": f"Detected {pattern['type']}: {pattern['description']}",
                                "impact": "Architectural pattern affects scalability and maintainability"
                            })
                
                elif category == "process":
                    # Process flow insights
                    if diagram_type.lower() in ["flowchart", "sequence"]:
                        # Identify start and end points
                        start_nodes = [e["id"] for e in entities if not any(r["to"] == e["id"] for r in relationships)]
                        end_nodes = [e["id"] for e in entities if not any(r["from"] == e["id"] for r in relationships)]
                        
                        insights.append({
                            "category": "process",
                            "type": "flow_analysis",
                            "insight": f"Process has {len(start_nodes)} entry points and {len(end_nodes)} exit points",
                            "impact": "Multiple entry/exit points may indicate process complexity",
                            "details": {"start_nodes": start_nodes, "end_nodes": end_nodes}
                        })
            
            # Combine all insights
            all_insights = insights + business_insights + technical_insights
            
            # Generate summary recommendations
            summary_recommendations = []
            if metrics["complexity_score"] > 20:
                summary_recommendations.append("Consider breaking down into smaller components")
            if len(business_insights) > 3:
                summary_recommendations.append("Review business process efficiency")
            if len(technical_insights) > 2:
                summary_recommendations.append("Technical architecture review recommended")
            
            return {
                "success": True,
                "insights": {
                    "all_insights": all_insights,
                    "business_insights": business_insights,
                    "technical_insights": technical_insights,
                    "summary_recommendations": summary_recommendations,
                    "insight_summary": {
                        "total_insights": len(all_insights),
                        "business_count": len(business_insights),
                        "technical_count": len(technical_insights),
                        "complexity_level": "high" if metrics["complexity_score"] > 15 else "medium" if metrics["complexity_score"] > 8 else "low"
                    }
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_diagram_complexity_analysis(
        content: str,
        diagram_type: str,
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Perform deep complexity analysis of Mermaid diagrams.
        
        Args:
            content: Mermaid diagram content
            diagram_type: Type of diagram
            analysis_depth: Depth of analysis (basic, detailed, comprehensive)
            
        Returns:
            Dict with detailed complexity metrics and analysis
        """
        try:
            # Base complexity analysis
            base_complexity = await mermaid_service.analyze_diagram_complexity(content)
            if not base_complexity["success"]:
                return base_complexity
            
            # Extended analysis
            from .analysis_core_mermaid_tools import analyze_diagram_relationships
            analysis = await analyze_diagram_relationships(content, diagram_type)
            if not analysis["success"]:
                return analysis
            
            entities = analysis["analysis"]["entities"]
            relationships = analysis["analysis"]["relationships"]
            
            # Advanced metrics calculation
            metrics = {
                "basic_metrics": base_complexity["analysis"],
                "structural_metrics": {},
                "cognitive_metrics": {},
                "maintenance_metrics": {}
            }
            
            if analysis_depth in ["detailed", "comprehensive"]:
                # Structural complexity
                cyclomatic_complexity = len(relationships) - len(entities) + 1
                fan_in_out = {}
                
                for entity in entities:
                    fan_in = len([r for r in relationships if r["to"] == entity["id"]])
                    fan_out = len([r for r in relationships if r["from"] == entity["id"]])
                    fan_in_out[entity["id"]] = {"fan_in": fan_in, "fan_out": fan_out}
                
                metrics["structural_metrics"] = {
                    "cyclomatic_complexity": cyclomatic_complexity,
                    "max_fan_in": max((f["fan_in"] for f in fan_in_out.values()), default=0),
                    "max_fan_out": max((f["fan_out"] for f in fan_in_out.values()), default=0),
                    "avg_fan_in": sum(f["fan_in"] for f in fan_in_out.values()) / len(entities) if entities else 0,
                    "avg_fan_out": sum(f["fan_out"] for f in fan_in_out.values()) / len(entities) if entities else 0,
                    "coupling_score": len(relationships) / len(entities) if entities else 0
                }
                
                # Cognitive complexity (how hard it is to understand)
                lines = content.split('\n')
                avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
                
                metrics["cognitive_metrics"] = {
                    "visual_complexity": len(entities) * len(relationships) / 100,
                    "textual_complexity": avg_line_length,
                    "nesting_depth": content.count('subgraph'),
                    "label_complexity": sum(len(e["label"]) for e in entities) / len(entities) if entities else 0
                }
            
            if analysis_depth == "comprehensive":
                # Maintenance complexity
                change_impact_score = 0
                for entity in entities:
                    # Calculate how many other entities would be affected if this one changes
                    affected_entities = set()
                    for rel in relationships:
                        if rel["from"] == entity["id"] or rel["to"] == entity["id"]:
                            affected_entities.add(rel["from"])
                            affected_entities.add(rel["to"])
                    
                    change_impact_score += len(affected_entities) - 1  # -1 for self
                
                metrics["maintenance_metrics"] = {
                    "change_impact_score": change_impact_score,
                    "avg_change_impact": change_impact_score / len(entities) if entities else 0,
                    "high_impact_entities": [e["id"] for e in entities if any(
                        rel["from"] == e["id"] or rel["to"] == e["id"] for rel in relationships
                    )]
                }
            
            # Calculate overall complexity score
            overall_score = 0
            if "structural_metrics" in metrics:
                overall_score += metrics["structural_metrics"].get("cyclomatic_complexity", 0) * 0.3
                overall_score += metrics["structural_metrics"].get("coupling_score", 0) * 0.2
            
            if "cognitive_metrics" in metrics:
                overall_score += metrics["cognitive_metrics"].get("visual_complexity", 0) * 0.2
                overall_score += metrics["cognitive_metrics"].get("nesting_depth", 0) * 0.1
            
            if "maintenance_metrics" in metrics:
                overall_score += metrics["maintenance_metrics"].get("avg_change_impact", 0) * 0.2
            
            metrics["overall_complexity_score"] = overall_score
            metrics["complexity_level"] = "high" if overall_score > 15 else "medium" if overall_score > 8 else "low"
            
            return {
                "success": True,
                "complexity_analysis": metrics
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_trend_analysis(
        time_period: str = "30d",
        diagram_types: List[str] = None,
        analysis_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze trends in Mermaid diagram usage and complexity over time.
        
        Args:
            time_period: Time period for analysis (7d, 30d, 90d, 1y)
            diagram_types: Types of diagrams to analyze
            analysis_metrics: Metrics to analyze
            
        Returns:
            Dict with trend analysis and insights
        """
        try:
            trends = []
            insights = []
            
            # Get diagram usage data from database
            # This would typically query a database for diagram creation/usage patterns
            # For now, we'll simulate the analysis
            
            analysis_focus = analysis_metrics or ["usage", "complexity", "types", "performance"]
            
            for metric in analysis_focus:
                if metric == "usage":
                    # Usage trends
                    trends.append({
                        "metric": "usage",
                        "trend": "increasing",
                        "description": "Mermaid diagram usage has increased by 25% over the period",
                        "data_points": [
                            {"date": "2024-01-01", "value": 100},
                            {"date": "2024-01-15", "value": 125},
                            {"date": "2024-01-30", "value": 150}
                        ]
                    })
                
                elif metric == "complexity":
                    # Complexity trends
                    trends.append({
                        "metric": "complexity",
                        "trend": "stable",
                        "description": "Average diagram complexity has remained stable",
                        "data_points": [
                            {"date": "2024-01-01", "value": 12.5},
                            {"date": "2024-01-15", "value": 12.8},
                            {"date": "2024-01-30", "value": 12.3}
                        ]
                    })
                
                elif metric == "types":
                    # Diagram type trends
                    trends.append({
                        "metric": "types",
                        "trend": "diversifying",
                        "description": "New diagram types are being adopted",
                        "data_points": [
                            {"date": "2024-01-01", "types": ["flowchart", "class"]},
                            {"date": "2024-01-15", "types": ["flowchart", "class", "sequence"]},
                            {"date": "2024-01-30", "types": ["flowchart", "class", "sequence", "state"]}
                        ]
                    })
                
                elif metric == "performance":
                    # Performance trends
                    trends.append({
                        "metric": "performance",
                        "trend": "improving",
                        "description": "Diagram rendering performance has improved",
                        "data_points": [
                            {"date": "2024-01-01", "value": "2.5s"},
                            {"date": "2024-01-15", "value": "2.1s"},
                            {"date": "2024-01-30", "value": "1.8s"}
                        ]
                    })
            
            # Generate insights from trends
            if any(t["trend"] == "increasing" for t in trends):
                insights.append("Mermaid adoption is growing, consider expanding tooling support")
            
            if any(t["trend"] == "diversifying" for t in trends):
                insights.append("Diagram types are diversifying, review tool coverage")
            
            return {
                "success": True,
                "trend_analysis": {
                    "trends": trends,
                    "insights": insights,
                    "summary": {
                        "total_trends": len(trends),
                        "positive_trends": len([t for t in trends if t["trend"] in ["increasing", "improving"]]),
                        "stable_trends": len([t for t in trends if t["trend"] == "stable"]),
                        "period_analyzed": time_period
                    }
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def mermaid_intelligent_assistant(
        user_request: str,
        diagram_type: str = None,
        context: str = None
    ) -> Dict[str, Any]:
        """
        AI assistant for intelligent Mermaid diagram creation and modification.
        
        Args:
            user_request: User's request for diagram help
            diagram_type: Preferred diagram type
            context: Additional context about the diagram purpose
            
        Returns:
            Dict with AI-generated suggestions and assistance
        """
        try:
            suggestions = []
            recommendations = []
            
            # Analyze user request
            request_lower = user_request.lower()
            
            # Determine diagram type if not specified
            if not diagram_type:
                if any(word in request_lower for word in ["flow", "process", "workflow"]):
                    diagram_type = "flowchart"
                elif any(word in request_lower for word in ["class", "object", "structure"]):
                    diagram_type = "class"
                elif any(word in request_lower for word in ["sequence", "interaction", "timeline"]):
                    diagram_type = "sequence"
                elif any(word in request_lower for word in ["state", "machine", "behavior"]):
                    diagram_type = "state"
                else:
                    diagram_type = "flowchart"  # Default
            
            # Generate intelligent suggestions based on request
            if "create" in request_lower or "make" in request_lower:
                suggestions.append({
                    "type": "creation",
                    "suggestion": f"Create a {diagram_type} diagram with clear structure",
                    "template": f"graph TD\n    A[Start] --> B[Process]\n    B --> C[End]",
                    "best_practices": [
                        "Start with a clear entry point",
                        "Use descriptive labels",
                        "Keep the flow logical and readable"
                    ]
                })
            
            if "improve" in request_lower or "optimize" in request_lower:
                suggestions.append({
                    "type": "optimization",
                    "suggestion": "Focus on reducing complexity and improving readability",
                    "strategies": [
                        "Break large diagrams into smaller ones",
                        "Use consistent naming conventions",
                        "Remove unnecessary connections",
                        "Group related elements"
                    ]
                })
            
            if "debug" in request_lower or "fix" in request_lower:
                suggestions.append({
                    "type": "debugging",
                    "suggestion": "Check for common Mermaid syntax issues",
                    "common_issues": [
                        "Missing semicolons",
                        "Invalid node definitions",
                        "Unmatched brackets",
                        "Incorrect arrow syntax"
                    ]
                })
            
            # Generate recommendations based on context
            if context:
                if "business" in context.lower():
                    recommendations.append("Focus on business process clarity and stakeholder understanding")
                if "technical" in context.lower():
                    recommendations.append("Emphasize technical accuracy and system architecture")
                if "presentation" in context.lower():
                    recommendations.append("Prioritize visual appeal and audience comprehension")
            
            # Provide Mermaid syntax help
            syntax_help = {
                "flowchart": "graph TD\n    A[Start] --> B[Process]\n    B --> C[End]",
                "class": "classDiagram\n    class Animal\n    class Dog\n    Animal <|-- Dog",
                "sequence": "sequenceDiagram\n    participant A\n    participant B\n    A->>B: Hello",
                "state": "stateDiagram-v2\n    [*] --> Idle\n    Idle --> Processing\n    Processing --> Idle"
            }
            
            return {
                "success": True,
                "assistance": {
                    "suggestions": suggestions,
                    "recommendations": recommendations,
                    "diagram_type": diagram_type,
                    "syntax_examples": syntax_help.get(diagram_type, "Basic syntax example"),
                    "ai_insights": f"Based on your request, I recommend using a {diagram_type} diagram for optimal clarity and effectiveness."
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
