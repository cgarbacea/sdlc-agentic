# ── SDLC Agentic — MCP Server Docker image ───────────────────────────────────
# Multi-stage build: keeps the final image lean by separating dependency
# installation from the runtime layer.
#
# Build:  docker build -t sdlc-mcp-server .
# Run:    docker run --rm -i \
#           -e ANTHROPIC_API_KEY=sk-ant-... \
#           -v /host/path/checkpoints:/app/.checkpoints \
#           sdlc-mcp-server
#
# The server reads from stdin and writes to stdout (MCP stdio transport).
# Mount a volume for .checkpoints/ to persist state across container restarts.

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools only in the builder stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user — never run production containers as root
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source — exclude runtime dirs (see .dockerignore)
COPY . .

# Runtime directories — owned by the non-root user
RUN mkdir -p .checkpoints rag_db \
    && chown -R appuser:appgroup /app

USER appuser

# Required env vars (must be passed at runtime via -e or docker-compose)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CHECKPOINT_DB_PATH=/app/.checkpoints/sdlc.db

# MCP stdio transport — no PORT exposure needed
# The container is invoked by the MCP client directly via stdin/stdout
ENTRYPOINT ["python", "mcp_server.py"]
