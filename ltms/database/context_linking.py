"""Context linking functionality for LTMC."""

import sqlite3
from typing import List, Dict, Any


def create_context_links_table(conn: sqlite3.Connection) -> None:
    """Create the ContextLinks table if it doesn't exist.
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ContextLinks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id INTEGER,
        chunk_id INTEGER,
        FOREIGN KEY (message_id) REFERENCES ChatHistory (id),
        FOREIGN KEY (chunk_id) REFERENCES ResourceChunks (id)
    )''')
    conn.commit()


def store_context_links(
    conn: sqlite3.Connection, 
    message_id: int, 
    chunk_ids: List[int]
) -> Dict[str, Any]:
    """Store context links between a message and the chunks it used.
    
    Args:
        conn: SQLite database connection
        message_id: ID of the chat message
        chunk_ids: List of chunk IDs that were used to answer the message
        
    Returns:
        Dictionary with success status and number of links created
    """
    try:
        cursor = conn.cursor()
        
        # Verify message exists
        cursor.execute(
            "SELECT id FROM ChatHistory WHERE id = ?",
            (message_id,)
        )
        if not cursor.fetchone():
            return {
                "success": False,
                "error": f"Message with id {message_id} does not exist"
            }
        
        # Verify chunks exist
        for chunk_id in chunk_ids:
            cursor.execute(
                "SELECT id FROM ResourceChunks WHERE id = ?",
                (chunk_id,)
            )
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"Chunk with id {chunk_id} does not exist"
                }
        
        # Store context links
        links_created = 0
        for chunk_id in chunk_ids:
            cursor.execute(
                "INSERT INTO ContextLinks (message_id, chunk_id) VALUES (?, ?)",
                (message_id, chunk_id)
            )
            links_created += 1
        
        conn.commit()
        
        return {
            "success": True,
            "links_created": links_created,
            "message_id": message_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_context_links_for_message(
    conn: sqlite3.Connection, 
    message_id: int
) -> Dict[str, Any]:
    """Get all context links for a specific message.
    
    Args:
        conn: SQLite database connection
        message_id: ID of the chat message
        
    Returns:
        Dictionary with success status and list of context links
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT chunk_id FROM ContextLinks WHERE message_id = ?",
            (message_id,)
        )
        
        links = []
        for row in cursor.fetchall():
            links.append({
                "message_id": message_id,
                "chunk_id": row[0]
            })
        
        return {
            "success": True,
            "links": links,
            "count": len(links)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_messages_for_chunk(
    conn: sqlite3.Connection, 
    chunk_id: int
) -> Dict[str, Any]:
    """Get all messages that used a specific chunk.
    
    Args:
        conn: SQLite database connection
        chunk_id: ID of the chunk
        
    Returns:
        Dictionary with success status and list of messages
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT cl.message_id, ch.conversation_id, ch.role, ch.content, 
                      ch.timestamp 
               FROM ContextLinks cl
               JOIN ChatHistory ch ON cl.message_id = ch.id
               WHERE cl.chunk_id = ?""",
            (chunk_id,)
        )
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "message_id": row[0],
                "conversation_id": row[1],
                "role": row[2],
                "content": row[3],
                "timestamp": row[4]
            })
        
        return {
            "success": True,
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_context_usage_statistics(
    conn: sqlite3.Connection
) -> Dict[str, Any]:
    """Get statistics about context usage.
    
    Args:
        conn: SQLite database connection
        
    Returns:
        Dictionary with usage statistics
    """
    try:
        cursor = conn.cursor()
        
        # Total context links
        cursor.execute("SELECT COUNT(*) FROM ContextLinks")
        total_links = cursor.fetchone()[0]
        
        # Unique messages that used context
        cursor.execute("SELECT COUNT(DISTINCT message_id) FROM ContextLinks")
        unique_messages = cursor.fetchone()[0]
        
        # Unique chunks that were used
        cursor.execute("SELECT COUNT(DISTINCT chunk_id) FROM ContextLinks")
        unique_chunks = cursor.fetchone()[0]
        
        # Most used chunks
        cursor.execute(
            """SELECT chunk_id, COUNT(*) as usage_count 
               FROM ContextLinks 
               GROUP BY chunk_id 
               ORDER BY usage_count DESC 
               LIMIT 10"""
        )
        most_used_chunks = [
            {"chunk_id": row[0], "usage_count": row[1]}
            for row in cursor.fetchall()
        ]
        
        return {
            "success": True,
            "statistics": {
                "total_context_links": total_links,
                "unique_messages": unique_messages,
                "unique_chunks_used": unique_chunks,
                "most_used_chunks": most_used_chunks
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def delete_context_links_for_message(
    conn: sqlite3.Connection, 
    message_id: int
) -> Dict[str, Any]:
    """Delete all context links for a specific message.
    
    Args:
        conn: SQLite database connection
        message_id: ID of the chat message
        
    Returns:
        Dictionary with success status and number of links deleted
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM ContextLinks WHERE message_id = ?",
            (message_id,)
        )
        
        links_deleted = cursor.rowcount
        conn.commit()
        
        return {
            "success": True,
            "links_deleted": links_deleted,
            "message_id": message_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
