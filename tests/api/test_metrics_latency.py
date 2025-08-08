"""TDD: Tool latency metrics endpoint aggregates latency_ms from metadata."""

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
    now = datetime.now()
    rows = [
        ("c1", "tool", "tools/call:list_todos", now.isoformat(), "Cursor", '{"tool":"list_todos","latency_ms":120}'),
        ("c1", "tool", "tools/call:list_todos", (now - timedelta(minutes=1)).isoformat(), "Cursor", '{"tool":"list_todos","latency_ms":80}'),
        ("c1", "tool", "tools/call:store_memory", (now - timedelta(minutes=2)).isoformat(), "Claude", '{"tool":"store_memory","latency_ms":300}'),
    ]
    cur.executemany(
        "INSERT INTO ChatHistory (conversation_id, role, content, timestamp, agent_name, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def test_metrics_latency_aggregates_per_tool():
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

    resp = client.get("/api/v1/metrics/latency")
    assert resp.status_code == 200
    data = resp.json()
    lat = {t["tool"]: t for t in data.get("tools", [])}
    assert lat["list_todos"]["count"] == 2
    assert lat["list_todos"]["min_ms"] == 80
    assert lat["list_todos"]["max_ms"] == 120
    assert lat["list_todos"]["avg_ms"] == 100
    assert lat["store_memory"]["count"] == 1
    assert lat["store_memory"]["avg_ms"] == 300


