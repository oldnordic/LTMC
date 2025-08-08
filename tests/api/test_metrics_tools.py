"""TDD: Tool usage metrics endpoint counts and filters."""

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
    conn.commit()


def _seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    base = datetime.now()
    rows = [
        ("c1", "tool", "tools/call:list_todos", (base - timedelta(days=2)).isoformat(), "Cursor", '{"tool":"list_todos","arguments":{}}'),
        ("c1", "tool", "tools/call:store_memory", (base - timedelta(days=1)).isoformat(), "Cursor", '{"tool":"store_memory","arguments":{}}'),
        ("c2", "tool", "tools/call:list_todos", base.isoformat(), "Claude", '{"tool":"list_todos","arguments":{}}'),
    ]
    cur.executemany(
        "INSERT INTO ChatHistory (conversation_id, role, content, timestamp, agent_name, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def test_metrics_tools_counts_and_last_used():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path

    from ltms.mcp_server_http import app
    client = TestClient(app)

    conn = sqlite3.connect(db_path)
    _init_db(conn)
    _seed(conn)
    conn.close()

    resp = client.get("/api/v1/metrics/tools")
    assert resp.status_code == 200
    data = resp.json()
    tools = {t["tool"]: t for t in data.get("tools", [])}
    assert tools["list_todos"]["count"] == 2
    assert tools["store_memory"]["count"] == 1
    assert isinstance(tools["list_todos"]["last_used"], str)
    assert "Cursor" in tools["list_todos"]["agents"]


def test_metrics_tools_filters_by_agent_and_since():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path

    from ltms.mcp_server_http import app
    client = TestClient(app)

    conn = sqlite3.connect(db_path)
    _init_db(conn)
    _seed(conn)
    conn.close()

    # Use a window that includes store_memory (1 day ago) but excludes list_todos (2 days ago)
    since = (datetime.now() - timedelta(hours=36)).isoformat()
    resp = client.get("/api/v1/metrics/tools", params={"agent": "Cursor", "since": since})
    assert resp.status_code == 200
    data = resp.json()
    tools = {t["tool"]: t for t in data.get("tools", [])}
    # only Cursor since recent time should include store_memory (1) but not the older list_todos
    assert tools.get("store_memory", {}).get("count") == 1
    assert tools.get("list_todos", {}) == {}


