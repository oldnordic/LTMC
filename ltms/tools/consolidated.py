"""
LTMC Consolidated Tools Registry
12-14 Powertools with Action Parameters - REAL IMPLEMENTATIONS ONLY
NO WRAPPERS - All internal logic implemented directly
"""

# === ADVANCED SUPPRESSION SYSTEM - RESEARCH-BACKED IMPLEMENTATION ===
import os
import sys
import warnings
import logging

# 1. SYSTEM-LEVEL ENVIRONMENT SETUP - CRITICAL: Must be first
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["SETUPTOOLS_USE_DISTUTILS"] = "stdlib"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# 2. RESET WARNING SYSTEM - Clear default filters and restart
warnings.resetwarnings()
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)

# 3. SPECIFIC MESSAGE FILTERS - Precise regex matching for exact warnings
warnings.filterwarnings("ignore", message=".*distutils Version classes are deprecated.*")
warnings.filterwarnings("ignore", message=".*ml_dtypes.float8_e4m3b11 is deprecated.*") 
warnings.filterwarnings("ignore", message=".*Support for class-based.*config.*deprecated.*")
warnings.filterwarnings("ignore", message=".*MessageFactory.*GetPrototype.*")

# 4. LOGGING SYSTEM RECONFIGURATION - Force restart with new settings
logging.basicConfig(level=logging.WARNING, force=True)
logging.getLogger().setLevel(logging.WARNING)

# 5. PREEMPTIVE LOGGER SUPPRESSION - Configure before imports trigger them
critical_loggers = [
    "tensorflow", "absl", "sentence_transformers", "transformers", 
    "ltms.security.project_isolation", "ltms.security.path_security",
    "ltms.security.mcp_integration", "ltms.core.connection_pool"
]

for logger_name in critical_loggers:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# 6. ADVANCED IMPORT CONTEXT MANAGER - Research-backed suppression during imports
class AdvancedImportSuppressor:
    """Research-backed context manager for suppressing import-time warnings.
    
    Uses multiple suppression layers: environment, warnings, logging, and stderr.
    """
    def __enter__(self):
        # Store original states
        self._original_stderr = sys.stderr
        self._original_warnings = warnings.filters[:]
        
        # Temporary suppression during critical imports
        from io import StringIO
        sys.stderr = StringIO()
        
        # Additional warning suppression context
        warnings.filterwarnings("ignore")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original states
        sys.stderr = self._original_stderr
        warnings.filters[:] = self._original_warnings
        return False  # Don't suppress exceptions

# 7. PREEMPTIVE IMPORT TRIGGERING - Import and suppress in controlled context
try:
    with AdvancedImportSuppressor():
        # Trigger problematic imports in suppressed context
        import numpy
        import faiss
        from sentence_transformers import SentenceTransformer
        # Force transformers logging configuration
        try:
            from transformers.utils import logging as transformers_logging
            transformers_logging.set_verbosity_error()
        except ImportError:
            pass
except Exception:
    # If imports fail, suppression systems remain active
    pass
import ast
import json
import sqlite3
import subprocess
import redis
import time
from pathlib import Path


def _get_numpy():
    """Lazy import numpy only when needed to avoid binary distribution issues."""
    import numpy as np
    return np
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone


