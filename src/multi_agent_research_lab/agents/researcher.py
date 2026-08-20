"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.

        Search, retain provenance, and create citation-ready notes.
        """
        state.sources = SearchClient().search(state.request.query, state.request.max_sources)
        state.research_notes = "\n".join(
            f"[{source.metadata.get('source_id', f'source-{index}')}] "
            f"{source.title}: {source.snippet}"
            for index, source in enumerate(state.sources, 1)
        )
        state.add_trace_event("researcher", {"source_count": len(state.sources)})
        return state
