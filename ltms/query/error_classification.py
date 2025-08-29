"""
LTMC Error Classification
Modular error analysis and classification - NO PLACEHOLDERS

Provides intelligent error classification, severity assessment, and
recovery strategy recommendations for LTMC execution failures.
"""

from typing import Dict, Any, Tuple, List
from enum import Enum
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels for intelligent handling."""
    LOW = "low"           # Non-critical errors, continue execution
    MEDIUM = "medium"     # Degraded functionality, try alternatives
    HIGH = "high"         # Critical errors, fallback to safe operation
    CRITICAL = "critical" # System failure, minimal response


class FallbackStrategy(Enum):
    """Fallback strategies for different error scenarios."""
    RETRY_OPERATION = "retry_operation"
    USE_ALTERNATIVE_DATABASE = "use_alternative_database"
    SINGLE_DATABASE_FALLBACK = "single_database_fallback"
    CACHED_RESULTS = "cached_results"
    MINIMAL_RESPONSE = "minimal_response"


class ErrorClassifier:
    """Intelligent error classification and strategy recommendation."""
    
    def __init__(self):
        """Initialize error classifier with patterns and strategies."""
        # Error pattern mappings
        self.error_patterns = {
            "timeout": {
                "keywords": ["timeout", "timed out", "connection timeout", "read timeout"],
                "severity": ErrorSeverity.MEDIUM,
                "strategy": FallbackStrategy.RETRY_OPERATION
            },
            "connection": {
                "keywords": ["connection", "connect", "network", "unreachable"],
                "severity": ErrorSeverity.HIGH,
                "strategy": FallbackStrategy.USE_ALTERNATIVE_DATABASE
            },
            "database_unavailable": {
                "keywords": ["unavailable", "not found", "does not exist", "offline"],
                "severity": ErrorSeverity.HIGH,
                "strategy": FallbackStrategy.USE_ALTERNATIVE_DATABASE
            },
            "permission": {
                "keywords": ["permission", "unauthorized", "access denied", "forbidden"],
                "severity": ErrorSeverity.HIGH,
                "strategy": FallbackStrategy.USE_ALTERNATIVE_DATABASE
            },
            "resource_exhausted": {
                "keywords": ["memory", "disk full", "quota exceeded", "resources"],
                "severity": ErrorSeverity.CRITICAL,
                "strategy": FallbackStrategy.MINIMAL_RESPONSE
            },
            "syntax_error": {
                "keywords": ["syntax", "malformed", "invalid query", "parse error"],
                "severity": ErrorSeverity.LOW,
                "strategy": FallbackStrategy.SINGLE_DATABASE_FALLBACK
            }
        }
        
        # Statistics tracking
        self.classification_stats = {
            "total_errors_classified": 0,
            "errors_by_severity": {severity.value: 0 for severity in ErrorSeverity},
            "errors_by_strategy": {strategy.value: 0 for strategy in FallbackStrategy},
            "error_patterns_matched": {},
            "unclassified_errors": 0
        }
        
    def classify_error(self, error_message: str, error_context: Dict[str, Any] = None) -> Tuple[ErrorSeverity, FallbackStrategy, Dict[str, Any]]:
        """
        Classify error and recommend handling strategy.
        
        Args:
            error_message: The error message to classify
            error_context: Additional context about the error
            
        Returns:
            Tuple of (severity, strategy, classification_details)
        """
        if not error_message:
            return ErrorSeverity.LOW, FallbackStrategy.RETRY_OPERATION, {"pattern": "empty_error"}
            
        self.classification_stats["total_errors_classified"] += 1
        error_lower = error_message.lower()
        
        # Try to match error patterns
        for pattern_name, pattern_config in self.error_patterns.items():
            if any(keyword in error_lower for keyword in pattern_config["keywords"]):
                severity = pattern_config["severity"]
                strategy = pattern_config["strategy"]
                
                # Update statistics
                self.classification_stats["errors_by_severity"][severity.value] += 1
                self.classification_stats["errors_by_strategy"][strategy.value] += 1
                self.classification_stats["error_patterns_matched"][pattern_name] = \
                    self.classification_stats["error_patterns_matched"].get(pattern_name, 0) + 1
                
                classification_details = {
                    "pattern": pattern_name,
                    "matched_keywords": [kw for kw in pattern_config["keywords"] if kw in error_lower],
                    "confidence": self._calculate_match_confidence(error_lower, pattern_config["keywords"]),
                    "classification_timestamp": datetime.now().isoformat()
                }
                
                return severity, strategy, classification_details
                
        # No pattern matched - use context-based classification
        return self._classify_by_context(error_message, error_context)
        
    def _classify_by_context(self, error_message: str, error_context: Dict[str, Any] = None) -> Tuple[ErrorSeverity, FallbackStrategy, Dict[str, Any]]:
        """Classify error based on context when no pattern matches."""
        self.classification_stats["unclassified_errors"] += 1
        
        # Default classification based on context
        if error_context:
            database_type = error_context.get("database_type", "")
            operation_type = error_context.get("operation_type", "")
            
            # Database-specific fallback strategies
            if database_type in ["faiss", "redis"]:
                # These are less critical - try alternatives
                severity = ErrorSeverity.MEDIUM
                strategy = FallbackStrategy.USE_ALTERNATIVE_DATABASE
            elif database_type in ["sqlite", "neo4j"]:
                # More critical databases - retry first
                severity = ErrorSeverity.HIGH
                strategy = FallbackStrategy.RETRY_OPERATION
            else:
                # Unknown database - safe fallback
                severity = ErrorSeverity.MEDIUM
                strategy = FallbackStrategy.SINGLE_DATABASE_FALLBACK
        else:
            # No context - conservative approach
            severity = ErrorSeverity.MEDIUM
            strategy = FallbackStrategy.RETRY_OPERATION
            
        self.classification_stats["errors_by_severity"][severity.value] += 1
        self.classification_stats["errors_by_strategy"][strategy.value] += 1
        
        return severity, strategy, {
            "pattern": "context_based",
            "reason": "no_pattern_match",
            "classification_timestamp": datetime.now().isoformat()
        }
        
    def _calculate_match_confidence(self, error_message: str, keywords: List[str]) -> float:
        """Calculate confidence score for pattern match."""
        matched_keywords = [kw for kw in keywords if kw in error_message]
        if not keywords:
            return 0.0
        return len(matched_keywords) / len(keywords)
        
    def get_error_insights(self) -> Dict[str, Any]:
        """Get insights about error patterns and trends."""
        total_errors = self.classification_stats["total_errors_classified"]
        if total_errors == 0:
            return {"status": "no_errors_processed"}
            
        # Calculate error distribution
        severity_distribution = {}
        for severity, count in self.classification_stats["errors_by_severity"].items():
            severity_distribution[severity] = {
                "count": count,
                "percentage": round((count / total_errors) * 100, 2)
            }
            
        strategy_distribution = {}
        for strategy, count in self.classification_stats["errors_by_strategy"].items():
            strategy_distribution[strategy] = {
                "count": count,
                "percentage": round((count / total_errors) * 100, 2)
            }
            
        return {
            "total_errors_classified": total_errors,
            "unclassified_errors": self.classification_stats["unclassified_errors"],
            "classification_success_rate": round(
                ((total_errors - self.classification_stats["unclassified_errors"]) / total_errors) * 100, 2
            ),
            "severity_distribution": severity_distribution,
            "strategy_distribution": strategy_distribution,
            "most_common_patterns": sorted(
                self.classification_stats["error_patterns_matched"].items(),
                key=lambda x: x[1], reverse=True
            )[:5]
        }
        
    def reset_statistics(self):
        """Reset error classification statistics."""
        self.classification_stats = {
            "total_errors_classified": 0,
            "errors_by_severity": {severity.value: 0 for severity in ErrorSeverity},
            "errors_by_strategy": {strategy.value: 0 for strategy in FallbackStrategy},
            "error_patterns_matched": {},
            "unclassified_errors": 0
        }