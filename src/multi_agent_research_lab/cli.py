"""Command-line entrypoint for the lab starter."""

from time import perf_counter
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import (
    baseline_runner,
    multi_agent_runner,
    run_suite,
)
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _parse_query(query: str) -> ResearchQuery:
    try:
        return ResearchQuery(query=query)
    except ValidationError as exc:
        console.print(
            Panel.fit(
                f"Invalid query: {exc.errors()[0]['msg']}",
                title="Input Error",
                style="red",
            )
        )
        raise typer.Exit(code=1) from exc


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline and report latency/token usage."""

    _init()
    request = _parse_query(query)
    state = ResearchState(request=request)
    started = perf_counter()
    response = LLMClient().complete(
        "You are a concise research assistant. Cite supplied source IDs and state limitations.",
        query,
    )
    latency = perf_counter() - started
    state.final_answer = response.content
    state.add_trace_event(
        "baseline",
        {
            "latency_seconds": latency,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd,
        },
    )
    console.print(
        f"Latency: {latency:.2f}s | input_tokens={response.input_tokens} | "
        f"output_tokens={response.output_tokens} | cost_usd={response.cost_usd}"
    )
    console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=_parse_query(query))
    workflow = MultiAgentWorkflow()
    result = workflow.run(state)
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    queries: Annotated[
        list[str] | None,
        typer.Option("--query", "-q", help="Query to benchmark; repeat for a suite."),
    ] = None,
    output: Annotated[str, typer.Option("--output", help="Markdown report path.")] = (
        "reports/benchmark_report.md"
    ),
) -> None:
    """Compare baseline and multi-agent on the same offline-safe query suite."""

    _init()
    selected = queries or [
        "Research GraphRAG state-of-the-art and write a 500-word summary",
        "Explain multi-agent systems and their failure modes",
        "Compare retrieval augmented generation with GraphRAG",
    ]
    report = render_markdown_report(run_suite(selected, baseline_runner, multi_agent_runner))
    from pathlib import Path

    report_path = Path(output)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    console.print(f"Benchmark report written to {report_path}")


if __name__ == "__main__":
    app()
