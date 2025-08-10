"""
BlueprintService for LTMC Taskmaster Integration Phase 2.

This module implements the core BlueprintService including:
- BlueprintManager: CRUD operations for task blueprints
- Database schema extensions for blueprint storage
- Complexity analysis engine integration
- Dependency resolution algorithms
- Performance optimization with caching
- Security integration with Phase 1 project isolation

Performance Requirements:
- Blueprint creation: <5ms
- Dependency resolution: O(n log n) for n tasks
- Bulk operations: <5ms average per operation

Security Integration:
- Project isolation via project_id
- Input validation and sanitization
- Secure database operations
"""

import sqlite3
import time
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, deque

from ltms.models.task_blueprint import (
    TaskBlueprint,
    TaskComplexity,
    TaskDependency,
    TaskMetadata,
    ComplexityScorer,
    BlueprintValidationError
)


class BlueprintServiceError(Exception):
    """Base exception for blueprint service operations."""
    pass


class BlueprintNotFoundError(BlueprintServiceError):
    """Exception raised when a blueprint is not found."""
    
    def __init__(self, message: str, blueprint_id: str = None):
        super().__init__(message)
        self.blueprint_id = blueprint_id


class DependencyResolutionError(BlueprintServiceError):
    """Exception raised when dependency resolution fails."""
    
    def __init__(self, message: str, affected_blueprints: List[str] = None):
        super().__init__(message)
        self.affected_blueprints = affected_blueprints or []


