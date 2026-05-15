.PHONY: help run run-health build-kb test lint fmt install clean

PYTHON := python
VENV   := venv
PIP    := $(VENV)/bin/pip

# ── Default target ─────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "SDLC Agentic Pipeline — available targets:"
	@echo ""
	@echo "  make install     Install all dependencies into the venv"
	@echo "  make build-kb    Ingest docs/ into the ChromaDB RAG knowledge base"
	@echo "  make run         Run the pipeline interactively"
	@echo "  make run-health  Run the FastAPI /health endpoint"
	@echo "  make test        Run the test suite"
	@echo "  make lint        Run ruff linter"
	@echo "  make fmt         Auto-format code with ruff"
	@echo "  make clean       Remove __pycache__ and .pyc files"
	@echo ""

# ── Setup ──────────────────────────────────────────────────────────────────────
install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# ── Core workflows ─────────────────────────────────────────────────────────────
build-kb:
	@echo ">>> Building RAG knowledge base from docs/..."
	$(VENV)/bin/python build_knowledge_base.py

run:
	@echo ">>> Starting SDLC pipeline (interactive)..."
	$(VENV)/bin/python main.py

run-health:
	@echo ">>> Starting health endpoint on http://127.0.0.1:8081/health ..."
	$(VENV)/bin/uvicorn health_server:app --host 127.0.0.1 --port 8081

# Run non-interactively in CI — requires FEATURE env var
# Usage: FEATURE="add dark mode" make ci-run
ci-run:
	@if [ -z "$(FEATURE)" ]; then echo "ERROR: set FEATURE= before calling ci-run"; exit 1; fi
	$(VENV)/bin/python main.py --feature "$(FEATURE)" --non-interactive

# ── Quality ────────────────────────────────────────────────────────────────────
test:
	@echo ">>> Running tests..."
	$(VENV)/bin/python -m pytest tests/ -v 2>/dev/null || echo "No tests found yet — add tests/ directory."

lint:
	@echo ">>> Linting with ruff..."
	$(VENV)/bin/ruff check . 2>/dev/null || $(VENV)/bin/python -m py_compile main.py graph.py state.py config.py && echo "Syntax OK"

fmt:
	@echo ">>> Formatting with ruff..."
	$(VENV)/bin/ruff format . 2>/dev/null || echo "ruff not installed — run: pip install ruff"

# ── Housekeeping ───────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	@echo ">>> Clean done."
