from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_first() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    SupervisorAgent().run(state)

    assert state.route_history == ["researcher"]


def test_supervisor_routes_workers_in_order() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        sources=[
            SourceDocument(
                title="Research source",
                snippet="Evidence about multi-agent systems.",
            )
        ],
        research_notes="Collected evidence.",
    )
    supervisor = SupervisorAgent()

    supervisor.run(state)
    assert state.route_history == ["analyst"]

    state.analysis_notes = "Compared the evidence and assessed source reliability."
    supervisor.run(state)
    assert state.route_history == ["analyst", "writer"]


def test_supervisor_stops_after_writing() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        final_answer="A completed answer with citations.",
    )

    SupervisorAgent().run(state)

    assert state.route_history == ["done"]
