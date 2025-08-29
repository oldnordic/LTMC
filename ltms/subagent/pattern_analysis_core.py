"""
Core Pattern Analysis
Core pattern detection and analysis for subagent tool usage and behavior.

File: ltms/subagent/pattern_analysis_core.py
Lines: ~295 (under 300 limit)
Purpose: Core pattern analyzer with main analysis logic
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .pattern_helpers import PatternDatabaseHelpers, PatternUtilities

logger = logging.getLogger(__name__)


class CorePatternAnalyzer:
    """Core pattern detection and analysis for subagent behavior."""
    
    def __init__(self):
        self.db_helpers = PatternDatabaseHelpers()
        self.utilities = PatternUtilities()
        self.pattern_cache = {}
        self._pattern_thresholds = {
            'sequence_min_length': 2, 'frequency_threshold': 3,
            'timing_variance_threshold': 0.3, 'effectiveness_threshold': 0.7
        }
    
    async def analyze_tool_usage(self, tool_name: str, arguments: Dict[str, Any], 
                                session_id: str) -> List[Dict[str, Any]]:
        """Comprehensive analysis of tool usage patterns."""
        patterns = []
        try:
            # Analyze all pattern types
            patterns.extend(await self._analyze_tool_sequences(session_id, tool_name))
            if arguments:
                patterns.extend(await self._analyze_argument_patterns(tool_name, arguments))
            patterns.extend(await self._analyze_timing_patterns(session_id, tool_name))
            patterns.extend(await self._analyze_success_patterns(session_id, tool_name))
            patterns.extend(await self._analyze_tool_correlations(session_id, tool_name))
            logger.debug(f"Detected {len(patterns)} patterns for tool {tool_name}")
        except Exception as e:
            logger.error(f"Pattern analysis error for {tool_name}: {e}")
        return patterns
    
    async def _analyze_tool_sequences(self, session_id: str, current_tool: str) -> List[Dict[str, Any]]:
        """Analyze tool usage sequences for pattern detection."""
        patterns = []
        
        try:
            # Get recent tool sequence using helper
            tool_sequence = await self.db_helpers.get_recent_tool_sequence(session_id, limit=10)
            
            if len(tool_sequence) >= self._pattern_thresholds['sequence_min_length']:
                # Create sequence patterns of different lengths
                for seq_length in range(2, min(len(tool_sequence) + 1, 6)):
                    if len(tool_sequence) >= seq_length:
                        sequence = tool_sequence[-seq_length:]
                        sequence_signature = '->'.join(sequence)
                        
                        # Check frequency across all sessions using helper
                        frequency = await self.db_helpers.get_sequence_frequency(sequence_signature)
                        
                        if frequency >= self._pattern_thresholds['frequency_threshold']:
                            patterns.append({
                                'type': 'tool_sequence',
                                'signature': sequence_signature,
                                'data': {
                                    'sequence': sequence,
                                    'length': seq_length,
                                    'current_tool': current_tool,
                                    'frequency': frequency,
                                    'pattern_strength': self.utilities.calculate_pattern_strength(frequency, 100)
                                },
                                'confidence': self.utilities.calculate_sequence_confidence(sequence, frequency)
                            })
            
        except Exception as e:
            logger.error(f"Tool sequence analysis error: {e}")
        
        return patterns
    
    async def _analyze_argument_patterns(self, tool_name: str, 
                                        arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze argument usage patterns for intelligence extraction."""
        patterns = []
        
        try:
            # Common argument patterns
            action = arguments.get('action')
            target = arguments.get('target', arguments.get('path', arguments.get('file_path')))
            
            if action:
                # Action-based pattern
                action_signature = f"{tool_name}:{action}"
                action_frequency = await self.db_helpers.get_argument_pattern_frequency(action_signature)
                
                patterns.append({
                    'type': 'argument_pattern',
                    'signature': action_signature,
                    'data': {
                        'tool': tool_name,
                        'action': action,
                        'frequency': action_frequency,
                        'pattern_type': 'action_based'
                    },
                    'confidence': min(action_frequency / 5.0, 1.0)
                })
            
            if target:
                # Target-based pattern using utility helper
                target_pattern = self.utilities.extract_target_pattern(target)
                if target_pattern:
                    target_signature = f"{tool_name}:target:{target_pattern}"
                    target_frequency = await self.db_helpers.get_argument_pattern_frequency(target_signature)
                    
                    patterns.append({
                        'type': 'target_pattern',
                        'signature': target_signature,
                        'data': {
                            'tool': tool_name,
                            'target_pattern': target_pattern,
                            'frequency': target_frequency,
                            'pattern_type': 'target_based'
                        },
                        'confidence': min(target_frequency / 3.0, 1.0)
                    })
            
            # Complex argument combinations using utility helper
            if len(arguments) > 1:
                arg_combination = self.utilities.create_argument_signature(arguments)
                combo_frequency = await self.db_helpers.get_argument_pattern_frequency(arg_combination)
                
                if combo_frequency >= 2:  # Lower threshold for complex patterns
                    patterns.append({
                        'type': 'argument_combination',
                        'signature': arg_combination,
                        'data': {
                            'tool': tool_name,
                            'argument_keys': list(arguments.keys()),
                            'frequency': combo_frequency,
                            'complexity': len(arguments)
                        },
                        'confidence': min(combo_frequency / 4.0, 1.0)
                    })
            
        except Exception as e:
            logger.error(f"Argument pattern analysis error: {e}")
        
        return patterns
    
    async def _analyze_timing_patterns(self, session_id: str, 
                                      tool_name: str) -> List[Dict[str, Any]]:
        """Analyze timing patterns in tool usage."""
        patterns = []
        
        try:
            # Get recent tool invocations with timestamps using helper
            recent_invocations = await self.db_helpers.get_recent_invocations_with_timing(session_id, limit=20)
            
            if len(recent_invocations) >= 3:
                # Calculate intervals between tool calls
                intervals = []
                tool_intervals = []
                
                for i in range(1, len(recent_invocations)):
                    prev_time = datetime.fromisoformat(recent_invocations[i-1]['timestamp'])
                    curr_time = datetime.fromisoformat(recent_invocations[i]['timestamp'])
                    interval = (curr_time - prev_time).total_seconds()
                    
                    intervals.append(interval)
                    if recent_invocations[i]['tool_name'] == tool_name:
                        tool_intervals.append(interval)
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    interval_variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                    
                    # Detect burst patterns (rapid successive calls)
                    burst_count = sum(1 for interval in intervals if interval < 5.0)  # < 5 seconds
                    
                    if burst_count >= 3:
                        patterns.append({
                            'type': 'timing_burst',
                            'signature': f"burst:{tool_name}",
                            'data': {
                                'tool': tool_name,
                                'burst_frequency': burst_count,
                                'avg_interval': avg_interval,
                                'pattern_strength': min(burst_count / 5.0, 1.0)
                            },
                            'confidence': min(burst_count / 5.0, 1.0)
                        })
                    
                    # Detect regular interval patterns
                    if interval_variance < (avg_interval * self._pattern_thresholds['timing_variance_threshold']):
                        patterns.append({
                            'type': 'timing_regular',
                            'signature': f"regular:{tool_name}:{int(avg_interval)}s",
                            'data': {
                                'tool': tool_name,
                                'avg_interval': avg_interval,
                                'variance': interval_variance,
                                'regularity_score': 1.0 - (interval_variance / avg_interval)
                            },
                            'confidence': 1.0 - (interval_variance / avg_interval)
                        })
            
        except Exception as e:
            logger.error(f"Timing pattern analysis error: {e}")
        
        return patterns
    
    async def _analyze_success_patterns(self, session_id: str, 
                                       tool_name: str) -> List[Dict[str, Any]]:
        """Analyze success/failure patterns for predictive intelligence."""
        patterns = []
        
        try:
            # Get success rates for this tool across sessions using helper
            success_data = await self.db_helpers.get_tool_success_statistics(tool_name)
            
            if success_data['total_uses'] >= 5:  # Minimum data points
                success_rate = success_data['success_rate']
                
                if success_rate >= self._pattern_thresholds['effectiveness_threshold']:
                    patterns.append({
                        'type': 'high_success',
                        'signature': f"success:{tool_name}:{int(success_rate*100)}",
                        'data': {
                            'tool': tool_name,
                            'success_rate': success_rate,
                            'total_uses': success_data['total_uses'],
                            'confidence_level': 'high' if success_data['total_uses'] > 20 else 'medium'
                        },
                        'confidence': min(success_data['total_uses'] / 20.0, 1.0)
                    })
                
                elif success_rate < 0.5:  # Low success rate
                    patterns.append({
                        'type': 'low_success',
                        'signature': f"failure:{tool_name}:{int(success_rate*100)}",
                        'data': {
                            'tool': tool_name,
                            'success_rate': success_rate,
                            'total_uses': success_data['total_uses'],
                            'common_errors': success_data.get('common_errors', [])
                        },
                        'confidence': min(success_data['total_uses'] / 10.0, 1.0)
                    })
            
        except Exception as e:
            logger.error(f"Success pattern analysis error: {e}")
        
        return patterns
    
    async def _analyze_tool_correlations(self, session_id: str, 
                                        current_tool: str) -> List[Dict[str, Any]]:
        """Analyze correlations between different tools."""
        patterns = []
        
        try:
            # Get tools commonly used before/after current tool using helper
            correlation_data = await self.db_helpers.get_tool_correlations(current_tool)
            
            for correlation in correlation_data:
                if correlation['correlation_strength'] > 0.6:  # Strong correlation
                    patterns.append({
                        'type': 'tool_correlation',
                        'signature': f"correlation:{current_tool}<->{correlation['related_tool']}",
                        'data': {
                            'primary_tool': current_tool,
                            'related_tool': correlation['related_tool'],
                            'correlation_strength': correlation['correlation_strength'],
                            'correlation_type': correlation['type'],  # 'precedes' or 'follows'
                            'frequency': correlation['frequency']
                        },
                        'confidence': correlation['correlation_strength']
                    })
            
        except Exception as e:
            logger.error(f"Tool correlation analysis error: {e}")
        
        return patterns