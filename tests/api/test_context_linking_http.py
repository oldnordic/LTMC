"""TDD: HTTP /api/v1/context logs chat and stores context links."""

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


def _init_db(conn: sqlite3.Connection) -> None:
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
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ChatHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            agent_name TEXT,
            metadata TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ContextLinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            chunk_id INTEGER
        )
        """
    )
    conn.commit()


def _seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
        ("doc.txt", "document", "2025-01-01T00:00:00"),
    )
    res_id = cur.lastrowid
    for i in range(3):
        cur.execute(
            (
                "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) "
                "VALUES (?, ?, ?)"
            ),
            (res_id, f"chunk {i}", i),
        )
    conn.commit()


def test_http_context_creates_chat_and_links():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path
    os.environ["FAISS_INDEX_PATH"] = db_path + ".faiss.missing"

    from ltms.mcp_server_http import app
    client = TestClient(app)

    conn = sqlite3.connect(db_path)
    _init_db(conn)
    _seed(conn)
    conn.close()

    resp = client.get(
        "/api/v1/context",
        params={"conversation_id": "convZ", "query": "q", "top_k": 2},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM ChatHistory WHERE conversation_id = ? ORDER BY id DESC LIMIT 1",
        ("convZ",),
    )
    row = cur.fetchone()
    assert row is not None
    message_id = row[0]
    cur.execute(
        "SELECT COUNT(*) FROM ContextLinks WHERE message_id = ?",
        (message_id,),
    )
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 1