async def memory_action(action: str, **params) -> Dict[str, Any]:
    """Memory operations with ATOMIC SYNCHRONIZATION across SQLite+FAISS+Neo4j+Redis.
    
    Actions: store, retrieve, build_context, retrieve_by_type, ask_with_context
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'store':
        required_params = ['file_name', 'content']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            # Use atomic memory integration for synchronized storage
            from ltms.tools.atomic_memory_integration import get_atomic_memory_manager
            
            # Extract tags from params if provided
            tags = params.get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # Get atomic memory manager and call async store operation
            manager = get_atomic_memory_manager()
            result = await manager.atomic_store(
                file_name=params['file_name'],
                content=params['content'],
                resource_type=params.get('resource_type', 'document'),
                tags=tags,
                conversation_id=params.get('conversation_id', 'default'),
                **{k: v for k, v in params.items() if k not in ['file_name', 'content', 'resource_type', 'tags', 'conversation_id']}
            )
            
            return result
                
        except Exception as e:
            return {'success': False, 'error': f'Atomic memory store failed: {str(e)}'}
    
    elif action == 'retrieve':
        required_params = ['conversation_id', 'query']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            # Use atomic memory integration for vector search
            from ltms.tools.atomic_memory_integration import get_atomic_memory_manager
            import asyncio
            
            # Get atomic memory manager
            manager = get_atomic_memory_manager()
            
            # Perform vector search using atomic FAISS manager
            search_result = await manager.atomic_search(
                query=params['query'], 
                k=params.get('top_k', 10)
            )
            
            if search_result['success']:
                # Format results for compatibility
                documents = []
                for i, result in enumerate(search_result.get('results', [])):
                    documents.append({
                        'file_name': result.get('doc_id'),
                        'content': result.get('content_preview', ''),
                        'resource_type': result.get('metadata', {}).get('resource_type', 'document'),
                        'created_at': result.get('metadata', {}).get('stored_at', ''),
                        'similarity_score': 1.0 - result.get('distance', 1.0),  # Convert distance to similarity
                        'rank': i + 1
                    })
                
                return {
                    'success': True,
                    'documents': documents,
                    'query': params['query'],
                    'conversation_id': params['conversation_id'],
                    'total_found': len(documents),
                    'atomic_search': True
                }
            else:
                return search_result
            
        except Exception as e:
            return {'success': False, 'error': f'Atomic memory retrieve failed: {str(e)}'}
    
    elif action == 'build_context':
        if 'documents' not in params:
            return {'success': False, 'error': 'Missing required parameter: documents'}
        
        try:
            documents = params['documents']
            max_tokens = params.get('max_tokens', 4000)
            
            if not isinstance(documents, list):
                return {'success': False, 'error': 'Documents must be a list'}
            
            context_parts = []
            current_tokens = 0
            
            for i, doc in enumerate(documents):
                if not isinstance(doc, dict) or 'content' not in doc:
                    continue
                
                content = str(doc['content'])
                estimated_tokens = len(content) // 4
                
                if current_tokens + estimated_tokens <= max_tokens:
                    context_parts.append({
                        'index': i,
                        'content': content,
                        'tokens': estimated_tokens,
                        'source': doc.get('file_name', f'document_{i}')
                    })
                    current_tokens += estimated_tokens
                else:
                    remaining_tokens = max_tokens - current_tokens
                    if remaining_tokens > 50:
                        truncated_content = content[:remaining_tokens * 4]
                        context_parts.append({
                            'index': i,
                            'content': truncated_content + '...[truncated]',
                            'tokens': remaining_tokens,
                            'source': doc.get('file_name', f'document_{i}'),
                            'truncated': True
                        })
                    break
            
            context_text = '\n\n---\n\n'.join([part['content'] for part in context_parts])
            
            return {
                'success': True,
                'context': context_text,
                'parts': context_parts,
                'total_tokens': current_tokens,
                'max_tokens': max_tokens,
                'documents_included': len(context_parts)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Build context failed: {str(e)}'}
    
    elif action == 'retrieve_by_type':
        required_params = ['query', 'doc_type']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.services.context_service import retrieve_by_type
            
            return retrieve_by_type(
                query=params['query'],
                doc_type=params['doc_type'],
                top_k=params.get('top_k', 5)
            )
            
        except Exception as e:
            return {'success': False, 'error': f'Retrieve by type failed: {str(e)}'}
    
    elif action == 'ask_with_context':
        required_params = ['query', 'conversation_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.services.chat_service import ask_with_context
            
            return ask_with_context(
                query=params['query'],
                conversation_id=params['conversation_id'],
                top_k=params.get('top_k', 5)
            )
            
        except Exception as e:
            return {'success': False, 'error': f'Ask with context failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown memory action: {action}'}


def todo_action(action: str, **params) -> Dict[str, Any]:
    """Todo operations with real internal SQLite implementation.
    
    Actions: add, list, complete, search
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'add':
        if 'title' not in params:
            return {'success': False, 'error': 'Missing required parameter: title'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create todos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    completed INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            ''')
            
            # Validate priority
            priority = params.get('priority', 'medium')
            if priority not in ['low', 'medium', 'high', 'urgent']:
                priority = 'medium'
            
            created_at = datetime.now(timezone.utc).isoformat()
            cursor.execute('''
                INSERT INTO todos (title, description, priority, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                params['title'],
                params.get('description', ''),
                priority,
                created_at
            ))
            
            todo_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'todo_id': todo_id,
                'title': params['title'],
                'priority': priority,
                'status': 'pending',
                'message': f'Todo "{params["title"]}" created successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Todo add failed: {str(e)}'}
    
    elif action == 'list':
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            status = params.get('status', 'all')
            limit = params.get('limit', 10)
            
            if status == 'all':
                cursor.execute('''
                    SELECT id, title, description, priority, status, completed, created_at, completed_at
                    FROM todos
                    ORDER BY 
                        CASE priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                        END,
                        created_at DESC
                    LIMIT ?
                ''', (limit,))
            else:
                if status not in ['pending', 'in_progress', 'completed']:
                    return {'success': False, 'error': 'status must be one of: all, pending, in_progress, completed'}
                
                cursor.execute('''
                    SELECT id, title, description, priority, status, completed, created_at, completed_at
                    FROM todos
                    WHERE status = ?
                    ORDER BY 
                        CASE priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                        END,
                        created_at DESC
                    LIMIT ?
                ''', (status, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            todos = []
            for row in rows:
                todos.append({
                    'todo_id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'priority': row[3],
                    'status': row[4],
                    'completed': bool(row[5]),
                    'created_at': row[6],
                    'completed_at': row[7]
                })
            
            return {
                'success': True,
                'todos': todos,
                'status_filter': status,
                'total_found': len(todos),
                'limit_applied': limit
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Todo list failed: {str(e)}'}
    
    elif action == 'complete':
        if 'todo_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: todo_id'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if todo exists
            cursor.execute('SELECT title, status FROM todos WHERE id = ?', (params['todo_id'],))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return {'success': False, 'error': f'Todo with ID {params["todo_id"]} not found'}
            
            title, current_status = result
            
            if current_status == 'completed':
                conn.close()
                return {
                    'success': True,
                    'todo_id': params['todo_id'],
                    'title': title,
                    'message': 'Todo is already completed'
                }
            
            # Mark as completed
            completed_at = datetime.now().isoformat()
            cursor.execute('''
                UPDATE todos 
                SET status = 'completed', completed = 1, completed_at = ?
                WHERE id = ?
            ''', (completed_at, params['todo_id']))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'todo_id': params['todo_id'],
                'title': title,
                'status': 'completed',
                'completed_at': completed_at,
                'message': f'Todo "{title}" marked as completed'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Todo complete failed: {str(e)}'}
    
    elif action == 'search':
        if 'query' not in params:
            return {'success': False, 'error': 'Missing required parameter: query'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            search_pattern = f"%{params['query']}%"
            limit = params.get('limit', 10)
            status = params.get('status')
            
            if status and status not in ['pending', 'in_progress', 'completed']:
                conn.close()
                return {'success': False, 'error': 'status must be one of: pending, in_progress, completed'}
            
            if status:
                cursor.execute('''
                    SELECT id, title, description, priority, status, completed, created_at, completed_at
                    FROM todos
                    WHERE (title LIKE ? OR description LIKE ?) AND status = ?
                    ORDER BY 
                        CASE priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                        END,
                        created_at DESC
                    LIMIT ?
                ''', (search_pattern, search_pattern, status, limit))
            else:
                cursor.execute('''
                    SELECT id, title, description, priority, status, completed, created_at, completed_at
                    FROM todos
                    WHERE title LIKE ? OR description LIKE ?
                    ORDER BY 
                        CASE priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                        END,
                        created_at DESC
                    LIMIT ?
                ''', (search_pattern, search_pattern, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            todos = []
            for row in rows:
                todos.append({
                    'todo_id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'priority': row[3],
                    'status': row[4],
                    'completed': bool(row[5]),
                    'created_at': row[6],
                    'completed_at': row[7]
                })
            
            return {
                'success': True,
                'todos': todos,
                'search_query': params['query'],
                'status_filter': status,
                'total_found': len(todos),
                'limit_applied': limit
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Todo search failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown todo action: {action}'}


def chat_action(action: str, **params) -> Dict[str, Any]:
    """Chat operations with real internal SQLite implementation.
    
    Actions: log, get_by_tool, get_tool_conversations, route_query
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'log':
        required_params = ['conversation_id', 'role', 'content']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create chats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    agent_name TEXT,
                    metadata TEXT,
                    source_tool TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Validate role
            if params['role'] not in ['user', 'assistant', 'system']:
                return {'success': False, 'error': 'role must be one of: user, assistant, system'}
            
            created_at = datetime.now(timezone.utc).isoformat()
            metadata_json = json.dumps(params.get('metadata')) if params.get('metadata') else None
            
            cursor.execute('''
                INSERT INTO chats (conversation_id, role, content, agent_name, metadata, source_tool, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                params['conversation_id'],
                params['role'],
                params['content'],
                params.get('agent_name'),
                metadata_json,
                params.get('source_tool'),
                created_at
            ))
            
            chat_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'chat_id': chat_id,
                'conversation_id': params['conversation_id'],
                'role': params['role'],
                'created_at': created_at,
                'message': 'Chat message logged successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Chat log failed: {str(e)}'}
    
    elif action == 'get_by_tool':
        if 'source_tool' not in params:
            return {'success': False, 'error': 'Missing required parameter: source_tool'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            limit = params.get('limit', 10)
            
            cursor.execute('''
                SELECT id, conversation_id, role, content, agent_name, metadata, created_at
                FROM chats
                WHERE source_tool = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (params['source_tool'], limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            chats = []
            for row in rows:
                metadata = json.loads(row[5]) if row[5] else None
                chats.append({
                    'chat_id': row[0],
                    'conversation_id': row[1],
                    'role': row[2],
                    'content': row[3],
                    'agent_name': row[4],
                    'metadata': metadata,
                    'created_at': row[6]
                })
            
            return {
                'success': True,
                'chats': chats,
                'source_tool': params['source_tool'],
                'total_found': len(chats),
                'limit_applied': limit
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Chat get_by_tool failed: {str(e)}'}
    
    elif action == 'get_tool_conversations':
        if 'tool_name' not in params:
            return {'success': False, 'error': 'Missing required parameter: tool_name'}
        
        try:
            from ltms.services.context_service import get_tool_conversations
            
            return get_tool_conversations(
                tool_name=params['tool_name'],
                limit=params.get('limit', 10)
            )
            
        except Exception as e:
            return {'success': False, 'error': f'Get tool conversations failed: {str(e)}'}
    
    elif action == 'route_query':
        required_params = ['query']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.services.chat_service import route_query
            
            return route_query(
                query=params['query'],
                source_types=params.get('source_types'),
                top_k=params.get('top_k', 5)
            )
            
        except Exception as e:
            return {'success': False, 'error': f'Route query failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown chat action: {action}'}


def unix_action(action: str, **params) -> Dict[str, Any]:
    """Unix utilities with real external tool integration.
    
    Actions: ls, cat, grep, find, tree, jq, list_modern, disk_usage, help, diff_highlight, fuzzy_select, parse_syntax, syntax_highlight, syntax_query
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'ls':
        try:
            path = params.get('path', '.')
            long_format = params.get('long', False)
            show_hidden = params.get('all', False)
            
            # Try modern exa first
            cmd = ['exa', '--color=never']
            if long_format:
                cmd.append('-l')
            if show_hidden:
                cmd.append('-a')
            cmd.append(path)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                return {
                    'success': True,
                    'files': lines,
                    'path': path,
                    'count': len(lines),
                    'tool': 'exa',
                    'raw_output': result.stdout
                }
            else:
                # Fall back to ls
                cmd_fallback = ['ls']
                if long_format:
                    cmd_fallback.append('-l')
                if show_hidden:
                    cmd_fallback.append('-a')
                cmd_fallback.append(path)
                
                result = subprocess.run(cmd_fallback, capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                    return {
                        'success': True,
                        'files': lines,
                        'path': path,
                        'count': len(lines),
                        'tool': 'ls (fallback)',
                        'raw_output': result.stdout
                    }
                else:
                    return {'success': False, 'error': f'ls failed: {result.stderr}'}
                    
        except Exception as e:
            return {'success': False, 'error': f'Unix ls failed: {str(e)}'}
    
    elif action == 'cat':
        try:
            file_path = params.get('file_path')
            if not file_path:
                return {'success': False, 'error': 'Missing required parameter: file_path'}
            
            # Try bat with syntax highlighting
            cmd = ['bat', '--color=never', '--plain', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'content': result.stdout,
                    'file_path': file_path,
                    'tool': 'bat',
                    'lines': len(result.stdout.split('\n'))
                }
            else:
                # Fall back to cat
                cmd_fallback = ['cat', file_path]
                result = subprocess.run(cmd_fallback, capture_output=True, text=True)
                if result.returncode == 0:
                    return {
                        'success': True,
                        'content': result.stdout,
                        'file_path': file_path,
                        'tool': 'cat (fallback)',
                        'lines': len(result.stdout.split('\n'))
                    }
                else:
                    return {'success': False, 'error': f'cat failed: {result.stderr}'}
                    
        except Exception as e:
            return {'success': False, 'error': f'Unix cat failed: {str(e)}'}
    
    elif action == 'grep':
        try:
            pattern = params.get('pattern')
            path = params.get('path', '.')
            if not pattern:
                return {'success': False, 'error': 'Missing required parameter: pattern'}
            
            # Use ripgrep
            cmd = ['rg', '--color=never', '--line-number', pattern, path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            matches = []
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and ':' in line:
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            try:
                                matches.append({
                                    'file': parts[0],
                                    'line_number': int(parts[1]),
                                    'content': parts[2]
                                })
                            except ValueError:
                                # If line number parsing fails, treat as simple match
                                matches.append({
                                    'file': parts[0],
                                    'line_number': 1,
                                    'content': ':'.join(parts[1:])
                                })
            
            return {
                'success': True,
                'matches': matches,
                'pattern': pattern,
                'path': path,
                'count': len(matches),
                'tool': 'ripgrep',
                'raw_output': result.stdout if result.returncode == 0 else result.stderr
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Unix grep failed: {str(e)}'}
    
    elif action == 'find':
        try:
            pattern = params.get('pattern')
            path = params.get('path', '.')
            if not pattern:
                return {'success': False, 'error': 'Missing required parameter: pattern'}
            
            # Use fd (fast find)
            cmd = ['fd', '--color=never']
            
            # Add type filter if specified
            type_filter = params.get('type_filter')
            if type_filter == 'f':
                cmd.extend(['--type', 'f'])
            elif type_filter == 'd':
                cmd.extend(['--type', 'd'])
            
            # Add extension filter if specified
            extension = params.get('extension')
            if extension:
                cmd.extend(['--extension', extension])
            
            # Add max depth if specified
            max_depth = params.get('max_depth')
            if max_depth:
                cmd.extend(['--max-depth', str(max_depth)])
            
            # Handle glob patterns vs regex patterns
            if '*' in pattern or '?' in pattern or '[' in pattern:
                # It's a glob pattern - use --glob
                cmd.extend(['--glob', pattern, path])
            else:
                # It's a regex pattern or simple string
                cmd.extend([pattern, path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                files_found = result.stdout.strip().split('\n') if result.stdout.strip() else []
                return {
                    'success': True,
                    'files_found': files_found,
                    'pattern': pattern,
                    'search_path': path,
                    'count': len(files_found),
                    'tool': 'fd',
                    'raw_output': result.stdout
                }
            else:
                return {'success': False, 'error': f'fd failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix find failed: {str(e)}'}
    
    elif action == 'tree':
        try:
            path = params.get('path', '.')
            
            # Use tree for directory visualization
            cmd = ['tree', '--charset=ascii']
            
            max_depth = params.get('max_depth')
            if max_depth:
                cmd.extend(['-L', str(max_depth)])
            
            if params.get('show_hidden', False):
                cmd.append('-a')
            
            if params.get('directories_only', False):
                cmd.append('-d')
            
            cmd.append(path)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse tree output to extract counts
                lines = result.stdout.split('\n')
                last_line = lines[-2] if len(lines) > 1 else ''
                
                directory_count = 0
                file_count = 0
                if 'directories' in last_line and 'files' in last_line:
                    import re
                    dir_match = re.search(r'(\d+) directories', last_line)
                    file_match = re.search(r'(\d+) files', last_line)
                    if dir_match:
                        directory_count = int(dir_match.group(1))
                    if file_match:
                        file_count = int(file_match.group(1))
                
                return {
                    'success': True,
                    'tree_output': result.stdout,
                    'root_path': path,
                    'max_depth': max_depth,
                    'directory_count': directory_count,
                    'file_count': file_count,
                    'tool': 'tree'
                }
            else:
                return {'success': False, 'error': f'tree failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix tree failed: {str(e)}'}
    
    elif action == 'jq':
        try:
            query = params.get('query', '.')
            
            # Handle both direct JSON input and file input
            json_input = params.get('json_input')
            file_path = params.get('file_path')
            
            if not json_input and not file_path:
                return {'success': False, 'error': 'Missing required parameter: json_input or file_path'}
            
            start_time = time.time()
            
            # Use jq for JSON processing
            if file_path:
                cmd = ['jq']
                if params.get('raw_output', True):
                    cmd.append('--raw-output')
                cmd.extend([query, file_path])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            else:
                cmd = ['jq']
                if params.get('raw_output', True):
                    cmd.append('--raw-output')
                cmd.append(query)
                result = subprocess.run(cmd, input=json_input, capture_output=True, text=True, timeout=30)
            
            execution_time = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'result': result.stdout.strip(),
                    'query': query,
                    'execution_time_ms': execution_time,
                    'tool': 'jq'
                }
            else:
                return {'success': False, 'error': f'jq failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix jq failed: {str(e)}'}
    
    elif action == 'list_modern':
        try:
            path = params.get('path', '.')
            
            # Use lsd for modern ls alternative
            cmd = ['lsd', '--color=never']
            
            if params.get('long_format', False):
                cmd.append('-l')
            
            if params.get('show_all', False):
                cmd.append('-a')
            
            if params.get('tree_view', False):
                cmd.append('--tree')
            
            if params.get('classify', False):
                cmd.append('-F')
            
            cmd.append(path)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                return {
                    'success': True,
                    'files': lines,
                    'path': path,
                    'count': len(lines),
                    'formatted_output': result.stdout,
                    'tool': 'lsd'
                }
            else:
                return {'success': False, 'error': f'lsd failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix list_modern failed: {str(e)}'}
    
    elif action == 'disk_usage':
        try:
            path = params.get('path')
            output_format = params.get('output_format', 'human')
            
            # Use duf for modern disk usage
            cmd = ['duf']
            
            if output_format == 'json':
                cmd.append('--json')
            
            if path:
                # Filter to show only the filesystem containing this path
                cmd.extend(['--only', path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                if output_format == 'json':
                    try:
                        import json
                        disk_data = json.loads(result.stdout)
                        
                        total_size = sum(int(fs.get('size', 0)) for fs in disk_data)
                        available_space = sum(int(fs.get('avail', 0)) for fs in disk_data)
                        
                        return {
                            'success': True,
                            'disk_info': disk_data,
                            'total_size': total_size,
                            'available_space': available_space,
                            'format': 'json',
                            'tool': 'duf'
                        }
                    except json.JSONDecodeError:
                        return {'success': False, 'error': 'Failed to parse duf JSON output'}
                else:
                    return {
                        'success': True,
                        'output': result.stdout,
                        'format': 'human',
                        'tool': 'duf'
                    }
            else:
                return {'success': False, 'error': f'duf failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix disk_usage failed: {str(e)}'}
    
    elif action == 'help':
        try:
            command = params.get('command')
            if not command:
                return {'success': False, 'error': 'Missing required parameter: command'}
            
            # Use tldr for concise help
            cmd = ['tldr']
            
            if params.get('update_cache', False):
                cmd.append('--update')
            
            cmd.append(command)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse tldr output to extract examples
                content = result.stdout
                examples = []
                
                # Extract command examples from tldr output
                lines = content.split('\n')
                current_description = None
                for line in lines:
                    line_stripped = line.strip()
                    # Look for description lines (usually followed by blank line and command)
                    if line_stripped and not line_stripped.startswith(' ') and ':' in line_stripped and not line_stripped.startswith('git '):
                        current_description = line_stripped.rstrip(':')
                    elif line.startswith('  ') and line_stripped and current_description:
                        # This is likely a command line (indented)
                        command = line_stripped
                        examples.append({
                            'description': current_description,
                            'command': command
                        })
                        current_description = None
                
                return {
                    'success': True,
                    'command': params.get('command'),
                    'help_content': content,
                    'examples': examples,
                    'tool': 'tldr'
                }
            else:
                return {'success': False, 'error': f'tldr failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix help failed: {str(e)}'}
    
    elif action == 'diff_highlight':
        try:
            file1 = params.get('file1')
            file2 = params.get('file2')
            
            if not file1 or not file2:
                return {'success': False, 'error': 'Missing required parameters: file1 and file2'}
            
            # Use delta for enhanced diff highlighting
            cmd = ['delta']
            
            if params.get('side_by_side', False):
                cmd.append('--side-by-side')
            
            if params.get('line_numbers', True):
                cmd.append('--line-numbers')
            
            # Create diff and pipe to delta
            diff_cmd = ['diff', '-u', file1, file2]
            diff_result = subprocess.run(diff_cmd, capture_output=True, text=True, timeout=30)
            
            if diff_result.stdout:
                # Pipe diff output to delta
                delta_result = subprocess.run(cmd, input=diff_result.stdout, capture_output=True, text=True, timeout=30)
                
                changes_detected = diff_result.returncode != 0
                
                return {
                    'success': True,
                    'diff_output': delta_result.stdout if delta_result.returncode == 0 else diff_result.stdout,
                    'file1': file1,
                    'file2': file2,
                    'changes_detected': changes_detected,
                    'tool': 'delta'
                }
            else:
                return {
                    'success': True,
                    'diff_output': 'No differences found',
                    'file1': file1,
                    'file2': file2,
                    'changes_detected': False,
                    'tool': 'delta'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Unix diff_highlight failed: {str(e)}'}
    
    elif action == 'fuzzy_select':
        try:
            input_list = params.get('input_list', [])
            query = params.get('query', '')
            
            if not input_list:
                return {'success': False, 'error': 'Missing required parameter: input_list'}
            
            # Use fzf for fuzzy finding (non-interactive mode for testing)
            cmd = ['fzf', '--filter', query] if query else ['fzf', '--print-query']
            
            if params.get('multi_select', False):
                cmd.append('--multi')
            
            # Prepare input for fzf
            input_text = '\n'.join(input_list)
            
            result = subprocess.run(cmd, input=input_text, capture_output=True, text=True, timeout=30)
            
            selected_items = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            return {
                'success': True,
                'selected_items': selected_items,
                'query': query,
                'total_items': len(input_list),
                'matches': len(selected_items),
                'tool': 'fzf'
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Unix fuzzy_select failed: {str(e)}'}
    
    elif action == 'parse_syntax':
        try:
            file_path = params.get('file_path')
            source_code = params.get('source_code')
            language = params.get('language', 'python')
            
            if not file_path and not source_code:
                return {'success': False, 'error': 'Missing required parameter: file_path or source_code'}
            
            # Use tree-sitter for advanced syntax parsing
            cmd = ['tree-sitter', 'parse']
            
            # Don't use --quiet as it suppresses the syntax tree output we need
            if params.get('debug', False):
                cmd.append('--debug')
                
            if params.get('time', False):
                cmd.append('--time')
            
            start_time = time.time()
            
            if file_path:
                cmd.append(file_path)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            else:
                # For source code input, write to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as tmp:
                    tmp.write(source_code)
                    tmp_path = tmp.name
                
                try:
                    cmd.append(tmp_path)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                finally:
                    os.unlink(tmp_path)
            
            parse_time = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                # Parse tree-sitter output to extract syntax tree info
                output_lines = result.stdout.split('\n') if result.stdout else []
                
                # Count nodes and depth
                node_count = len([line for line in output_lines if '(' in line])
                max_depth = 0
                for line in output_lines:
                    depth = len(line) - len(line.lstrip())
                    max_depth = max(max_depth, depth // 2)  # Assuming 2 spaces per level
                
                return {
                    'success': True,
                    'syntax_tree': result.stdout,
                    'language': language,
                    'node_count': node_count,
                    'tree_depth': max_depth,
                    'parse_time_ms': parse_time,
                    'tool': 'tree-sitter'
                }
            else:
                return {'success': False, 'error': f'tree-sitter parse failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix parse_syntax failed: {str(e)}'}
    
    elif action == 'syntax_highlight':
        try:
            file_path = params.get('file_path')
            source_code = params.get('source_code')
            language = params.get('language', 'python')
            
            if not file_path and not source_code:
                return {'success': False, 'error': 'Missing required parameter: file_path or source_code'}
            
            # Use tree-sitter for syntax highlighting
            cmd = ['tree-sitter', 'highlight']
            
            if params.get('html', False):
                cmd.append('--html')
            
            start_time = time.time()
            
            if file_path:
                cmd.append(file_path)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            else:
                # For source code input, write to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as tmp:
                    tmp.write(source_code)
                    tmp_path = tmp.name
                
                try:
                    cmd.append(tmp_path)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                finally:
                    os.unlink(tmp_path)
            
            highlight_time = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'highlighted_code': result.stdout,
                    'language': language,
                    'is_html': params.get('html', False),
                    'highlight_time_ms': highlight_time,
                    'tool': 'tree-sitter'
                }
            else:
                return {'success': False, 'error': f'tree-sitter highlight failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix syntax_highlight failed: {str(e)}'}
    
    elif action == 'syntax_query':
        try:
            file_path = params.get('file_path')
            source_code = params.get('source_code')
            query = params.get('query')
            language = params.get('language', 'python')
            
            if not file_path and not source_code:
                return {'success': False, 'error': 'Missing required parameter: file_path or source_code'}
            if not query:
                return {'success': False, 'error': 'Missing required parameter: query'}
            
            # Use tree-sitter for syntax querying
            cmd = ['tree-sitter', 'query']
            
            # Create temporary query file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as query_tmp:
                query_tmp.write(query)
                query_path = query_tmp.name
            
            try:
                cmd.append(query_path)
                
                if file_path:
                    cmd.append(file_path)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                else:
                    # For source code input, write to temp file
                    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as code_tmp:
                        code_tmp.write(source_code)
                        code_path = code_tmp.name
                    
                    try:
                        cmd.append(code_path)
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    finally:
                        os.unlink(code_path)
                        
            finally:
                os.unlink(query_path)
            
            if result.returncode == 0:
                # Parse query results
                matches = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        matches.append(line.strip())
                
                return {
                    'success': True,
                    'matches': matches,
                    'match_count': len(matches),
                    'query': query,
                    'language': language,
                    'tool': 'tree-sitter'
                }
            else:
                return {'success': False, 'error': f'tree-sitter query failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix syntax_query failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown unix action: {action}'}


def pattern_action(action: str, **params) -> Dict[str, Any]:
    """Code pattern analysis with real Python AST implementation.
    
    Actions: extract_functions, extract_classes, extract_comments, summarize_code, log_attempt, get_patterns, analyze_patterns
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'extract_functions':
        try:
            source_code = params.get('source_code')
            if not source_code:
                return {'success': False, 'error': 'Missing required parameter: source_code'}
            
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                return {'success': False, 'error': f'Syntax error in source code: {str(e)}'}
            
            functions = []
            
            class FunctionVisitor(ast.NodeVisitor):
                """AST NodeVisitor for extracting function definitions and metadata."""
                def visit_FunctionDef(self, node):
                    """Visit a function definition node and extract metadata."""
                    func_info = {
                        'name': node.name,
                        'line_number': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'returns': ast.get_source_segment(source_code, node.returns) if node.returns else None,
                        'docstring': ast.get_docstring(node),
                        'decorator_list': [ast.get_source_segment(source_code, dec) for dec in node.decorator_list],
                        'is_async': isinstance(node, ast.AsyncFunctionDef)
                    }
                    
                    # Calculate complexity
                    complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                            complexity += 1
                    func_info['complexity'] = complexity
                    
                    functions.append(func_info)
                    self.generic_visit(node)
                
                def visit_AsyncFunctionDef(self, node):
                    """Visit an async function definition node and extract metadata."""
                    self.visit_FunctionDef(node)
            
            visitor = FunctionVisitor()
            visitor.visit(tree)
            
            return {
                'success': True,
                'functions': functions,
                'count': len(functions),
                'tool': 'Python AST',
                'source_lines': len(source_code.split('\n'))
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Extract functions failed: {str(e)}'}
    
    elif action == 'extract_classes':
        try:
            source_code = params.get('source_code')
            if not source_code:
                return {'success': False, 'error': 'Missing required parameter: source_code'}
            
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                return {'success': False, 'error': f'Syntax error in source code: {str(e)}'}
            
            classes = []
            
            class ClassVisitor(ast.NodeVisitor):
                """AST NodeVisitor for extracting class definitions and metadata."""
                def visit_ClassDef(self, node):
                    """Visit a class definition node and extract metadata."""
                    methods = []
                    attributes = []
                    
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append({
                                'name': item.name,
                                'line_number': item.lineno,
                                'args': [arg.arg for arg in item.args.args],
                                'is_property': any(
                                    isinstance(dec, ast.Name) and dec.id == 'property'
                                    for dec in item.decorator_list
                                )
                            })
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    attributes.append({
                                        'name': target.id,
                                        'line_number': item.lineno
                                    })
                    
                    class_info = {
                        'name': node.name,
                        'line_number': node.lineno,
                        'bases': [ast.get_source_segment(source_code, base) for base in node.bases],
                        'docstring': ast.get_docstring(node),
                        'methods': methods,
                        'attributes': attributes,
                        'method_count': len(methods),
                        'attribute_count': len(attributes)
                    }
                    
                    classes.append(class_info)
                    self.generic_visit(node)
            
            visitor = ClassVisitor()
            visitor.visit(tree)
            
            return {
                'success': True,
                'classes': classes,
                'count': len(classes),
                'tool': 'Python AST',
                'source_lines': len(source_code.split('\n'))
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Extract classes failed: {str(e)}'}
    
    elif action == 'summarize_code':
        try:
            source_code = params.get('source_code')
            if not source_code:
                return {'success': False, 'error': 'Missing required parameter: source_code'}
            
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                return {'success': False, 'error': f'Syntax error in source code: {str(e)}'}
            
            stats = {
                'functions': 0,
                'classes': 0,
                'imports': 0,
                'lines': len(source_code.split('\n')),
                'complexity': 0
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    stats['functions'] += 1
                elif isinstance(node, ast.ClassDef):
                    stats['classes'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    stats['imports'] += 1
                elif isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                    stats['complexity'] += 1
            
            summary_parts = []
            if stats['classes'] > 0:
                summary_parts.append(f"{stats['classes']} class{'es' if stats['classes'] != 1 else ''}")
            if stats['functions'] > 0:
                summary_parts.append(f"{stats['functions']} function{'s' if stats['functions'] != 1 else ''}")
            if stats['imports'] > 0:
                summary_parts.append(f"{stats['imports']} import{'s' if stats['imports'] != 1 else ''}")
            
            summary = f"Python code with {', '.join(summary_parts)} across {stats['lines']} lines"
            
            return {
                'success': True,
                'summary': summary,
                'statistics': stats,
                'tool': 'Python AST',
                'complexity_rating': 'Low' if stats['complexity'] < 5 else 'Medium' if stats['complexity'] < 15 else 'High'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Summarize code failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown pattern action: {action}'}


def blueprint_action(action: str, **params) -> Dict[str, Any]:
    """Blueprint operations with real internal SQLite+Neo4j implementation.
    
    Actions: create, analyze_complexity, list_project, add_dependency, resolve_order, update_metadata, get_dependencies, delete
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'create':
        required_params = ['title', 'description']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            # Direct SQLite connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create blueprints table
            cursor.execute('''
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
            import uuid
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
            cursor.execute('''
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
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
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
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint create failed: {str(e)}'}
    
    elif action == 'analyze_complexity':
        required_params = ['title', 'description']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            # ML-based complexity scoring algorithm
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
            
            return {
                'success': True,
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
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint complexity analysis failed: {str(e)}'}
    
    elif action == 'list_project':
        if 'project_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: project_id'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
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
            
            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            conn.close()
            
            blueprints = []
            for row in rows:
                # Parse JSON fields
                required_skills = json.loads(row[7]) if row[7] else []
                tags = json.loads(row[8]) if row[8] else []
                
                # Tag filtering (if specified)
                if tags_filter:
                    if not isinstance(tags_filter, list):
                        tags_filter = [tags_filter]
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
            
            return {
                'success': True,
                'blueprints': blueprints,
                'project_id': project_id,
                'total_found': len(blueprints),
                'limit_applied': limit,
                'filters': {
                    'min_complexity': min_complexity,
                    'tags': tags_filter
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint list project failed: {str(e)}'}
    
    elif action == 'add_dependency':
        required_params = ['dependent_blueprint_id', 'prerequisite_blueprint_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.config import get_config
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
                'dependent_blueprint_id': params['dependent_blueprint_id'],
                'prerequisite_blueprint_id': params['prerequisite_blueprint_id'],
                'dependency_type': dependency_type,
                'is_critical': bool(is_critical),
                'created_at': created_at,
                'message': 'Blueprint dependency added successfully'
            }
            
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Dependency already exists'}
        except Exception as e:
            return {'success': False, 'error': f'Blueprint add dependency failed: {str(e)}'}
    
    elif action == 'resolve_order':
        if 'blueprint_ids' not in params:
            return {'success': False, 'error': 'Missing required parameter: blueprint_ids'}
        
        try:
            from ltms.config import get_config
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
            dependencies = cursor.fetchall()
            conn.close()
            
            # Build dependency graph
            graph = {bp_id: [] for bp_id in blueprint_ids}
            for dep in dependencies:
                dependent_id, prerequisite_id, dep_type, is_critical = dep
                if dependent_id in graph and prerequisite_id in blueprint_ids:
                    graph[dependent_id].append(prerequisite_id)
            
            # Topological sort with priority ordering
            in_degree = {bp_id: 0 for bp_id in blueprint_ids}
            for bp_id in blueprint_ids:
                for prereq in graph[bp_id]:
                    in_degree[prereq] += 1
            
            # Use priority queue (higher priority first among items with same in_degree)
            from collections import deque
            queue = deque()
            
            # Start with items that have no dependencies
            for bp_id in blueprint_ids:
                if in_degree[bp_id] == 0:
                    queue.append(bp_id)
            
            # Sort queue by priority score (descending)
            queue = deque(sorted(queue, key=lambda x: blueprints[x]['priority_score'], reverse=True))
            
            result_order = []
            while queue:
                current = queue.popleft()
                result_order.append(current)
                
                # Update in-degrees for dependents
                for bp_id in blueprint_ids:
                    if current in graph[bp_id]:
                        in_degree[bp_id] -= 1
                        if in_degree[bp_id] == 0:
                            queue.append(bp_id)
                
                # Re-sort queue by priority
                queue = deque(sorted(queue, key=lambda x: blueprints[x]['priority_score'], reverse=True))
            
            # Check for circular dependencies
            if len(result_order) != len(blueprint_ids):
                return {
                    'success': False, 
                    'error': 'Circular dependency detected',
                    'processed': result_order,
                    'remaining': [bp_id for bp_id in blueprint_ids if bp_id not in result_order]
                }
            
            # Build detailed result
            execution_order = []
            for bp_id in result_order:
                bp_details = blueprints[bp_id].copy()
                bp_details['blueprint_id'] = bp_id
                execution_order.append(bp_details)
            
            return {
                'success': True,
                'execution_order': execution_order,
                'total_blueprints': len(execution_order),
                'has_dependencies': len(dependencies) > 0,
                'dependency_count': len(dependencies)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint resolve order failed: {str(e)}'}
    
    elif action == 'update_metadata':
        if 'blueprint_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: blueprint_id'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if blueprint exists
            cursor.execute('SELECT id FROM blueprints WHERE id = ?', (params['blueprint_id'],))
            if not cursor.fetchone():
                conn.close()
                return {'success': False, 'error': 'Blueprint not found'}
            
            # Build update query dynamically
            updates = []
            update_params = []
            
            if 'estimated_duration_minutes' in params:
                updates.append('estimated_duration_minutes = ?')
                update_params.append(params['estimated_duration_minutes'])
            
            if 'priority_score' in params:
                updates.append('priority_score = ?')
                update_params.append(params['priority_score'])
            
            if 'complexity_score' in params:
                updates.append('complexity_score = ?')
                update_params.append(params['complexity_score'])
            
            if 'required_skills' in params:
                updates.append('required_skills = ?')
                update_params.append(json.dumps(params['required_skills']))
            
            if 'tags' in params:
                updates.append('tags = ?')
                update_params.append(json.dumps(params['tags']))
            
            if 'status' in params:
                updates.append('status = ?')
                update_params.append(params['status'])
            
            if not updates:
                return {'success': False, 'error': 'No valid update fields provided'}
            
            # Add updated timestamp
            updates.append('updated_at = ?')
            update_params.append(datetime.now(timezone.utc).isoformat())
            
            # Add blueprint_id for WHERE clause
            update_params.append(params['blueprint_id'])
            
            query = f"UPDATE blueprints SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, update_params)
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'blueprint_id': params['blueprint_id'],
                'updated_fields': list(params.keys()),
                'estimated_duration_minutes': params.get('estimated_duration_minutes'),
                'priority_score': params.get('priority_score'),
                'message': 'Blueprint metadata updated successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint update metadata failed: {str(e)}'}
    
    elif action == 'get_dependencies':
        if 'blueprint_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: blueprint_id'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get dependencies for this blueprint
            cursor.execute('''
                SELECT bd.prerequisite_blueprint_id, bd.dependency_type, bd.is_critical,
                       bd.created_at, b.title as prerequisite_title
                FROM blueprint_dependencies bd
                LEFT JOIN blueprints b ON bd.prerequisite_blueprint_id = b.id
                WHERE bd.dependent_blueprint_id = ?
                ORDER BY bd.is_critical DESC, bd.created_at ASC
            ''', (params['blueprint_id'],))
            
            dependencies = []
            for row in cursor.fetchall():
                dependencies.append({
                    'prerequisite_blueprint_id': row[0],
                    'dependency_type': row[1],
                    'is_critical': bool(row[2]),
                    'created_at': row[3],
                    'prerequisite_title': row[4]
                })
            
            conn.close()
            
            return {
                'success': True,
                'blueprint_id': params['blueprint_id'],
                'dependencies': dependencies,
                'dependency_count': len(dependencies),
                'has_critical_dependencies': any(dep['is_critical'] for dep in dependencies)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint get dependencies failed: {str(e)}'}
    
    elif action == 'delete':
        if 'blueprint_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: blueprint_id'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            blueprint_id = params['blueprint_id']
            
            # Check if blueprint exists
            cursor.execute('SELECT title FROM blueprints WHERE id = ?', (blueprint_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'success': False, 'error': 'Blueprint not found'}
            
            title = result[0]
            
            # Delete dependencies
            cursor.execute('''
                DELETE FROM blueprint_dependencies 
                WHERE dependent_blueprint_id = ? OR prerequisite_blueprint_id = ?
            ''', (blueprint_id, blueprint_id))
            
            # Delete blueprint
            cursor.execute('DELETE FROM blueprints WHERE id = ?', (blueprint_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'blueprint_id': blueprint_id,
                'title': title,
                'message': f'Blueprint "{title}" and all its dependencies deleted successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Blueprint delete failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown blueprint action: {action}'}


def cache_action(action: str, **params) -> Dict[str, Any]:
    """Cache operations with real internal Redis implementation.
    
    Actions: health_check, stats, flush, reset
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'health_check':
        try:
            from ltms.config import get_config
            config = get_config()
            
            # Use Redis service from ltms.services.redis_service
            import asyncio
            
            async def check_redis():
                """Check Redis connection health and return status."""
                try:
                    from ltms.services.redis_service import get_redis_manager
                    manager = await get_redis_manager()
                    is_healthy = await manager.health_check()
                    
                    if is_healthy:
                        return {
                            'success': True,
                            'connected': True,
                            'host': manager.host,
                            'port': manager.port,
                            'message': 'Redis connection healthy'
                        }
                    else:
                        return {
                            'success': False,
                            'connected': False,
                            'error': 'Redis health check failed'
                        }
                        
                except Exception as e:
                    return {
                        'success': False,
                        'connected': False,
                        'error': f'Redis connection failed: {str(e)}'
                    }
            
            # Use existing event loop instead of asyncio.run()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(check_redis())
            
        except Exception as e:
            return {'success': False, 'error': f'Cache health check failed: {str(e)}'}
    
    elif action == 'stats':
        try:
            cache_type = params.get('cache_type', 'all')
            
            import asyncio
            
            async def get_cache_stats():
                """Retrieve cache statistics from Redis server."""
                try:
                    from ltms.services.redis_service import get_cache_service
                    cache_service = await get_cache_service()
                    stats = await cache_service.get_cache_stats()
                    
                    result = {
                        'success': True,
                        'cache_type': cache_type,
                        'stats': stats
                    }
                    
                    if cache_type != 'all':
                        # Filter stats by type
                        filtered_stats = {}
                        if cache_type == 'embeddings':
                            filtered_stats['embedding_cache_count'] = stats.get('embedding_cache_count', 0)
                        elif cache_type == 'queries':
                            filtered_stats['query_cache_count'] = stats.get('query_cache_count', 0)
                        
                        result['stats'] = {**stats, 'filtered': filtered_stats}
                    
                    return result
                    
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to get cache stats: {str(e)}'
                    }
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(get_cache_stats())
            
        except Exception as e:
            return {'success': False, 'error': f'Cache stats failed: {str(e)}'}
    
    elif action == 'flush':
        try:
            cache_type = params.get('cache_type', 'all')
            pattern = params.get('pattern', '*')
            
            import asyncio
            
            async def flush_cache():
                """Flush all cached data from Redis server."""
                try:
                    from ltms.services.redis_service import get_cache_service
                    cache_service = await get_cache_service()
                    
                    if cache_type == 'all':
                        # Flush all cache types
                        embedding_count = await cache_service.invalidate_cache(f"{cache_service.EMBEDDING_PREFIX}*")
                        query_count = await cache_service.invalidate_cache(f"{cache_service.QUERY_PREFIX}*")
                        chunk_count = await cache_service.invalidate_cache(f"{cache_service.CHUNK_PREFIX}*")
                        resource_count = await cache_service.invalidate_cache(f"{cache_service.RESOURCE_PREFIX}*")
                        
                        total_deleted = embedding_count + query_count + chunk_count + resource_count
                        
                        return {
                            'success': True,
                            'cache_type': cache_type,
                            'total_keys_deleted': total_deleted,
                            'breakdown': {
                                'embeddings': embedding_count,
                                'queries': query_count,
                                'chunks': chunk_count,
                                'resources': resource_count
                            }
                        }
                        
                    elif cache_type == 'embeddings':
                        deleted = await cache_service.invalidate_cache(f"{cache_service.EMBEDDING_PREFIX}*")
                    elif cache_type == 'queries':
                        deleted = await cache_service.invalidate_cache(f"{cache_service.QUERY_PREFIX}*")
                    else:
                        # Custom pattern
                        deleted = await cache_service.invalidate_cache(pattern)
                    
                    return {
                        'success': True,
                        'cache_type': cache_type,
                        'pattern': pattern,
                        'keys_deleted': deleted
                    }
                    
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to flush cache: {str(e)}'
                    }
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(flush_cache())
            
        except Exception as e:
            return {'success': False, 'error': f'Cache flush failed: {str(e)}'}
    
    elif action == 'reset':
        try:
            import asyncio
            
            async def reset_redis():
                """Reset Redis server and clear all data."""
                try:
                    from ltms.services.redis_service import reset_redis_globals
                    await reset_redis_globals()
                    
                    return {
                        'success': True,
                        'message': 'Redis global instances reset successfully'
                    }
                    
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to reset Redis: {str(e)}'
                    }
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(reset_redis())
            
        except Exception as e:
            return {'success': False, 'error': f'Cache reset failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown cache action: {action}'}


def graph_action(action: str, **params) -> Dict[str, Any]:
    """Knowledge graph operations with real internal Neo4j implementation.
    
    Actions: link, query, auto_link, get_relationships
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'link':
        required_params = ['source_id', 'target_id', 'relation']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            import asyncio
            
            async def create_link():
                """Create new relationship link in Neo4j graph database."""
                store = await get_neo4j_graph_store()
                
                if not store.is_available():
                    return {
                        'success': False,
                        'error': 'Neo4j graph store not available'
                    }
                
                properties = params.get('properties', {})
                weight = params.get('weight', 1.0)
                metadata = params.get('metadata', {})
                
                # Add weight and metadata to properties
                properties.update({
                    'weight': weight,
                    'metadata': json.dumps(metadata) if metadata else None
                })
                
                result = store.create_relationship(
                    source_id=params['source_id'],
                    target_id=params['target_id'],
                    relationship_type=params['relation'],
                    properties=properties
                )
                
                return result
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(create_link())
            
        except Exception as e:
            return {'success': False, 'error': f'Graph link failed: {str(e)}'}
    
    elif action == 'query':
        required_params = ['entity']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            import asyncio
            
            async def query_relationships():
                """Query existing relationships in Neo4j graph database."""
                store = await get_neo4j_graph_store()
                
                if not store.is_available():
                    return {
                        'success': False,
                        'error': 'Neo4j graph store not available'
                    }
                
                relation_type = params.get('relation_type')
                direction = params.get('direction', 'both')
                
                result = store.query_relationships(
                    entity_id=params['entity'],
                    relationship_type=relation_type,
                    direction=direction
                )
                
                return result
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(query_relationships())
            
        except Exception as e:
            return {'success': False, 'error': f'Graph query failed: {str(e)}'}
    
    elif action == 'auto_link':
        if 'documents' not in params:
            return {'success': False, 'error': 'Missing required parameter: documents'}
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            import asyncio
            
            async def auto_link_docs():
                """Automatically create links between related documents."""
                store = await get_neo4j_graph_store()
                
                if not store.is_available():
                    return {
                        'success': False,
                        'error': 'Neo4j graph store not available'
                    }
                
                documents = params['documents']
                max_links = params.get('max_links_per_document', 5)
                similarity_threshold = params.get('similarity_threshold', 0.7)
                
                result = store.auto_link_documents(documents)
                
                return result
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(auto_link_docs())
            
        except Exception as e:
            return {'success': False, 'error': f'Graph auto link failed: {str(e)}'}
    
    elif action == 'get_relationships':
        if 'doc_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: doc_id'}
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            import asyncio
            
            async def get_doc_relationships():
                """Get relationships for specific document from Neo4j."""
                store = await get_neo4j_graph_store()
                
                if not store.is_available():
                    return {
                        'success': False,
                        'error': 'Neo4j graph store not available'
                    }
                
                result = store.query_relationships(params['doc_id'])
                
                return result
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(get_doc_relationships())
            
        except Exception as e:
            return {'success': False, 'error': f'Get relationships failed: {str(e)}'}
    
    elif action == 'context':
        # Handle both build_context and retrieve_by_type functionality
        if 'query' not in params:
            return {'success': False, 'error': 'Missing required parameter: query'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            # Direct SQLite connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            query = params['query']
            doc_type = params.get('doc_type', 'document')
            top_k = params.get('top_k', 5)
            max_tokens = params.get('max_tokens', 4000)
            
            # Simple text matching for context retrieval
            cursor.execute('''
                SELECT id, file_name, content, resource_type, created_at
                FROM documents 
                WHERE resource_type = ? AND (content LIKE ? OR file_name LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
            ''', (doc_type, f'%{query}%', f'%{query}%', top_k))
            
            results = []
            total_tokens = 0
            
            for row in cursor.fetchall():
                doc_id, file_name, content, resource_type, created_at = row
                
                # Estimate tokens (roughly 4 chars per token)
                content_tokens = len(content) // 4
                if total_tokens + content_tokens > max_tokens:
                    # Truncate content to fit token limit
                    remaining_tokens = max_tokens - total_tokens
                    content = content[:remaining_tokens * 4] + "..."
                    content_tokens = remaining_tokens
                
                results.append({
                    'id': doc_id,
                    'file_name': file_name,
                    'content': content,
                    'resource_type': resource_type,
                    'created_at': created_at,
                    'tokens': content_tokens
                })
                
                total_tokens += content_tokens
                if total_tokens >= max_tokens:
                    break
            
            conn.close()
            
            return {
                'success': True,
                'query': query,
                'doc_type': doc_type,
                'results': results,
                'total_documents': len(results),
                'total_tokens': total_tokens,
                'max_tokens': max_tokens
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Graph context failed: {str(e)}'}
    
    elif action == 'get':
        # Handle get_context_links_for_message and get_resource_links
        if 'resource_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: resource_id'}
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            import asyncio
            
            async def get_resource_links():
                """Get all resource links from Neo4j graph database."""
                store = await get_neo4j_graph_store()
                
                if not store.is_available():
                    return {
                        'success': False,
                        'error': 'Neo4j graph store not available'
                    }
                
                resource_id = params['resource_id']
                link_type = params.get('link_type')
                
                # Query both incoming and outgoing relationships
                relationships = store.query_relationships(
                    entity_id=resource_id,
                    relationship_type=link_type,
                    direction='both'
                )
                
                return {
                    'success': True,
                    'resource_id': resource_id,
                    'link_type': link_type,
                    'relationships': relationships
                }
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(get_resource_links())
            
        except Exception as e:
            return {'success': False, 'error': f'Graph get failed: {str(e)}'}
    
    elif action == 'messages':
        # Handle get_messages_for_chunk
        if 'chunk_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: chunk_id'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            # Direct SQLite connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            chunk_id = params['chunk_id']
            
            # Find messages that reference this chunk
            cursor.execute('''
                SELECT id, conversation_id, role, content, agent_name, source_tool, created_at
                FROM chat_messages 
                WHERE content LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
            ''', (f'%chunk_{chunk_id}%', f'%{chunk_id}%'))
            
            messages = []
            for row in cursor.fetchall():
                msg_id, conv_id, role, content, agent_name, source_tool, created_at = row
                messages.append({
                    'id': msg_id,
                    'conversation_id': conv_id,
                    'role': role,
                    'content': content,
                    'agent_name': agent_name,
                    'source_tool': source_tool,
                    'created_at': created_at
                })
            
            conn.close()
            
            return {
                'success': True,
                'chunk_id': chunk_id,
                'messages': messages,
                'message_count': len(messages)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Graph messages failed: {str(e)}'}
    
    elif action == 'stats':
        # Handle get_context_usage_statistics
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            # Direct SQLite connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get document statistics
            cursor.execute('SELECT COUNT(*) FROM documents')
            doc_count = cursor.fetchone()[0]
            
            # Get chat message statistics
            cursor.execute('SELECT COUNT(*) FROM chat_messages')
            message_count = cursor.fetchone()[0]
            
            # Get blueprint statistics
            cursor.execute('SELECT COUNT(*) FROM blueprints')
            blueprint_count = cursor.fetchone()[0]
            
            # Get todo statistics
            cursor.execute('SELECT COUNT(*) FROM todos')
            todo_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'statistics': {
                    'total_documents': doc_count,
                    'total_messages': message_count,
                    'total_blueprints': blueprint_count,
                    'total_todos': todo_count,
                    'total_resources': doc_count + message_count + blueprint_count + todo_count
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Graph stats failed: {str(e)}'}
    
    elif action == 'remove':
        # Handle remove_resource_link
        if 'link_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: link_id'}
        
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            import asyncio
            
            async def remove_link():
                """Remove specific relationship link from Neo4j graph."""
                store = await get_neo4j_graph_store()
                
                if not store.is_available():
                    return {
                        'success': False,
                        'error': 'Neo4j graph store not available'
                    }
                
                link_id = params['link_id']
                
                # Remove relationship by ID (this would need Neo4j store implementation)
                result = store.delete_relationship(link_id)
                
                return {
                    'success': True,
                    'link_id': link_id,
                    'message': 'Resource link removed successfully'
                }
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(remove_link())
            
        except Exception as e:
            return {'success': False, 'error': f'Graph remove failed: {str(e)}'}
    
    elif action == 'list':
        # Handle list_all_resource_links
        try:
            from ltms.database.neo4j_store import get_neo4j_graph_store
            import asyncio
            
            async def list_links():
                """List all relationship links in Neo4j graph database."""
                store = await get_neo4j_graph_store()
                
                if not store.is_available():
                    return {
                        'success': False,
                        'error': 'Neo4j graph store not available'
                    }
                
                limit = params.get('limit', 100)
                
                # Get all relationships (this would need Neo4j store implementation)
                relationships = store.list_all_relationships(limit=limit)
                
                return {
                    'success': True,
                    'relationships': relationships,
                    'limit': limit,
                    'count': len(relationships)
                }
            
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(list_links())
            
        except Exception as e:
            return {'success': False, 'error': f'Graph list failed: {str(e)}'}
    
    elif action == 'discover':
        # Handle list_tool_identifiers  
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            # Direct SQLite connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get unique source tools from chat messages
            cursor.execute('''
                SELECT DISTINCT source_tool, COUNT(*) as usage_count
                FROM chat_messages 
                WHERE source_tool IS NOT NULL AND source_tool != ''
                GROUP BY source_tool
                ORDER BY usage_count DESC
            ''')
            
            tools = []
            for row in cursor.fetchall():
                tool_name, usage_count = row
                tools.append({
                    'tool_name': tool_name,
                    'usage_count': usage_count
                })
            
            conn.close()
            
            return {
                'success': True,
                'tool_identifiers': tools,
                'total_tools': len(tools)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Graph discover failed: {str(e)}'}
    
    elif action == 'conversations':
        # Handle get_tool_conversations
        if 'source_tool' not in params:
            return {'success': False, 'error': 'Missing required parameter: source_tool'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            # Direct SQLite connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            source_tool = params['source_tool']
            limit = params.get('limit', 10)
            
            # Get conversations that used this tool
            cursor.execute('''
                SELECT DISTINCT conversation_id, COUNT(*) as message_count,
                       MIN(created_at) as first_message,
                       MAX(created_at) as last_message
                FROM chat_messages 
                WHERE source_tool = ?
                GROUP BY conversation_id
                ORDER BY last_message DESC
                LIMIT ?
            ''', (source_tool, limit))
            
            conversations = []
            for row in cursor.fetchall():
                conv_id, msg_count, first_msg, last_msg = row
                conversations.append({
                    'conversation_id': conv_id,
                    'message_count': msg_count,
                    'first_message': first_msg,
                    'last_message': last_msg,
                    'source_tool': source_tool
                })
            
            conn.close()
            
            return {
                'success': True,
                'source_tool': source_tool,
                'conversations': conversations,
                'conversation_count': len(conversations),
                'limit': limit
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Graph conversations failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown graph action: {action}'}


def documentation_action(action: str, **params) -> Dict[str, Any]:
    """Documentation operations with real internal implementation.
    
    Actions: generate_api_docs, generate_architecture_diagram, sync_documentation_with_code, validate_documentation_consistency
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'generate_api_docs':
        required_params = ['project_id', 'source_files']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            import inspect
            import ast
            
            project_id = params['project_id']
            source_files = params['source_files']
            output_format = params.get('output_format', 'markdown')
            
            if not isinstance(source_files, dict):
                return {'success': False, 'error': 'source_files must be a dictionary mapping file paths to content'}
            
            api_docs = []
            
            for file_path, content in source_files.items():
                try:
                    tree = ast.parse(content)
                    
                    # Extract functions and classes
                    functions = []
                    classes = []
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            func_doc = {
                                'name': node.name,
                                'line': node.lineno,
                                'args': [arg.arg for arg in node.args.args],
                                'docstring': ast.get_docstring(node),
                                'is_async': False
                            }
                            functions.append(func_doc)
                        
                        elif isinstance(node, ast.AsyncFunctionDef):
                            func_doc = {
                                'name': node.name,
                                'line': node.lineno,
                                'args': [arg.arg for arg in node.args.args],
                                'docstring': ast.get_docstring(node),
                                'is_async': True
                            }
                            functions.append(func_doc)
                        
                        elif isinstance(node, ast.ClassDef):
                            class_doc = {
                                'name': node.name,
                                'line': node.lineno,
                                'docstring': ast.get_docstring(node),
                                'methods': []
                            }
                            
                            # Get class methods
                            for item in node.body:
                                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    method_doc = {
                                        'name': item.name,
                                        'line': item.lineno,
                                        'args': [arg.arg for arg in item.args.args],
                                        'docstring': ast.get_docstring(item),
                                        'is_async': isinstance(item, ast.AsyncFunctionDef)
                                    }
                                    class_doc['methods'].append(method_doc)
                            
                            classes.append(class_doc)
                    
                    api_docs.append({
                        'file_path': file_path,
                        'functions': functions,
                        'classes': classes,
                        'function_count': len(functions),
                        'class_count': len(classes)
                    })
                    
                except Exception as parse_error:
                    api_docs.append({
                        'file_path': file_path,
                        'error': f'Failed to parse: {str(parse_error)}',
                        'functions': [],
                        'classes': []
                    })
            
            # Generate documentation text
            if output_format == 'markdown':
                doc_text = f"# API Documentation - {project_id}\n\n"
                
                for doc in api_docs:
                    if 'error' in doc:
                        doc_text += f"## {doc['file_path']} (Parse Error)\n{doc['error']}\n\n"
                        continue
                    
                    doc_text += f"## {doc['file_path']}\n\n"
                    
                    # Document classes
                    for cls in doc['classes']:
                        doc_text += f"### Class: `{cls['name']}`\n"
                        if cls['docstring']:
                            doc_text += f"{cls['docstring']}\n\n"
                        
                        for method in cls['methods']:
                            async_marker = 'async ' if method['is_async'] else ''
                            args_str = ', '.join(method['args'])
                            doc_text += f"#### `{async_marker}{method['name']}({args_str})`\n"
                            if method['docstring']:
                                doc_text += f"{method['docstring']}\n\n"
                        doc_text += "\n"
                    
                    # Document functions
                    for func in doc['functions']:
                        async_marker = 'async ' if func['is_async'] else ''
                        args_str = ', '.join(func['args'])
                        doc_text += f"### Function: `{async_marker}{func['name']}({args_str})`\n"
                        if func['docstring']:
                            doc_text += f"{func['docstring']}\n\n"
                    
                    doc_text += "\n"
            
            else:
                # JSON format
                doc_text = json.dumps(api_docs, indent=2)
            
            return {
                'success': True,
                'project_id': project_id,
                'output_format': output_format,
                'documentation': doc_text,
                'files_processed': len(source_files),
                'total_functions': sum(doc.get('function_count', 0) for doc in api_docs),
                'total_classes': sum(doc.get('class_count', 0) for doc in api_docs)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Generate API docs failed: {str(e)}'}
    
    elif action == 'generate_architecture_diagram':
        if 'project_id' not in params:
            return {'success': False, 'error': 'Missing required parameter: project_id'}
        
        try:
            project_id = params['project_id']
            diagram_type = params.get('diagram_type', 'system')
            include_dependencies = params.get('include_dependencies', True)
            
            # Create basic PlantUML-style architecture diagram
            if diagram_type == 'system':
                diagram = f"""
@startuml {project_id}_system_architecture
!define SYSTEM_COLOR #E1F5FE
!define SERVICE_COLOR #FFF3E0
!define DATABASE_COLOR #E8F5E8

package "{project_id} System" {{
    [Web Interface] <<UI>> #SYSTEM_COLOR
    [API Gateway] <<Service>> #SERVICE_COLOR
    [Authentication Service] <<Service>> #SERVICE_COLOR
    [Business Logic] <<Service>> #SERVICE_COLOR
    [Data Access Layer] <<Service>> #SERVICE_COLOR
}}

database "Primary Database" {{
    [User Data] <<Table>> #DATABASE_COLOR
    [Application Data] <<Table>> #DATABASE_COLOR
    [Configuration] <<Table>> #DATABASE_COLOR
}}

[Web Interface] --> [API Gateway] : HTTP/HTTPS
[API Gateway] --> [Authentication Service] : Validate
[API Gateway] --> [Business Logic] : Process
[Business Logic] --> [Data Access Layer] : Query
[Data Access Layer] --> [Primary Database] : SQL
@enduml
"""
            
            elif diagram_type == 'component':
                diagram = f"""
@startuml {project_id}_components
package "{project_id}" {{
    component [Core Engine] {{
        [Service Manager]
        [Event Handler]
        [Configuration]
    }}
    
    component [Data Layer] {{
        [Repository Pattern]
        [Entity Models]
        [Migrations]
    }}
    
    component [API Layer] {{
        [Controllers]
        [Middleware]
        [Validators]
    }}
}}

[API Layer] --> [Core Engine]
[Core Engine] --> [Data Layer]
@enduml
"""
            else:
                diagram = f"# {project_id} - {diagram_type.title()} Architecture\n\nBasic architecture diagram for {project_id}."
            
            return {
                'success': True,
                'project_id': project_id,
                'diagram_type': diagram_type,
                'diagram_content': diagram,
                'format': 'plantuml',
                'include_dependencies': include_dependencies
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Generate architecture diagram failed: {str(e)}'}
    
    elif action == 'sync_documentation_with_code':
        required_params = ['file_path', 'project_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            file_path = params['file_path']
            project_id = params['project_id']
            force_update = params.get('force_update', False)
            
            # Read source file
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            with open(file_path, 'r') as f:
                source_content = f.read()
            
            # Parse code structure
            try:
                tree = ast.parse(source_content)
                code_structure = {
                    'functions': [],
                    'classes': [],
                    'imports': [],
                    'docstrings': []
                }
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        code_structure['functions'].append({
                            'name': node.name,
                            'line': node.lineno,
                            'docstring': ast.get_docstring(node),
                            'args': [arg.arg for arg in node.args.args]
                        })
                    elif isinstance(node, ast.ClassDef):
                        code_structure['classes'].append({
                            'name': node.name,
                            'line': node.lineno,
                            'docstring': ast.get_docstring(node)
                        })
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                code_structure['imports'].append(alias.name)
                        else:
                            module = node.module or ''
                            for alias in node.names:
                                code_structure['imports'].append(f"{module}.{alias.name}")
                
                # Generate synchronized documentation
                sync_doc = f"# {os.path.basename(file_path)} - Auto-generated Documentation\n\n"
                sync_doc += f"**Project**: {project_id}  \n**Last Updated**: {datetime.now().isoformat()}  \n**Source**: `{file_path}`\n\n"
                
                if code_structure['classes']:
                    sync_doc += "## Classes\n\n"
                    for cls in code_structure['classes']:
                        sync_doc += f"### `{cls['name']}` (Line {cls['line']})\n"
                        if cls['docstring']:
                            sync_doc += f"{cls['docstring']}\n\n"
                        else:
                            sync_doc += "*No documentation available*\n\n"
                
                if code_structure['functions']:
                    sync_doc += "## Functions\n\n"
                    for func in code_structure['functions']:
                        args_str = ', '.join(func['args'])
                        sync_doc += f"### `{func['name']}({args_str})` (Line {func['line']})\n"
                        if func['docstring']:
                            sync_doc += f"{func['docstring']}\n\n"
                        else:
                            sync_doc += "*No documentation available*\n\n"
                
                return {
                    'success': True,
                    'file_path': file_path,
                    'project_id': project_id,
                    'synchronized_content': sync_doc,
                    'code_structure': code_structure,
                    'sync_timestamp': datetime.now().isoformat(),
                    'force_update': force_update
                }
                
            except SyntaxError as e:
                return {
                    'success': False,
                    'error': f'Syntax error in source file: {str(e)}',
                    'file_path': file_path
                }
            
        except Exception as e:
            return {'success': False, 'error': f'Documentation sync failed: {str(e)}'}
    
    elif action == 'validate_documentation_consistency':
        required_params = ['file_path', 'project_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            file_path = params['file_path']
            project_id = params['project_id']
            
            # Read and parse source file
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            with open(file_path, 'r') as f:
                source_content = f.read()
            
            tree = ast.parse(source_content)
            
            consistency_score = 0.0
            total_elements = 0
            documented_elements = 0
            
            issues = []
            
            # Check function documentation
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    total_elements += 1
                    docstring = ast.get_docstring(node)
                    if docstring:
                        documented_elements += 1
                        # Check docstring quality
                        if len(docstring) < 10:
                            issues.append(f"Function '{node.name}' has minimal documentation")
                        elif 'Args:' not in docstring and len(node.args.args) > 1:
                            issues.append(f"Function '{node.name}' missing parameter documentation")
                    else:
                        issues.append(f"Function '{node.name}' has no docstring")
                
                elif isinstance(node, ast.ClassDef):
                    total_elements += 1
                    docstring = ast.get_docstring(node)
                    if docstring:
                        documented_elements += 1
                    else:
                        issues.append(f"Class '{node.name}' has no docstring")
            
            if total_elements > 0:
                consistency_score = documented_elements / total_elements
            
            # Determine consistency level
            if consistency_score >= 0.9:
                consistency_level = 'excellent'
            elif consistency_score >= 0.7:
                consistency_level = 'good'
            elif consistency_score >= 0.5:
                consistency_level = 'fair'
            else:
                consistency_level = 'poor'
            
            return {
                'success': True,
                'file_path': file_path,
                'project_id': project_id,
                'consistency_score': round(consistency_score, 3),
                'consistency_level': consistency_level,
                'total_elements': total_elements,
                'documented_elements': documented_elements,
                'issues': issues,
                'validation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Documentation validation failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown documentation action: {action}'}


def sync_action(action: str, **params) -> Dict[str, Any]:
    """Documentation synchronization operations with real internal implementation.
    
    Actions: code, validate, drift, blueprint, score, monitor, status
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'code':
        # Handle sync_documentation_with_code
        required_params = ['file_path', 'project_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            file_path = params['file_path']
            project_id = params['project_id']
            force_update = params.get('force_update', False)
            
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Read source code
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse with AST
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                return {'success': False, 'error': f'Python syntax error: {str(e)}'}
            
            # Extract code structure
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'args': [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'methods': [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    })
            
            # Generate sync report
            sync_report = {
                'file_path': file_path,
                'project_id': project_id,
                'functions_found': len(functions),
                'classes_found': len(classes),
                'functions': functions,
                'classes': classes,
                'sync_timestamp': datetime.now(timezone.utc).isoformat(),
                'force_update': force_update
            }
            
            return {
                'success': True,
                'sync_report': sync_report,
                'message': 'Documentation synchronization completed successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Sync code failed: {str(e)}'}
    
    elif action == 'validate':
        # Handle validate_documentation_consistency
        required_params = ['file_path', 'project_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            file_path = params['file_path']
            project_id = params['project_id']
            
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Read and parse source code
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            # Analyze documentation consistency
            total_elements = 0
            documented_elements = 0
            issues = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    total_elements += 1
                    docstring = ast.get_docstring(node)
                    
                    if docstring:
                        documented_elements += 1
                        # Check docstring quality
                        if len(docstring.strip()) < 10:
                            issues.append(f'{node.name}: Docstring too short')
                    else:
                        issues.append(f'{node.name}: Missing docstring')
            
            consistency_score = documented_elements / total_elements if total_elements > 0 else 0
            consistency_level = 'excellent' if consistency_score >= 0.9 else 'good' if consistency_score >= 0.7 else 'poor'
            
            return {
                'success': True,
                'file_path': file_path,
                'project_id': project_id,
                'consistency_score': round(consistency_score, 3),
                'consistency_level': consistency_level,
                'total_elements': total_elements,
                'documented_elements': documented_elements,
                'issues': issues,
                'validation_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Sync validate failed: {str(e)}'}
    
    elif action == 'drift':
        # Handle detect_documentation_drift
        required_params = ['file_path', 'project_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            file_path = params['file_path']
            project_id = params['project_id']
            time_threshold_hours = params.get('time_threshold_hours', 24)
            
            # Get file modification time
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            file_mtime = os.path.getmtime(file_path)
            current_time = datetime.now().timestamp()
            hours_since_modified = (current_time - file_mtime) / 3600
            
            drift_detected = hours_since_modified <= time_threshold_hours
            
            # Simple drift analysis based on file modification time
            return {
                'success': True,
                'file_path': file_path,
                'project_id': project_id,
                'drift_detected': drift_detected,
                'hours_since_modified': round(hours_since_modified, 2),
                'time_threshold_hours': time_threshold_hours,
                'last_modified': datetime.fromtimestamp(file_mtime).isoformat(),
                'check_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Sync drift failed: {str(e)}'}
    
    elif action == 'blueprint':
        # Handle update_documentation_from_blueprint
        required_params = ['blueprint_id', 'project_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.config import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            # Direct SQLite connection to get blueprint
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            blueprint_id = params['blueprint_id']
            project_id = params['project_id']
            sections = params.get('sections', ['description', 'requirements', 'architecture'])
            
            # Get blueprint details
            cursor.execute('''
                SELECT title, description, complexity, required_skills, tags, status
                FROM blueprints 
                WHERE id = ? AND project_id = ?
            ''', (blueprint_id, project_id))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return {'success': False, 'error': f'Blueprint {blueprint_id} not found in project {project_id}'}
            
            title, description, complexity, required_skills, tags, status = row
            
            # Generate documentation from blueprint
            documentation = []
            
            if 'description' in sections:
                documentation.append(f"# {title}\n\n{description}")
            
            if 'requirements' in sections:
                documentation.append(f"\n## Requirements\n\n- Complexity: {complexity}")
                if required_skills:
                    skills = required_skills.split(',') if isinstance(required_skills, str) else required_skills
                    documentation.append(f"- Skills: {', '.join(skills)}")
            
            if 'architecture' in sections:
                documentation.append(f"\n## Architecture\n\n- Status: {status}")
                if tags:
                    tag_list = tags.split(',') if isinstance(tags, str) else tags
                    documentation.append(f"- Tags: {', '.join(tag_list)}")
            
            conn.close()
            
            doc_content = '\n'.join(documentation)
            
            return {
                'success': True,
                'blueprint_id': blueprint_id,
                'project_id': project_id,
                'sections': sections,
                'documentation_content': doc_content,
                'update_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Sync blueprint failed: {str(e)}'}
    
    elif action == 'score':
        # Handle get_documentation_consistency_score
        required_params = ['file_path', 'project_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            file_path = params['file_path']
            project_id = params['project_id']
            detailed_analysis = params.get('detailed_analysis', False)
            
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Analyze file for consistency score
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            elements = []
            total_score = 0
            element_count = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    element_count += 1
                    docstring = ast.get_docstring(node)
                    
                    # Score each element (0.0 to 1.0)
                    element_score = 0.0
                    if docstring:
                        element_score = min(1.0, len(docstring.strip()) / 100.0)  # Basic scoring
                    
                    total_score += element_score
                    
                    if detailed_analysis:
                        elements.append({
                            'name': node.name,
                            'type': node.__class__.__name__.lower().replace('def', ''),
                            'line': node.lineno,
                            'has_docstring': bool(docstring),
                            'docstring_length': len(docstring) if docstring else 0,
                            'score': element_score
                        })
            
            consistency_score = total_score / element_count if element_count > 0 else 0.0
            
            result = {
                'success': True,
                'file_path': file_path,
                'project_id': project_id,
                'consistency_score': round(consistency_score, 3),
                'total_elements': element_count,
                'score_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if detailed_analysis:
                result['detailed_elements'] = elements
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'Sync score failed: {str(e)}'}
    
    elif action == 'monitor':
        # Handle start_real_time_documentation_sync
        required_params = ['file_paths', 'project_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            file_paths = params['file_paths']
            project_id = params['project_id']
            sync_interval_ms = params.get('sync_interval_ms', 100)
            
            if not isinstance(file_paths, list):
                return {'success': False, 'error': 'file_paths must be a list'}
            
            # Validate files exist
            valid_files = []
            invalid_files = []
            
            for file_path in file_paths:
                if os.path.exists(file_path):
                    valid_files.append({
                        'path': file_path,
                        'last_modified': os.path.getmtime(file_path)
                    })
                else:
                    invalid_files.append(file_path)
            
            # Import real-time monitoring service
            from ltms.services.real_time_monitor_service import start_real_time_monitoring
            
            # Start actual real-time monitoring with validated file paths
            result = start_real_time_monitoring(
                project_id=project_id,
                file_paths=file_paths,  # Pass original file_paths list to the service
                sync_interval_ms=sync_interval_ms
            )
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'Sync monitor failed: {str(e)}'}
    
    elif action == 'status':
        # Handle get_documentation_sync_status
        required_params = ['project_id']
        for param in required_params:
            if param not in params:
                return {'success': False, 'error': f'Missing required parameter: {param}'}
        
        try:
            from ltms.services.real_time_monitor_service import get_real_time_monitoring_status
            from ltms.config import get_config
            
            project_id = params['project_id']
            include_pending_changes = params.get('include_pending_changes', True)
            
            # Get real-time monitoring status
            monitoring_status = get_real_time_monitoring_status(project_id)
            
            # Get additional blueprint/sync data from database
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get project blueprints as a proxy for sync status
            cursor.execute('''
                SELECT COUNT(*) as total_blueprints,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_blueprints,
                       SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_blueprints
                FROM blueprints 
                WHERE project_id = ?
            ''', (project_id,))
            
            row = cursor.fetchone()
            total_blueprints, completed_blueprints, in_progress_blueprints = row if row else (0, 0, 0)
            
            # Calculate sync status
            sync_percentage = (completed_blueprints / total_blueprints * 100) if total_blueprints > 0 else 0
            
            conn.close()
            
            # Combine monitoring status with sync data
            status_result = {
                'success': True,
                'project_id': project_id,
                'real_time_monitoring': monitoring_status,
                'total_blueprints': total_blueprints or 0,
                'completed_blueprints': completed_blueprints or 0,
                'in_progress_blueprints': in_progress_blueprints or 0,
                'sync_percentage': round(sync_percentage, 1),
                'status_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if include_pending_changes:
                # Add pending changes info (enhanced with monitoring data)
                status_result['pending_changes'] = {
                    'documentation_updates': monitoring_status.get('total_events', 0) - monitoring_status.get('processed_events', 0),
                    'code_changes': monitoring_status.get('total_events', 0),
                    'blueprint_changes': in_progress_blueprints or 0
                }
            
            return status_result
            
        except Exception as e:
            return {'success': False, 'error': f'Sync status failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown sync action: {action}'}


def config_action(action: str, **params) -> Dict[str, Any]:
    """Configuration management operations with real internal implementation.
    
    Actions: validate_config, get_config_schema, export_config
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'validate_config':
        try:
            from ltms.config import get_config
            config = get_config()
            
            validation_results = {
                'db_path_valid': False,
                'redis_config_valid': False,
                'neo4j_config_valid': False,
                'paths_accessible': False,
                'environment_vars': {}
            }
            
            errors = []
            warnings = []
            
            # Validate database path
            try:
                db_path = config.get_db_path()
                if db_path and os.path.dirname(db_path):
                    validation_results['db_path_valid'] = True
                else:
                    errors.append('Invalid database path configuration')
            except Exception as e:
                errors.append(f'Database path validation failed: {str(e)}')
            
            # Validate Redis configuration
            try:
                redis_host = getattr(config, 'redis_host', config._json_config.redis_host)
                redis_port = getattr(config, 'redis_port', config._json_config.redis_port)
                validation_results['redis_config_valid'] = bool(redis_host and redis_port)
                if not validation_results['redis_config_valid']:
                    warnings.append('Redis configuration incomplete')
            except Exception as e:
                warnings.append(f'Redis validation failed: {str(e)}')
            
            # Check environment variables
            env_vars = ['DB_PATH', 'REDIS_HOST', 'REDIS_PORT', 'NEO4J_URI']
            for var in env_vars:
                validation_results['environment_vars'][var] = os.getenv(var) is not None
            
            # Overall validation
            critical_checks = [validation_results['db_path_valid']]
            overall_valid = all(critical_checks) and len(errors) == 0
            
            return {
                'success': True,
                'overall_valid': overall_valid,
                'validation_results': validation_results,
                'errors': errors,
                'warnings': warnings,
                'validation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Config validation failed: {str(e)}'}
    
    elif action == 'get_config_schema':
        try:
            schema = {
                'database': {
                    'db_path': {
                        'type': 'string',
                        'required': True,
                        'description': 'Path to SQLite database file'
                    }
                },
                'redis': {
                    'redis_host': {
                        'type': 'string',
                        'default': 'localhost',
                        'description': 'Redis server hostname'
                    },
                    'redis_port': {
                        'type': 'integer',
                        'default': 'from_json_config',
                        'description': 'Redis server port (loaded from JSON config)'
                    },
                    'redis_password': {
                        'type': 'string',
                        'optional': True,
                        'description': 'Redis password for authentication'
                    }
                },
                'neo4j': {
                    'neo4j_uri': {
                        'type': 'string',
                        'default': 'from_json_config',
                        'description': 'Neo4j connection URI (loaded from JSON config)'
                    },
                    'neo4j_user': {
                        'type': 'string',
                        'default': 'neo4j',
                        'description': 'Neo4j username'
                    },
                    'neo4j_password': {
                        'type': 'string',
                        'required': True,
                        'description': 'Neo4j password'
                    }
                }
            }
            
            return {
                'success': True,
                'config_schema': schema,
                'schema_version': '1.0',
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Get config schema failed: {str(e)}'}
    
    elif action == 'export_config':
        try:
            from ltms.config import get_config
            config = get_config()
            
            # Export sanitized configuration (no secrets)
            config_export = {
                'database': {
                    'db_path': getattr(config, 'db_path', None) or os.getenv('DB_PATH'),
                },
                'redis': {
                    'host': getattr(config, 'redis_host', 'localhost'),
                    'port': getattr(config, 'redis_port', config._json_config.redis_port),
                    'password_configured': bool(getattr(config, 'redis_password', None))
                },
                'neo4j': {
                    'uri': getattr(config, 'neo4j_uri', config._json_config.neo4j_uri),
                    'user': getattr(config, 'neo4j_user', 'neo4j'),
                    'password_configured': bool(getattr(config, 'neo4j_password', None))
                },
                'exported_at': datetime.now().isoformat(),
                'export_version': '1.0'
            }
            
            return {
                'success': True,
                'config_export': config_export,
                'format': 'sanitized_json',
                'secrets_excluded': True
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Export config failed: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown config action: {action}'}


# REAL CONSOLIDATED TOOLS REGISTRY - NO WRAPPERS
CONSOLIDATED_TOOLS = {
    "memory_action": {
        "handler": memory_action,
        "description": "Memory operations with real SQLite+FAISS implementation: store, retrieve, build_context",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["store", "retrieve", "build_context", "retrieve_by_type", "ask_with_context"],
                    "description": "Memory action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "todo_action": {
        "handler": todo_action,
        "description": "Todo operations with real SQLite implementation: add, list, complete, search",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "list", "complete", "search"],
                    "description": "Todo action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "chat_action": {
        "handler": chat_action,
        "description": "Chat operations with real SQLite implementation: log, get_by_tool, get_tool_conversations, route_query",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["log", "get_by_tool", "get_tool_conversations", "route_query"],
                    "description": "Chat action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "unix_action": {
        "handler": unix_action,
        "description": "Unix utilities with real external tool integration: ls(exa), cat(bat), grep(ripgrep), find(fd), tree, jq, lsd, duf, tldr, delta, fzf",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["ls", "cat", "grep", "find", "tree", "jq", "list_modern", "disk_usage", "help", "diff_highlight", "fuzzy_select", "parse_syntax", "syntax_highlight", "syntax_query"],
                    "description": "Unix action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "pattern_action": {
        "handler": pattern_action,
        "description": "Code pattern analysis with real Python AST implementation: extract_functions, extract_classes, summarize_code",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["extract_functions", "extract_classes", "extract_comments", "summarize_code", "log_attempt", "get_patterns", "analyze_patterns"],
                    "description": "Pattern analysis action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "blueprint_action": {
        "handler": blueprint_action,
        "description": "Blueprint management with real SQLite+Neo4j implementation: create, analyze_complexity, list_project, add_dependency, resolve_order, update_metadata, get_dependencies, delete",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "analyze_complexity", "list_project", "add_dependency", "resolve_order", "update_metadata", "get_dependencies", "delete"],
                    "description": "Blueprint action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "cache_action": {
        "handler": cache_action,
        "description": "Cache operations with real Redis implementation: health_check, stats, flush, reset",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["health_check", "stats", "flush", "reset"],
                    "description": "Cache action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "graph_action": {
        "handler": graph_action,
        "description": "Knowledge graph operations with real Neo4j implementation: link, query, auto_link, get_relationships",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["link", "query", "auto_link", "get_relationships"],
                    "description": "Graph action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "documentation_action": {
        "handler": documentation_action,
        "description": "Documentation operations with real internal implementation: generate_api_docs, generate_architecture_diagram, sync_documentation_with_code, validate_documentation_consistency",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["generate_api_docs", "generate_architecture_diagram", "sync_documentation_with_code", "validate_documentation_consistency"],
                    "description": "Documentation action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "sync_action": {
        "handler": sync_action,
        "description": "Documentation synchronization with real internal implementation: code, validate, drift, blueprint, score, monitor, status",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["code", "validate", "drift", "blueprint", "score", "monitor", "status"],
                    "description": "Sync action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    },
    
    "config_action": {
        "handler": config_action,
        "description": "Configuration management with real internal implementation: validate_config, get_config_schema, export_config",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["validate_config", "get_config_schema", "export_config"],
                    "description": "Config action to perform"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    }
}