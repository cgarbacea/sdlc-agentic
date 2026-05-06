"""
tools/git.py — Real Git + GitHub PR integration
================================================
Phase 3: replaces the simulated PR stub with real gitpython commits and
PyGithub pull request creation.

Behaviour is controlled by config.GITHUB_ENABLED:
  - True  → push branch to remote + open a real GitHub PR
  - False → local commit only + log a warning (safe fallback for local dev
             without GitHub credentials)
"""

import logging
import os

import git as gitpython
from github import Github, GithubException
from langchain_core.tools import tool

from config import (
    ALLOWED_ROOTS,
    GITHUB_BASE_BRANCH,
    GITHUB_BE_REPO,
    GITHUB_ENABLED,
    GITHUB_FE_REPO,
    GITHUB_OWNER,
    GITHUB_TOKEN,
)

log = logging.getLogger(__name__)


def _repo_name_for_path(repo_path: str) -> str:
    """Map a local repo path to its GitHub repo name."""
    real = os.path.realpath(repo_path)
    from config import FE_REPO_PATH, BE_REPO_PATH
    if real == os.path.realpath(FE_REPO_PATH):
        return GITHUB_FE_REPO
    if real == os.path.realpath(BE_REPO_PATH):
        return GITHUB_BE_REPO
    return os.path.basename(real)


def _ensure_git_repo(repo_path: str) -> gitpython.Repo:
    """Return a gitpython Repo, initialising one with an initial commit if needed."""
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        log.info("Initialising git repo at %s", repo_path)
        print(f"   📦 [GIT] Initialising git repo at {repo_path}...")
        repo = gitpython.Repo.init(repo_path, initial_branch="main")
        with repo.config_writer() as cw:
            cw.set_value("user", "email", "agent@sdlc-agentic.ai")
            cw.set_value("user", "name", "SDLC Agent")
        gitignore = os.path.join(repo_path, ".gitignore")
        if not os.path.exists(gitignore):
            with open(gitignore, "w") as f:
                f.write("*.pyc\n__pycache__/\n.DS_Store\nnode_modules/\n.env\n")
        repo.index.add([".gitignore"])
        repo.index.commit("chore: initial commit")
        print(f"   ✅ [GIT] Repo initialised.")
    else:
        repo = gitpython.Repo(repo_path)

    with repo.config_writer() as cw:
        cw.set_value("user", "email", "agent@sdlc-agentic.ai")
        cw.set_value("user", "name", "SDLC Agent")

    return repo


def _push_branch(repo: gitpython.Repo, branch_name: str, github_repo_name: str) -> bool:
    """Push branch to GitHub remote. Returns True on success."""
    remote_url = (
        f"https://x-access-token:{GITHUB_TOKEN}@github.com/"
        f"{GITHUB_OWNER}/{github_repo_name}.git"
    )
    try:
        if "origin" in [r.name for r in repo.remotes]:
            repo.remotes.origin.set_url(remote_url)
        else:
            repo.create_remote("origin", remote_url)
        repo.remotes.origin.push(refspec=f"{branch_name}:{branch_name}", force=True)
        log.info("Pushed branch %s to %s/%s", branch_name, GITHUB_OWNER, github_repo_name)
        return True
    except Exception as exc:
        log.error("Push failed: %s", exc)
        return False


def _open_github_pr(github_repo_name: str, branch_name: str, title: str, body: str) -> str:
    """Open a PR on GitHub. Returns the PR URL. Raises GithubException on error."""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(f"{GITHUB_OWNER}/{github_repo_name}")
    existing = list(repo.get_pulls(state="open", head=f"{GITHUB_OWNER}:{branch_name}"))
    if existing:
        return existing[0].html_url
    pr = repo.create_pull(title=title, body=body, head=branch_name, base=GITHUB_BASE_BRANCH)
    log.info("PR #%d opened: %s", pr.number, pr.html_url)
    return pr.html_url


@tool
def git_commit_to_branch(repo_path: str, branch_name: str, commit_message: str) -> str:
    """
    Creates (or resets) a git branch, stages all changed files, and commits.
    If GITHUB_ENABLED, also pushes the branch to the GitHub remote.
    Use this AFTER writing code files to save your work.
    """
    if not any(os.path.realpath(repo_path).startswith(root) for root in ALLOWED_ROOTS):
        return f"Git error: repo_path '{repo_path}' is outside the allowed workspace."

    os.makedirs(repo_path, exist_ok=True)
    repo = _ensure_git_repo(repo_path)

    print(f"\n🌱 [GIT] Creating branch '{branch_name}' in {repo_path}...")
    try:
        if branch_name in repo.heads:
            repo.heads[branch_name].checkout()
        else:
            repo.create_head(branch_name).checkout()

        repo.git.add(A=True)

        if repo.is_dirty(untracked_files=True):
            repo.index.commit(commit_message)
            print(f"   ✅ [GIT] Committed to '{branch_name}': {commit_message}")
        else:
            return f"Branch '{branch_name}' checked out. No new changes to commit."

        if GITHUB_ENABLED:
            github_repo_name = _repo_name_for_path(repo_path)
            pushed = _push_branch(repo, branch_name, github_repo_name)
            if pushed:
                print(f"   🚀 [GITHUB] Pushed '{branch_name}' to {GITHUB_OWNER}/{github_repo_name}")
                return f"Committed and pushed branch '{branch_name}' to GitHub."
            return f"Committed to '{branch_name}' locally. GitHub push failed — check GITHUB_TOKEN."
        else:
            log.warning("GITHUB_ENABLED=False — branch committed locally only.")
            return f"Committed to branch '{branch_name}' locally (GitHub push skipped — credentials not configured)."

    except gitpython.GitCommandError as exc:
        return f"Git error: {exc}"
    except Exception as exc:
        return f"Git error: {exc}"


@tool
def create_github_pr(repo_name: str, branch_name: str, title: str, pr_body: str) -> str:
    """
    Opens a Pull Request on GitHub for the given branch.
    If GITHUB_ENABLED is False, returns a local summary instead of failing.
    Use this AFTER committing and pushing your code.
    """
    if not GITHUB_ENABLED:
        msg = (
            f"[SIMULATED PR] '{title}' | {repo_name}:{branch_name} → {GITHUB_BASE_BRANCH}\n"
            f"Set GITHUB_TOKEN, GITHUB_OWNER, GITHUB_FE_REPO, GITHUB_BE_REPO in .env to open real PRs."
        )
        print(f"\n📋 {msg}")
        return msg

    print(f"\n🚀 [GITHUB] Opening PR: '{title}' ({branch_name} → {GITHUB_BASE_BRANCH})...")
    try:
        url = _open_github_pr(repo_name, branch_name, title, pr_body)
        print(f"   ✅ [GITHUB] PR opened: {url}")
        return f"PR opened: {url}"
    except GithubException as exc:
        return f"GitHub API error: {exc.data.get('message', str(exc))}"
    except Exception as exc:
        return f"Error opening PR: {exc}"
