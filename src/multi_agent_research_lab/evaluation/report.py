"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown.

    TODO(student): Add richer analysis, examples, screenshots, and trace links.
    """

    lines = [
        "# Benchmark Report",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Citation cov. | Failure rate | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        citation = "" if item.citation_coverage is None else f"{item.citation_coverage:.0%}"
        failure = "" if item.failure_rate is None else f"{item.failure_rate:.0%}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} "
            f"| {citation} | {failure} | {item.notes} |"
        )
    lines.extend(["", "## Analysis", ""])
    grouped: dict[str, list[BenchmarkMetrics]] = {}
    for item in metrics:
        grouped.setdefault(item.run_name, []).append(item)
    for name, items in grouped.items():
        avg_latency = sum(item.latency_seconds for item in items) / len(items)
        avg_quality = sum(item.quality_score or 0 for item in items) / len(items)
        failure_rate = sum(item.failure_rate or 0 for item in items) / len(items)
        lines.append(
            f"- **{name}**: average latency {avg_latency:.2f}s, quality {avg_quality:.1f}/10, "
            f"failure rate {failure_rate:.0%}."
        )
    lines.extend([
        "",
        "### Failure modes",
        "",
        "The main observed failure modes are missing evidence, provider/API errors, and "
        "citation loss during synthesis. The benchmark records these as a failed run when "
        "the state contains errors or no final answer. The multi-agent workflow reduces "
        "debugging ambiguity through route history and per-agent trace events, but it can "
        "still cost more latency and amplify an empty-search failure into a low-quality answer.",
        "",
    ])
    return "\n".join(lines)
