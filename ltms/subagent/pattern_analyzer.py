"""
Pattern Analysis for Subagent Intelligence Tracking
Unified interface for pattern analysis with modular architecture.

File: ltms/subagent/pattern_analyzer.py
Lines: ~50 (under 300 limit)
Purpose: Main interface for pattern analysis with modular components
"""

import logging
from typing import Dict, Any, List, Optional

from .pattern_analysis_core import CorePatternAnalyzer
from .pattern_specialized_analysis import SpecializedPatternAnalysis

logger = logging.getLogger(__name__)


class SubagentPatternAnalyzer:
    """
    Unified pattern analysis system for subagent intelligence tracking.
    
    Provides a clean interface to modular pattern analysis components:
    - Core pattern analysis for tool usage, arguments, timing, and correlations
    - Specialized analysis for anomalies, trends, and advanced behavioral analysis
    """
    
    def __init__(self):
        self.core_analyzer = CorePatternAnalyzer()
        self.specialized_analyzer = SpecializedPatternAnalysis()
    
    # Core pattern analysis delegation
    async def analyze_tool_usage(self, tool_name: str, arguments: Dict[str, Any], 
                                session_id: str) -> List[Dict[str, Any]]:
        """Comprehensive analysis of tool usage patterns."""
        return await self.core_analyzer.analyze_tool_usage(tool_name, arguments, session_id)
    
    # Specialized pattern analysis delegation
    def analyze_anomaly_patterns(self, tool_usage_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalous patterns in tool usage."""
        return self.specialized_analyzer.analyze_anomaly_patterns(tool_usage_history)
    
    def analyze_behavioral_trends(self, session_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze behavioral trends across sessions."""
        return self.specialized_analyzer.analyze_behavioral_trends(session_data)
    
    def analyze_context_patterns(self, context_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze patterns in session context usage."""
        return self.specialized_analyzer.analyze_context_patterns(context_data)
    
    # Combined analysis methods
    async def comprehensive_pattern_analysis(self, tool_name: str, arguments: Dict[str, Any], 
                                           session_id: str, 
                                           historical_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform comprehensive pattern analysis combining core and specialized methods.
        
        Args:
            tool_name: Name of the tool being analyzed
            arguments: Tool arguments
            session_id: Current session identifier
            historical_data: Optional historical data for advanced analysis
            
        Returns:
            Dict containing comprehensive pattern analysis results
        """
        results = {
            "tool_name": tool_name,
            "session_id": session_id,
            "analysis_timestamp": None,
            "core_patterns": [],
            "specialized_patterns": []
        }
        
        try:
            from datetime import datetime
            results["analysis_timestamp"] = datetime.now().isoformat()
            
            # Core pattern analysis
            core_patterns = await self.core_analyzer.analyze_tool_usage(tool_name, arguments, session_id)
            results["core_patterns"] = core_patterns
            
            # Specialized analysis if historical data is provided
            if historical_data:
                specialized_patterns = []
                
                # Anomaly analysis
                if historical_data.get('tool_usage_history'):
                    anomaly_patterns = self.analyze_anomaly_patterns(historical_data['tool_usage_history'])
                    specialized_patterns.extend(anomaly_patterns)
                
                # Behavioral trend analysis
                if historical_data.get('session_data'):
                    trend_analysis = self.analyze_behavioral_trends(historical_data['session_data'])
                    if trend_analysis.get('trend') != 'insufficient_data':
                        specialized_patterns.append({
                            'type': 'behavioral_trend',
                            'signature': f'trend:{session_id}',
                            'data': trend_analysis,
                            'confidence': trend_analysis.get('trend_confidence', 0.5)
                        })
                
                # Context pattern analysis
                if historical_data.get('context_data'):
                    context_patterns = self.analyze_context_patterns(historical_data['context_data'])
                    specialized_patterns.extend(context_patterns)
                
                results["specialized_patterns"] = specialized_patterns
            
            # Generate summary
            results["summary"] = {
                "total_patterns": len(results["core_patterns"]) + len(results["specialized_patterns"]),
                "core_pattern_count": len(results["core_patterns"]),
                "specialized_pattern_count": len(results["specialized_patterns"]),
                "high_confidence_patterns": len([
                    p for p in results["core_patterns"] + results["specialized_patterns"] 
                    if p.get('confidence', 0) > 0.7
                ])
            }
            
        except Exception as e:
            logger.error(f"Comprehensive pattern analysis error: {e}")
            results["error"] = str(e)
        
        return results


# Maintain backward compatibility by exposing the individual analyzers
CorePatternAnalyzer = CorePatternAnalyzer
SpecializedPatternAnalysis = SpecializedPatternAnalysis