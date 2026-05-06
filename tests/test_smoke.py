"""
Smoke tests — verify the project wires up correctly without calling the LLM.
All tests here must be fast (<1s) and require no API keys.
"""

import importlib
import sys
from pathlib import Path

# Ensure project root is on the path when running from the tests/ dir
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_state_schema_has_required_keys():
    """SDLCState must contain all fields that nodes read/write."""
    from state import SDLCState
    import typing

    hints = typing.get_type_hints(SDLCState)
    required = {
        "user_request",
        "prd",
        "architect_plan",
        "fe_output",
        "be_output",
        "test_output",
        "qa_report",
        "infra_output",
        "pr_urls",
    }
    missing = required - hints.keys()
    assert not missing, f"SDLCState is missing fields: {missing}"


def test_graph_compiles():
    """LangGraph workflow must compile without errors (no LLM calls)."""
    from graph import app
    assert app is not None, "graph.app failed to compile"


def test_main_argparser():
    """CLI parser must accept --feature and --thread-id without error."""
    from main import _parse_args
    import sys as _sys

    _sys.argv = ["sdlc-agent", "--feature", "test feature", "--thread-id", "test-123"]
    args = _parse_args()
    assert args.feature == "test feature"
    assert args.thread_id == "test-123"
    assert not args.non_interactive


def test_main_argparser_non_interactive_flag():
    """--non-interactive flag must be parseable (used by CI)."""
    from main import _parse_args
    import sys as _sys

    _sys.argv = ["sdlc-agent", "--feature", "dark mode", "--non-interactive"]
    args = _parse_args()
    assert args.non_interactive is True


def test_prompts_exist():
    """Every executor must have a corresponding prompt file."""
    prompt_dir = PROJECT_ROOT / "prompts"
    expected = [
        "be_executor.md",
        "fe_executor.md",
        "infra_executor.md",
        "qa_executor.md",
        "test_executor.md",
    ]
    for fname in expected:
        path = prompt_dir / fname
        assert path.exists(), f"Missing prompt file: prompts/{fname}"
        assert path.stat().st_size > 0, f"Prompt file is empty: prompts/{fname}"
