"""TDD: Validate log_chat response shape and error handling without mocks."""

import os
import sys
from pathlib import Path
import tempfile


def test_log_chat_returns_standard_shape():
    """log_chat should return {success: True, message_id: int} on success."""
    # Use a temporary SQLite DB for isolation
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        os.environ["DB_PATH"] = db_path

        # Ensure project root on sys.path for imports
        project_root = Path(__file__).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from ltms.mcp_server import log_chat  # import after setting env

        result = log_chat("conv_tdd_1", "user", "hello world")

        assert isinstance(result, dict)
        assert result.get("success") is True
        assert isinstance(result.get("message_id"), int)
    finally:
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass


def test_log_chat_invalid_input_returns_error():
    """Invalid inputs return {success: False, error: str} without raising."""
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from ltms.mcp_server import log_chat

    result = log_chat("", "", "")
    assert isinstance(result, dict)
    assert result.get("success") is False
    assert isinstance(result.get("error"), str)
