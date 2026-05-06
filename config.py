import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise EnvironmentError(
        "ANTHROPIC_API_KEY is not set. Add it to your .env file.")

FE_REPO_PATH = os.getenv(
    "FE_REPO_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/fe-repo")
BE_REPO_PATH = os.getenv(
    "BE_REPO_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/be-repo")
JIRA_PATH = os.getenv(
    "JIRA_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/jira")
CONFLUENCE_PATH = os.getenv(
    "CONFLUENCE_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/confluence")

CURRENT_DATE = date.today().strftime("%d %B %Y")  # e.g. "23 April 2026"

# ── Checkpointer database ─────────────────────────────────────────────────────
# Stores paused LangGraph state so pipeline runs survive process restarts.
# Override via CHECKPOINT_DB_PATH env var (e.g. a shared volume in Docker).
CHECKPOINT_DB_PATH = os.getenv(
    "CHECKPOINT_DB_PATH",
    os.path.join(os.path.dirname(__file__), ".checkpoints", "sdlc.db"),
)
os.makedirs(os.path.dirname(CHECKPOINT_DB_PATH), exist_ok=True)

# ── GitHub integration ────────────────────────────────────────────────────────
# Required for Phase 3: real git branches + GitHub PRs.
# Create a fine-grained PAT at https://github.com/settings/tokens with:
#   - Contents: read & write (to push branches)
#   - Pull requests: read & write (to open PRs)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
# The GitHub org or user that owns the FE and BE repos, e.g. "cgarbacea"
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "")
# Repo names on GitHub (without the owner prefix), e.g. "youpage-fe"
GITHUB_FE_REPO = os.getenv("GITHUB_FE_REPO", "")
GITHUB_BE_REPO = os.getenv("GITHUB_BE_REPO", "")
# Base branch PRs will target (almost always "main")
GITHUB_BASE_BRANCH = os.getenv("GITHUB_BASE_BRANCH", "main")

GITHUB_ENABLED = bool(GITHUB_TOKEN and GITHUB_OWNER and GITHUB_FE_REPO and GITHUB_BE_REPO)

ALLOWED_ROOTS = (
    os.path.realpath(FE_REPO_PATH),
    os.path.realpath(BE_REPO_PATH),
)
