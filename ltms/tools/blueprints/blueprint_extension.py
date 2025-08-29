"""
Blueprint extension for complex dependency operations.
Contains advanced blueprint management functions that exceed the 300-line limit.

File: ltms/tools/blueprints/blueprint_extension.py
Lines: ~290 (under 300 limit)
Purpose: Blueprint dependency resolution and metadata management
"""

import json
import sqlite3
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class BlueprintExtension:
    """Extension class for complex blueprint operations."""
    
    @staticmethod
    async def execute_extended_action(action: str, **params) -> Dict[str, Any]:
        """Execute extended blueprint action."""
        try:
            if action == 'add_dependency':
                return await BlueprintExtension._action_add_dependency(**params)
            elif action == 'resolve_order':
                return await BlueprintExtension._action_resolve_order(**params)
            elif action == 'update_metadata':
                return await BlueprintExtension._action_update_metadata(**params)
            elif action == 'get_dependencies':
                return await BlueprintExtension._action_get_dependencies(**params)
            else:
                return {'success': False, 'error': f'Unknown extended blueprint action: {action}'}
        except Exception as e:
            return {'success': False, 'error': f'Extended blueprint action failed: {str(e)}'}
    
    @staticmethod
    async def _action_add_dependency(**params) -> Dict[str, Any]:
        """Add blueprint dependency relationship."""
        required_params = ['dependent_blueprint_id', 'prerequisite_blueprint_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.config.json_config_loader import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create dependencies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blueprint_dependencies (
                    id INTEGER PRIMARY KEY,
                    dependent_blueprint_id TEXT NOT NULL,
                    prerequisite_blueprint_id TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'blocking',
                    is_critical INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(dependent_blueprint_id, prerequisite_blueprint_id)
                )
            ''')
            
            dependency_type = params.get('dependency_type', 'blocking')
            is_critical = 1 if params.get('is_critical', False) else 0
            created_at = datetime.now(timezone.utc).isoformat()
            
            # Insert dependency
            cursor.execute('''
                INSERT INTO blueprint_dependencies (
                    dependent_blueprint_id, prerequisite_blueprint_id, 
                    dependency_type, is_critical, created_at
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                params['dependent_blueprint_id'],
                params['prerequisite_blueprint_id'],
                dependency_type,
                is_critical,
                created_at
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'data': {
                    'dependent_blueprint_id': params['dependent_blueprint_id'],
                    'prerequisite_blueprint_id': params['prerequisite_blueprint_id'],
                    'dependency_type': dependency_type,
                    'is_critical': bool(is_critical),
                    'created_at': created_at,
                    'message': 'Blueprint dependency added successfully'
                }
            }
            
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Dependency already exists'}
        except Exception as e:
            return {'success': False, 'error': f'Blueprint add dependency failed: {str(e)}'}
    
    @staticmethod
    async def _action_resolve_order(**params) -> Dict[str, Any]:
        """Resolve blueprint execution order using topological sorting."""
        if 'blueprint_ids' not in params:
            return {'success': False, 'error': 'Missing required parameter: blueprint_ids'}
        
        try:
            from ltms.config.json_config_loader import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            blueprint_ids = params['blueprint_ids']
            if not isinstance(blueprint_ids, list):
                return {'success': False, 'error': 'blueprint_ids must be a list'}
            
            # Get blueprint details
            placeholders = ','.join(['?' for _ in blueprint_ids])
            cursor.execute(f'''
                SELECT id, title, description, complexity_score, priority_score
                FROM blueprints WHERE id IN ({placeholders})
            ''', blueprint_ids)
            blueprints = {row[0]: {'id': row[0], 'title': row[1], 'description': row[2], 
                                  'complexity_score': row[3], 'priority_score': row[4]} 
                         for row in cursor.fetchall()}
            
            # Get dependencies
            cursor.execute(f'''
                SELECT dependent_blueprint_id, prerequisite_blueprint_id, dependency_type, is_critical
                FROM blueprint_dependencies 
                WHERE dependent_blueprint_id IN ({placeholders}) 
                   OR prerequisite_blueprint_id IN ({placeholders})
            ''', blueprint_ids + blueprint_ids)
            
            dependencies = []
            for row in cursor.fetchall():
                dependencies.append({
                    'dependent': row[0],
                    'prerequisite': row[1],
                    'type': row[2],
                    'is_critical': bool(row[3])
                })
            
            conn.close()
            
            # Topological sort algorithm
            def topological_sort(nodes, edges):
                # Build adjacency list and in-degree count
                in_degree = {node: 0 for node in nodes}
                adj_list = {node: [] for node in nodes}
                
                for edge in edges:
                    prerequisite, dependent = edge['prerequisite'], edge['dependent']
                    if prerequisite in nodes and dependent in nodes:
                        adj_list[prerequisite].append(dependent)
                        in_degree[dependent] += 1
                
                # Queue for nodes with no incoming edges
                queue = [node for node in nodes if in_degree[node] == 0]
                result = []
                
                while queue:
                    # Sort by priority and complexity for consistent ordering
                    queue.sort(key=lambda x: (-blueprints.get(x, {}).get('priority_score', 0), 
                                            -blueprints.get(x, {}).get('complexity_score', 0)))
                    current = queue.pop(0)
                    result.append(current)
                    
                    # Update neighbors
                    for neighbor in adj_list[current]:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)
                
                # Check for cycles
                if len(result) != len(nodes):
                    remaining = [node for node in nodes if node not in result]
                    return None, remaining
                
                return result, []
            
            ordered_ids, cyclic_deps = topological_sort(blueprint_ids, dependencies)
            
            if ordered_ids is None:
                return {
                    'success': False,
                    'error': 'Circular dependencies detected',
                    'cyclic_dependencies': cyclic_deps
                }
            
            # Build detailed execution order
            execution_order = []
            for blueprint_id in ordered_ids:
                if blueprint_id in blueprints:
                    bp = blueprints[blueprint_id]
                    execution_order.append({
                        'blueprint_id': blueprint_id,
                        'title': bp['title'],
                        'complexity_score': bp['complexity_score'],
                        'priority_score': bp['priority_score'],
                        'prerequisites': [dep['prerequisite'] for dep in dependencies if dep['dependent'] == blueprint_id]
                    })
            
            return {
                'success': True,
                'data': {
                    'execution_order': execution_order,
                    'total_blueprints': len(execution_order),
                    'dependencies_analyzed': len(dependencies),
                    'has_dependencies': len(dependencies) > 0
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint resolve order failed: {str(e)}'}
    
    @staticmethod
    async def _action_update_metadata(**params) -> Dict[str, Any]:
        """Update blueprint metadata."""
        if 'blueprint_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: blueprint_id'}
        
        try:
            from ltms.config.json_config_loader import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            blueprint_id = params['blueprint_id']
            
            # Check if blueprint exists
            cursor.execute('SELECT title FROM blueprints WHERE id = ?', (blueprint_id,))
            if not cursor.fetchone():
                conn.close()
                return {'success': False, 'error': f'Blueprint with ID {blueprint_id} not found'}
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            updatable_fields = {
                'title': str,
                'description': str,
                'complexity': str,
                'complexity_score': float,
                'priority_score': float,
                'estimated_duration_minutes': int,
                'status': str
            }
            
            for field, field_type in updatable_fields.items():
                if field in params:
                    update_fields.append(f"{field} = ?")
                    try:
                        update_values.append(field_type(params[field]))
                    except (ValueError, TypeError):
                        conn.close()
                        return {'success': False, 'error': f'Invalid type for field {field}'}
            
            # Handle JSON fields
            if 'required_skills' in params:
                update_fields.append("required_skills = ?")
                update_values.append(json.dumps(params['required_skills']))
            
            if 'tags' in params:
                update_fields.append("tags = ?")
                update_values.append(json.dumps(params['tags']))
            
            if not update_fields:
                conn.close()
                return {'success': False, 'error': 'No valid fields provided for update'}
            
            # Add updated_at timestamp
            update_fields.append("updated_at = ?")
            update_values.append(datetime.now(timezone.utc).isoformat())
            
            # Execute update
            query = f"UPDATE blueprints SET {', '.join(update_fields)} WHERE id = ?"
            update_values.append(blueprint_id)
            
            cursor.execute(query, update_values)
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'data': {
                    'blueprint_id': blueprint_id,
                    'updated_fields': list(params.keys()),
                    'message': 'Blueprint metadata updated successfully'
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint update metadata failed: {str(e)}'}
    
    @staticmethod
    async def _action_get_dependencies(**params) -> Dict[str, Any]:
        """Get blueprint dependencies."""
        if 'blueprint_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: blueprint_id'}
        
        try:
            from ltms.config.json_config_loader import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            blueprint_id = params['blueprint_id']
            
            # Get prerequisites (what this blueprint depends on)
            cursor.execute('''
                SELECT bd.prerequisite_blueprint_id, bd.dependency_type, bd.is_critical,
                       b.title, b.complexity, b.status
                FROM blueprint_dependencies bd
                JOIN blueprints b ON bd.prerequisite_blueprint_id = b.id
                WHERE bd.dependent_blueprint_id = ?
            ''', (blueprint_id,))
            
            prerequisites = []
            for row in cursor.fetchall():
                prerequisites.append({
                    'blueprint_id': row[0],
                    'dependency_type': row[1],
                    'is_critical': bool(row[2]),
                    'title': row[3],
                    'complexity': row[4],
                    'status': row[5]
                })
            
            # Get dependents (what depends on this blueprint)
            cursor.execute('''
                SELECT bd.dependent_blueprint_id, bd.dependency_type, bd.is_critical,
                       b.title, b.complexity, b.status
                FROM blueprint_dependencies bd
                JOIN blueprints b ON bd.dependent_blueprint_id = b.id
                WHERE bd.prerequisite_blueprint_id = ?
            ''', (blueprint_id,))
            
            dependents = []
            for row in cursor.fetchall():
                dependents.append({
                    'blueprint_id': row[0],
                    'dependency_type': row[1],
                    'is_critical': bool(row[2]),
                    'title': row[3],
                    'complexity': row[4],
                    'status': row[5]
                })
            
            conn.close()
            
            return {
                'success': True,
                'data': {
                    'blueprint_id': blueprint_id,
                    'prerequisites': prerequisites,
                    'dependents': dependents,
                    'prerequisite_count': len(prerequisites),
                    'dependent_count': len(dependents),
                    'has_critical_dependencies': any(dep['is_critical'] for dep in prerequisites + dependents)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint get dependencies failed: {str(e)}'}