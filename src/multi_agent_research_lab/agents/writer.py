"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.

        Synthesize the analysis and preserve source citations.
        """
        citations = ", ".join(
            f"[{source.metadata.get('source_id', 'source')}]" for source in state.sources
        ) or "[offline-fallback]"
        evidence = state.analysis_notes or state.research_notes or "No evidence available."
        state.final_answer = (
            f"Research answer for: {state.request.query}\n\n"
            f"{evidence}\n\n"
            f"Citations: {citations}\n"
            "Limitation: conclusions are bounded by the retrieved sources and should be "
            "verified before high-stakes use."
        )
        state.add_trace_event("writer", {"citation_count": len(state.sources)})
        return state
