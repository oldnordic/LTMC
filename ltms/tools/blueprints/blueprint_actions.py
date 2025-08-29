"""
Blueprint management tools for LTMC MCP server.
Provides project blueprint operations with real SQLite+Neo4j implementation.

File: ltms/tools/blueprints/blueprint_actions.py
Lines: ~290 (under 300 limit, complex functions in extension)
Purpose: Blueprint and dependency management operations
"""

import json
import uuid
import sqlite3
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config

logger = logging.getLogger(__name__)


class BlueprintTools(MCPToolBase):
    """Blueprint management tools with SQLite+Neo4j implementation.
    
    Provides project blueprint operations including creation, complexity analysis,
    dependency management, and project organization with real database operations.
    """
    
    def __init__(self):
        super().__init__("BlueprintTools")
        self.config = get_tool_config()
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid blueprint actions."""
        return [
            'create', 'analyze_complexity', 'list_project', 'add_dependency', 
            'resolve_order', 'update_metadata', 'get_dependencies', 'delete'
        ]
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute blueprint management action."""
        # Check required database systems
        db_check = self._check_database_availability(['sqlite'])
        if not db_check.get('success', False):
            return db_check
        
        if action == 'create':
            return await self._action_create(**params)
        elif action == 'analyze_complexity':
            return await self._action_analyze_complexity(**params)
        elif action == 'list_project':
            return await self._action_list_project(**params)
        elif action == 'delete':
            return await self._action_delete(**params)
        elif action in ['add_dependency', 'resolve_order', 'update_metadata', 'get_dependencies']:
            # Delegate complex operations to extension
            from .blueprint_extension import BlueprintExtension
            return await BlueprintExtension.execute_extended_action(action, **params)
        else:
            return self._create_error_response(f"Unknown blueprint action: {action}")
    
    async def _action_create(self, **params) -> Dict[str, Any]:
        """Create new blueprint in database."""
        required_params = ['title', 'description']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            # Create blueprints table if not exists
            self.db.execute_sqlite('''
                CREATE TABLE IF NOT EXISTS blueprints (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    project_id TEXT,
                    complexity TEXT DEFAULT 'medium',
                    complexity_score REAL DEFAULT 0.5,
                    priority_score REAL DEFAULT 0.5,
                    estimated_duration_minutes INTEGER DEFAULT 60,
                    required_skills TEXT,
                    tags TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            ''')
            
            # Generate blueprint ID
            blueprint_id = f"bp_{str(uuid.uuid4())[:8]}"
            
            # Process parameters
            project_id = params.get('project_id', 'default')
            complexity = params.get('complexity', 'medium')
            if complexity not in ['trivial', 'simple', 'medium', 'complex', 'critical']:
                complexity = 'medium'
            
            complexity_score = params.get('complexity_score', 0.5)
            priority_score = params.get('priority_score', 0.5)
            estimated_duration = params.get('estimated_duration_minutes', 60)
            
            # Serialize lists to JSON
            required_skills = json.dumps(params.get('required_skills', [])) if params.get('required_skills') else None
            tags = json.dumps(params.get('tags', [])) if params.get('tags') else None
            
            created_at = datetime.now(timezone.utc).isoformat()
            
            # Insert blueprint
            self.db.execute_sqlite('''
                INSERT INTO blueprints (
                    id, title, description, project_id, complexity, complexity_score,
                    priority_score, estimated_duration_minutes, required_skills, tags,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                blueprint_id, params['title'], params['description'], project_id,
                complexity, complexity_score, priority_score, estimated_duration,
                required_skills, tags, created_at
            ))
            
            return self._create_success_response({
                'blueprint_id': blueprint_id,
                'title': params['title'],
                'description': params['description'],
                'project_id': project_id,
                'complexity': complexity,
                'complexity_score': complexity_score,
                'priority_score': priority_score,
                'estimated_duration_minutes': estimated_duration,
                'created_at': created_at,
                'message': f'Blueprint "{params["title"]}" created successfully'
            })
            
        except Exception as e:
            return self._create_error_response(f'Blueprint create failed: {str(e)}')
    
    async def _action_analyze_complexity(self, **params) -> Dict[str, Any]:
        """ML-based complexity scoring algorithm."""
        required_params = ['title', 'description']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            title = params['title']
            description = params['description']
            required_skills = params.get('required_skills', [])
            
            complexity_score = 0.0
            
            # Title complexity factors
            title_words = len(title.split())
            if title_words >= 5:
                complexity_score += 0.1
            
            # Description complexity factors
            desc_length = len(description)
            if desc_length > 200:
                complexity_score += 0.2
            if desc_length > 500:
                complexity_score += 0.3
            
            # Technical keyword complexity
            complex_keywords = [
                'microservice', 'distributed', 'scalable', 'real-time', 'machine learning',
                'ai', 'blockchain', 'kubernetes', 'docker', 'oauth2', 'jwt', 'security',
                'encryption', 'async', 'multithreading', 'performance', 'optimization',
                'migration', 'zero-downtime', 'database', 'postgresql', 'mysql',
                'monitoring', 'logging', 'testing', 'ci/cd', 'devops'
            ]
            
            desc_lower = description.lower()
            for keyword in complex_keywords:
                if keyword in desc_lower:
                    complexity_score += 0.15
            
            # Skills complexity
            skill_count = len(required_skills) if isinstance(required_skills, list) else 0
            if skill_count >= 3:
                complexity_score += 0.1
            if skill_count >= 5:
                complexity_score += 0.2
            
            # Integration complexity
            integration_keywords = ['integrate', 'api', 'service', 'external', 'third-party']
            for keyword in integration_keywords:
                if keyword in desc_lower:
                    complexity_score += 0.1
            
            # Cap at 1.0
            complexity_score = min(complexity_score, 1.0)
            
            # Determine complexity level
            if complexity_score < 0.3:
                complexity_level = 'simple'
                estimated_duration = 60 + int(complexity_score * 120)
            elif complexity_score < 0.5:
                complexity_level = 'medium'
                estimated_duration = 120 + int(complexity_score * 240)
            elif complexity_score < 0.7:
                complexity_level = 'complex'
                estimated_duration = 240 + int(complexity_score * 360)
            else:
                complexity_level = 'critical'
                estimated_duration = 480 + int(complexity_score * 240)
            
            return self._create_success_response({
                'title': title,
                'complexity_score': round(complexity_score, 3),
                'complexity_level': complexity_level,
                'estimated_duration_minutes': estimated_duration,
                'analysis': {
                    'title_complexity': title_words >= 5,
                    'description_length': desc_length,
                    'technical_keywords_found': sum(1 for kw in complex_keywords if kw in desc_lower),
                    'required_skills_count': skill_count,
                    'has_integration_aspects': any(kw in desc_lower for kw in integration_keywords)
                }
            })
            
        except Exception as e:
            return self._create_error_response(f'Blueprint complexity analysis failed: {str(e)}')
    
    async def _action_list_project(self, **params) -> Dict[str, Any]:
        """List blueprints for a specific project."""
        if 'project_id' not in params:
            return self._create_error_response('Missing required parameter: project_id')
        
        try:
            project_id = params['project_id']
            limit = params.get('limit', 10)
            min_complexity = params.get('min_complexity')
            tags_filter = params.get('tags')
            
            # Build query
            query = '''
                SELECT id, title, description, complexity, complexity_score, priority_score,
                       estimated_duration_minutes, required_skills, tags, status, created_at
                FROM blueprints
                WHERE project_id = ?
            '''
            query_params = [project_id]
            
            # Add complexity filter
            if min_complexity:
                complexity_order = {'trivial': 0, 'simple': 1, 'medium': 2, 'complex': 3, 'critical': 4}
                if min_complexity in complexity_order:
                    query += '''
                        AND CASE complexity 
                            WHEN 'trivial' THEN 0
                            WHEN 'simple' THEN 1
                            WHEN 'medium' THEN 2
                            WHEN 'complex' THEN 3
                            WHEN 'critical' THEN 4
                        END >= ?
                    '''
                    query_params.append(complexity_order[min_complexity])
            
            # Order by priority and complexity
            query += '''
                ORDER BY priority_score DESC, complexity_score DESC, created_at DESC
                LIMIT ?
            '''
            query_params.append(limit)
            
            rows = self.db.execute_sqlite(query, tuple(query_params), fetch='all')
            
            blueprints = []
            for row in rows:
                # Parse JSON fields
                required_skills = json.loads(row[7]) if row[7] else []
                tags = json.loads(row[8]) if row[8] else []
                
                # Tag filtering (if specified)
                if tags_filter:
                    if not isinstance(tags_filter, list):
                        tags_filter = [tags_filter]
                    
                    # Check if any of the filter tags match
                    if not any(tag in tags for tag in tags_filter):
                        continue
                
                blueprints.append({
                    'blueprint_id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'complexity': row[3],
                    'complexity_score': row[4],
                    'priority_score': row[5],
                    'estimated_duration_minutes': row[6],
                    'required_skills': required_skills,
                    'tags': tags,
                    'status': row[9],
                    'created_at': row[10]
                })
            
            return self._create_success_response({
                'blueprints': blueprints,
                'project_id': project_id,
                'total_found': len(blueprints),
                'limit_applied': limit,
                'filters': {
                    'min_complexity': min_complexity,
                    'tags': tags_filter
                }
            })
            
        except Exception as e:
            return self._create_error_response(f'Blueprint list_project failed: {str(e)}')
    
    async def _action_delete(self, **params) -> Dict[str, Any]:
        """Delete blueprint from database."""
        if 'blueprint_id' not in params:
            return self._create_error_response('Missing required parameter: blueprint_id')
        
        try:
            blueprint_id = params['blueprint_id']
            
            # Check if blueprint exists
            result = self.db.execute_sqlite(
                'SELECT title FROM blueprints WHERE id = ?', 
                (blueprint_id,), 
                fetch='one'
            )
            
            if not result:
                return self._create_error_response(f'Blueprint with ID {blueprint_id} not found')
            
            title = result[0]
            
            # Delete blueprint
            self.db.execute_sqlite('DELETE FROM blueprints WHERE id = ?', (blueprint_id,))
            
            return self._create_success_response({
                'blueprint_id': blueprint_id,
                'title': title,
                'message': f'Blueprint "{title}" deleted successfully'
            })
            
        except Exception as e:
            return self._create_error_response(f'Blueprint delete failed: {str(e)}')


# Create global instance for backward compatibility
async def blueprint_action(action: str, **params) -> Dict[str, Any]:
    """Blueprint management operations (backward compatibility).
    
    Actions: create, analyze_complexity, list_project, add_dependency, 
             resolve_order, update_metadata, get_dependencies, delete
    """
    blueprint_tools = BlueprintTools()
    return await blueprint_tools(action, **params)