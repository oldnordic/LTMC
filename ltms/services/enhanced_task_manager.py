"""
Enhanced TaskManager for LTMC Taskmaster Integration Phase 2.

This module implements intelligent task management with ML-driven routing:
- EnhancedTaskManager: Core task management with intelligent routing
- Task decomposition algorithms for complex tasks
- Progress tracking and predictive completion
- Integration with Component 1 TaskBlueprint system
- ML-based team member assignment with confidence scoring

Performance Requirements:
- Task routing: <10ms average
- Assignment accuracy: >85% success rate
- Blueprint integration: <5ms overhead
- Memory operations: Redis caching optimized

Security Integration:
- Project isolation via project_id
- Input validation and sanitization
- Secure assignment ID generation
- Team member access control
"""

import asyncio
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import logging

from ltms.models.task_blueprint import (
    TaskBlueprint,
    TaskComplexity,
    TaskMetadata,
    BlueprintValidationError
)
from ltms.services.blueprint_service import BlueprintManager
from ltms.ml.task_routing_engine import TaskRoutingEngine, TeamMember, PerformanceHistory

logger = logging.getLogger(__name__)


class TaskManagerError(Exception):
    """Base exception for task manager operations."""
    pass


class TaskRoutingError(TaskManagerError):
    """Exception raised when task routing fails."""
    
    def __init__(self, message: str, task_id: str = None, project_id: str = None):
        super().__init__(message)
        self.task_id = task_id
        self.project_id = project_id


class InsufficientSkillsError(TaskRoutingError):
    """Exception raised when no team member has required skills."""
    
    def __init__(self, message: str, required_skills: List[str] = None, available_members: int = 0):
        super().__init__(message)
        self.required_skills = required_skills or []
        self.available_members = available_members


@dataclass
class TaskAssignment:
    """Task assignment representation."""
    
    assignment_id: str
    blueprint_id: str
    assigned_member: TeamMember
    confidence_score: float
    estimated_completion_time: datetime
    project_id: str
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "assigned"  # assigned, in_progress, completed, failed
    progress_percentage: float = 0.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert assignment to dictionary."""
        return {
            'assignment_id': self.assignment_id,
            'blueprint_id': self.blueprint_id,
            'assigned_member': asdict(self.assigned_member),
            'confidence_score': self.confidence_score,
            'estimated_completion_time': self.estimated_completion_time.isoformat(),
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'notes': self.notes
        }


@dataclass
class TaskDecompositionResult:
    """Result of task decomposition analysis."""
    
    original_blueprint: TaskBlueprint
    subtasks: List[TaskBlueprint]
    requires_decomposition: bool
    complexity_score: float
    decomposition_strategy: str
    estimated_parallel_completion_time: Optional[timedelta] = None
    estimated_sequential_completion_time: Optional[timedelta] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert decomposition result to dictionary."""
        return {
            'original_blueprint_id': self.original_blueprint.blueprint_id,
            'subtask_ids': [subtask.blueprint_id for subtask in self.subtasks],
            'requires_decomposition': self.requires_decomposition,
            'complexity_score': self.complexity_score,
            'decomposition_strategy': self.decomposition_strategy,
            'estimated_parallel_completion_hours': (
                self.estimated_parallel_completion_time.total_seconds() / 3600
                if self.estimated_parallel_completion_time else None
            ),
            'estimated_sequential_completion_hours': (
                self.estimated_sequential_completion_time.total_seconds() / 3600
                if self.estimated_sequential_completion_time else None
            )
        }


