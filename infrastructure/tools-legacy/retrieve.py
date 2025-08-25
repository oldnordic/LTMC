"""Retrieve relevant vectors and documents from FAISS + SQLite."""

from typing import List, Tuple, Optional, Dict, Any
import sqlite3
import os
from datetime import datetime, timedelta

from sentence_transformers import SentenceTransformer

# Handle import path for different execution contexts
try:
    from core.config import settings  # noqa: F401
except ImportError:
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from core.config import settings  # type: ignore  # noqa: F401

# Default environment variables (used as fallbacks).
# Actual paths are read at call time.
DEFAULT_DB_PATH = os.getenv("DB_PATH", "ltmc.db")
DEFAULT_FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Initialize embedding model
embedding_model = SentenceTransformer(EMBEDDING_MODEL)


def _column_exists(
    connection: sqlite3.Connection, table_name: str, column_name: str
) -> bool:
    """Return True if a column exists in the given table."""
    try:
        cur = connection.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        for _, name, *_ in cur.fetchall():
            if name == column_name:
                return True
    except Exception:
        return False
    return False


def _load_weights_from_db(connection: sqlite3.Connection) -> Dict[str, float]:
    """Load retrieval weights from DB, falling back to sensible defaults.

    Returns a mapping with keys: alpha, beta, gamma, delta, epsilon.
    """
    defaults = {"alpha": 1.0, "beta": 0.2, "gamma": 0.1, "delta": 0.05, "epsilon": 0.1}
    try:
        cur = connection.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS RetrievalWeights ("
            "id INTEGER PRIMARY KEY CHECK (id = 1), "
            "alpha REAL, beta REAL, gamma REAL, delta REAL, epsilon REAL)"
        )
        cur.execute(
            "SELECT alpha, beta, gamma, delta, epsilon FROM RetrievalWeights "
            "WHERE id = 1"
        )
        row = cur.fetchone()
        if not row:
            cur.execute(
                "INSERT INTO RetrievalWeights (id, alpha, beta, gamma, delta, "
                "epsilon) VALUES (1, ?, ?, ?, ?, ?)",
                (
                    defaults["alpha"],
                    defaults["beta"],
                    defaults["gamma"],
                    defaults["delta"],
                    defaults["epsilon"],
                ),
            )
            connection.commit()
            return defaults
        a, b, g, d, e = row
        return {
            "alpha": float(a),
            "beta": float(b),
            "gamma": float(g),
            "delta": float(d),
            "epsilon": float(e),
        }
    except Exception:
        return defaults


def _normalize_recency_iso8601(created_at_iso: str) -> float:
    """Normalize recency based on created_at timestamp to [0, 1]. Newer → closer to 1.

    Uses linear scaling over a 90-day window for stability. Older than window → 0.
    """
    try:
        now = datetime.now()
        created = datetime.fromisoformat(created_at_iso)
        delta = now - created
        window_days = 90.0
        score = max(0.0, 1.0 - min(delta.days, window_days) / window_days)
        return float(score)
    except Exception:
        return 0.0


