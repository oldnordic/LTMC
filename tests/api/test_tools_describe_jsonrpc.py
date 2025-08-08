"""TDD: JSON-RPC tools/describe returns schema for a specific tool."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def test_tools_describe_returns_params_for_tool():
    _ensure_project_root_on_path()
    from ltms.mcp_server_http import app
    client = TestClient(app)

    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/describe",
        "params": {"name": "store_memory"}
    }
    resp = client.post("/jsonrpc", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("result") is not None
    result = data["result"]
    assert result.get("name") == "store_memory"
    assert isinstance(result.get("params"), list)
    assert any(p.get("name") == "file_name" for p in result["params"])


