"""TDD: Read-only graph query endpoint with write-protection."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def test_graph_query_read_only_accepts_match():
    _ensure_project_root_on_path()
    from ltms.mcp_server_http import app
    client = TestClient(app)

    payload = {"cypher": "MATCH (n) RETURN n LIMIT 1"}
    resp = client.post("/api/v1/graph/query", json=payload)
    assert resp.status_code in (200, 500)
    data = resp.json()
    assert isinstance(data, dict)
    assert "success" in data


def test_graph_query_rejects_writes():
    _ensure_project_root_on_path()
    from ltms.mcp_server_http import app
    client = TestClient(app)

    payload = {"cypher": "CREATE (n:Test {id: '1'}) RETURN n"}
    resp = client.post("/api/v1/graph/query", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert data.get("success") is False
    assert "write" in data.get("error", "").lower()
