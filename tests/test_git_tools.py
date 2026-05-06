"""
Phase 3 tests — real git tooling (gitpython) + GitHub integration config.
All tests are offline: no GitHub API calls, no network access required.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ── Config tests ───────────────────────────────────────────────────────────────

def test_github_config_fields_exist():
    """config.py must export all GitHub-related fields."""
    import config
    required = [
        "GITHUB_TOKEN", "GITHUB_OWNER", "GITHUB_FE_REPO",
        "GITHUB_BE_REPO", "GITHUB_BASE_BRANCH", "GITHUB_ENABLED",
    ]
    for field in required:
        assert hasattr(config, field), f"config.py missing field: {field}"


def test_github_enabled_is_false_without_credentials():
    """GITHUB_ENABLED must be False when env vars are not set."""
    import importlib
    with patch.dict(os.environ, {
        "GITHUB_TOKEN": "",
        "GITHUB_OWNER": "",
        "GITHUB_FE_REPO": "",
        "GITHUB_BE_REPO": "",
    }):
        import config
        importlib.reload(config)
        assert config.GITHUB_ENABLED is False, (
            "GITHUB_ENABLED should be False when any required GitHub env var is missing"
        )


def test_github_enabled_is_true_with_all_credentials():
    """GITHUB_ENABLED must be True when all four env vars are set."""
    import importlib
    with patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test_token",
        "GITHUB_OWNER": "testowner",
        "GITHUB_FE_REPO": "test-fe",
        "GITHUB_BE_REPO": "test-be",
    }):
        import config
        importlib.reload(config)
        assert config.GITHUB_ENABLED is True


# ── git_commit_to_branch tests ────────────────────────────────────────────────

def test_git_commit_to_branch_rejects_outside_allowed_roots():
    """git_commit_to_branch must refuse paths outside ALLOWED_ROOTS."""
    from tools.git import git_commit_to_branch
    result = git_commit_to_branch.invoke({
        "repo_path": "/tmp/not-allowed-path",
        "branch_name": "feature/test",
        "commit_message": "test commit",
    })
    assert "outside the allowed workspace" in result or "Git error" in result


def test_git_commit_creates_branch_and_commits(tmp_path):
    """git_commit_to_branch must create a branch and commit in a temp repo."""
    import importlib
    # Point ALLOWED_ROOTS at tmp_path so the tool accepts it
    with patch.dict(os.environ, {
        "FE_REPO_PATH": str(tmp_path),
        "BE_REPO_PATH": str(tmp_path / "be"),
        "GITHUB_TOKEN": "",
        "GITHUB_OWNER": "",
        "GITHUB_FE_REPO": "",
        "GITHUB_BE_REPO": "",
    }):
        import config
        importlib.reload(config)

        # Write a dummy file so there's something to commit
        (tmp_path / "hello.txt").write_text("hello world")

        from tools import git as git_tools
        importlib.reload(git_tools)

        result = git_tools.git_commit_to_branch.invoke({
            "repo_path": str(tmp_path),
            "branch_name": "feature/dark-mode",
            "commit_message": "feat: add dark mode",
        })

        assert "feature/dark-mode" in result
        # Verify branch actually exists in the repo
        import git
        repo = git.Repo(str(tmp_path))
        branch_names = [h.name for h in repo.heads]
        assert "feature/dark-mode" in branch_names


# ── create_github_pr tests ────────────────────────────────────────────────────

def test_create_github_pr_simulates_when_not_enabled():
    """create_github_pr must return a simulation message when GITHUB_ENABLED=False."""
    import importlib
    with patch.dict(os.environ, {
        "GITHUB_TOKEN": "", "GITHUB_OWNER": "",
        "GITHUB_FE_REPO": "", "GITHUB_BE_REPO": "",
    }):
        import config
        importlib.reload(config)
        from tools import git as git_tools
        importlib.reload(git_tools)

        result = git_tools.create_github_pr.invoke({
            "repo_name": "test-fe",
            "branch_name": "feature/dark-mode",
            "title": "feat: dark mode toggle",
            "pr_body": "Adds dark mode support.",
        })
        assert "SIMULATED PR" in result or "simulated" in result.lower()


def test_create_github_pr_calls_api_when_enabled():
    """create_github_pr must call the GitHub API when GITHUB_ENABLED=True."""
    import importlib
    with patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_fake",
        "GITHUB_OWNER": "testowner",
        "GITHUB_FE_REPO": "test-fe",
        "GITHUB_BE_REPO": "test-be",
    }):
        import config
        importlib.reload(config)
        from tools import git as git_tools
        importlib.reload(git_tools)

        mock_pr = MagicMock()
        mock_pr.html_url = "https://github.com/testowner/test-fe/pull/42"
        mock_pr.number = 42

        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = []
        mock_repo.create_pull.return_value = mock_pr

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch("tools.git.Github", return_value=mock_github):
            result = git_tools.create_github_pr.invoke({
                "repo_name": "test-fe",
                "branch_name": "feature/dark-mode",
                "title": "feat: dark mode toggle",
                "pr_body": "Adds dark mode.",
            })

        assert "pull/42" in result
        mock_repo.create_pull.assert_called_once()
