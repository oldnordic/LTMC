"""TDD: TTL and archival filtering for /api/v1/context retrieval."""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta
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
    conn.commit()


def _seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    base = datetime.now()
    rows = [
        ("old.txt", (base - timedelta(days=400)).isoformat(), 0, "old content"),
        ("mid.txt", (base - timedelta(days=150)).isoformat(), 0, "mid content"),
        ("new.txt", (base - timedelta(days=10)).isoformat(), 0, "new content"),
        ("archived.txt", (base - timedelta(days=5)).isoformat(), 1, "archived content"),
    ]
    for idx, (fname, c_at, archived, text) in enumerate(rows):
        cur.execute(
            "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
            (fname, "document", c_at),
        )
        res_id = cur.lastrowid
        cur.execute(
            (
                "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id, archived) "
                "VALUES (?, ?, ?, ?)"
            ),
            (res_id, text, idx, archived),
        )
    conn.commit()


def test_context_respects_ttl_and_excludes_archived():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path
    # force DB fallback path
    os.environ["FAISS_INDEX_PATH"] = db_path + ".faiss.missing"

    from ltms.mcp_server_http import app

    conn = sqlite3.connect(db_path)
    _init_db(conn)
    _seed(conn)
    conn.close()

    client = TestClient(app)
    # max_age_days=200 should include mid/new, exclude old; also exclude archived
    resp = client.get(
        "/api/v1/context",
        params={"conversation_id": "c1", "query": "q", "top_k": 10, "max_age_days": 200},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    titles = [it["title"] for it in data.get("items", [])]
    assert "old.txt" not in titles
    assert "archived.txt" not in titles
    assert "mid.txt" in titles and "new.txt" in titles


