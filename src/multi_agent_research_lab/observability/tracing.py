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
        trace_file = (attributes or {}).get("trace_file") or get_settings().trace_file
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
    client = None
    traceable = None
    if settings.langsmith_enabled and settings.langsmith_api_key:
        try:
            from langsmith import Client, traceable

            client = Client(api_key=settings.langsmith_api_key)
        except ImportError:
            pass

    def decorator(function: Any) -> Any:
        traced_function = function
        if traceable is not None and client is not None and settings.langsmith_enabled:
            traced_function = traceable(
                function,
                name=name,
                run_type="chain",
                client=client,
                project_name=settings.langsmith_project,
                enabled=True,
            )

        @wraps(function)
        def local_wrapper(*args: Any, **kwargs: Any) -> Any:
            attributes = {
                "mode": "local",
                "function": function.__qualname__,
                "input_keys": list(kwargs),
            }
            with trace_span(name, attributes) as span:
                try:
                    result = traced_function(*args, **kwargs)
                    span["status"] = "ok"
                    if isinstance(result, dict):
                        span["output_keys"] = list(result)
                    return result
                except Exception as exc:
                    span["status"] = "error"
                    span["error_type"] = type(exc).__name__
                    span["error"] = str(exc)
                    raise

        return local_wrapper

    return decorator
