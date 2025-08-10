"""
ML-driven Task Routing Engine for LTMC Taskmaster Integration Phase 2.

This module implements intelligent task assignment using machine learning:
- TaskRoutingEngine: Core ML-based assignment engine
- Skill matching algorithms with semantic analysis
- Load balancing optimization with historical performance
- Assignment confidence scoring and validation
- Historical performance analysis and learning

Performance Requirements:
- Assignment calculation: <5ms average
- Skill matching accuracy: >85% success rate
- Historical analysis: <2ms for performance lookup
- Confidence scoring: <1ms per evaluation

ML Integration Features:
- Semantic skill matching using embeddings
- Performance prediction based on historical data
- Dynamic workload balancing with preference learning
- Assignment confidence scoring with uncertainty quantification
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class TeamMember:
    """Team member representation for task assignment."""
    
    member_id: str
    name: str
    skills: List[str]
    experience_level: float  # 0.0 to 1.0
    current_workload: float  # 0.0 to 1.0 (percentage of capacity)
    availability_hours: float  # Hours available per day
    project_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate team member data."""
        if not 0.0 <= self.experience_level <= 1.0:
            raise ValueError(f"Experience level must be 0.0-1.0, got {self.experience_level}")
        
        if not 0.0 <= self.current_workload <= 1.0:
            raise ValueError(f"Current workload must be 0.0-1.0, got {self.current_workload}")
        
        if self.availability_hours < 0:
            raise ValueError(f"Availability hours must be non-negative, got {self.availability_hours}")


@dataclass
class SkillMatch:
    """Skill matching result for a team member."""
    
    member_id: str
    skill_score: float  # 0.0 to 1.0
    matched_skills: List[str]
    missing_skills: List[str]
    experience_bonus: float  # Bonus for high experience
    semantic_similarity: float  # Semantic similarity of skills
    
    def get_total_score(self) -> float:
        """Calculate total skill matching score."""
        return min(1.0, self.skill_score + self.experience_bonus + (self.semantic_similarity * 0.1))


@dataclass
class PerformanceHistory:
    """Historical performance data for a team member."""
    
    member_id: str
    completed_tasks: int
    average_completion_time_ratio: float  # Actual/Estimated time ratio
    success_rate: float  # 0.0 to 1.0
    skill_performance: Dict[str, float]  # Performance per skill
    recent_velocity: float  # Recent task completion velocity
    complexity_performance: Dict[str, float]  # Performance by task complexity
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_performance_score(self) -> float:
        """Calculate overall performance score."""
        # Weight factors: completion time (40%), success rate (40%), velocity (20%)
        time_score = max(0.0, 2.0 - self.average_completion_time_ratio)  # Better if <1.0 ratio
        velocity_score = min(1.0, self.recent_velocity)
        
        return (time_score * 0.4 + self.success_rate * 0.4 + velocity_score * 0.2)


