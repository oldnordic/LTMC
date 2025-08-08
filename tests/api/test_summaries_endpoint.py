"""TDD: Auto-summary ingestion endpoint tests (no mocks)."""

import os
import sys
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient


def test_post_summaries_persists_and_returns_id():
    """POST /api/v1/summaries should persist and return an id and success."""
    # Use temp DB for isolation
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    os.environ["DB_PATH"] = db_path

    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from ltms.mcp_server_http import app

    client = TestClient(app)

    payload = {
        "doc_id": "doc_test_1",
        "summary_text": "This is a test summary.",
        "model": "unit-test"
    }

    resp = client.post("/api/v1/summaries", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    assert isinstance(data.get("summary_id"), int)


def test_post_summaries_invalid_payload_returns_error():
    """Invalid payload should return an error, not raise exceptions."""
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from ltms.mcp_server_http import app
    client = TestClient(app)

    # Missing summary_text
    bad_payload = {"doc_id": "doc_test_2"}
    resp = client.post("/api/v1/summaries", json=bad_payload)
    assert resp.status_code in (200, 400)
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("success") is False or "error" in data
