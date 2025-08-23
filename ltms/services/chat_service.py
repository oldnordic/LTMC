"""Chat and conversation management service for LTMC."""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

from ltms.config import get_config
from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables
from ltms.services.context_service import get_context_for_query, log_chat_message


def log_chat(
    conversation_id: str, 
    role: str, 
    content: str, 
    agent_name: Optional[str] = None, 
    metadata: Optional[Dict[str, Any]] = None, 
    source_tool: Optional[str] = None
) -> Dict[str, Any]:
    """Log a chat message with automatic context linking.
    
    Args:
        conversation_id: Unique identifier for the conversation
        role: Role of the message sender ('user', 'ai', 'system')
        content: Message content
        agent_name: Name of the agent if applicable
        metadata: Optional metadata dictionary
        source_tool: Tool that generated this message
        
    Returns:
        Dictionary with success status and message_id
    """
    if not conversation_id or not role or not content:
        return {
            'success': False,
            'error': 'conversation_id, role, and content are required'
        }
    
    if role not in ['user', 'ai', 'system']:
        return {
            'success': False,
            'error': 'role must be one of: user, ai, system'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        # Ensure tables exist
        create_tables(conn)
        
        # Log the message
        message_id = log_chat_message(
            conn=conn,
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_name=agent_name,
            metadata=metadata,
            source_tool=source_tool
        )
        
        return {
            'success': True,
            'message_id': message_id,
            'conversation_id': conversation_id,
            'message': f'Chat message logged for {conversation_id}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def ask_with_context(query: str, conversation_id: str, top_k: int = 5) -> Dict[str, Any]:
    """Ask a question with relevant context from memory.
    
    This function combines query processing with context retrieval:
    1. Retrieve relevant context using vector search
    2. Log the query as a chat message
    3. Return both the context and query information
    
    Args:
        query: User's question
        conversation_id: ID of the conversation
        top_k: Number of context chunks to retrieve
        
    Returns:
        Dictionary with context, retrieved chunks, and query information
    """
    if not query or not conversation_id:
        return {
            'success': False,
            'error': 'query and conversation_id are required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        # Get FAISS index path
        config = get_config()
        index_path = config.get_faiss_index_path()
        
        # Use the existing context service to get context
        context_result = get_context_for_query(
            conn=conn,
            index_path=index_path,
            conversation_id=conversation_id,
            query=query,
            top_k=top_k
        )
        
        if not context_result['success']:
            return context_result
        
        return {
            'success': True,
            'query': query,
            'context': context_result['context'],
            'retrieved_chunks': context_result['retrieved_chunks'],
            'conversation_id': conversation_id,
            'message': f'Retrieved {len(context_result["retrieved_chunks"])} context chunks'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def route_query(query: str, source_types: Optional[List[str]] = None, top_k: int = 5) -> Dict[str, Any]:
    """Route a query to the most appropriate context or tool.
    
    This function analyzes a query and finds the best matching content
    from available sources, optionally filtered by source type.
    
    Args:
        query: Query to route
        source_types: Optional list of resource types to search ('document', 'code', etc.)
        top_k: Number of results to return
        
    Returns:
        Dictionary with routing results and recommendations
    """
    if not query:
        return {
            'success': False,
            'error': 'query is required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        # If source types specified, search within those types
        if source_types:
            from ltms.services.memory_service import search_memory_by_type
            
            all_results = []
            for source_type in source_types:
                type_results = search_memory_by_type(query, source_type, top_k)
                if type_results['success'] and type_results['retrieved_chunks']:
                    for chunk in type_results['retrieved_chunks']:
                        chunk['source_type_filter'] = source_type
                    all_results.extend(type_results['retrieved_chunks'])
            
            # Sort by score and limit
            all_results.sort(key=lambda x: x['score'], reverse=True)
            all_results = all_results[:top_k]
            
            return {
                'success': True,
                'query': query,
                'routed_chunks': all_results,
                'source_types_searched': source_types,
                'total_found': len(all_results),
                'routing_strategy': 'filtered_by_type'
            }
        
        else:
            # Search all available content
            from ltms.services.memory_service import retrieve_memory
            
            memory_results = retrieve_memory(
                conversation_id="routing_query",  # Special conversation for routing
                query=query,
                top_k=top_k
            )
            
            if not memory_results['success']:
                return memory_results
            
            return {
                'success': True,
                'query': query,
                'routed_chunks': memory_results['retrieved_chunks'],
                'context': memory_results.get('context', ''),
                'total_found': memory_results.get('total_found', 0),
                'routing_strategy': 'general_search'
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def get_chats_by_tool(source_tool: str, limit: int = 10) -> Dict[str, Any]:
    """Get chat messages by source tool.
    
    Args:
        source_tool: Name of the source tool to filter by
        limit: Maximum number of messages to return
        
    Returns:
        Dictionary with chat messages from the specified tool
    """
    if not source_tool:
        return {
            'success': False,
            'error': 'source_tool is required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, conversation_id, role, content, timestamp, agent_name, metadata, source_tool
            FROM chat_history
            WHERE source_tool = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (source_tool, limit)
        )
        
        rows = cursor.fetchall()
        
        chat_messages = []
        for row in rows:
            message_id, conversation_id, role, content, timestamp, agent_name, metadata_json, tool = row
            
            # Parse metadata if present
            metadata = None
            if metadata_json:
                try:
                    metadata = json.loads(metadata_json)
                except json.JSONDecodeError:
                    metadata = None
            
            chat_messages.append({
                'message_id': message_id,
                'conversation_id': conversation_id,
                'role': role,
                'content': content,
                'timestamp': timestamp,
                'agent_name': agent_name,
                'metadata': metadata,
                'source_tool': tool
            })
        
        return {
            'success': True,
            'chat_messages': chat_messages,
            'source_tool': source_tool,
            'total_found': len(chat_messages),
            'limit_applied': limit
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def get_conversation_history(conversation_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get full conversation history for a conversation ID.
    
    Args:
        conversation_id: ID of the conversation
        limit: Maximum number of messages to return
        
    Returns:
        Dictionary with conversation history
    """
    if not conversation_id:
        return {
            'success': False,
            'error': 'conversation_id is required'
        }
    
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, conversation_id, role, content, timestamp, agent_name, metadata, source_tool
            FROM chat_history
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
            """,
            (conversation_id, limit)
        )
        
        rows = cursor.fetchall()
        
        chat_messages = []
        for row in rows:
            message_id, conv_id, role, content, timestamp, agent_name, metadata_json, tool = row
            
            # Parse metadata if present
            metadata = None
            if metadata_json:
                try:
                    metadata = json.loads(metadata_json)
                except json.JSONDecodeError:
                    metadata = None
            
            chat_messages.append({
                'message_id': message_id,
                'conversation_id': conv_id,
                'role': role,
                'content': content,
                'timestamp': timestamp,
                'agent_name': agent_name,
                'metadata': metadata,
                'source_tool': tool
            })
        
        return {
            'success': True,
            'chat_messages': chat_messages,
            'conversation_id': conversation_id,
            'total_found': len(chat_messages),
            'limit_applied': limit
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)


def get_recent_conversations(days: int = 7, limit: int = 10) -> Dict[str, Any]:
    """Get list of recent conversations.
    
    Args:
        days: Number of days to look back
        limit: Maximum number of conversations to return
        
    Returns:
        Dictionary with recent conversation summaries
    """
    conn = None
    try:
        # Get database connection
        config = get_config()
        db_path = config.get_db_path()
        conn = get_db_connection(db_path)
        
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT conversation_id, 
                   COUNT(*) as message_count,
                   MIN(timestamp) as first_message,
                   MAX(timestamp) as last_message,
                   GROUP_CONCAT(DISTINCT source_tool) as tools_used
            FROM chat_history
            WHERE datetime(timestamp) >= datetime('now', '-{} days')
            GROUP BY conversation_id
            ORDER BY last_message DESC
            LIMIT ?
            """.format(days),
            (limit,)
        )
        
        rows = cursor.fetchall()
        
        conversations = []
        for row in rows:
            conv_id, msg_count, first_msg, last_msg, tools = row
            
            conversations.append({
                'conversation_id': conv_id,
                'message_count': msg_count,
                'first_message_time': first_msg,
                'last_message_time': last_msg,
                'tools_used': tools.split(',') if tools else []
            })
        
        return {
            'success': True,
            'conversations': conversations,
            'days_searched': days,
            'total_found': len(conversations)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if conn:
            close_db_connection(conn)