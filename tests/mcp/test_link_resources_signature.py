"""TDD: Validate link_resources signature and basic behavior without mocks."""

import sys
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def test_link_resources_new_signature_accepts_keywords():
    """link_resources should accept source_id/target_id/relation keywords."""
    _ensure_project_root_on_path()
    from ltms.mcp_server import link_resources

    # Use empty strings to trigger validation and avoid external calls
    result = link_resources(source_id="", target_id="", relation="")
    assert isinstance(result, dict)
    assert result.get("success") is False
    assert "error" in result


def test_link_resources_with_values_returns_response_dict():
    """With values, should return a dict (may error if Neo4j is absent)."""
    _ensure_project_root_on_path()
    from ltms.mcp_server import link_resources

    result = link_resources(
        source_id="doc_a",
        target_id="doc_b",
        relation="REFERENCES",
    )
    assert isinstance(result, dict)
    assert "success" in result