def retrieve_similar(
    query: str,
    top_k: int = 5,
    source_filter: Optional[List[str]] = None,
) -> List[Tuple[str, str]]:
    """Return (title, content) tuples of top-k matches using FAISS."""
    try:
        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        faiss_index_path = os.getenv(
            "FAISS_INDEX_PATH", DEFAULT_FAISS_INDEX_PATH
        )
        # Get query embedding
        query_vector = embedding_model.encode([query])[0]
        
        # Load FAISS index
        try:
            import importlib
            from typing import Any as _Any
            faiss: _Any = importlib.import_module("faiss")
        except Exception:
            print("FAISS not available, returning empty results")
            return []
        if os.path.exists(faiss_index_path):
            index = faiss.read_index(faiss_index_path)
            
            # Search for similar vectors
            query_vector_reshaped = query_vector.reshape(1, -1)
            _, indices = index.search(query_vector_reshaped, top_k)
            
            # Get database connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT,
                    type TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ResourceChunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_id INTEGER,
                    chunk_text TEXT NOT NULL,
                    vector_id INTEGER UNIQUE NOT NULL,
                    archived INTEGER DEFAULT 0,
                    FOREIGN KEY(resource_id) REFERENCES Resources(id)
                )
                """
            )
            
            results = []
            for i, vector_id in enumerate(indices[0]):
                if vector_id == -1:  # No more results
                    break
                    
                # Get chunk details from database
                cursor.execute(
                    "SELECT rc.chunk_text, r.file_name, r.type FROM ResourceChunks rc "
                    "JOIN Resources r ON rc.resource_id = r.id "
                    "WHERE rc.vector_id = ?",
                    (int(vector_id),)
                )
                row = cursor.fetchone()
                
                if row:
                    chunk_text, file_name, doc_type = row
                    
                    # Filter by source if specified
                    if source_filter and doc_type not in source_filter:
                        continue
                    
                    results.append((file_name, chunk_text))
            
            conn.close()
            return results[:top_k]
        else:
            # No FAISS index exists, return empty results
            return []
        
    except Exception as e:
        print(f"Error in retrieve_similar: {e}")
        return []


def retrieve_with_metadata(
    query: str,
    top_k: int = 5,
    source_filter: Optional[List[str]] = None,
    max_age_days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return documents with metadata; FAISS if available else DB fallback.

    Hybrid ranking uses similarity as primary with recency as tie-breaker.
    """
    try:
        # Get query embedding
        query_vector = embedding_model.encode([query])[0]
        
        # Load FAISS index
        try:
            import importlib
            from typing import Any as _Any
            faiss: _Any = importlib.import_module("faiss")
            has_faiss = True
        except Exception:
            has_faiss = False

        db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
        faiss_index_path = os.getenv(
            "FAISS_INDEX_PATH", DEFAULT_FAISS_INDEX_PATH
        )
        if has_faiss and os.path.exists(faiss_index_path):
            index = faiss.read_index(faiss_index_path)
            
            # Search for similar vectors
            query_vector_reshaped = query_vector.reshape(1, -1)
            distances, indices = index.search(query_vector_reshaped, top_k)
            
            # Get database connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''CREATE TABLE IF NOT EXISTS Resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                type TEXT NOT NULL,
                created_at TEXT NOT NULL
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS ResourceChunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER,
                chunk_text TEXT NOT NULL,
                vector_id INTEGER UNIQUE NOT NULL,
                FOREIGN KEY(resource_id) REFERENCES Resources(id)
            )''')
            
            results_with_metadata: List[Dict[str, Any]] = []
            # Load weights once per request
            weights = _load_weights_from_db(conn)

            for i, vector_id in enumerate(indices[0]):
                if vector_id == -1:  # No more results
                    break
                    
                # Get chunk details from database
                if _column_exists(conn, "ResourceChunks", "archived"):
                    cursor.execute(
                        "SELECT rc.chunk_text, r.file_name, r.type, r.created_at, "
                        "rc.id, rc.archived FROM ResourceChunks rc JOIN Resources r "
                        "ON rc.resource_id = r.id WHERE rc.vector_id = ?",
                        (int(vector_id),),
                    )
                else:
                    cursor.execute(
                        "SELECT rc.chunk_text, r.file_name, r.type, r.created_at, rc.id, "
                        "0 as archived FROM ResourceChunks rc JOIN Resources r "
                        "ON rc.resource_id = r.id WHERE rc.vector_id = ?",
                        (int(vector_id),),
                    )
                row = cursor.fetchone()
                
                if row:
                    chunk_text, file_name, doc_type, created_at, chunk_id, archived = row
                    
                    # Filter by source if specified
                    if source_filter and doc_type not in source_filter:
                        continue
                    # Exclude archived
                    if archived:
                        continue
                    # Exclude older than TTL if provided
                    if max_age_days is not None:
                        try:
                            cutoff = datetime.now() - timedelta(days=max_age_days)
                            if created_at < cutoff.isoformat():
                                continue
                        except Exception:
                            pass
                    
                    # Calculate similarity score (inverse of distance)
                    distance = float(distances[0][i])
                    similarity = 1.0 / (1.0 + distance)
                    recency = _normalize_recency_iso8601(created_at)
                    combined = (
                        weights["alpha"] * similarity + weights["beta"] * recency
                    )
                    
                    results_with_metadata.append({
                        "id": f"chunk-{chunk_id}",
                        "title": file_name,
                        "content": chunk_text,
                        "type": doc_type,
                        "created_at": created_at,
                        "metadata": {
                            "source": "faiss",
                            "similarity": similarity,
                            "recency": recency,
                            "weights": weights,
                        },
                        "score": combined
                    })
            
            # Hybrid ranking: by combined score (weights applied)
            def sort_key(item: Dict[str, Any]):
                return -float(item.get("score", 0.0))

            results_with_metadata.sort(key=sort_key)
            conn.close()
            return results_with_metadata
        else:
            # Fallback: no FAISS; return most recent chunks (optionally filtered)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Ensure tables exist with archived column for filtering if possible
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT,
                    type TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ResourceChunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_id INTEGER,
                    chunk_text TEXT NOT NULL,
                    vector_id INTEGER UNIQUE NOT NULL,
                    archived INTEGER DEFAULT 0,
                    FOREIGN KEY(resource_id) REFERENCES Resources(id)
                )
                """
            )

            has_archived = _column_exists(conn, "ResourceChunks", "archived")
            if max_age_days is not None:
                if has_archived:
                    cursor.execute(
                        """
                        SELECT rc.id, rc.chunk_text, r.file_name, r.type, r.created_at
                        FROM ResourceChunks rc
                        JOIN Resources r ON rc.resource_id = r.id
                        WHERE rc.archived = 0 AND r.created_at >= ?
                        ORDER BY r.created_at DESC
                        LIMIT ?
                        """,
                        (
                            (datetime.now() - timedelta(days=max_age_days)).isoformat(),
                            top_k,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT rc.id, rc.chunk_text, r.file_name, r.type, r.created_at
                        FROM ResourceChunks rc
                        JOIN Resources r ON rc.resource_id = r.id
                        WHERE r.created_at >= ?
                        ORDER BY r.created_at DESC
                        LIMIT ?
                        """,
                        (
                            (datetime.now() - timedelta(days=max_age_days)).isoformat(),
                            top_k,
                        ),
                    )
            else:
                if has_archived:
                    cursor.execute(
                        """
                        SELECT rc.id, rc.chunk_text, r.file_name, r.type, r.created_at
                        FROM ResourceChunks rc
                        JOIN Resources r ON rc.resource_id = r.id
                        WHERE rc.archived = 0
                        ORDER BY r.created_at DESC
                        LIMIT ?
                        """,
                        (top_k,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT rc.id, rc.chunk_text, r.file_name, r.type, r.created_at
                        FROM ResourceChunks rc
                        JOIN Resources r ON rc.resource_id = r.id
                        ORDER BY r.created_at DESC
                        LIMIT ?
                        """,
                        (top_k,),
                    )
            rows = cursor.fetchall()
            weights = _load_weights_from_db(conn)
            results: List[Dict[str, Any]] = []
            for row in rows:
                chunk_id, chunk_text, file_name, doc_type, created_at = row
                if source_filter and doc_type not in source_filter:
                    continue
                recency = _normalize_recency_iso8601(created_at)
                combined = weights["beta"] * recency
                results.append({
                    "id": f"chunk-{chunk_id}",
                    "title": file_name,
                    "content": chunk_text,
                    "type": doc_type,
                    "created_at": created_at,
                    "metadata": {"source": "db", "recency": recency, "weights": weights},
                    "score": combined,
                })
            conn.close()
            # Already ordered by created_at DESC, but ensure consistency with score
            results.sort(key=lambda it: -float(it.get("score", 0.0)))
            return results
        
    except Exception as e:
        print(f"Error in retrieve_with_metadata: {e}")
        return []


def retrieve_by_type(query: str, doc_type: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve documents of a specific type (document, code, chat, todo) using real FAISS."""
    return retrieve_with_metadata(query, top_k, source_filter=[doc_type])


def retrieve_all_types(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve documents from all types using real FAISS."""
    return retrieve_with_metadata(query, top_k, source_filter=None)
