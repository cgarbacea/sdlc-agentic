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

ALLOWED_ROOTS = (
    os.path.realpath(FE_REPO_PATH),
    os.path.realpath(BE_REPO_PATH),
)
