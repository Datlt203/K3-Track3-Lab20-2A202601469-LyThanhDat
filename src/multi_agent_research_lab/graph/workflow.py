"""LangGraph workflow orchestration."""

from typing import Any

from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import traced


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def build(self) -> object:
        """Create a LangGraph graph.

        Create supervisor -> worker conditional routing with a bounded stop path.
        """
        from langgraph.graph import END, StateGraph

        graph = StateGraph(dict)
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("researcher", self._researcher_node)
        graph.add_node("analyst", self._analyst_node)
        graph.add_node("writer", self._writer_node)
        graph.set_entry_point("supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._next_route,
            {"researcher": "researcher", "analyst": "analyst", "writer": "writer", "done": END},
        )
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", END)
        return graph.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state.

        Compile and invoke the graph, preserving the Pydantic state contract.
        """
        graph = self.build()
        result = graph.invoke(state.model_dump())
        return ResearchState.model_validate(result)

    @staticmethod
    def _next_route(value: dict[str, Any]) -> str:
        return value["route_history"][-1]

    @staticmethod
    @traced("multi-agent.supervisor")
    def _supervisor_node(value: dict[str, Any]) -> dict[str, Any]:
        return SupervisorAgent().run(ResearchState.model_validate(value)).model_dump()

    @staticmethod
    @traced("multi-agent.researcher")
    def _researcher_node(value: dict[str, Any]) -> dict[str, Any]:
        return ResearcherAgent().run(ResearchState.model_validate(value)).model_dump()

    @staticmethod
    @traced("multi-agent.analyst")
    def _analyst_node(value: dict[str, Any]) -> dict[str, Any]:
        return AnalystAgent().run(ResearchState.model_validate(value)).model_dump()

    @staticmethod
    @traced("multi-agent.writer")
    def _writer_node(value: dict[str, Any]) -> dict[str, Any]:
        return WriterAgent().run(ResearchState.model_validate(value)).model_dump()
