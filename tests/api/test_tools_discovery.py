"""TDD: Tools discovery returns names, descriptions, and param schemas."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def test_tools_discovery_returns_schema():
    _ensure_project_root_on_path()
    from ltms.mcp_server_http import app
    client = TestClient(app)

    resp = client.get("/api/v1/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert isinstance(data.get("tools"), list)
    assert len(data["tools"]) >= 5
    first = data["tools"][0]
    assert "name" in first
    assert "description" in first
    assert "params" in first and isinstance(first["params"], list)
    if first["params"]:
        p0 = first["params"][0]
        assert "name" in p0 and "type" in p0 and "required" in p0


