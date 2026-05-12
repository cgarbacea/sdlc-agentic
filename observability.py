import logging
import os
import sys

import structlog

from config import (
    LANGSMITH_API_KEY,
    LANGSMITH_ENDPOINT,
    LANGSMITH_PROJECT,
    LANGSMITH_TRACING_ENABLED,
    LOG_FORMAT,
    LOG_LEVEL,
)


def _as_level(value: str) -> int:
    return getattr(logging, (value or "INFO").upper(), logging.INFO)


def _configure_structured_logging() -> None:
    level = _as_level(LOG_LEVEL)

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    use_json = (LOG_FORMAT or "json").strip().lower() == "json"
    renderer = (
        structlog.processors.JSONRenderer()
        if use_json
        else structlog.dev.ConsoleRenderer(colors=False)
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def _configure_langsmith_env() -> dict[str, object]:
    enabled = bool(LANGSMITH_TRACING_ENABLED)

    if not enabled:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return {"enabled": False, "project": LANGSMITH_PROJECT, "reason": "disabled"}

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", LANGSMITH_PROJECT)
    os.environ.setdefault("LANGSMITH_PROJECT", LANGSMITH_PROJECT)

    if LANGSMITH_ENDPOINT:
        os.environ.setdefault("LANGSMITH_ENDPOINT", LANGSMITH_ENDPOINT)

    if LANGSMITH_API_KEY:
        os.environ.setdefault("LANGSMITH_API_KEY", LANGSMITH_API_KEY)
        return {
            "enabled": True,
            "project": LANGSMITH_PROJECT,
            "reason": "configured",
        }

    return {
        "enabled": True,
        "project": LANGSMITH_PROJECT,
        "reason": "missing_api_key",
    }


def configure_observability(service_name: str) -> dict[str, object]:
    _configure_structured_logging()
    tracing = _configure_langsmith_env()

    logger = structlog.get_logger(service_name)
    logger.info(
        "observability_configured",
        service=service_name,
        log_format=LOG_FORMAT,
        log_level=LOG_LEVEL,
        langsmith_enabled=tracing["enabled"],
        langsmith_project=tracing["project"],
        langsmith_reason=tracing["reason"],
    )

    return tracing
