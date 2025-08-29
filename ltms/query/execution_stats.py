"""
LTMC Execution Statistics Tracking
Modular statistics tracking for execution coordination - NO PLACEHOLDERS

Provides centralized statistics tracking for execution coordination,
parallel/sequential operation monitoring, and performance metrics.
"""

from typing import Dict, Any
from datetime import datetime


class CoordinationStatistics:
    """Tracks coordination performance and execution statistics."""
    
    def __init__(self):
        """Initialize coordination statistics tracker."""
        self.stats = {
            "total_coordinations": 0,
            "parallel_executions": 0,
            "sequential_executions": 0,
            "mixed_executions": 0,
            "total_operations_coordinated": 0,
            "average_coordination_overhead_ms": 0.0,
            "successful_coordinations": 0,
            "failed_coordinations": 0,
            "fastest_coordination_ms": float('inf'),
            "slowest_coordination_ms": 0.0,
            "last_coordination_timestamp": None
        }
        
    def record_coordination(self, operation_count: int, execution_type: str, 
                          coordination_overhead_ms: float, success: bool):
        """Record a coordination execution."""
        self.stats["total_coordinations"] += 1
        self.stats["total_operations_coordinated"] += operation_count
        self.stats["last_coordination_timestamp"] = datetime.now().isoformat()
        
        # Update execution type counters
        if execution_type == "parallel":
            self.stats["parallel_executions"] += 1
        elif execution_type == "sequential":
            self.stats["sequential_executions"] += 1
        else:
            self.stats["mixed_executions"] += 1
            
        # Update success/failure counters
        if success:
            self.stats["successful_coordinations"] += 1
        else:
            self.stats["failed_coordinations"] += 1
            
        # Update overhead statistics
        self._update_overhead_stats(coordination_overhead_ms)
        
    def _update_overhead_stats(self, overhead_ms: float):
        """Update coordination overhead statistics."""
        # Update min/max
        self.stats["fastest_coordination_ms"] = min(
            self.stats["fastest_coordination_ms"], overhead_ms
        )
        self.stats["slowest_coordination_ms"] = max(
            self.stats["slowest_coordination_ms"], overhead_ms
        )
        
        # Update average
        total_coordinations = self.stats["total_coordinations"]
        current_avg = self.stats["average_coordination_overhead_ms"]
        new_avg = ((current_avg * (total_coordinations - 1)) + overhead_ms) / total_coordinations
        self.stats["average_coordination_overhead_ms"] = round(new_avg, 2)
        
    def get_coordination_efficiency(self) -> Dict[str, Any]:
        """Calculate coordination efficiency metrics."""
        total = self.stats["total_coordinations"]
        if total == 0:
            return {"efficiency_score": 100.0, "status": "no_data"}
            
        success_rate = (self.stats["successful_coordinations"] / total) * 100
        avg_overhead = self.stats["average_coordination_overhead_ms"]
        
        # Efficiency scoring (lower overhead and higher success rate = higher score)
        overhead_score = max(0, 100 - (avg_overhead / 10))  # 10ms overhead = 1 point deduction
        efficiency_score = (success_rate * 0.7) + (overhead_score * 0.3)
        
        status = "excellent" if efficiency_score >= 90 else \
                 "good" if efficiency_score >= 80 else \
                 "fair" if efficiency_score >= 70 else "poor"
        
        return {
            "efficiency_score": round(efficiency_score, 2),
            "success_rate": round(success_rate, 2),
            "average_overhead_ms": avg_overhead,
            "status": status
        }
        
    def get_execution_breakdown(self) -> Dict[str, Any]:
        """Get breakdown of execution types."""
        total = self.stats["total_coordinations"]
        if total == 0:
            return {"breakdown": {}, "total_executions": 0}
            
        return {
            "breakdown": {
                "parallel": {
                    "count": self.stats["parallel_executions"],
                    "percentage": round((self.stats["parallel_executions"] / total) * 100, 1)
                },
                "sequential": {
                    "count": self.stats["sequential_executions"], 
                    "percentage": round((self.stats["sequential_executions"] / total) * 100, 1)
                },
                "mixed": {
                    "count": self.stats["mixed_executions"],
                    "percentage": round((self.stats["mixed_executions"] / total) * 100, 1)
                }
            },
            "total_executions": total,
            "total_operations": self.stats["total_operations_coordinated"],
            "average_operations_per_execution": round(
                self.stats["total_operations_coordinated"] / total, 2
            ) if total > 0 else 0.0
        }
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        return {
            **self.stats,
            "coordination_efficiency": self.get_coordination_efficiency(),
            "execution_breakdown": self.get_execution_breakdown()
        }
        
    def reset(self):
        """Reset all statistics."""
        for key, value in self.stats.items():
            if isinstance(value, (int, float)):
                if key == "fastest_coordination_ms":
                    self.stats[key] = float('inf')
                else:
                    self.stats[key] = 0 if isinstance(value, int) else 0.0
            else:
                self.stats[key] = None