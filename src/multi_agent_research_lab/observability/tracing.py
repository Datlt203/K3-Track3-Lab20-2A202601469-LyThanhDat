"""Provider-neutral tracing with a local JSONL exporter."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Capture a span and optionally export it when ``TRACE_FILE`` is set."""

    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started
        trace_file = attributes.get("trace_file") if attributes else None
        if trace_file:
            path = Path(str(trace_file))
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(span, ensure_ascii=False) + "\n")


def export_trace(events: list[dict[str, Any]], path: Path) -> Path:
    """Write state trace events as portable JSONL evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def traced(name: str) -> Any:
    """Decorate a workflow node with LangSmith when configured.

    Without ``LANGSMITH_API_KEY`` this is a no-op, so local/offline runs do not
    require network access. LangSmith receives inputs, outputs, errors, timing,
    project name, and the node name when enabled.
    """

    settings = get_settings()
    try:
        from langsmith import Client, traceable

        client = (
            Client(api_key=settings.langsmith_api_key)
            if settings.langsmith_api_key
            else None
        )
    except ImportError:
        client = None
        traceable = None

    def decorator(function: Any) -> Any:
        if traceable is not None and client is not None:
            return traceable(
                function,
                name=name,
                run_type="chain",
                client=client,
                project_name=settings.langsmith_project,
                enabled=True,
            )

        @wraps(function)
        def local_wrapper(*args: Any, **kwargs: Any) -> Any:
            return function(*args, **kwargs)

        return local_wrapper

    return decorator
