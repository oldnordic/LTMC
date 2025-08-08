"""TDD: Agent trace logging via log_chat (agent_name, metadata)."""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def test_log_chat_persists_agent_name_and_metadata():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["DB_PATH"] = db_path

    from ltms.mcp_server import log_chat
    result = log_chat(
        conversation_id="convX",
        role="user",
        content="hello",
        agent_name="Cursor",
        metadata={"tool": "store_memory", "model": "claude-3"},
    )
    assert result.get("success") is True
    msg_id = result.get("message_id")
    assert isinstance(msg_id, int)

    # Verify DB row
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(ChatHistory)")
    cols = [row[1] for row in cur.fetchall()]
    assert "agent_name" in cols and "metadata" in cols
    cur.execute("SELECT agent_name, metadata FROM ChatHistory WHERE id = ?", (msg_id,))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "Cursor"
    assert "store_memory" in (row[1] or "")
    conn.close()


def test_log_chat_works_without_agent_fields():
    _ensure_project_root_on_path()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["DB_PATH"] = db_path

    from ltms.mcp_server import log_chat
    result = log_chat("convY", "assistant", "hi")
    assert result.get("success") is True
    assert isinstance(result.get("message_id"), int)


