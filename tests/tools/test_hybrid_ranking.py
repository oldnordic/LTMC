"""TDD: Hybrid ranking retrieves and orders by recency when similarity ties."""

import os
import sys
import tempfile
from pathlib import Path
import sqlite3
import numpy as np


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def _init_db(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
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
            FOREIGN KEY(resource_id) REFERENCES Resources(id)
        )
        """
    )
    conn.commit()


def test_hybrid_ranking_prefers_recent_when_similarity_equal():
    _ensure_project_root_on_path()
    # temp DB and FAISS index paths
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    index_path = db_path + ".faiss"

    # Set env so retrieve module picks them up
    os.environ["DB_PATH"] = db_path
    os.environ["FAISS_INDEX_PATH"] = index_path
    from tools import retrieve as r

    # Ensure FAISS fallback by pointing to non-existent index path
    if os.path.exists(index_path):
        os.remove(index_path)

    # Prepare DB with 2 chunks having same vector_ids: 0 and 1
    conn = sqlite3.connect(db_path)
    _init_db(conn)
    cur = conn.cursor()
    # Older doc
    cur.execute(
        "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
        ("old.txt", "document", "2024-01-01T00:00:00"),
    )
    old_res_id = cur.lastrowid
    cur.execute(
        (
            "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) "
            "VALUES (?, ?, ?)"
        ),
        (old_res_id, "old content", 0),
    )
    # Newer doc
    cur.execute(
        "INSERT INTO Resources (file_name, type, created_at) VALUES (?, ?, ?)",
        ("new.txt", "document", "2025-01-01T00:00:00"),
    )
    new_res_id = cur.lastrowid
    cur.execute(
        (
            "INSERT INTO ResourceChunks (resource_id, chunk_text, vector_id) "
            "VALUES (?, ?, ?)"
        ),
        (new_res_id, "new content", 1),
    )
    conn.commit()
    conn.close()

    # No need to embed for fallback path

    # Call retrieve_with_metadata and expect newer file first
    results = r.retrieve_with_metadata("query", top_k=2)
    assert len(results) >= 2
    # Titles should be ordered by recency
    titles = [item["title"] for item in results[:2]]
    assert titles[0] == "new.txt"
