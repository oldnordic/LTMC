"""TDD: Read-only graph search endpoint."""

import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def test_graph_search_endpoint_shape_and_readonly():
    _ensure_project_root_on_path()
    # Ensure DB path present for app init
    os.environ.setdefault("DB_PATH", "/tmp/lltmc_test_graph.db")

    from ltms.mcp_server_http import app

    client = TestClient(app)
    payload = {"entity_id": "doc-1", "relation_type": None, "direction": "both"}
    resp = client.post("/api/v1/graph/search", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("success") is True
    assert isinstance(data.get("records"), list)


