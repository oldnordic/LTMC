"""TDD: Changing retrieval weights affects ranking order."""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def _seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            type TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
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
    # Two docs, different recency
    cur.execute(
        "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
        ("older.txt", "document", "2024-01-01T00:00:00"),
    )
    older_id = cur.lastrowid
    cur.execute(
        "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
        (older_id, "older content", 1),
    )
    cur.execute(
        "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
        ("newer.txt", "document", "2025-01-01T00:00:00"),
    )
    newer_id = cur.lastrowid
    cur.execute(
        "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) VALUES (?, ?, ?)",
        (newer_id, "newer content", 2),
    )
    conn.commit()


def test_weight_changes_ranking_order_db_fallback():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path
    # Make sure FAISS path is nonexistent to trigger DB fallback
    os.environ["FAISS_INDEX_PATH"] = db_path + ".faiss"
    if os.path.exists(os.environ["FAISS_INDEX_PATH"]):
        os.remove(os.environ["FAISS_INDEX_PATH"])

    conn = sqlite3.connect(db_path)
    _seed(conn)
    conn.close()

    from ltms.mcp_server_http import app
    client = TestClient(app)

    # Set beta high (recency importance high)
    resp = client.post(
        "/api/v1/retrieval/weights",
        json={"alpha": 0.0, "beta": 1.0, "gamma": 0.0, "delta": 0.0, "epsilon": 0.0},
    )
    assert resp.status_code == 200

    # Query context via HTTP which internally calls retrieve_with_metadata
    resp2 = client.get(
        "/api/v1/context",
        params={"conversation_id": "w1", "query": "x", "top_k": 2},
    )
    assert resp2.status_code == 200
    items = resp2.json().get("items", [])
    assert len(items) >= 2
    titles = [it["title"] for it in items[:2]]
    assert titles[0] == "newer.txt"


