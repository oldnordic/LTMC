"""TDD: SSE streaming for /api/v1/context and JSON fallback."""

import os
import sys
import tempfile
import sqlite3
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
            FOREIGN KEY(resource_id) REFERENCES Resources(id)
        )
        """
    )
    conn.commit()


def _seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Three resources with increasing recency
    for idx, (fname, date) in enumerate(
        [
            ("a.txt", "2024-01-01T00:00:00"),
            ("b.txt", "2024-06-01T00:00:00"),
            ("c.txt", "2025-01-01T00:00:00"),
        ]
    ):
        cur.execute(
            "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
            (fname, "document", date),
        )
        res_id = cur.lastrowid
        cur.execute(
            (
                "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) "
                "VALUES (?, ?, ?)"
            ),
            (res_id, f"content {idx}", idx),
        )
    conn.commit()


def test_context_sse_streams_events():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path
    os.environ["FAISS_INDEX_PATH"] = db_path + ".faiss.missing"

    from ltms.mcp_server_http import app

    # Prepare DB
    conn = sqlite3.connect(db_path)
    _init_db(conn)
    _seed(conn)
    conn.close()

    client = TestClient(app)
    resp = client.get(
        "/api/v1/context",
        params={"conversation_id": "conv1", "query": "hello", "top_k": 3, "transport": "sse"},
        headers={"Accept": "text/event-stream"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")
    body = resp.text
    # Expect multiple SSE data lines
    assert body.count("data:") >= 2


def test_context_json_returns_items():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path
    os.environ["FAISS_INDEX_PATH"] = db_path + ".faiss.missing"

    from ltms.mcp_server_http import app

    # Prepare DB
    conn = sqlite3.connect(db_path)
    _init_db(conn)
    _seed(conn)
    conn.close()

    client = TestClient(app)
    resp = client.get(
        "/api/v1/context",
        params={"conversation_id": "conv1", "query": "hello", "top_k": 2},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    assert isinstance(data.get("items"), list)
    assert len(data["items"]) >= 2


