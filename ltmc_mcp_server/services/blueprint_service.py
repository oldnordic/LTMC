"""
Blueprint Service - Task Blueprint Management for LTMC
======================================================

Provides task blueprint creation and management capabilities.
"""
import time
import uuid
from typing import Dict, List, Any, Optional
from ..config.settings import LTMCSettings


class BlueprintService:
    """Service for managing task blueprints."""
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self._blueprints = {}  # In-memory storage for simplicity
        
    def create_blueprint(self, title: str, description: str, estimated_duration_minutes: int = 60,
                        required_skills: Optional[List[str]] = None, priority_score: float = 0.5) -> str:
        """Create a new task blueprint."""
        try:
            blueprint_id = str(uuid.uuid4())
            
            if required_skills is None:
                required_skills = []
                
            # Calculate complexity score based on description length and required skills
            complexity_score = min(1.0, (len(description) / 500.0) + (len(required_skills) * 0.1))
            
            blueprint = {
                "id": blueprint_id,
                "title": title,
                "description": description,
                "estimated_duration_minutes": estimated_duration_minutes,
                "required_skills": required_skills,
                "priority_score": priority_score,
                "complexity_score": complexity_score,
                "created_at": time.time(),
                "status": "draft",
                "metadata": {
                    "word_count": len(description.split()),
                    "skill_count": len(required_skills)
                }
            }
            
            self._blueprints[blueprint_id] = blueprint
            return blueprint_id
            
        except Exception as e:
            raise Exception(f"Failed to create blueprint: {str(e)}")
    
    def get_blueprint(self, blueprint_id: str) -> Optional[Dict[str, Any]]:
        """Get a blueprint by ID."""
        return self._blueprints.get(blueprint_id)
    
    def update_blueprint_status(self, blueprint_id: str, status: str) -> bool:
        """Update blueprint status."""
        if blueprint_id in self._blueprints:
            self._blueprints[blueprint_id]["status"] = status
            self._blueprints[blueprint_id]["updated_at"] = time.time()
            return True
        return False
    
    def list_blueprints(self, status: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """List blueprints with optional filtering."""
        blueprints = list(self._blueprints.values())
        
        if status:
            blueprints = [bp for bp in blueprints if bp["status"] == status]
        
        # Sort by creation time, most recent first
        blueprints.sort(key=lambda x: x["created_at"], reverse=True)
        
        return blueprints[:limit]
    
    def get_blueprint_statistics(self) -> Dict[str, Any]:
        """Get blueprint statistics."""
        total = len(self._blueprints)
        if total == 0:
            return {"total": 0, "status_distribution": {}, "average_complexity": 0.0}
        
        status_counts = {}
        total_complexity = 0.0
        
        for blueprint in self._blueprints.values():
            status = blueprint["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            total_complexity += blueprint["complexity_score"]
        
        return {
            "total": total,
            "status_distribution": status_counts,
            "average_complexity": total_complexity / total
        }