class BlueprintManager:
    """
    Core manager for TaskBlueprint CRUD operations and analysis.
    
    Provides comprehensive blueprint management including:
    - Create, read, update, delete operations
    - Automatic complexity scoring
    - Dependency graph management
    - Performance optimization
    - Database persistence
    """
    
    def __init__(self, connection: sqlite3.Connection):
        """
        Initialize BlueprintManager with database connection.
        
        Args:
            connection: SQLite database connection
        """
        self.connection = connection
        self.complexity_scorer = ComplexityScorer()
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Ensure blueprint tables exist in database."""
        try:
            self.create_blueprint_tables(self.connection)
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                raise
    
    @staticmethod
    def create_blueprint_tables(conn: sqlite3.Connection):
        """
        Create blueprint-specific database tables.
        
        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()
        
        # Create TaskBlueprints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TaskBlueprints (
                blueprint_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                complexity TEXT NOT NULL,
                complexity_score REAL NOT NULL,
                project_id TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create BlueprintDependencies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BlueprintDependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dependent_task_id TEXT NOT NULL,
                prerequisite_task_id TEXT NOT NULL,
                dependency_type TEXT NOT NULL DEFAULT 'blocking',
                is_critical BOOLEAN NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (dependent_task_id) REFERENCES TaskBlueprints (blueprint_id),
                FOREIGN KEY (prerequisite_task_id) REFERENCES TaskBlueprints (blueprint_id),
                UNIQUE(dependent_task_id, prerequisite_task_id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_blueprints_project_id 
            ON TaskBlueprints (project_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_blueprints_complexity 
            ON TaskBlueprints (complexity_score)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dependencies_dependent 
            ON BlueprintDependencies (dependent_task_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dependencies_prerequisite 
            ON BlueprintDependencies (prerequisite_task_id)
        """)
        
        conn.commit()
    
    def _generate_blueprint_id(self) -> str:
        """Generate unique blueprint ID."""
        return f"bp_{uuid.uuid4().hex[:12]}"
    
    def _serialize_metadata(self, metadata: TaskMetadata) -> str:
        """Serialize TaskMetadata to JSON string."""
        return json.dumps(metadata.to_dict())
    
    def _deserialize_metadata(self, metadata_json: str) -> TaskMetadata:
        """Deserialize JSON string to TaskMetadata."""
        data = json.loads(metadata_json)
        return TaskMetadata.from_dict(data)
    
    def create_blueprint(
        self,
        title: str,
        description: str,
        metadata: TaskMetadata = None,
        project_id: Optional[str] = None,
        complexity: Optional[TaskComplexity] = None
    ) -> TaskBlueprint:
        """
        Create a new task blueprint with automatic complexity scoring.
        
        Args:
            title: Blueprint title
            description: Detailed description
            metadata: Optional metadata (creates default if None)
            project_id: Optional project identifier for isolation
            complexity: Optional explicit complexity (auto-scored if None)
        
        Returns:
            Created TaskBlueprint instance
        
        Raises:
            BlueprintValidationError: If validation fails
            BlueprintServiceError: If creation fails
        """
        if metadata is None:
            metadata = TaskMetadata()
        
        # Auto-score complexity if not provided
        if complexity is None:
            complexity_score = self.complexity_scorer.score_task_complexity(
                title=title,
                description=description,
                required_skills=metadata.required_skills
            )
            complexity = TaskComplexity.from_score(complexity_score)
        
        # Generate unique ID
        blueprint_id = self._generate_blueprint_id()
        
        # Create blueprint instance
        blueprint = TaskBlueprint(
            blueprint_id=blueprint_id,
            title=title,
            description=description,
            complexity=complexity,
            metadata=metadata,
            project_id=project_id
        )
        
        # Save to database
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO TaskBlueprints (
                    blueprint_id, title, description, complexity, complexity_score,
                    project_id, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                blueprint.blueprint_id,
                blueprint.title,
                blueprint.description,
                blueprint.complexity.name,
                blueprint.complexity.score,
                blueprint.project_id,
                self._serialize_metadata(blueprint.metadata),
                blueprint.created_at.isoformat(),
                blueprint.updated_at.isoformat()
            ))
            self.connection.commit()
            
        except sqlite3.Error as e:
            raise BlueprintServiceError(f"Failed to create blueprint: {e}")
        
        return blueprint
    
    def get_blueprint(self, blueprint_id: str) -> TaskBlueprint:
        """
        Retrieve a blueprint by ID.
        
        Args:
            blueprint_id: Unique blueprint identifier
        
        Returns:
            TaskBlueprint instance
        
        Raises:
            BlueprintNotFoundError: If blueprint doesn't exist
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT blueprint_id, title, description, complexity, complexity_score,
                   project_id, metadata_json, created_at, updated_at
            FROM TaskBlueprints
            WHERE blueprint_id = ?
        """, (blueprint_id,))
        
        row = cursor.fetchone()
        if not row:
            raise BlueprintNotFoundError(
                f"Blueprint not found: {blueprint_id}",
                blueprint_id=blueprint_id
            )
        
        # Reconstruct blueprint
        complexity = TaskComplexity[row[3]]
        metadata = self._deserialize_metadata(row[6])
        created_at = datetime.fromisoformat(row[7])
        updated_at = datetime.fromisoformat(row[8])
        
        blueprint = TaskBlueprint(
            blueprint_id=row[0],
            title=row[1],
            description=row[2],
            complexity=complexity,
            metadata=metadata,
            project_id=row[5],
            created_at=created_at,
            updated_at=updated_at
        )
        
        # Load dependencies
        blueprint.dependencies = self.get_blueprint_dependencies(blueprint_id)
        
        return blueprint
    
    def update_blueprint(
        self,
        blueprint_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[TaskMetadata] = None,
        complexity: Optional[TaskComplexity] = None
    ) -> TaskBlueprint:
        """
        Update an existing blueprint.
        
        Args:
            blueprint_id: Blueprint to update
            title: New title (optional)
            description: New description (optional)
            metadata: New metadata (optional)
            complexity: New complexity (optional, will auto-score if None and description changed)
        
        Returns:
            Updated TaskBlueprint instance
        
        Raises:
            BlueprintNotFoundError: If blueprint doesn't exist
            BlueprintServiceError: If update fails
        """
        # Get existing blueprint
        existing = self.get_blueprint(blueprint_id)
        
        # Update fields
        if title is not None:
            existing.title = title
        if description is not None:
            existing.description = description
        if metadata is not None:
            existing.metadata = metadata
        
        # Re-score complexity if description or metadata changed and complexity not explicitly set
        if complexity is None and (description is not None or metadata is not None):
            complexity_score = self.complexity_scorer.score_task_complexity(
                title=existing.title,
                description=existing.description,
                required_skills=existing.metadata.required_skills
            )
            existing.complexity = TaskComplexity.from_score(complexity_score)
        elif complexity is not None:
            existing.complexity = complexity
        
        # Update timestamp
        existing.updated_at = datetime.now()
        
        # Save to database
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                UPDATE TaskBlueprints
                SET title = ?, description = ?, complexity = ?, complexity_score = ?,
                    metadata_json = ?, updated_at = ?
                WHERE blueprint_id = ?
            """, (
                existing.title,
                existing.description,
                existing.complexity.name,
                existing.complexity.score,
                self._serialize_metadata(existing.metadata),
                existing.updated_at.isoformat(),
                blueprint_id
            ))
            
            if cursor.rowcount == 0:
                raise BlueprintNotFoundError(
                    f"Blueprint not found for update: {blueprint_id}",
                    blueprint_id=blueprint_id
                )
            
            self.connection.commit()
            
        except sqlite3.Error as e:
            raise BlueprintServiceError(f"Failed to update blueprint: {e}")
        
        return existing
    
    def delete_blueprint(self, blueprint_id: str) -> bool:
        """
        Delete a blueprint and its dependencies.
        
        Args:
            blueprint_id: Blueprint to delete
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            BlueprintServiceError: If deletion fails
        """
        cursor = self.connection.cursor()
        try:
            # Delete dependencies first
            cursor.execute("""
                DELETE FROM BlueprintDependencies
                WHERE dependent_task_id = ? OR prerequisite_task_id = ?
            """, (blueprint_id, blueprint_id))
            
            # Delete blueprint
            cursor.execute("""
                DELETE FROM TaskBlueprints
                WHERE blueprint_id = ?
            """, (blueprint_id,))
            
            deleted = cursor.rowcount > 0
            self.connection.commit()
            return deleted
            
        except sqlite3.Error as e:
            raise BlueprintServiceError(f"Failed to delete blueprint: {e}")
    
    def list_blueprints(
        self,
        project_id: Optional[str] = None,
        min_complexity: Optional[TaskComplexity] = None,
        max_complexity: Optional[TaskComplexity] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[TaskBlueprint]:
        """
        List blueprints with optional filtering.
        
        Args:
            project_id: Filter by project
            min_complexity: Minimum complexity level
            max_complexity: Maximum complexity level
            tags: Filter by tags (blueprints must have at least one tag)
            limit: Maximum number of results
            offset: Number of results to skip
        
        Returns:
            List of TaskBlueprint instances
        """
        query_parts = ["SELECT blueprint_id FROM TaskBlueprints WHERE 1=1"]
        params = []
        
        # Add filters
        if project_id is not None:
            query_parts.append("AND project_id = ?")
            params.append(project_id)
        
        if min_complexity is not None:
            query_parts.append("AND complexity_score >= ?")
            params.append(min_complexity.score)
        
        if max_complexity is not None:
            query_parts.append("AND complexity_score <= ?")
            params.append(max_complexity.score)
        
        # Order by created_at (newest first)
        query_parts.append("ORDER BY created_at DESC")
        
        # Add pagination
        if limit is not None:
            query_parts.append("LIMIT ?")
            params.append(limit)
        
        if offset > 0:
            query_parts.append("OFFSET ?")
            params.append(offset)
        
        query = " ".join(query_parts)
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        
        blueprints = []
        for row in cursor.fetchall():
            blueprint = self.get_blueprint(row[0])
            
            # Apply tag filter (done in Python for simplicity)
            if tags:
                if not any(tag in blueprint.metadata.tags for tag in tags):
                    continue
            
            blueprints.append(blueprint)
        
        return blueprints
    
    def add_dependency(
        self,
        dependent_blueprint_id: str,
        prerequisite_blueprint_id: str,
        dependency_type: str = "blocking",
        is_critical: bool = False
    ):
        """
        Add a dependency between blueprints.
        
        Args:
            dependent_blueprint_id: Blueprint that depends on prerequisite
            prerequisite_blueprint_id: Blueprint that must be completed first
            dependency_type: Type of dependency ("blocking", "soft", "resource")
            is_critical: Whether this is a critical dependency
        
        Raises:
            BlueprintNotFoundError: If either blueprint doesn't exist
            DependencyResolutionError: If this would create circular dependency
            BlueprintServiceError: If operation fails
        """
        # Verify both blueprints exist
        self.get_blueprint(dependent_blueprint_id)  # Will raise if not found
        self.get_blueprint(prerequisite_blueprint_id)  # Will raise if not found
        
        # Create dependency object for validation
        dependency = TaskDependency(
            dependent_task_id=dependent_blueprint_id,
            prerequisite_task_id=prerequisite_blueprint_id,
            dependency_type=dependency_type,
            is_critical=is_critical
        )
        
        # Get all existing dependencies for circular detection
        existing_deps = self._get_all_dependencies()
        existing_deps.append(dependency)
        
        # Validate no circular dependencies
        try:
            TaskDependency.validate_dependency_graph(existing_deps)
        except BlueprintValidationError as e:
            raise DependencyResolutionError(
                f"Adding dependency would create circular dependency: {e}",
                affected_blueprints=[dependent_blueprint_id, prerequisite_blueprint_id]
            )
        
        # Save dependency
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO BlueprintDependencies (
                    dependent_task_id, prerequisite_task_id, dependency_type,
                    is_critical, created_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                dependent_blueprint_id,
                prerequisite_blueprint_id,
                dependency_type,
                is_critical,
                datetime.now().isoformat()
            ))
            self.connection.commit()
            
        except sqlite3.IntegrityError:
            raise BlueprintServiceError(
                f"Dependency already exists: {dependent_blueprint_id} -> {prerequisite_blueprint_id}"
            )
        except sqlite3.Error as e:
            raise BlueprintServiceError(f"Failed to add dependency: {e}")
    
    def get_blueprint_dependencies(self, blueprint_id: str) -> List[TaskDependency]:
        """
        Get all dependencies for a blueprint.
        
        Args:
            blueprint_id: Blueprint to get dependencies for
        
        Returns:
            List of TaskDependency instances
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT dependent_task_id, prerequisite_task_id, dependency_type,
                   is_critical, created_at
            FROM BlueprintDependencies
            WHERE dependent_task_id = ?
        """, (blueprint_id,))
        
        dependencies = []
        for row in cursor.fetchall():
            dependency = TaskDependency(
                dependent_task_id=row[0],
                prerequisite_task_id=row[1],
                dependency_type=row[2],
                is_critical=bool(row[3]),
                created_at=datetime.fromisoformat(row[4])
            )
            dependencies.append(dependency)
        
        return dependencies
    
    def _get_all_dependencies(self) -> List[TaskDependency]:
        """Get all dependencies in the system."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT dependent_task_id, prerequisite_task_id, dependency_type,
                   is_critical, created_at
            FROM BlueprintDependencies
        """)
        
        dependencies = []
        for row in cursor.fetchall():
            dependency = TaskDependency(
                dependent_task_id=row[0],
                prerequisite_task_id=row[1],
                dependency_type=row[2],
                is_critical=bool(row[3]),
                created_at=datetime.fromisoformat(row[4])
            )
            dependencies.append(dependency)
        
        return dependencies
    
    def resolve_execution_order(self, blueprint_ids: List[str]) -> List[str]:
        """
        Resolve execution order for a set of blueprints based on dependencies.
        
        Args:
            blueprint_ids: List of blueprint IDs to order
        
        Returns:
            List of blueprint IDs in execution order
        
        Raises:
            DependencyResolutionError: If circular dependencies exist
        """
        # Get dependencies for the specified blueprints
        relevant_deps = []
        for blueprint_id in blueprint_ids:
            deps = self.get_blueprint_dependencies(blueprint_id)
            # Only include dependencies where both tasks are in our list
            for dep in deps:
                if dep.prerequisite_task_id in blueprint_ids:
                    relevant_deps.append(dep)
        
        # Use the TaskDependency resolution algorithm
        try:
            return TaskDependency.resolve_execution_order(relevant_deps)
        except Exception as e:
            raise DependencyResolutionError(
                f"Failed to resolve execution order: {e}",
                affected_blueprints=blueprint_ids
            )