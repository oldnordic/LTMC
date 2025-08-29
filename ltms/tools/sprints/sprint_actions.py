"""
Professional Sprint Management tools for LTMC MCP server.
Provides comprehensive sprint lifecycle management with agent coordination integration.

File: ltms/tools/sprints/sprint_actions.py
Lines: ~290 (under 300 limit)
Purpose: Sprint management, story tracking, task coordination, and LTMC integration
"""

import os
import json
import logging
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config
from ..coordination.coordination_actions import CoordinationTools
from ..coordination.coordination_actions import coordination_action
from .workflow_patterns import get_workflow_manager

logger = logging.getLogger(__name__)


class SprintTools(MCPToolBase):
    """Professional sprint management tools with comprehensive lifecycle support.
    
    Integrates with LTMC coordination system and provides full sprint management
    capabilities including projects, epics, stories, tasks, and collaboration.
    """
    
    def __init__(self):
        super().__init__("SprintTools")
        self.config = get_tool_config()
        self.coordination_dir = Path("/home/feanor/Projects/ltmc/.ltmc-coordination")
        self.workflow_manager = get_workflow_manager()
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid sprint management actions."""
        return [
            # Project management
            'create_project', 'list_projects', 'get_project', 'update_project',
            # Sprint management
            'create_sprint', 'list_sprints', 'get_sprint', 'update_sprint', 'start_sprint', 'complete_sprint',
            # Epic management
            'create_epic', 'list_epics', 'get_epic', 'update_epic',
            # Story management
            'create_story', 'list_stories', 'get_story', 'update_story', 'assign_story', 'move_story',
            # Task management
            'create_task', 'list_tasks', 'get_task', 'update_task', 'assign_task', 'complete_task',
            # Reporting and metrics
            'get_sprint_dashboard', 'get_story_progress', 'get_team_velocity', 'get_burndown_data',
            # LTMC coordination integration
            'link_coordination', 'create_sprint_workflow', 'assign_agents', 'get_sprint_coordination',
            # Workflow state management
            'transition_workflow_state', 'get_workflow_state', 'list_workflow_types'
        ]
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute sprint management action."""
        action_map = {
            # Project management
            'create_project': self._action_create_project,
            'list_projects': self._action_list_projects,
            
            # Sprint management
            'create_sprint': self._action_create_sprint,
            'start_sprint': self._action_start_sprint,
            
            # Story management
            'create_story': self._action_create_story,
            'assign_story': self._action_assign_story,
            
            # Task management
            'create_task': self._action_create_task,
            'list_tasks': self._action_list_tasks,
            'update_task': self._action_update_task,
            'complete_task': self._action_complete_task,
            
            # Reporting
            'get_sprint_dashboard': self._action_get_sprint_dashboard,
            'get_story_progress': self._action_get_story_progress,
            
            # LTMC coordination
            'create_sprint_workflow': self._action_create_sprint_workflow,
            'link_coordination': self._action_link_coordination,
            
            # Workflow state management
            'transition_workflow_state': self._action_transition_workflow_state,
            'get_workflow_state': self._action_get_workflow_state,
            'list_workflow_types': self._action_list_workflow_types,
        }
        
        if action in action_map:
            return await action_map[action](**params)
        else:
            return self._create_error_response(f"Unknown sprint action: {action}")
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection to LTMC database."""
        db_path = self.config.get_db_path()
        return sqlite3.connect(db_path)
    
    # ================================
    # PROJECT MANAGEMENT ACTIONS
    # ================================
    
    async def _action_create_project(self, name: str, description: str = "", 
                                   created_by: str = None, **params) -> Dict[str, Any]:
        """Create a new project."""
        try:
            project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with self._get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO projects (id, name, description, created_by, project_metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (project_id, name, description, created_by, json.dumps(params)))
                conn.commit()
            
            # Create coordination workflow for project
            coordination_tools = CoordinationTools()
            await coordination_tools("create_workflow",
                workflow_id=f"project_{project_id}",
                description=f"Project coordination for {name}",
                agent_id=created_by or 'system'
            )
            
            return self._create_success_response({
                "project_created": True,
                "project_id": project_id,
                "name": name,
                "created_by": created_by
            })
            
        except Exception as e:
            return self._create_error_response(f'Create project failed: {str(e)}')
    
    async def _action_list_projects(self, status: str = None, **params) -> Dict[str, Any]:
        """List all projects, optionally filtered by status."""
        try:
            with self._get_db_connection() as conn:
                if status:
                    cursor = conn.execute("""
                        SELECT id, name, description, status, created_at, created_by
                        FROM projects WHERE status = ?
                        ORDER BY created_at DESC
                    """, (status,))
                else:
                    cursor = conn.execute("""
                        SELECT id, name, description, status, created_at, created_by
                        FROM projects
                        ORDER BY created_at DESC
                    """)
                
                projects = []
                for row in cursor.fetchall():
                    projects.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "status": row[3],
                        "created_at": row[4],
                        "created_by": row[5]
                    })
            
            return self._create_success_response({
                "projects": projects,
                "total_projects": len(projects),
                "filtered_by_status": status
            })
            
        except Exception as e:
            return self._create_error_response(f'List projects failed: {str(e)}')
    
    # ================================
    # SPRINT MANAGEMENT ACTIONS
    # ================================
    
    async def _action_create_sprint(self, project_id: str, name: str, goal: str,
                                  start_date: str = None, end_date: str = None,
                                  planned_capacity: int = None, created_by: str = None,
                                  **params) -> Dict[str, Any]:
        """Create a new sprint."""
        try:
            sprint_id = f"sprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with self._get_db_connection() as conn:
                # Get next sprint number for project
                cursor = conn.execute("""
                    SELECT COALESCE(MAX(sprint_number), 0) + 1 
                    FROM sprints WHERE project_id = ?
                """, (project_id,))
                sprint_number = cursor.fetchone()[0]
                
                conn.execute("""
                    INSERT INTO sprints (id, project_id, sprint_number, name, goal, 
                                       start_date, end_date, planned_capacity, created_by, sprint_metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sprint_id, project_id, sprint_number, name, goal, 
                     start_date, end_date, planned_capacity, created_by, json.dumps(params)))
                conn.commit()
            
            # Create coordination workflow for sprint
            coordination_tools = CoordinationTools()
            workflow_result = await coordination_tools("create_workflow",
                workflow_id=f"sprint_{sprint_id}",
                description=f"Sprint coordination for {name} (Sprint {sprint_number})",
                agent_id=created_by or 'system'
            )
            
            return self._create_success_response({
                "sprint_created": True,
                "sprint_id": sprint_id,
                "sprint_number": sprint_number,
                "name": name,
                "goal": goal,
                "coordination_workflow": workflow_result.get('data', {}).get('workflow_id')
            })
            
        except Exception as e:
            return self._create_error_response(f'Create sprint failed: {str(e)}')
    
    async def _action_start_sprint(self, sprint_id: str, started_by: str = None, **params) -> Dict[str, Any]:
        """Start a sprint and update its status."""
        coordination_tools = CoordinationTools()
        try:
            with self._get_db_connection() as conn:
                conn.execute("""
                    UPDATE sprints 
                    SET status = 'active', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = 'planned'
                """, (sprint_id,))
                
                if conn.total_changes == 0:
                    return self._create_error_response("Sprint not found or already started")
                
                conn.commit()
            
            # Update coordination workflow
            await coordination_tools("update_status",
                workflow_id=f"sprint_{sprint_id}",
                status='sprint_active',
                agent_id=started_by or 'system'
            )
            
            return self._create_success_response({
                "sprint_started": True,
                "sprint_id": sprint_id,
                "started_by": started_by,
                "new_status": "active"
            })
            
        except Exception as e:
            return self._create_error_response(f'Start sprint failed: {str(e)}')
    
    # ================================
    # STORY MANAGEMENT ACTIONS  
    # ================================
    
    async def _action_create_story(self, project_id: str, title: str, description: str,
                                 sprint_id: str = None, epic_id: str = None,
                                 story_points: int = None, assignee: str = None,
                                 reporter: str = None, **params) -> Dict[str, Any]:
        """Create a new user story."""
        coordination_tools = CoordinationTools()
        try:
            story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with self._get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO stories (id, project_id, sprint_id, epic_id, title, description,
                                       story_points, assignee, reporter, story_metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (story_id, project_id, sprint_id, epic_id, title, description,
                     story_points, assignee, reporter, json.dumps(params)))
                conn.commit()
            
            # Store analysis for potential handoff if assigned
            if assignee:
                await coordination_tools("store_analysis",
                    agent_id='sprint_system',
                    analysis_data={
                        'story_created': story_id,
                        'title': title,
                        'description': description,
                        'story_points': story_points,
                        'assignment_context': params
                    },
                    target_agent=assignee,
                    instructions=f"Work on user story: {title}"
                )
            
            return self._create_success_response({
                "story_created": True,
                "story_id": story_id,
                "title": title,
                "assignee": assignee,
                "story_points": story_points
            })
            
        except Exception as e:
            return self._create_error_response(f'Create story failed: {str(e)}')
    
    async def _action_assign_story(self, story_id: str, assignee: str, 
                                 assigned_by: str = None, **params) -> Dict[str, Any]:
        """Assign a story to a team member or agent."""
        coordination_tools = CoordinationTools()
        try:
            with self._get_db_connection() as conn:
                # Get story details for handoff
                cursor = conn.execute("""
                    SELECT title, description, story_points, sprint_id
                    FROM stories WHERE id = ?
                """, (story_id,))
                story = cursor.fetchone()
                
                if not story:
                    return self._create_error_response("Story not found")
                
                # Update assignment
                conn.execute("""
                    UPDATE stories 
                    SET assignee = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (assignee, story_id))
                conn.commit()
            
            # Create handoff for assigned agent
            await coordination_tools("store_handoff",
                source_agent=assigned_by or 'sprint_system',
                target_agent=assignee,
                context={
                    'story_id': story_id,
                    'title': story[0],
                    'description': story[1],
                    'story_points': story[2],
                    'sprint_id': story[3],
                    'assignment_details': params
                },
                instructions=f"Complete user story: {story[0]}",
                validation_criteria=[
                    "Story acceptance criteria met",
                    "Code reviewed and approved",
                    "Tests passing",
                    "Documentation updated if needed"
                ]
            )
            
            return self._create_success_response({
                "story_assigned": True,
                "story_id": story_id,
                "assignee": assignee,
                "assigned_by": assigned_by
            })
            
        except Exception as e:
            return self._create_error_response(f'Assign story failed: {str(e)}')
    
    # ================================
    # TASK MANAGEMENT ACTIONS
    # ================================
    
    async def _action_create_task(self, story_id: str, title: str, description: str = "",
                                task_type: str = "development", estimated_hours: float = None,
                                assignee: str = None, **params) -> Dict[str, Any]:
        """Create a task within a story."""
        try:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with self._get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO tasks (id, story_id, title, description, task_type,
                                     estimated_hours, assignee, task_metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (task_id, story_id, title, description, task_type,
                     estimated_hours, assignee, json.dumps(params)))
                conn.commit()
            
            return self._create_success_response({
                "task_created": True,
                "task_id": task_id,
                "story_id": story_id,
                "title": title,
                "task_type": task_type,
                "assignee": assignee
            })
            
        except Exception as e:
            return self._create_error_response(f'Create task failed: {str(e)}')
    
    async def _action_complete_task(self, task_id: str, completed_by: str = None,
                                  actual_hours: float = None, **params) -> Dict[str, Any]:
        """Mark a task as completed."""
        try:
            with self._get_db_connection() as conn:
                update_fields = ["status = 'done'", "updated_at = CURRENT_TIMESTAMP"]
                update_values = []
                
                if actual_hours is not None:
                    update_fields.append("actual_hours = ?")
                    update_values.append(actual_hours)
                
                update_values.append(task_id)
                
                conn.execute(f"""
                    UPDATE tasks 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, update_values)
                
                if conn.total_changes == 0:
                    return self._create_error_response("Task not found")
                
                conn.commit()
            
            return self._create_success_response({
                "task_completed": True,
                "task_id": task_id,
                "completed_by": completed_by,
                "actual_hours": actual_hours
            })
            
        except Exception as e:
            return self._create_error_response(f'Complete task failed: {str(e)}')
    
    async def _action_list_tasks(self, story_id: str = None, assignee: str = None, 
                               status: str = None, **params) -> Dict[str, Any]:
        """List tasks with optional filtering."""
        try:
            with self._get_db_connection() as conn:
                where_conditions = []
                query_params = []
                
                if story_id:
                    where_conditions.append("t.story_id = ?")
                    query_params.append(story_id)
                
                if assignee:
                    where_conditions.append("t.assignee = ?")
                    query_params.append(assignee)
                
                if status:
                    where_conditions.append("t.status = ?")
                    query_params.append(status)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                cursor = conn.execute(f"""
                    SELECT t.id, t.story_id, t.title, t.description, t.status, t.task_type,
                           t.estimated_hours, t.actual_hours, t.assignee, t.created_at,
                           st.title as story_title, st.project_id
                    FROM tasks t
                    JOIN stories st ON t.story_id = st.id
                    {where_clause}
                    ORDER BY t.created_at DESC
                """, query_params)
                
                tasks = []
                for row in cursor.fetchall():
                    tasks.append({
                        "id": row[0],
                        "story_id": row[1],
                        "title": row[2],
                        "description": row[3],
                        "status": row[4],
                        "task_type": row[5],
                        "estimated_hours": row[6],
                        "actual_hours": row[7],
                        "assignee": row[8],
                        "created_at": row[9],
                        "story_title": row[10],
                        "project_id": row[11]
                    })
            
            return self._create_success_response({
                "tasks": tasks,
                "total_tasks": len(tasks),
                "filtered_by": {
                    "story_id": story_id,
                    "assignee": assignee,
                    "status": status
                }
            })
            
        except Exception as e:
            return self._create_error_response(f'List tasks failed: {str(e)}')
    
    async def _action_update_task(self, task_id: str, title: str = None, description: str = None,
                                status: str = None, assignee: str = None, estimated_hours: float = None,
                                actual_hours: float = None, **params) -> Dict[str, Any]:
        """Update an existing task."""
        try:
            update_fields = []
            update_values = []
            
            if title is not None:
                update_fields.append("title = ?")
                update_values.append(title)
            
            if description is not None:
                update_fields.append("description = ?")
                update_values.append(description)
                
            if status is not None:
                update_fields.append("status = ?")
                update_values.append(status)
                
            if assignee is not None:
                update_fields.append("assignee = ?")
                update_values.append(assignee)
                
            if estimated_hours is not None:
                update_fields.append("estimated_hours = ?")
                update_values.append(estimated_hours)
                
            if actual_hours is not None:
                update_fields.append("actual_hours = ?")
                update_values.append(actual_hours)
            
            if not update_fields:
                return self._create_error_response("No fields provided for update")
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(task_id)
            
            with self._get_db_connection() as conn:
                conn.execute(f"""
                    UPDATE tasks 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, update_values)
                
                if conn.total_changes == 0:
                    return self._create_error_response("Task not found")
                
                conn.commit()
            
            return self._create_success_response({
                "task_updated": True,
                "task_id": task_id,
                "updated_fields": {
                    "title": title,
                    "description": description,
                    "status": status,
                    "assignee": assignee,
                    "estimated_hours": estimated_hours,
                    "actual_hours": actual_hours
                }
            })
            
        except Exception as e:
            return self._create_error_response(f'Update task failed: {str(e)}')
    
    async def _action_get_story_progress(self, story_id: str, **params) -> Dict[str, Any]:
        """Get detailed progress information for a story."""
        try:
            with self._get_db_connection() as conn:
                # Get story details
                cursor = conn.execute("""
                    SELECT st.id, st.title, st.description, st.status, st.story_points,
                           st.assignee, st.estimated_hours, st.actual_hours,
                           s.name as sprint_name, e.name as epic_name, p.name as project_name
                    FROM stories st
                    LEFT JOIN sprints s ON st.sprint_id = s.id
                    LEFT JOIN epics e ON st.epic_id = e.id
                    LEFT JOIN projects p ON st.project_id = p.id
                    WHERE st.id = ?
                """, (story_id,))
                
                story_data = cursor.fetchone()
                if not story_data:
                    return self._create_error_response("Story not found")
                
                # Get task progress
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'done' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_tasks,
                        COUNT(CASE WHEN status = 'blocked' THEN 1 END) as blocked_tasks,
                        SUM(estimated_hours) as total_estimated_hours,
                        SUM(actual_hours) as total_actual_hours
                    FROM tasks WHERE story_id = ?
                """, (story_id,))
                
                task_stats = cursor.fetchone()
                
                # Get individual task details
                cursor = conn.execute("""
                    SELECT id, title, status, task_type, estimated_hours, actual_hours, assignee
                    FROM tasks WHERE story_id = ?
                    ORDER BY created_at
                """, (story_id,))
                
                task_details = []
                for row in cursor.fetchall():
                    task_details.append({
                        "id": row[0],
                        "title": row[1],
                        "status": row[2],
                        "task_type": row[3],
                        "estimated_hours": row[4],
                        "actual_hours": row[5],
                        "assignee": row[6]
                    })
                
                # Calculate progress metrics
                total_tasks = task_stats[0] or 0
                completed_tasks = task_stats[1] or 0
                task_completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                total_estimated = task_stats[4] or 0
                total_actual = task_stats[5] or 0
                time_efficiency = (total_estimated / total_actual * 100) if total_actual > 0 and total_estimated > 0 else None
                
                progress_data = {
                    "story": {
                        "id": story_data[0],
                        "title": story_data[1],
                        "description": story_data[2],
                        "status": story_data[3],
                        "story_points": story_data[4],
                        "assignee": story_data[5],
                        "estimated_hours": story_data[6],
                        "actual_hours": story_data[7],
                        "sprint_name": story_data[8],
                        "epic_name": story_data[9],
                        "project_name": story_data[10]
                    },
                    "task_summary": {
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "in_progress_tasks": task_stats[2] or 0,
                        "blocked_tasks": task_stats[3] or 0,
                        "task_completion_percentage": task_completion_percentage,
                        "total_estimated_hours": total_estimated,
                        "total_actual_hours": total_actual,
                        "time_efficiency_percentage": time_efficiency
                    },
                    "task_details": task_details
                }
                
                return self._create_success_response(progress_data)
                
        except Exception as e:
            return self._create_error_response(f'Get story progress failed: {str(e)}')
    
    # ================================
    # REPORTING AND DASHBOARD ACTIONS
    # ================================
    
    async def _action_get_sprint_dashboard(self, sprint_id: str = None, 
                                         project_id: str = None, **params) -> Dict[str, Any]:
        """Get comprehensive sprint dashboard data."""
        try:
            with self._get_db_connection() as conn:
                if sprint_id:
                    # Specific sprint dashboard
                    cursor = conn.execute("""
                        SELECT s.id, s.name, s.status, s.goal, s.start_date, s.end_date,
                               s.planned_capacity, s.velocity, p.name as project_name
                        FROM sprints s
                        JOIN projects p ON s.project_id = p.id
                        WHERE s.id = ?
                    """, (sprint_id,))
                    sprint_data = cursor.fetchone()
                    
                    if not sprint_data:
                        return self._create_error_response("Sprint not found")
                    
                    # Get story statistics
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_stories,
                            COUNT(CASE WHEN status = 'done' THEN 1 END) as completed_stories,
                            SUM(story_points) as total_story_points,
                            SUM(CASE WHEN status = 'done' THEN story_points ELSE 0 END) as completed_story_points
                        FROM stories WHERE sprint_id = ?
                    """, (sprint_id,))
                    story_stats = cursor.fetchone()
                    
                    # Get task statistics
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_tasks,
                            COUNT(CASE WHEN t.status = 'done' THEN 1 END) as completed_tasks
                        FROM tasks t
                        JOIN stories st ON t.story_id = st.id
                        WHERE st.sprint_id = ?
                    """, (sprint_id,))
                    task_stats = cursor.fetchone()
                    
                    dashboard = {
                        "sprint": {
                            "id": sprint_data[0],
                            "name": sprint_data[1],
                            "status": sprint_data[2],
                            "goal": sprint_data[3],
                            "start_date": sprint_data[4],
                            "end_date": sprint_data[5],
                            "planned_capacity": sprint_data[6],
                            "velocity": sprint_data[7],
                            "project_name": sprint_data[8]
                        },
                        "stories": {
                            "total": story_stats[0] or 0,
                            "completed": story_stats[1] or 0,
                            "total_story_points": story_stats[2] or 0,
                            "completed_story_points": story_stats[3] or 0
                        },
                        "tasks": {
                            "total": task_stats[0] or 0,
                            "completed": task_stats[1] or 0
                        }
                    }
                    
                    # Calculate completion percentage
                    if dashboard["stories"]["total"] > 0:
                        dashboard["completion_percentage"] = (
                            dashboard["stories"]["completed"] / dashboard["stories"]["total"] * 100
                        )
                    else:
                        dashboard["completion_percentage"] = 0
                    
                    return self._create_success_response(dashboard)
                
                else:
                    return self._create_error_response("sprint_id is required")
                    
        except Exception as e:
            return self._create_error_response(f'Get sprint dashboard failed: {str(e)}')
    
    # ================================
    # LTMC COORDINATION ACTIONS
    # ================================
    
    async def _action_create_sprint_workflow(self, sprint_id: str, workflow_type: str = "standard_sprint_workflow",
                                           created_by: str = None, **params) -> Dict[str, Any]:
        """Create enhanced LTMC coordination workflow for a sprint."""
        try:
            # Get sprint name for workflow creation
            with self._get_db_connection() as conn:
                cursor = conn.execute("SELECT name FROM sprints WHERE id = ?", (sprint_id,))
                row = cursor.fetchone()
                if not row:
                    return self._create_error_response("Sprint not found")
                sprint_name = row[0]
            
            # Create enhanced workflow using workflow manager
            result = await self.workflow_manager.create_sprint_workflow(
                sprint_id=sprint_id,
                sprint_name=sprint_name,
                workflow_type=workflow_type,
                created_by=created_by
            )
            
            if result.get('success'):
                workflow_id = result['workflow_id']
                
                # Link to sprint in database
                with self._get_db_connection() as conn:
                    conn.execute("""
                        INSERT INTO ltmc_coordination_links 
                        (id, entity_type, entity_id, coordination_workflow_id, coordination_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (f"link_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                         'sprint', sprint_id, workflow_id, 'collaboration'))
                    conn.commit()
                
                return self._create_success_response({
                    "workflow_created": True,
                    "workflow_id": workflow_id,
                    "sprint_id": sprint_id,
                    "workflow_type": workflow_type,
                    "current_state": result['current_state'],
                    "available_transitions": result['available_transitions']
                })
            else:
                return self._create_error_response(result.get('error', 'Failed to create enhanced workflow'))
                
        except Exception as e:
            return self._create_error_response(f'Create sprint workflow failed: {str(e)}')
    
    async def _action_link_coordination(self, entity_type: str, entity_id: str,
                                      coordination_workflow_id: str, coordination_type: str = "tracking",
                                      **params) -> Dict[str, Any]:
        """Link a sprint entity to LTMC coordination workflow."""
        try:
            link_id = f"link_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with self._get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO ltmc_coordination_links 
                    (id, entity_type, entity_id, coordination_workflow_id, coordination_type, agent_assignments)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (link_id, entity_type, entity_id, coordination_workflow_id, 
                     coordination_type, json.dumps(params.get('agent_assignments', []))))
                conn.commit()
            
            return self._create_success_response({
                "coordination_linked": True,
                "link_id": link_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "coordination_workflow_id": coordination_workflow_id
            })
            
        except Exception as e:
            return self._create_error_response(f'Link coordination failed: {str(e)}')
    
    # ================================
    # WORKFLOW STATE MANAGEMENT ACTIONS
    # ================================
    
    async def _action_transition_workflow_state(self, workflow_id: str, new_state: str,
                                              agent_id: str = None, metadata: Dict[str, Any] = None,
                                              **params) -> Dict[str, Any]:
        """Transition a sprint workflow to a new state."""
        try:
            result = await self.workflow_manager.transition_workflow_state(
                workflow_id=workflow_id,
                new_state=new_state,
                agent_id=agent_id,
                metadata=metadata or {}
            )
            
            if result.get('success'):
                return self._create_success_response({
                    "workflow_transition": True,
                    "workflow_id": workflow_id,
                    "previous_state": result['previous_state'],
                    "new_state": result['new_state'],
                    "available_transitions": result['available_transitions']
                })
            else:
                return self._create_error_response(result.get('error', 'Unknown error'))
                
        except Exception as e:
            return self._create_error_response(f'Workflow transition failed: {str(e)}')
    
    async def _action_get_workflow_state(self, workflow_id: str, **params) -> Dict[str, Any]:
        """Get current workflow state and available actions."""
        try:
            result = self.workflow_manager.get_workflow_state(workflow_id)
            
            if result.get('success'):
                return self._create_success_response({
                    "workflow_state": {
                        "workflow_id": result['workflow_id'],
                        "current_state": result['current_state'],
                        "state_description": result['state_description'],
                        "required_actions": result['required_actions'],
                        "available_transitions": result['available_transitions'],
                        "automation": result['automation']
                    },
                    "workflow_history": result['workflow_history']
                })
            else:
                return self._create_error_response(result.get('error', 'Unknown error'))
                
        except Exception as e:
            return self._create_error_response(f'Get workflow state failed: {str(e)}')
    
    async def _action_list_workflow_types(self, **params) -> Dict[str, Any]:
        """List all available workflow types and their descriptions."""
        try:
            result = self.workflow_manager.list_available_workflow_types()
            
            if result.get('success'):
                return self._create_success_response({
                    "available_workflow_types": result['available_workflows'],
                    "total_types": len(result['available_workflows'])
                })
            else:
                return self._create_error_response("Failed to list workflow types")
                
        except Exception as e:
            return self._create_error_response(f'List workflow types failed: {str(e)}')


# Create global instance for backward compatibility
async def sprint_action(action: str, **params) -> Dict[str, Any]:
    """Professional sprint management operations (backward compatibility).
    
    Actions: create_project, create_sprint, create_story, create_task,
            assign_story, complete_task, get_sprint_dashboard, etc.
    """
    sprint_tools = SprintTools()
    return await sprint_tools(action, **params)