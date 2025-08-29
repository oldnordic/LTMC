"""
Specialized Pattern Analysis Modules
Advanced and specialized pattern analysis functions for specific use cases.

File: ltms/subagent/pattern_specialized_analysis.py
Lines: ~122 (under 300 limit)
Purpose: Specialized analysis modules for advanced pattern detection
"""

import logging
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class SpecializedPatternAnalysis:
    """
    Specialized pattern analysis modules for advanced use cases.
    
    Provides specialized analysis functions for complex pattern detection,
    anomaly detection, and advanced behavioral analysis.
    """
    
    def __init__(self):
        self.anomaly_threshold = 0.3
        self.trend_analysis_window = 10
    
    def analyze_anomaly_patterns(self, tool_usage_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect anomalous patterns in tool usage.
        
        Args:
            tool_usage_history: Historical tool usage data
            
        Returns:
            List of detected anomaly patterns
        """
        anomalies = []
        
        if len(tool_usage_history) < 5:
            return anomalies
        
        try:
            # Analyze tool frequency anomalies
            tool_frequencies = Counter(usage['tool_name'] for usage in tool_usage_history)
            total_usage = len(tool_usage_history)
            
            # Detect unusually high or low frequency tools
            for tool_name, frequency in tool_frequencies.items():
                frequency_ratio = frequency / total_usage
                
                # Detect tools with unusually high usage
                if frequency_ratio > 0.5:  # More than 50% of all tool calls
                    anomalies.append({
                        'type': 'high_frequency_anomaly',
                        'signature': f"anomaly:high_freq:{tool_name}",
                        'data': {
                            'tool': tool_name,
                            'frequency': frequency,
                            'frequency_ratio': frequency_ratio,
                            'severity': 'high' if frequency_ratio > 0.7 else 'medium'
                        },
                        'confidence': min(frequency_ratio, 1.0)
                    })
                
                # Detect tools used only once (potential one-off issues)
                elif frequency == 1 and total_usage > 20:
                    anomalies.append({
                        'type': 'low_frequency_anomaly',
                        'signature': f"anomaly:low_freq:{tool_name}",
                        'data': {
                            'tool': tool_name,
                            'frequency': frequency,
                            'total_usage': total_usage,
                            'severity': 'low'
                        },
                        'confidence': 0.3
                    })
            
            # Analyze execution time anomalies
            execution_times = [usage.get('execution_time_ms', 0) for usage in tool_usage_history if usage.get('execution_time_ms')]
            if execution_times:
                avg_time = sum(execution_times) / len(execution_times)
                time_threshold = avg_time * 3  # 3x average is anomalous
                
                anomalous_executions = [t for t in execution_times if t > time_threshold]
                if anomalous_executions:
                    anomalies.append({
                        'type': 'execution_time_anomaly',
                        'signature': f"anomaly:slow_execution",
                        'data': {
                            'anomalous_count': len(anomalous_executions),
                            'average_time': avg_time,
                            'max_anomalous_time': max(anomalous_executions),
                            'threshold': time_threshold
                        },
                        'confidence': min(len(anomalous_executions) / len(execution_times), 1.0)
                    })
            
        except Exception as e:
            logger.error(f"Anomaly pattern analysis error: {e}")
        
        return anomalies
    
    def analyze_behavioral_trends(self, session_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze behavioral trends across sessions.
        
        Args:
            session_data: List of session data for trend analysis
            
        Returns:
            Dict containing trend analysis results
        """
        if len(session_data) < 3:
            return {"trend": "insufficient_data"}
        
        try:
            # Analyze success score trends
            success_scores = [session.get('success_score', 0) for session in session_data]
            success_trend = self._calculate_trend(success_scores)
            
            # Analyze tool usage diversity trends
            tool_diversity_scores = []
            for session in session_data:
                tools_used = len(set(session.get('tools_used', [])))
                tool_diversity_scores.append(tools_used)
            
            diversity_trend = self._calculate_trend(tool_diversity_scores)
            
            # Analyze session duration trends
            durations = []
            for session in session_data:
                if session.get('start_time') and session.get('end_time'):
                    from datetime import datetime
                    start = datetime.fromisoformat(session['start_time'])
                    end = datetime.fromisoformat(session['end_time'])
                    duration = (end - start).total_seconds()
                    durations.append(duration)
            
            duration_trend = self._calculate_trend(durations) if durations else {"trend": "no_data"}
            
            return {
                "success_trend": success_trend,
                "tool_diversity_trend": diversity_trend,
                "duration_trend": duration_trend,
                "sessions_analyzed": len(session_data),
                "trend_confidence": min(len(session_data) / 10.0, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Behavioral trend analysis error: {e}")
            return {"trend": "analysis_error", "error": str(e)}
    
    def analyze_context_patterns(self, context_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze patterns in session context usage.
        
        Args:
            context_data: List of session context data
            
        Returns:
            List of context usage patterns
        """
        patterns = []
        
        if not context_data:
            return patterns
        
        try:
            # Analyze common context keys
            key_frequency = defaultdict(int)
            value_patterns = defaultdict(Counter)
            
            for context in context_data:
                for key, value in context.items():
                    key_frequency[key] += 1
                    # Track value patterns for common keys
                    if isinstance(value, (str, int, float, bool)):
                        value_patterns[key][str(value)] += 1
            
            total_contexts = len(context_data)
            
            # Identify frequently used context keys
            for key, frequency in key_frequency.items():
                usage_ratio = frequency / total_contexts
                
                if usage_ratio > 0.7:  # Used in >70% of contexts
                    patterns.append({
                        'type': 'common_context_key',
                        'signature': f"context:common:{key}",
                        'data': {
                            'context_key': key,
                            'usage_frequency': frequency,
                            'usage_ratio': usage_ratio,
                            'common_values': dict(value_patterns[key].most_common(3))
                        },
                        'confidence': usage_ratio
                    })
            
            # Identify context key combinations
            key_combinations = Counter()
            for context in context_data:
                keys = tuple(sorted(context.keys()))
                if len(keys) > 1:
                    key_combinations[keys] += 1
            
            # Find common combinations
            for combination, frequency in key_combinations.most_common(5):
                if frequency > 2:  # Appears in multiple contexts
                    patterns.append({
                        'type': 'context_key_combination',
                        'signature': f"context:combo:{'_'.join(combination)}",
                        'data': {
                            'key_combination': list(combination),
                            'frequency': frequency,
                            'combination_size': len(combination)
                        },
                        'confidence': min(frequency / 5.0, 1.0)
                    })
            
        except Exception as e:
            logger.error(f"Context pattern analysis error: {e}")
        
        return patterns
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """
        Calculate trend for a series of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Dict containing trend analysis
        """
        if len(values) < 2:
            return {"trend": "insufficient_data"}
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * val for i, val in enumerate(values))
        x2_sum = sum(i * i for i in range(n))
        
        denominator = n * x2_sum - x_sum * x_sum
        if denominator == 0:
            return {"trend": "stable", "slope": 0}
        
        slope = (n * xy_sum - x_sum * y_sum) / denominator
        
        # Categorize trend
        if slope > 0.1:
            trend_type = "increasing"
        elif slope < -0.1:
            trend_type = "decreasing"
        else:
            trend_type = "stable"
        
        return {
            "trend": trend_type,
            "slope": slope,
            "start_value": values[0],
            "end_value": values[-1],
            "change_magnitude": abs(values[-1] - values[0]),
            "data_points": n
        }