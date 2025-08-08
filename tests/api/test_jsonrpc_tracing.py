"""TDD: Trace JSON-RPC tool calls into ChatHistory with agent metadata."""

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


def test_jsonrpc_tools_call_traced_to_chat_history():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_db:
        db_path = f_db.name
    os.environ["DB_PATH"] = db_path

    from ltms.mcp_server_http import app
    client = TestClient(app)

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "list_todos",
            "arguments": {"completed": None}
        }
    }

    resp = client.post(
        "/jsonrpc",
        json=payload,
        headers={"X-Agent-Name": "Cursor"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("result") is not None or data.get("error") is None

    # Verify trace row inserted
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(ChatHistory)")
    cols = [row[1] for row in cur.fetchall()]
    assert "agent_name" in cols and "metadata" in cols
    cur.execute("SELECT agent_name, metadata FROM ChatHistory ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "Cursor"
    assert "list_todos" in (row[1] or "")


