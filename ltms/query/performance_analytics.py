"""
LTMC Performance Analytics
Advanced analytics and reporting for performance monitoring - NO PLACEHOLDERS

Provides comprehensive analytics, trend analysis, and health indicators
for LTMC execution performance optimization and monitoring.
"""

from typing import Dict, Any, List
from collections import deque, defaultdict

from .performance_metrics import ExecutionMetrics


class PerformanceAnalytics:
    """Advanced performance analytics for LTMC execution monitoring."""
    
    def __init__(self, sla_target_ms: float = 2000.0):
        self.sla_target_ms = sla_target_ms
        
    def calculate_sla_analysis(self, performance_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed SLA analysis."""
        total = performance_stats["total_executions"]
        if total == 0:
            return {"status": "no_data"}
            
        violations = performance_stats["sla_violations"]
        compliance_rate = performance_stats["current_sla_compliance_rate"]
        
        status = "excellent" if compliance_rate >= 99.0 else \
                 "good" if compliance_rate >= 95.0 else \
                 "warning" if compliance_rate >= 90.0 else "critical"
                 
        return {
            "status": status,
            "compliance_rate": compliance_rate,
            "violations": violations,
            "sla_target_ms": self.sla_target_ms,
            "average_overage_ms": max(0, performance_stats["average_execution_time_ms"] - self.sla_target_ms)
        }
        
    def calculate_trend_analysis(self, execution_history: deque) -> Dict[str, Any]:
        """Calculate execution trend analysis."""
        if len(execution_history) < 20:
            return {"status": "insufficient_data"}
            
        # Compare recent vs older performance
        recent_executions = list(execution_history)[-20:]
        older_executions = list(execution_history)[-40:-20] if len(execution_history) >= 40 else []
        
        if not older_executions:
            return {"status": "insufficient_historical_data"}
            
        recent_avg_time = sum(metrics.get_execution_time_ms() 
                             for metrics in recent_executions if metrics.end_time) / len(recent_executions)
        older_avg_time = sum(metrics.get_execution_time_ms() 
                           for metrics in older_executions if metrics.end_time) / len(older_executions)
        
        trend = "improving" if recent_avg_time < older_avg_time * 0.95 else \
               "degrading" if recent_avg_time > older_avg_time * 1.05 else "stable"
               
        return {
            "trend": trend,
            "recent_avg_ms": round(recent_avg_time, 2),
            "previous_avg_ms": round(older_avg_time, 2),
            "change_percent": round(((recent_avg_time - older_avg_time) / older_avg_time) * 100, 2)
        }
        
    def calculate_health_indicators(self, performance_stats: Dict[str, Any],
                                  database_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate system health indicators."""
        indicators = {}
        
        # Performance health
        avg_time = performance_stats["average_execution_time_ms"]
        performance_health = "healthy" if avg_time < self.sla_target_ms * 0.5 else \
                           "warning" if avg_time < self.sla_target_ms * 0.8 else "critical"
        indicators["performance_health"] = performance_health
        
        # Reliability health
        success_rate = (performance_stats["successful_executions"] / 
                       max(1, performance_stats["total_executions"])) * 100
        reliability_health = "healthy" if success_rate >= 99.0 else \
                           "warning" if success_rate >= 95.0 else "critical"
        indicators["reliability_health"] = reliability_health
        
        # SLA health
        sla_rate = performance_stats["current_sla_compliance_rate"]
        sla_health = "healthy" if sla_rate >= 95.0 else \
                    "warning" if sla_rate >= 90.0 else "critical"
        indicators["sla_health"] = sla_health
        
        # Database health
        db_health_scores = []
        for db_name, db_stats in database_performance.items():
            reliability = db_stats["reliability_score"]
            if reliability >= 95.0:
                db_health_scores.append(3)  # healthy
            elif reliability >= 90.0:
                db_health_scores.append(2)  # warning
            else:
                db_health_scores.append(1)  # critical
                
        if db_health_scores:
            avg_db_health = sum(db_health_scores) / len(db_health_scores)
            database_health = "healthy" if avg_db_health >= 2.5 else \
                            "warning" if avg_db_health >= 2.0 else "critical"
        else:
            database_health = "healthy"
        indicators["database_health"] = database_health
        
        # Overall health
        health_scores = {"healthy": 3, "warning": 2, "critical": 1}
        health_values = [performance_health, reliability_health, sla_health, database_health]
        avg_health_score = sum(health_scores[status] for status in health_values) / len(health_values)
        
        overall_health = "healthy" if avg_health_score >= 2.7 else \
                        "warning" if avg_health_score >= 2.0 else "critical"
        indicators["overall_health"] = overall_health
        
        return indicators
        
    def generate_performance_recommendations(self, performance_stats: Dict[str, Any],
                                          database_performance: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # SLA violation recommendations
        if performance_stats["current_sla_compliance_rate"] < 95.0:
            recommendations.append("SLA compliance is below 95%. Consider optimizing slow database operations.")
            
        # Database performance recommendations
        for db_name, db_stats in database_performance.items():
            if db_stats["reliability_score"] < 95.0:
                recommendations.append(f"Database {db_name} reliability is {db_stats['reliability_score']}%. Check connectivity.")
            if db_stats["average_response_time_ms"] > 1000.0:
                recommendations.append(f"Database {db_name} average response time is high ({db_stats['average_response_time_ms']}ms).")
                
        # Parallel efficiency recommendations
        if performance_stats["parallel_efficiency_avg"] < 50.0:
            recommendations.append("Parallel execution efficiency is low. Consider reviewing operation dependencies.")
            
        # Coordination overhead recommendations
        if performance_stats["coordination_overhead_avg_ms"] > 100.0:
            recommendations.append("Coordination overhead is high. Consider optimizing operation planning.")
            
        # Performance trend recommendations
        avg_time = performance_stats["average_execution_time_ms"]
        if avg_time > self.sla_target_ms * 0.8:
            recommendations.append("Average execution time approaching SLA limit. Monitor closely.")
            
        return recommendations
        
    def generate_sla_compliance_report(self, performance_stats: Dict[str, Any],
                                     execution_history: deque) -> Dict[str, Any]:
        """Generate detailed SLA compliance report."""
        total_executions = performance_stats["total_executions"]
        
        if total_executions == 0:
            return {
                "overall_compliance_rate": 100.0,
                "total_executions": 0,
                "sla_violations": 0,
                "violation_analysis": {},
                "recommendations": []
            }
            
        compliance_rate = performance_stats["current_sla_compliance_rate"]
        
        # Analyze violations by database
        violation_analysis = defaultdict(int)
        slow_executions = [
            metrics for metrics in execution_history
            if metrics.end_time and not metrics.sla_compliance
        ]
        
        for metrics in slow_executions:
            for db in metrics.databases_used:
                violation_analysis[db] += 1
                
        # Generate recommendations
        recommendations = self.generate_performance_recommendations(performance_stats, {})
        
        return {
            "overall_compliance_rate": round(compliance_rate, 2),
            "total_executions": total_executions,
            "sla_violations": performance_stats["sla_violations"],
            "sla_target_ms": self.sla_target_ms,
            "violation_analysis": dict(violation_analysis),
            "slowest_execution_ms": performance_stats["slowest_execution_ms"],
            "p99_execution_time_ms": performance_stats["p99_execution_time_ms"],
            "recommendations": recommendations
        }
        
    def calculate_efficiency_metrics(self, performance_stats: Dict[str, Any],
                                   execution_history: deque) -> Dict[str, Any]:
        """Calculate execution efficiency metrics."""
        if not execution_history:
            return {"status": "no_data"}
            
        # Calculate parallelization benefits
        parallel_executions = [
            metrics for metrics in execution_history
            if metrics.parallel_operation_count > 0
        ]
        
        sequential_executions = [
            metrics for metrics in execution_history  
            if metrics.parallel_operation_count == 0 and metrics.operation_count > 0
        ]
        
        if not parallel_executions:
            return {"status": "no_parallel_executions"}
            
        # Average times for comparison
        parallel_avg = sum(metrics.get_execution_time_ms() for metrics in parallel_executions) / len(parallel_executions)
        
        if sequential_executions:
            sequential_avg = sum(metrics.get_execution_time_ms() for metrics in sequential_executions) / len(sequential_executions)
            speedup_factor = sequential_avg / parallel_avg if parallel_avg > 0 else 1.0
        else:
            speedup_factor = 1.0
            
        return {
            "parallel_executions": len(parallel_executions),
            "sequential_executions": len(sequential_executions),
            "parallel_avg_time_ms": round(parallel_avg, 2),
            "sequential_avg_time_ms": round(sequential_avg, 2) if sequential_executions else None,
            "speedup_factor": round(speedup_factor, 2),
            "parallel_efficiency": performance_stats["parallel_efficiency_avg"],
            "coordination_overhead_avg_ms": performance_stats["coordination_overhead_avg_ms"]
        }
        
    def generate_performance_summary(self, performance_stats: Dict[str, Any],
                                   database_performance: Dict[str, Any],
                                   recent_stats: Dict[str, Any],
                                   execution_history: deque) -> Dict[str, Any]:
        """Generate comprehensive performance summary."""
        return {
            "overall_statistics": performance_stats,
            "database_performance": database_performance,
            "recent_performance": recent_stats,
            "sla_analysis": self.calculate_sla_analysis(performance_stats),
            "trend_analysis": self.calculate_trend_analysis(execution_history),
            "health_indicators": self.calculate_health_indicators(performance_stats, database_performance),
            "efficiency_metrics": self.calculate_efficiency_metrics(performance_stats, execution_history),
            "recommendations": self.generate_performance_recommendations(performance_stats, database_performance),
            "sla_compliance_report": self.generate_sla_compliance_report(performance_stats, execution_history)
        }