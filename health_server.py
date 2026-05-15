from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI

from config import (
    LANGSMITH_TRACING_ENABLED,
    LOG_FORMAT,
    LOG_LEVEL,
)
from llm_factory import get_provider_name

app = FastAPI(title="sdlc-agentic-health", version="1.0.0")


@app.get("/health")
def health() -> dict[str, object]:
    """Operational health endpoint for monitoring probes."""
    return {
        "status": "ok",
        "service": "sdlc-agentic",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": get_provider_name(),
        "log_level": LOG_LEVEL,
        "log_format": LOG_FORMAT,
        "langsmith_tracing_enabled": LANGSMITH_TRACING_ENABLED,
    }
