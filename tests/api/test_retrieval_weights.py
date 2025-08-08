"""TDD: Retrieval ranking weights GET/POST endpoints."""

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
    # ensure schema create does not fail
    cur.execute("CREATE TABLE IF NOT EXISTS Resources (id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT, type TEXT NOT NULL, created_at TEXT NOT NULL)")
    conn.commit()


def test_get_retrieval_weights_defaults():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path

    from ltms.mcp_server_http import app
    client = TestClient(app)

    conn = sqlite3.connect(db_path)
    _init_db(conn)
    conn.close()

    resp = client.get("/api/v1/retrieval/weights")
    assert resp.status_code == 200
    data = resp.json()
    for k in ("alpha", "beta", "gamma", "delta", "epsilon"):
        assert k in data


def test_post_retrieval_weights_updates():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path

    from ltms.mcp_server_http import app
    client = TestClient(app)

    payload = {"alpha": 0.5, "beta": 1.2, "gamma": 0.0, "delta": 0.0, "epsilon": 0.0}
    resp = client.post("/api/v1/retrieval/weights", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

    resp2 = client.get("/api/v1/retrieval/weights")
    cfg = resp2.json()
    assert cfg["alpha"] == 0.5 and cfg["beta"] == 1.2


