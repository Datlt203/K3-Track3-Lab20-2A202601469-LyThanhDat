"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.

        Compare collected evidence and identify reliability limits.
        """
        if not state.research_notes:
            state.errors.append("Analyst received no research notes")
            state.analysis_notes = "No evidence was available for analysis."
        else:
            state.analysis_notes = (
                "Evidence comparison:\n"
                f"{state.research_notes}\n\n"
                "Reliability assessment: source-backed observations are separated from "
                "inference; offline or synthetic evidence should not support universal claims. "
                "Compare the result with a simpler single-agent baseline."
            )
        state.add_trace_event("analyst", {"has_research_notes": bool(state.research_notes)})
        return state
