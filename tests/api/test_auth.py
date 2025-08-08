"""TDD: API token auth for write endpoints (summaries)."""

import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def test_summaries_requires_token_when_auth_enabled():
    _ensure_project_root_on_path()
    os.environ["ENABLE_AUTH"] = "1"
    os.environ["LTMC_API_TOKEN"] = "testtoken"

    from ltms.mcp_server_http import app
    client = TestClient(app)

    payload = {"doc_id": "d1", "summary_text": "hello"}

    # Missing auth
    resp = client.post("/api/v1/summaries", json=payload)
    assert resp.status_code == 401

    # Wrong token
    resp = client.post(
        "/api/v1/summaries",
        json=payload,
        headers={"Authorization": "Bearer wrong"},
    )
    assert resp.status_code == 401

    # Correct token via Authorization header
    resp = client.post(
        "/api/v1/summaries",
        json=payload,
        headers={"Authorization": "Bearer testtoken"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True


