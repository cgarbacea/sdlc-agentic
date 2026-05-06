import os
import random
import subprocess
from langchain_core.tools import tool
from config import ALLOWED_ROOTS


def _ensure_git_repo(repo_path: str) -> None:
    """Initialise a git repo with an empty initial commit if one doesn't exist."""
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        print(f"   📦 [GIT] Initialising git repo at {repo_path}...")
        subprocess.run(["git", "init", "-b", "main"],
                       cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "agent@youpage.ai"],
                       cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "YOUPAGE Agent"],
                       cwd=repo_path, check=True, capture_output=True)
        # Create an initial commit so branches can be created off main
        gitignore = os.path.join(repo_path, ".gitignore")
        if not os.path.exists(gitignore):
            with open(gitignore, "w") as f:
                f.write("*.pyc\n__pycache__/\n.DS_Store\n")
        subprocess.run(["git", "add", "."], cwd=repo_path,
                       check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "chore: initial commit"],
                       cwd=repo_path, check=True, capture_output=True)
        print(f"   ✅ [GIT] Repo initialised.")


@tool
def git_commit_to_branch(repo_path: str, branch_name: str, commit_message: str) -> str:
    """
    Creates a new git branch, stages all changed files, and commits them.
    Use this AFTER writing your code files to save your work.
    """
    if not any(os.path.realpath(repo_path).startswith(root) for root in ALLOWED_ROOTS):
        return f"Git error: repo_path '{repo_path}' is outside the allowed workspace."

    _ensure_git_repo(repo_path)

    print(f"\n🌱 [GIT] Creating branch '{branch_name}' in {repo_path}...")
    try:
        subprocess.run(
            ["git", "checkout", "-B", branch_name],
            cwd=repo_path, check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path, check=True, capture_output=True, text=True,
        )
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_path, capture_output=True, text=True,
        )
        if result.returncode != 0:
            # Nothing to commit is not a failure
            if "nothing to commit" in result.stdout:
                return f"Branch '{branch_name}' created. No new changes to commit."
            return f"Git error: {result.stderr or result.stdout}"
        print(f"   ✅ [GIT] Committed to '{branch_name}'")
        return f"Success: Committed to branch '{branch_name}' with message: '{commit_message}'"
    except subprocess.CalledProcessError as e:
        return f"Git error: {e.stderr or e.stdout}"


@tool
def create_github_pr(repo_name: str, branch_name: str, title: str, pr_body: str) -> str:
    """
    Creates a Pull Request on GitHub. Use this AFTER committing your code.
    In production: replace the body of this function with a real PyGithub call.
    """
    # ── Production implementation (enable in Phase 2 with real repos) ──────────
    # from github import Github
    # g = Github(os.getenv("GITHUB_TOKEN"))
    # repo = g.get_repo(repo_name)
    # pr = repo.create_pull(title=title, body=pr_body, head=branch_name, base="main")
    # return f"PR #{pr.number} opened: {pr.html_url}"
    # ──────────────────────────────────────────────────────────────────────────

    # ── Realistic simulation (used until real repos are connected) ─────────────
    pr_number = random.randint(100, 999)
    fake_url = f"https://github.com/youpage/{repo_name}/pull/{pr_number}"
    print(f"\n🚀 [GITHUB PR SIMULATED]")
    print(f"   Repo:   {repo_name}")
    print(f"   Branch: {branch_name} → main")
    print(f"   Title:  {title}")
    print(
        f"   PR URL: {fake_url}  (simulated — connect real repo to activate)")
    return f"PR #{pr_number} '{title}' opened at {fake_url}"