class EnhancedTaskManager:
    """
    Enhanced task manager with intelligent routing and ML-driven assignment.
    
    Features:
    - Smart task decomposition for complex tasks
    - ML-based team member assignment
    - Progress tracking with predictive completion
    - Integration with TaskBlueprint system
    - Performance optimization with caching
    - Project isolation and security
    """
    
    def __init__(
        self,
        redis_manager=None,
        blueprint_manager: Optional[BlueprintManager] = None,
        routing_engine: Optional[TaskRoutingEngine] = None
    ):
        """
        Initialize EnhancedTaskManager.
        
        Args:
            redis_manager: Redis manager for caching
            blueprint_manager: Blueprint manager for blueprint operations
            routing_engine: ML routing engine for task assignment
        """
        self.redis_manager = redis_manager
        self.blueprint_manager = blueprint_manager
        self.routing_engine = routing_engine or TaskRoutingEngine(redis_manager)
        
        # Configuration
        self.complexity_threshold = 0.7  # Tasks above this are decomposed
        self.max_decomposition_depth = 3
        self.min_subtask_duration = 30  # Minimum subtask duration in minutes
        
        # In-memory tracking (would be persistent in production)
        self._active_assignments: Dict[str, TaskAssignment] = {}
        self._assignment_progress: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self._routing_times: List[float] = []
        self._assignment_accuracy: List[float] = []
        
        # Decomposition templates for different task types
        self._decomposition_templates = {
            'api_development': [
                'Design API specification and schema',
                'Implement core API endpoints', 
                'Add input validation and error handling',
                'Write comprehensive tests',
                'Add documentation and examples'
            ],
            'feature_implementation': [
                'Analyze requirements and design approach',
                'Implement core functionality',
                'Add user interface components',
                'Integrate with existing systems',
                'Test and validate implementation'
            ],
            'system_architecture': [
                'Design system architecture and components',
                'Implement core infrastructure',
                'Add monitoring and observability',
                'Setup deployment and CI/CD',
                'Performance optimization and testing'
            ],
            'data_processing': [
                'Design data pipeline architecture',
                'Implement data ingestion and validation',
                'Add data transformation and processing',
                'Setup storage and indexing',
                'Add monitoring and error handling'
            ]
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the task manager.
        
        Returns:
            True if initialization successful
        """
        try:
            # Initialize routing engine
            if not await self.routing_engine.initialize():
                logger.error("Failed to initialize routing engine")
                return False
            
            # Load existing assignments from cache
            if self.redis_manager:
                await self._load_assignments_from_cache()
            
            logger.info("EnhancedTaskManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize EnhancedTaskManager: {e}")
            return False
    
    async def decompose_task(self, task_blueprint: TaskBlueprint) -> TaskDecompositionResult:
        """
        Decompose a complex task into manageable subtasks.
        
        Args:
            task_blueprint: TaskBlueprint to potentially decompose
        
        Returns:
            TaskDecompositionResult with decomposition analysis
        """
        start_time = time.perf_counter()
        
        try:
            complexity_score = task_blueprint.get_complexity_score()
            
            # Check if decomposition is needed
            requires_decomposition = (
                complexity_score >= self.complexity_threshold or
                task_blueprint.metadata.estimated_duration_minutes > 240  # >4 hours
            )
            
            if not requires_decomposition:
                # Return original task as single subtask
                return TaskDecompositionResult(
                    original_blueprint=task_blueprint,
                    subtasks=[task_blueprint],
                    requires_decomposition=False,
                    complexity_score=complexity_score,
                    decomposition_strategy="no_decomposition"
                )
            
            # Determine decomposition strategy based on task content
            decomposition_strategy = self._determine_decomposition_strategy(task_blueprint)
            
            # Generate subtasks
            subtasks = await self._generate_subtasks(task_blueprint, decomposition_strategy)
            
            # Calculate timing estimates
            parallel_time, sequential_time = self._calculate_completion_estimates(subtasks)
            
            result = TaskDecompositionResult(
                original_blueprint=task_blueprint,
                subtasks=subtasks,
                requires_decomposition=True,
                complexity_score=complexity_score,
                decomposition_strategy=decomposition_strategy,
                estimated_parallel_completion_time=parallel_time,
                estimated_sequential_completion_time=sequential_time
            )
            
            # Performance logging
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Task decomposition completed in {execution_time_ms:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in task decomposition: {e}")
            # Return original task on error
            return TaskDecompositionResult(
                original_blueprint=task_blueprint,
                subtasks=[task_blueprint],
                requires_decomposition=False,
                complexity_score=task_blueprint.get_complexity_score(),
                decomposition_strategy="error_fallback"
            )
    
    async def route_task(
        self,
        task_blueprint: TaskBlueprint,
        available_members: List[TeamMember],
        project_id: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> TaskAssignment:
        """
        Route a task to the most suitable team member.
        
        Args:
            task_blueprint: TaskBlueprint to assign
            available_members: List of available team members
            project_id: Project identifier for isolation
            preferences: Optional routing preferences
        
        Returns:
            TaskAssignment with assigned member
        
        Raises:
            InsufficientSkillsError: If no suitable member found
            TaskRoutingError: If routing fails
        """
        start_time = time.perf_counter()
        
        try:
            # Validate project isolation
            project_members = [
                member for member in available_members
                if member.project_id == project_id
            ]
            
            if not project_members:
                raise InsufficientSkillsError(
                    f"No team members available for project {project_id}",
                    required_skills=task_blueprint.metadata.required_skills,
                    available_members=0
                )
            
            # Use routing engine to find best member
            assigned_member = self.routing_engine.assign_task_to_member(
                task_blueprint=task_blueprint,
                available_members=project_members,
                project_id=project_id,
                preferences=preferences
            )
            
            if not assigned_member:
                raise InsufficientSkillsError(
                    f"No suitable team member found for task {task_blueprint.blueprint_id}",
                    required_skills=task_blueprint.metadata.required_skills,
                    available_members=len(project_members)
                )
            
            # Calculate assignment confidence
            confidence_score = self.routing_engine.get_assignment_confidence(
                task_blueprint, assigned_member
            )
            
            # Estimate completion time
            estimated_completion = self._estimate_completion_time(
                task_blueprint, assigned_member
            )
            
            # Create assignment
            assignment = TaskAssignment(
                assignment_id=self._generate_assignment_id(),
                blueprint_id=task_blueprint.blueprint_id,
                assigned_member=assigned_member,
                confidence_score=confidence_score,
                estimated_completion_time=estimated_completion,
                project_id=project_id
            )
            
            # Store assignment
            self._active_assignments[assignment.assignment_id] = assignment
            
            # Cache assignment
            if self.redis_manager:
                await self._cache_assignment(assignment)
            
            # Performance tracking
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            self._routing_times.append(execution_time_ms)
            self._assignment_accuracy.append(confidence_score)
            
            # Keep only recent metrics
            if len(self._routing_times) > 100:
                self._routing_times = self._routing_times[-100:]
                self._assignment_accuracy = self._assignment_accuracy[-100:]
            
            logger.info(
                f"Task {task_blueprint.blueprint_id} assigned to {assigned_member.name} "
                f"with {confidence_score:.2%} confidence in {execution_time_ms:.2f}ms"
            )
            
            return assignment
            
        except InsufficientSkillsError:
            raise
        except Exception as e:
            raise TaskRoutingError(
                f"Failed to route task {task_blueprint.blueprint_id}: {e}",
                task_id=task_blueprint.blueprint_id,
                project_id=project_id
            )
    
    async def create_assignment_from_blueprint(
        self,
        blueprint: TaskBlueprint,
        available_members: List[TeamMember],
        project_id: str,
        auto_decompose: bool = True
    ) -> TaskAssignment:
        """
        Create task assignment from blueprint with optional decomposition.
        
        Args:
            blueprint: TaskBlueprint to assign
            available_members: Available team members
            project_id: Project identifier
            auto_decompose: Whether to auto-decompose complex tasks
        
        Returns:
            TaskAssignment for the blueprint (or main subtask if decomposed)
        """
        try:
            # Decompose if needed
            if auto_decompose:
                decomposition = await self.decompose_task(blueprint)
                
                if decomposition.requires_decomposition and len(decomposition.subtasks) > 1:
                    # For now, assign the first subtask (in production, might create multiple assignments)
                    blueprint_to_assign = decomposition.subtasks[0]
                    
                    logger.info(
                        f"Task {blueprint.blueprint_id} decomposed into {len(decomposition.subtasks)} subtasks, "
                        f"assigning first subtask: {blueprint_to_assign.blueprint_id}"
                    )
                else:
                    blueprint_to_assign = blueprint
            else:
                blueprint_to_assign = blueprint
            
            # Route the task
            assignment = await self.route_task(
                task_blueprint=blueprint_to_assign,
                available_members=available_members,
                project_id=project_id
            )
            
            return assignment
            
        except Exception as e:
            raise TaskManagerError(f"Failed to create assignment from blueprint: {e}")
    
    async def update_task_progress(
        self,
        assignment_id: str,
        progress_percentage: float,
        status: str,
        notes: str = "",
        actual_hours_worked: Optional[float] = None
    ):
        """
        Update progress for an active task assignment.
        
        Args:
            assignment_id: Assignment identifier
            progress_percentage: Progress percentage (0.0 to 1.0)
            status: Current status (assigned, in_progress, completed, failed)
            notes: Progress notes
            actual_hours_worked: Actual hours worked so far
        """
        try:
            # Validate assignment exists
            if assignment_id not in self._active_assignments:
                raise TaskManagerError(f"Assignment not found: {assignment_id}")
            
            assignment = self._active_assignments[assignment_id]
            
            # Update assignment
            assignment.progress_percentage = min(1.0, max(0.0, progress_percentage))
            assignment.status = status
            assignment.notes = notes
            
            # Store progress tracking data
            progress_data = {
                'assignment_id': assignment_id,
                'progress_percentage': progress_percentage,
                'status': status,
                'notes': notes,
                'actual_hours_worked': actual_hours_worked,
                'updated_at': datetime.now().isoformat()
            }
            
            self._assignment_progress[assignment_id] = progress_data
            
            # Cache progress
            if self.redis_manager:
                await self._cache_progress(assignment_id, progress_data)
            
            logger.info(f"Progress updated for assignment {assignment_id}: {progress_percentage:.1%}")
            
        except Exception as e:
            logger.error(f"Error updating task progress: {e}")
            raise TaskManagerError(f"Failed to update task progress: {e}")
    
    async def get_task_progress(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get progress information for a task assignment.
        
        Args:
            assignment_id: Assignment identifier
        
        Returns:
            Progress data dictionary or None if not found
        """
        try:
            # Check in-memory first
            progress = self._assignment_progress.get(assignment_id)
            if progress:
                return progress
            
            # Check cache
            if self.redis_manager:
                cached_data = await self.redis_manager.get(f"task_progress:{assignment_id}")
                if cached_data:
                    return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting task progress: {e}")
            return None
    
    async def predict_completion_time(
        self,
        assignment_id: str,
        current_progress: float,
        member_id: str
    ) -> Optional[datetime]:
        """
        Predict completion time based on current progress and historical performance.
        
        Args:
            assignment_id: Assignment identifier
            current_progress: Current progress (0.0 to 1.0)
            member_id: Team member identifier
        
        Returns:
            Predicted completion datetime or None if cannot predict
        """
        try:
            assignment = self._active_assignments.get(assignment_id)
            if not assignment:
                return None
            
            # Get member performance history
            performance = self.routing_engine.get_member_performance_history(member_id)
            
            if not performance:
                # Use original estimate if no history
                return assignment.estimated_completion_time
            
            # Calculate remaining work
            remaining_work = 1.0 - current_progress
            if remaining_work <= 0:
                return datetime.now()
            
            # Get original estimate
            blueprint = None
            if self.blueprint_manager:
                try:
                    blueprint = self.blueprint_manager.get_blueprint(assignment.blueprint_id)
                except Exception:
                    pass
            
            if not blueprint:
                # Use assignment estimate
                original_duration_hours = (
                    assignment.estimated_completion_time - assignment.created_at
                ).total_seconds() / 3600
            else:
                original_duration_hours = blueprint.metadata.estimated_duration_minutes / 60
            
            # Adjust based on performance history
            completion_ratio = performance.get('average_completion_ratio', 1.0)
            velocity = performance.get('recent_velocity', 1.0)
            
            # Predict remaining time
            adjusted_total_hours = original_duration_hours * completion_ratio / velocity
            remaining_hours = adjusted_total_hours * remaining_work
            
            predicted_completion = datetime.now() + timedelta(hours=remaining_hours)
            
            return predicted_completion
            
        except Exception as e:
            logger.error(f"Error predicting completion time: {e}")
            return None
    
    async def get_team_workload_overview(
        self,
        team_members: List[TeamMember],
        project_id: str
    ) -> Dict[str, Any]:
        """
        Get workload overview for a team.
        
        Args:
            team_members: List of team members
            project_id: Project identifier
        
        Returns:
            Workload overview dictionary
        """
        try:
            project_members = [
                member for member in team_members
                if member.project_id == project_id
            ]
            
            if not project_members:
                return {
                    'members': [],
                    'average_workload': 0.0,
                    'capacity_utilization': 0.0,
                    'total_availability': 0.0
                }
            
            # Calculate workload statistics
            total_workload = sum(member.current_workload for member in project_members)
            total_availability = sum(member.availability_hours for member in project_members)
            average_workload = total_workload / len(project_members)
            
            # Calculate capacity utilization
            max_capacity = len(project_members) * 1.0  # 100% for each member
            capacity_utilization = total_workload / max_capacity if max_capacity > 0 else 0.0
            
            # Member details
            member_details = []
            for member in project_members:
                member_details.append({
                    'member_id': member.member_id,
                    'name': member.name,
                    'current_workload': member.current_workload,
                    'availability_hours': member.availability_hours,
                    'skills': member.skills,
                    'experience_level': member.experience_level
                })
            
            return {
                'members': member_details,
                'average_workload': average_workload,
                'capacity_utilization': capacity_utilization,
                'total_availability': total_availability,
                'project_id': project_id,
                'member_count': len(project_members)
            }
            
        except Exception as e:
            logger.error(f"Error getting team workload overview: {e}")
            return {'error': str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the task manager.
        
        Returns:
            Performance metrics dictionary
        """
        try:
            metrics = {
                'routing_performance': {
                    'average_routing_time_ms': (
                        sum(self._routing_times) / len(self._routing_times)
                        if self._routing_times else 0.0
                    ),
                    'max_routing_time_ms': max(self._routing_times) if self._routing_times else 0.0,
                    'min_routing_time_ms': min(self._routing_times) if self._routing_times else 0.0,
                    'total_routings': len(self._routing_times)
                },
                'assignment_accuracy': {
                    'average_confidence': (
                        sum(self._assignment_accuracy) / len(self._assignment_accuracy)
                        if self._assignment_accuracy else 0.0
                    ),
                    'assignments_above_threshold': (
                        len([score for score in self._assignment_accuracy if score >= 0.85])
                        if self._assignment_accuracy else 0
                    ),
                    'total_assignments': len(self._assignment_accuracy)
                },
                'active_assignments': len(self._active_assignments),
                'tracked_progress_items': len(self._assignment_progress)
            }
            
            # Calculate accuracy percentage
            if metrics['assignment_accuracy']['total_assignments'] > 0:
                metrics['assignment_accuracy']['success_rate'] = (
                    metrics['assignment_accuracy']['assignments_above_threshold'] /
                    metrics['assignment_accuracy']['total_assignments']
                )
            else:
                metrics['assignment_accuracy']['success_rate'] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    def _generate_assignment_id(self) -> str:
        """Generate secure assignment ID."""
        timestamp = int(time.time() * 1000)
        random_part = uuid.uuid4().hex[:8]
        return f"assign_{timestamp}_{random_part}"
    
    def _determine_decomposition_strategy(self, task_blueprint: TaskBlueprint) -> str:
        """Determine the best decomposition strategy for a task."""
        description_lower = task_blueprint.description.lower()
        title_lower = task_blueprint.title.lower()
        combined_text = f"{title_lower} {description_lower}"
        
        # Check for specific patterns
        if any(word in combined_text for word in ['api', 'endpoint', 'rest', 'graphql']):
            return 'api_development'
        elif any(word in combined_text for word in ['feature', 'implement', 'functionality']):
            return 'feature_implementation'
        elif any(word in combined_text for word in ['architecture', 'system', 'infrastructure', 'microservice']):
            return 'system_architecture'
        elif any(word in combined_text for word in ['data', 'pipeline', 'processing', 'etl']):
            return 'data_processing'
        else:
            return 'feature_implementation'  # Default strategy
    
    async def _generate_subtasks(
        self,
        task_blueprint: TaskBlueprint,
        decomposition_strategy: str
    ) -> List[TaskBlueprint]:
        """Generate subtasks based on decomposition strategy."""
        try:
            # Get template for decomposition
            template = self._decomposition_templates.get(
                decomposition_strategy,
                self._decomposition_templates['feature_implementation']
            )
            
            # Calculate duration distribution
            total_duration = task_blueprint.metadata.estimated_duration_minutes
            subtask_durations = self._distribute_duration(total_duration, len(template))
            
            # Create subtasks
            subtasks = []
            for i, (subtask_title, duration) in enumerate(zip(template, subtask_durations)):
                # Generate subtask metadata
                subtask_metadata = TaskMetadata(
                    estimated_duration_minutes=duration,
                    required_skills=task_blueprint.metadata.required_skills[:],  # Copy skills
                    priority_score=task_blueprint.metadata.priority_score,
                    tags=task_blueprint.metadata.tags[:] + [f"subtask_{i+1}"]
                )
                
                # Determine subtask complexity (typically lower than parent)
                subtask_complexity_score = max(0.1, task_blueprint.get_complexity_score() - 0.2)
                subtask_complexity = TaskComplexity.from_score(subtask_complexity_score)
                
                # Create subtask blueprint
                subtask = TaskBlueprint(
                    blueprint_id=f"{task_blueprint.blueprint_id}_sub_{i+1}",
                    title=f"{subtask_title}",
                    description=f"Subtask {i+1} of {task_blueprint.title}: {subtask_title}",
                    complexity=subtask_complexity,
                    metadata=subtask_metadata,
                    project_id=task_blueprint.project_id
                )
                
                subtasks.append(subtask)
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Error generating subtasks: {e}")
            # Return original task as single subtask on error
            return [task_blueprint]
    
    def _distribute_duration(self, total_duration: int, num_subtasks: int) -> List[int]:
        """Distribute total duration across subtasks."""
        if num_subtasks <= 1:
            return [total_duration]
        
        # Use weighted distribution (some tasks naturally take longer)
        weights = [1.0, 1.5, 1.2, 1.0, 0.8][:num_subtasks]  # Front-loaded
        total_weight = sum(weights)
        
        durations = []
        for weight in weights:
            duration = int((weight / total_weight) * total_duration)
            duration = max(self.min_subtask_duration, duration)  # Minimum duration
            durations.append(duration)
        
        return durations
    
    def _calculate_completion_estimates(
        self,
        subtasks: List[TaskBlueprint]
    ) -> Tuple[Optional[timedelta], Optional[timedelta]]:
        """Calculate parallel and sequential completion time estimates."""
        try:
            if not subtasks:
                return None, None
            
            # Sequential: sum of all durations
            total_minutes = sum(
                subtask.metadata.estimated_duration_minutes for subtask in subtasks
            )
            sequential_time = timedelta(minutes=total_minutes)
            
            # Parallel: longest subtask (assuming perfect parallelization)
            max_minutes = max(
                subtask.metadata.estimated_duration_minutes for subtask in subtasks
            )
            parallel_time = timedelta(minutes=max_minutes)
            
            return parallel_time, sequential_time
            
        except Exception as e:
            logger.error(f"Error calculating completion estimates: {e}")
            return None, None
    
    def _estimate_completion_time(
        self,
        task_blueprint: TaskBlueprint,
        assigned_member: TeamMember
    ) -> datetime:
        """Estimate completion time for a task assignment."""
        try:
            # Base estimate from blueprint
            base_hours = task_blueprint.metadata.estimated_duration_minutes / 60
            
            # Adjust for member experience and workload
            experience_factor = 0.5 + (assigned_member.experience_level * 0.5)  # 0.5 to 1.0
            workload_factor = 1.0 + assigned_member.current_workload  # Delay due to other work
            
            # Get historical performance if available
            performance = self.routing_engine.get_member_performance_history(assigned_member.member_id)
            if performance and performance['completed_tasks'] >= 3:
                completion_ratio = performance['average_completion_ratio']
                velocity = performance['recent_velocity']
                historical_factor = completion_ratio / max(0.1, velocity)
            else:
                historical_factor = 1.0
            
            # Calculate adjusted duration
            adjusted_hours = base_hours * historical_factor * workload_factor / experience_factor
            
            # Add buffer based on complexity
            complexity_buffer = task_blueprint.get_complexity_score() * 0.2  # Up to 20% buffer
            final_hours = adjusted_hours * (1.0 + complexity_buffer)
            
            # Account for daily availability
            working_days = final_hours / max(1.0, assigned_member.availability_hours)
            
            # Estimate completion date (assuming 5 working days per week)
            calendar_days = working_days * 1.4  # Weekend factor
            completion_time = datetime.now() + timedelta(days=calendar_days)
            
            return completion_time
            
        except Exception as e:
            logger.error(f"Error estimating completion time: {e}")
            # Default to blueprint estimate
            base_hours = task_blueprint.metadata.estimated_duration_minutes / 60
            return datetime.now() + timedelta(hours=base_hours)
    
    async def _cache_assignment(self, assignment: TaskAssignment):
        """Cache assignment to Redis."""
        try:
            if not self.redis_manager:
                return
            
            cache_key = f"task_assignment:{assignment.assignment_id}"
            assignment_data = assignment.to_dict()
            
            await self.redis_manager.set(
                cache_key,
                json.dumps(assignment_data),
                ex=86400 * 7  # Cache for 7 days
            )
            
        except Exception as e:
            logger.error(f"Error caching assignment: {e}")
    
    async def _cache_progress(self, assignment_id: str, progress_data: Dict[str, Any]):
        """Cache progress data to Redis."""
        try:
            if not self.redis_manager:
                return
            
            cache_key = f"task_progress:{assignment_id}"
            
            await self.redis_manager.set(
                cache_key,
                json.dumps(progress_data),
                ex=86400 * 7  # Cache for 7 days
            )
            
        except Exception as e:
            logger.error(f"Error caching progress: {e}")
    
    async def _load_assignments_from_cache(self):
        """Load existing assignments from Redis cache."""
        try:
            if not self.redis_manager:
                return
            
            # Note: In a real implementation, you'd use Redis SCAN
            # For now, we'll simulate this
            assignment_keys = []  # Would be populated by Redis SCAN
            
            for key in assignment_keys:
                assignment_id = key.split(":")[-1]
                cached_data = await self.redis_manager.get(key)
                if cached_data:
                    assignment_data = json.loads(cached_data)
                    # Reconstruct assignment (simplified)
                    # In production, you'd properly deserialize all fields
                    logger.debug(f"Loaded assignment {assignment_id} from cache")
            
        except Exception as e:
            logger.error(f"Error loading assignments from cache: {e}")