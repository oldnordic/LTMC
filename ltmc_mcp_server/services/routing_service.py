"""
Routing Service - Smart Query Routing for LTMC
==============================================

Provides intelligent query routing to the most appropriate processing method.
"""
from typing import Dict, List, Any, Optional
from ..config.settings import LTMCSettings


class RoutingService:
    """Service for smart query routing."""
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        
    def route_query(self, query: str, available_methods: Optional[List[str]] = None) -> Dict[str, Any]:
        """Route query to the best processing method."""
        try:
            if available_methods is None:
                available_methods = ["database", "semantic", "graph", "cache"]
            
            # Simple routing logic based on query characteristics
            query_lower = query.lower()
            
            if any(word in query_lower for word in ["similar", "like", "related", "find"]):
                method = "semantic"
                confidence = 0.8
            elif any(word in query_lower for word in ["graph", "relationship", "connect"]):
                method = "graph"
                confidence = 0.9
            elif any(word in query_lower for word in ["recent", "latest", "new"]):
                method = "database"
                confidence = 0.7
            else:
                method = "database"
                confidence = 0.5
            
            # Ensure method is available
            if method not in available_methods and available_methods:
                method = available_methods[0]
                confidence = 0.3
                
            return {
                "method": method,
                "confidence": confidence,
                "query": query,
                "available_methods": available_methods,
                "reasoning": f"Selected {method} based on query characteristics"
            }
            
        except Exception as e:
            return {
                "method": "database",
                "confidence": 0.1,
                "query": query,
                "error": str(e),
                "reasoning": "Fallback to database due to error"
            }
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            "total_routes": 0,
            "method_distribution": {
                "database": 0,
                "semantic": 0,
                "graph": 0,
                "cache": 0
            },
            "average_confidence": 0.6
        }