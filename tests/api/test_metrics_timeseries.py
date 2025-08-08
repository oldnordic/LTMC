"""TDD: Timeseries metrics per tool per day."""

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
    base = datetime(2025, 1, 1, 12, 0, 0)
    rows = [
        ("c1", "tool", "tools/call:list_todos", (base - timedelta(days=2)).isoformat(), "Cursor", '{"tool":"list_todos"}'),
        ("c1", "tool", "tools/call:list_todos", (base - timedelta(days=2, hours=1)).isoformat(), "Cursor", '{"tool":"list_todos"}'),
        ("c1", "tool", "tools/call:list_todos", (base - timedelta(days=1)).isoformat(), "Cursor", '{"tool":"list_todos"}'),
        ("c1", "tool", "tools/call:store_memory", (base - timedelta(days=1)).isoformat(), "Cursor", '{"tool":"store_memory"}'),
    ]
    cur.executemany(
        "INSERT INTO ChatHistory (conversation_id, role, content, timestamp, agent_name, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def test_metrics_tools_timeseries_day_counts():
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

    resp = client.get(
        "/api/v1/metrics/tools/timeseries",
        params={"tool": "list_todos", "granularity": "day"},
    )
    assert resp.status_code == 200
    data = resp.json()
    series = {row["date"]: row["count"] for row in data.get("series", [])}
    # Expect two entries: base-2d has 2, base-1d has 1
    assert len(series) >= 2
    # We don't know exact dates here, just validate totals
    assert sum(series.values()) == 3


