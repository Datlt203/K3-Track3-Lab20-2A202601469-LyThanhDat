"""Deterministic benchmark helpers for single-agent vs multi-agent runs."""

from collections.abc import Callable, Iterable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def _citation_coverage(state: ResearchState) -> float:
    """Estimate the fraction of retrieved source IDs mentioned in the answer."""

    if not state.sources or not state.final_answer:
        return 0.0
    answer = state.final_answer.lower()
    cited = sum(
        1
        for source in state.sources
        if str(source.metadata.get("source_id", "")).lower() in answer
    )
    return cited / len(state.sources)


def _quality_score(state: ResearchState) -> float:
    """Apply a small offline rubric, avoiding an extra LLM call during evaluation."""

    answer = state.final_answer or ""
    score = 0.0
    score += 3.0 if len(answer.split()) >= 40 else 1.0 if answer else 0.0
    score += 2.0 if state.sources else 0.0
    score += 2.0 if _citation_coverage(state) >= 0.5 else 0.0
    score += 2.0 if state.analysis_notes else 0.0
    score += 1.0 if "limitation" in answer.lower() else 0.0
    return min(score, 10.0)


def _estimated_cost(state: ResearchState) -> float | None:
    values = [
        event.get("payload", {}).get("cost_usd")
        for event in state.trace
        if isinstance(event, dict)
    ]
    costs = [float(value) for value in values if isinstance(value, (int, float))]
    return sum(costs) if costs else 0.0


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Run one query and calculate latency, cost, quality, citations and failure."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    failed = bool(state.errors) or not state.final_answer
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=_estimated_cost(state),
        quality_score=_quality_score(state),
        citation_coverage=_citation_coverage(state),
        failure_rate=1.0 if failed else 0.0,
        notes=(
            "; ".join(state.errors)
            if state.errors
            else f"routes={','.join(state.route_history)}"
        ),
    )
    return state, metrics


def run_comparison(query: str, baseline: Runner, multi_agent: Runner) -> list[BenchmarkMetrics]:
    """Run the same query through both systems in a stable, comparable order."""

    return [
        run_benchmark("baseline", query, baseline)[1],
        run_benchmark("multi-agent", query, multi_agent)[1],
    ]


def run_suite(
    queries: Iterable[str], baseline: Runner, multi_agent: Runner
) -> list[BenchmarkMetrics]:
    """Benchmark every query and aggregate metrics by runner."""

    rows: list[BenchmarkMetrics] = []
    for query in queries:
        for name, runner in (("baseline", baseline), ("multi-agent", multi_agent)):
            try:
                _, metrics = run_benchmark(name, query, runner)
            except Exception as exc:
                metrics = BenchmarkMetrics(
                    run_name=name,
                    latency_seconds=0.0,
                    quality_score=0.0,
                    citation_coverage=0.0,
                    failure_rate=1.0,
                    notes=f"exception={type(exc).__name__}: {exc}",
                )
            rows.append(metrics)
    return rows


def baseline_runner(query: str) -> ResearchState:
    """Offline-safe single-agent runner used by the CLI benchmark command."""

    from multi_agent_research_lab.services.llm_client import LLMClient

    state = ResearchState(request=ResearchQuery(query=query))
    response = LLMClient().complete(
        "You are a concise research assistant. Cite source IDs and state limitations.", query
    )
    state.final_answer = response.content
    state.add_trace_event(
        "baseline",
        {"cost_usd": response.cost_usd or 0.0, "input_tokens": response.input_tokens or 0},
    )
    return state


def multi_agent_runner(query: str) -> ResearchState:
    """Run the production workflow through the same ResearchState contract."""

    from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow

    return MultiAgentWorkflow().run(ResearchState(request=ResearchQuery(query=query)))
