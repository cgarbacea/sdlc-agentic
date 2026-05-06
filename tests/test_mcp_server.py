"""
MCP server smoke tests — verify the server module loads and tools are
registered correctly without starting the server or calling the LLM.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_mcp_server_imports():
    """mcp_server module must import without error."""
    import importlib
    spec = importlib.util.spec_from_file_location(
        "mcp_server", PROJECT_ROOT / "mcp_server.py"
    )
    module = importlib.util.module_from_spec(spec)
    # Execute the module — should not raise
    spec.loader.exec_module(module)
    assert hasattr(
        module, "mcp"), "mcp_server must expose a 'mcp' FastMCP instance"


def test_mcp_server_has_required_tools():
    """All four required tools must be registered on the FastMCP instance."""
    import importlib
    spec = importlib.util.spec_from_file_location(
        "mcp_server", PROJECT_ROOT / "mcp_server.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # FastMCP stores tools internally; verify by checking the callables exist
    required_tools = [
        "start_pipeline",
        "get_pipeline_state",
        "approve_plan",
        "list_threads",
    ]
    for tool_name in required_tools:
        assert hasattr(module, tool_name), (
            f"mcp_server.py must define a '{tool_name}' function"
        )
        assert callable(getattr(module, tool_name)), (
            f"'{tool_name}' must be callable"
        )


def test_start_pipeline_rejects_empty_input():
    """start_pipeline must return an error dict for empty feature descriptions."""
    import importlib
    spec = importlib.util.spec_from_file_location(
        "mcp_server", PROJECT_ROOT / "mcp_server.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.start_pipeline("")
    assert "error" in result, "Empty feature_description must return an error"

    result2 = module.start_pipeline("   ")
    assert "error" in result2, "Whitespace-only feature_description must return an error"


def test_get_pipeline_state_handles_missing_thread():
    """get_pipeline_state must return an error dict for unknown thread IDs."""
    import importlib
    spec = importlib.util.spec_from_file_location(
        "mcp_server", PROJECT_ROOT / "mcp_server.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Patch _ensure_pipeline to return a mock app that raises on get_state
    mock_app = MagicMock()
    mock_app.get_state.return_value = None
    module._app = mock_app
    module._pipeline_ready = True

    result = module.get_pipeline_state("nonexistent-thread-id-xyz")
    assert "error" in result, "Missing thread must return an error dict"


def test_vscode_mcp_json_exists_and_is_valid():
    """The .vscode/mcp.json registration file must exist and be valid JSON."""
    import json

    mcp_json_path = PROJECT_ROOT / ".vscode" / "mcp.json"
    assert mcp_json_path.exists(), ".vscode/mcp.json must exist for VS Code registration"

    with open(mcp_json_path) as f:
        config = json.load(f)

    assert "servers" in config, "mcp.json must have a 'servers' key"
    assert "sdlc-pipeline" in config["servers"], (
        "mcp.json must register 'sdlc-pipeline'"
    )
    server = config["servers"]["sdlc-pipeline"]
    assert server.get("type") == "stdio", "Server type must be 'stdio'"
    assert "command" in server, "Server must specify a 'command'"
    assert "args" in server, "Server must specify 'args'"