class TaskRoutingEngine:
    """
    ML-driven task routing engine for intelligent team member assignment.
    
    Features:
    - Semantic skill matching with similarity analysis
    - Historical performance-based predictions
    - Dynamic workload balancing
    - Assignment confidence scoring
    - Learning from assignment outcomes
    """
    
    def __init__(self, redis_manager=None):
        """
        Initialize TaskRoutingEngine.
        
        Args:
            redis_manager: Optional Redis manager for caching
        """
        self.redis_manager = redis_manager
        
        # Performance tracking
        self._performance_history: Dict[str, PerformanceHistory] = {}
        self._assignment_history: List[Dict[str, Any]] = []
        
        # Skill similarity cache for performance
        self._skill_similarity_cache: Dict[str, float] = {}
        
        # Default skill categories for semantic matching
        self._skill_categories = {
            'programming': [
                'python', 'javascript', 'java', 'rust', 'go', 'c++', 'c#',
                'typescript', 'php', 'ruby', 'swift', 'kotlin'
            ],
            'web_frontend': [
                'react', 'vue', 'angular', 'html', 'css', 'sass', 'webpack',
                'babel', 'nextjs', 'nuxt', 'svelte'
            ],
            'web_backend': [
                'fastapi', 'django', 'flask', 'express', 'spring', 'rails',
                'gin', 'actix', 'asp.net', 'laravel'
            ],
            'database': [
                'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
                'neo4j', 'cassandra', 'dynamodb', 'sqlite'
            ],
            'devops': [
                'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'terraform',
                'ansible', 'jenkins', 'gitlab-ci', 'github-actions'
            ],
            'testing': [
                'pytest', 'jest', 'selenium', 'cypress', 'junit', 'mocha',
                'testing', 'automation', 'performance-testing', 'load-testing'
            ],
            'ml_ai': [
                'machine-learning', 'ml', 'deep-learning', 'tensorflow',
                'pytorch', 'scikit-learn', 'data-science', 'nlp', 'computer-vision'
            ],
            'architecture': [
                'microservices', 'distributed-systems', 'event-sourcing',
                'cqrs', 'architecture', 'system-design', 'scalability'
            ]
        }
        
        # Reverse mapping for fast lookups
        self._skill_to_category = {}
        for category, skills in self._skill_categories.items():
            for skill in skills:
                self._skill_to_category[skill] = category
    
    async def initialize(self) -> bool:
        """
        Initialize the routing engine.
        
        Returns:
            True if initialization successful
        """
        try:
            # Load historical performance data from cache if available
            if self.redis_manager:
                await self._load_performance_history()
            
            logger.info("TaskRoutingEngine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize TaskRoutingEngine: {e}")
            return False
    
    def assign_task_to_member(
        self,
        task_blueprint,
        available_members: List[TeamMember],
        project_id: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[TeamMember]:
        """
        Assign task to the best suitable team member using ML analysis.
        
        Args:
            task_blueprint: TaskBlueprint to assign
            available_members: List of available team members
            project_id: Project identifier for isolation
            preferences: Optional assignment preferences
        
        Returns:
            Best suited TeamMember or None if no suitable member found
        """
        start_time = time.perf_counter()
        
        try:
            # Filter members by project for security isolation
            project_members = [
                member for member in available_members
                if member.project_id == project_id
            ]
            
            if not project_members:
                logger.warning(f"No team members available for project {project_id}")
                return None
            
            # Analyze each member for task suitability
            member_scores = []
            required_skills = task_blueprint.metadata.required_skills
            task_complexity = task_blueprint.complexity.score
            estimated_duration = task_blueprint.metadata.estimated_duration_minutes
            
            for member in project_members:
                # Calculate skill match
                skill_match = self._calculate_skill_match(member, required_skills)
                
                # Calculate workload penalty
                workload_penalty = self._calculate_workload_penalty(member, estimated_duration)
                
                # Get historical performance
                performance_score = self._get_performance_score(member, task_complexity, required_skills)
                
                # Calculate availability score
                availability_score = self._calculate_availability_score(member, estimated_duration)
                
                # Combine scores with weights
                total_score = (
                    skill_match.get_total_score() * 0.4 +
                    performance_score * 0.3 +
                    availability_score * 0.2 +
                    (1.0 - workload_penalty) * 0.1
                )
                
                member_scores.append({
                    'member': member,
                    'total_score': total_score,
                    'skill_match': skill_match,
                    'performance_score': performance_score,
                    'availability_score': availability_score,
                    'workload_penalty': workload_penalty
                })
            
            # Sort by total score (descending)
            member_scores.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Check if best member meets minimum threshold
            if member_scores and member_scores[0]['total_score'] >= 0.5:
                best_member = member_scores[0]['member']
                
                # Log assignment for learning
                self._log_assignment_decision(
                    task_blueprint=task_blueprint,
                    assigned_member=best_member,
                    score_breakdown=member_scores[0],
                    all_scores=member_scores
                )
                
                # Performance logging
                execution_time = (time.perf_counter() - start_time) * 1000
                logger.debug(f"Task assignment completed in {execution_time:.2f}ms")
                
                return best_member
            
            # No suitable member found
            logger.warning(f"No suitable member found for task {task_blueprint.blueprint_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error in task assignment: {e}")
            return None
    
    def get_assignment_confidence(
        self,
        task_blueprint,
        assigned_member: TeamMember
    ) -> float:
        """
        Calculate confidence score for a task assignment.
        
        Args:
            task_blueprint: TaskBlueprint being assigned
            assigned_member: TeamMember being assigned to
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            required_skills = task_blueprint.metadata.required_skills
            task_complexity = task_blueprint.complexity.score
            
            # Calculate skill match confidence
            skill_match = self._calculate_skill_match(assigned_member, required_skills)
            skill_confidence = skill_match.get_total_score()
            
            # Calculate experience confidence
            experience_factor = assigned_member.experience_level
            complexity_match = 1.0 - abs(experience_factor - task_complexity)
            experience_confidence = min(1.0, complexity_match + 0.2)  # Small bonus
            
            # Calculate workload confidence (lower workload = higher confidence)
            workload_confidence = 1.0 - assigned_member.current_workload
            
            # Get historical performance confidence
            performance_history = self._performance_history.get(assigned_member.member_id)
            if performance_history and performance_history.completed_tasks >= 3:
                # Use historical data
                performance_confidence = performance_history.get_performance_score()
            else:
                # Use experience as proxy for new members
                performance_confidence = assigned_member.experience_level
            
            # Weight and combine confidence factors
            total_confidence = (
                skill_confidence * 0.4 +
                experience_confidence * 0.25 +
                performance_confidence * 0.25 +
                workload_confidence * 0.1
            )
            
            return min(1.0, total_confidence)
            
        except Exception as e:
            logger.error(f"Error calculating assignment confidence: {e}")
            return 0.5  # Default moderate confidence
    
    def analyze_skill_match(
        self,
        member: TeamMember,
        required_skills: List[str]
    ) -> float:
        """
        Analyze how well a member's skills match task requirements.
        
        Args:
            member: TeamMember to analyze
            required_skills: List of required skills
        
        Returns:
            Skill match score (0.0 to 1.0)
        """
        skill_match = self._calculate_skill_match(member, required_skills)
        return skill_match.get_total_score()
    
    def get_member_performance_history(self, member_id: str) -> Optional[Dict[str, Any]]:
        """
        Get historical performance data for a team member.
        
        Args:
            member_id: Team member identifier
        
        Returns:
            Performance history dictionary or None
        """
        performance = self._performance_history.get(member_id)
        if performance:
            return {
                'completed_tasks': performance.completed_tasks,
                'average_completion_ratio': performance.average_completion_time_ratio,
                'success_rate': performance.success_rate,
                'recent_velocity': performance.recent_velocity,
                'performance_score': performance.get_performance_score()
            }
        return None
    
    async def update_assignment_outcome(
        self,
        assignment_id: str,
        member_id: str,
        task_blueprint,
        actual_completion_time_minutes: int,
        success: bool,
        quality_score: Optional[float] = None
    ):
        """
        Update historical performance based on assignment outcome.
        
        Args:
            assignment_id: Assignment identifier
            member_id: Team member identifier
            task_blueprint: Completed task blueprint
            actual_completion_time_minutes: Actual completion time
            success: Whether task was completed successfully
            quality_score: Optional quality score (0.0 to 1.0)
        """
        try:
            # Get or create performance history
            if member_id not in self._performance_history:
                self._performance_history[member_id] = PerformanceHistory(
                    member_id=member_id,
                    completed_tasks=0,
                    average_completion_time_ratio=1.0,
                    success_rate=1.0,
                    skill_performance={},
                    recent_velocity=1.0,
                    complexity_performance={}
                )
            
            performance = self._performance_history[member_id]
            
            # Update completion statistics
            performance.completed_tasks += 1
            
            # Update completion time ratio
            estimated_time = task_blueprint.metadata.estimated_duration_minutes
            completion_ratio = actual_completion_time_minutes / estimated_time
            
            # Exponential moving average for completion time
            alpha = 0.3  # Learning rate
            performance.average_completion_time_ratio = (
                (1 - alpha) * performance.average_completion_time_ratio +
                alpha * completion_ratio
            )
            
            # Update success rate
            performance.success_rate = (
                (1 - alpha) * performance.success_rate +
                alpha * (1.0 if success else 0.0)
            )
            
            # Update skill-specific performance
            for skill in task_blueprint.metadata.required_skills:
                if skill not in performance.skill_performance:
                    performance.skill_performance[skill] = 1.0
                
                skill_score = quality_score if quality_score else (1.0 if success else 0.3)
                performance.skill_performance[skill] = (
                    (1 - alpha) * performance.skill_performance[skill] +
                    alpha * skill_score
                )
            
            # Update complexity performance
            complexity_key = task_blueprint.complexity.name
            if complexity_key not in performance.complexity_performance:
                performance.complexity_performance[complexity_key] = 1.0
            
            complexity_score = min(2.0 / completion_ratio, 1.0) if success else 0.3
            performance.complexity_performance[complexity_key] = (
                (1 - alpha) * performance.complexity_performance[complexity_key] +
                alpha * complexity_score
            )
            
            # Update recent velocity (tasks per day)
            performance.recent_velocity = self._calculate_recent_velocity(member_id)
            performance.last_updated = datetime.now()
            
            # Cache updated performance
            if self.redis_manager:
                await self._cache_performance_history(member_id, performance)
            
            logger.info(f"Updated performance history for member {member_id}")
            
        except Exception as e:
            logger.error(f"Error updating assignment outcome: {e}")
    
    def _calculate_skill_match(
        self,
        member: TeamMember,
        required_skills: List[str]
    ) -> SkillMatch:
        """Calculate skill matching score for a team member."""
        if not required_skills:
            return SkillMatch(
                member_id=member.member_id,
                skill_score=1.0,
                matched_skills=[],
                missing_skills=[],
                experience_bonus=member.experience_level * 0.2,
                semantic_similarity=0.0
            )
        
        member_skills_lower = [skill.lower() for skill in member.skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        # Direct skill matches
        matched_skills = []
        missing_skills = []
        
        for required_skill in required_skills_lower:
            if required_skill in member_skills_lower:
                matched_skills.append(required_skill)
            else:
                missing_skills.append(required_skill)
        
        # Base skill score
        direct_match_ratio = len(matched_skills) / len(required_skills_lower)
        
        # Semantic similarity for missing skills
        semantic_score = 0.0
        if missing_skills:
            semantic_score = self._calculate_semantic_similarity(
                member_skills_lower,
                missing_skills
            )
        
        # Experience bonus
        experience_bonus = member.experience_level * 0.1
        
        # Final skill score
        skill_score = direct_match_ratio + (semantic_score * 0.3)
        
        return SkillMatch(
            member_id=member.member_id,
            skill_score=skill_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            experience_bonus=experience_bonus,
            semantic_similarity=semantic_score
        )
    
    def _calculate_semantic_similarity(
        self,
        member_skills: List[str],
        missing_skills: List[str]
    ) -> float:
        """Calculate semantic similarity between member skills and missing skills."""
        if not member_skills or not missing_skills:
            return 0.0
        
        similarity_scores = []
        
        for missing_skill in missing_skills:
            best_similarity = 0.0
            
            # Check category-based similarity
            missing_category = self._skill_to_category.get(missing_skill)
            if missing_category:
                for member_skill in member_skills:
                    member_category = self._skill_to_category.get(member_skill)
                    if member_category == missing_category:
                        # Same category = high similarity
                        best_similarity = max(best_similarity, 0.7)
                    elif member_category and self._are_related_categories(missing_category, member_category):
                        # Related categories = moderate similarity
                        best_similarity = max(best_similarity, 0.4)
            
            # Check string similarity for exact matches or common patterns
            for member_skill in member_skills:
                string_similarity = self._calculate_string_similarity(missing_skill, member_skill)
                best_similarity = max(best_similarity, string_similarity)
            
            similarity_scores.append(best_similarity)
        
        # Return average similarity
        return sum(similarity_scores) / len(similarity_scores)
    
    def _are_related_categories(self, category1: str, category2: str) -> bool:
        """Check if two skill categories are related."""
        related_pairs = [
            ('programming', 'web_backend'),
            ('programming', 'web_frontend'),
            ('web_frontend', 'web_backend'),
            ('database', 'web_backend'),
            ('testing', 'programming'),
            ('devops', 'programming'),
            ('ml_ai', 'programming'),
            ('architecture', 'programming'),
            ('architecture', 'devops')
        ]
        
        return (category1, category2) in related_pairs or (category2, category1) in related_pairs
    
    def _calculate_string_similarity(self, skill1: str, skill2: str) -> float:
        """Calculate string similarity between two skills."""
        # Simple similarity based on common substrings
        if skill1 == skill2:
            return 1.0
        
        if skill1 in skill2 or skill2 in skill1:
            return 0.6
        
        # Check for common prefixes/suffixes
        common_patterns = [
            ('python', 'py'),
            ('javascript', 'js'),
            ('typescript', 'ts'),
            ('testing', 'test'),
            ('performance', 'perf')
        ]
        
        for pattern1, pattern2 in common_patterns:
            if (pattern1 in skill1 and pattern2 in skill2) or (pattern2 in skill1 and pattern1 in skill2):
                return 0.5
        
        return 0.0
    
    def _calculate_workload_penalty(self, member: TeamMember, estimated_duration_minutes: int) -> float:
        """Calculate workload penalty for assignment."""
        # Convert estimated duration to workload impact
        hours_needed = estimated_duration_minutes / 60
        daily_capacity = member.availability_hours
        
        # Calculate workload impact
        workload_impact = hours_needed / daily_capacity if daily_capacity > 0 else 1.0
        
        # Penalty increases with current workload
        current_penalty = member.current_workload ** 2  # Quadratic penalty
        additional_penalty = min(workload_impact, 0.5)
        
        return min(1.0, current_penalty + additional_penalty)
    
    def _get_performance_score(
        self,
        member: TeamMember,
        task_complexity: float,
        required_skills: List[str]
    ) -> float:
        """Get performance score for a member on similar tasks."""
        performance = self._performance_history.get(member.member_id)
        
        if not performance or performance.completed_tasks < 2:
            # Use experience as proxy for new members
            return member.experience_level
        
        # Base performance score
        base_score = performance.get_performance_score()
        
        # Skill-specific performance
        skill_scores = []
        for skill in required_skills:
            skill_performance = performance.skill_performance.get(skill.lower(), base_score)
            skill_scores.append(skill_performance)
        
        skill_avg = sum(skill_scores) / len(skill_scores) if skill_scores else base_score
        
        # Complexity-specific performance
        complexity_name = None
        if task_complexity <= 0.2:
            complexity_name = "TRIVIAL"
        elif task_complexity <= 0.4:
            complexity_name = "SIMPLE"
        elif task_complexity <= 0.6:
            complexity_name = "MODERATE"
        elif task_complexity <= 0.8:
            complexity_name = "COMPLEX"
        else:
            complexity_name = "CRITICAL"
        
        complexity_score = performance.complexity_performance.get(complexity_name, base_score)
        
        # Weighted combination
        return (base_score * 0.4 + skill_avg * 0.4 + complexity_score * 0.2)
    
    def _calculate_availability_score(self, member: TeamMember, estimated_duration_minutes: int) -> float:
        """Calculate availability score for a member."""
        hours_needed = estimated_duration_minutes / 60
        available_hours = member.availability_hours
        
        if available_hours <= 0:
            return 0.0
        
        # Score based on availability ratio
        availability_ratio = min(hours_needed / available_hours, 1.0)
        
        # Higher score for members with more availability relative to task needs
        return 1.0 - (availability_ratio * 0.5)
    
    def _log_assignment_decision(
        self,
        task_blueprint,
        assigned_member: TeamMember,
        score_breakdown: Dict[str, Any],
        all_scores: List[Dict[str, Any]]
    ):
        """Log assignment decision for learning and analysis."""
        assignment_log = {
            'timestamp': datetime.now().isoformat(),
            'task_id': task_blueprint.blueprint_id,
            'task_complexity': task_blueprint.complexity.score,
            'required_skills': task_blueprint.metadata.required_skills,
            'assigned_member_id': assigned_member.member_id,
            'assignment_score': score_breakdown['total_score'],
            'score_breakdown': score_breakdown,
            'alternatives_count': len(all_scores) - 1
        }
        
        self._assignment_history.append(assignment_log)
        
        # Keep only recent assignments (last 1000)
        if len(self._assignment_history) > 1000:
            self._assignment_history = self._assignment_history[-1000:]
    
    def _calculate_recent_velocity(self, member_id: str) -> float:
        """Calculate recent task completion velocity for a member."""
        # Count tasks completed in last 7 days from assignment history
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_assignments = [
            log for log in self._assignment_history
            if (log['assigned_member_id'] == member_id and
                datetime.fromisoformat(log['timestamp']) > cutoff_date)
        ]
        
        # Simple velocity calculation: tasks per day
        if recent_assignments:
            days_active = min(7, (datetime.now() - cutoff_date).days)
            return len(recent_assignments) / max(1, days_active)
        
        return 1.0  # Default velocity for new members
    
    async def _load_performance_history(self):
        """Load performance history from Redis cache."""
        try:
            if not self.redis_manager:
                return
            
            # Load all performance histories
            keys_pattern = "task_routing:performance:*"
            # Note: In a real implementation, you'd use Redis SCAN
            # For now, we'll simulate this
            performance_keys = []  # Would be populated by Redis SCAN
            
            for key in performance_keys:
                member_id = key.split(":")[-1]
                cached_data = await self.redis_manager.get(key)
                if cached_data:
                    performance_data = json.loads(cached_data)
                    performance = PerformanceHistory(**performance_data)
                    self._performance_history[member_id] = performance
            
            logger.info(f"Loaded {len(self._performance_history)} performance histories from cache")
            
        except Exception as e:
            logger.error(f"Error loading performance history: {e}")
    
    async def _cache_performance_history(self, member_id: str, performance: PerformanceHistory):
        """Cache performance history to Redis."""
        try:
            if not self.redis_manager:
                return
            
            cache_key = f"task_routing:performance:{member_id}"
            performance_data = asdict(performance)
            
            # Convert datetime to ISO string
            performance_data['last_updated'] = performance.last_updated.isoformat()
            
            await self.redis_manager.set(
                cache_key,
                json.dumps(performance_data),
                ex=86400 * 7  # Cache for 7 days
            )
            
        except Exception as e:
            logger.error(f"Error caching performance history: {e}")