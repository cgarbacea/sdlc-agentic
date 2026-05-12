import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

FE_REPO_PATH = os.getenv(
    "FE_REPO_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/fe-repo")
BE_REPO_PATH = os.getenv(
    "BE_REPO_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/be-repo")
JIRA_PATH = os.getenv(
    "JIRA_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/jira")
CONFLUENCE_PATH = os.getenv(
    "CONFLUENCE_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/confluence")

CURRENT_DATE = date.today().strftime("%d %B %Y")  # e.g. "23 April 2026"

# ── LLM provider configuration ───────────────────────────────────────────────
# Supported providers:
#   - anthropic
#   - openai_compatible (OpenAI or any OpenAI-compatible base URL)
#   - ollama
#   - stub (no external API calls; deterministic fallback output)
#   - auto (select anthropic if key exists, else stub)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").strip().lower()
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-5")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

# OpenAI-compatible settings
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")

# Ollama settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

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

GITHUB_ENABLED = bool(
    GITHUB_TOKEN and GITHUB_OWNER and GITHUB_FE_REPO and GITHUB_BE_REPO)

ALLOWED_ROOTS = (
    os.path.realpath(FE_REPO_PATH),
    os.path.realpath(BE_REPO_PATH),
)

# ── ArchUnit feedback loop (Phase 5) ─────────────────────────────────────────
# When enabled, BE generation is validated with an ArchUnit command and retried
# with failure context up to ARCHUNIT_MAX_RETRIES.
ARCHUNIT_VALIDATION_ENABLED = os.getenv(
    "ARCHUNIT_VALIDATION_ENABLED", "true"
).strip().lower() in {"1", "true", "yes", "on"}
ARCHUNIT_MAX_RETRIES = int(os.getenv("ARCHUNIT_MAX_RETRIES", "2"))
# Optional override, e.g.:
#   ./mvnw -q -Dtest=*ArchUnit* test
#   ./gradlew test --tests *ArchUnit*
ARCHUNIT_VALIDATION_COMMAND = os.getenv(
    "ARCHUNIT_VALIDATION_COMMAND", "").strip()

# ── Observability (Phase 6) ─────────────────────────────────────────────────
# Structured logs for ingestion by Datadog/Splunk/etc.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
# json | console
LOG_FORMAT = os.getenv("LOG_FORMAT", "json").strip().lower()

# LangSmith tracing (LangChain-compatible)
LANGSMITH_TRACING_ENABLED = os.getenv(
    "LANGSMITH_TRACING_ENABLED", "false"
).strip().lower() in {"1", "true", "yes", "on"}
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "").strip()
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "sdlc-agentic").strip()
LANGSMITH_ENDPOINT = os.getenv(
    "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"
).strip()
