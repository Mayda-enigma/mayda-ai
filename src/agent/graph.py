"""LangGraph construction for the nutrition analysis agent."""

from langgraph.graph import END, StateGraph

from src.agent.nodes import critique_node, estimate_calories_node, identify_food_node, input_node
from src.agent.state import AgentState


def _route(state: AgentState) -> str:
    """Route based on error state."""
    return "end" if state.get("error") else "continue"


def build_graph():
    """Construct and compile the nutrition analysis graph."""
    g = StateGraph(AgentState)

    g.add_node("input", input_node)
    g.add_node("identify_food", identify_food_node)
    g.add_node("estimate_calories", estimate_calories_node)
    g.add_node("critique", critique_node)

    g.set_entry_point("input")

    g.add_conditional_edges(
        "input",
        _route,
        {
            "continue": "identify_food",
            "end": END,
        },
    )
    g.add_conditional_edges(
        "identify_food",
        _route,
        {
            "continue": "estimate_calories",
            "end": END,
        },
    )
    g.add_conditional_edges(
        "estimate_calories",
        _route,
        {
            "continue": "critique",
            "end": END,
        },
    )
    g.add_edge("critique", END)

    return g.compile()


# Module-level singleton — compiled once at startup, reused across requests
food_agent = build_graph()
