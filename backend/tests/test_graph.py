import pytest

from app.graph.builder import build_graph, get_graph, route_after_evaluate


def test_get_graph_is_cached():
    assert get_graph() is get_graph()


def test_route_after_evaluate():
    assert route_after_evaluate({"retrieval_decision": "CORRECT"}) == "passthrough"
    assert route_after_evaluate({"retrieval_decision": "INCORRECT"}) == "web_correct"
    assert route_after_evaluate({"retrieval_decision": "AMBIGUOUS"}) == "filter_supplement"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("decision", "expected_node"),
    [
        ("CORRECT", "passthrough"),
        ("INCORRECT", "web_correct"),
        ("AMBIGUOUS", "filter_supplement"),
    ],
)
async def test_graph_takes_each_branch(decision, expected_node):
    visited = []

    async def retrieve(state):
        visited.append("retrieve")
        return {"retrieved": []}

    async def evaluate(state):
        visited.append("evaluate")
        return {"retrieval_decision": decision, "chunk_scores": []}

    async def passthrough(state):
        visited.append("passthrough")
        return {"context_sources": [], "chunk_scores": []}

    async def web_correct(state):
        visited.append("web_correct")
        return {"context_sources": [], "warnings": []}

    async def filter_supplement(state):
        visited.append("filter_supplement")
        return {"context_sources": [], "warnings": []}

    async def generate(state):
        visited.append("generate")
        return {"draft_answer": "draft", "abstained": False, "used_source_ids": []}

    graph = build_graph(
        nodes={
            "retrieve": retrieve,
            "evaluate": evaluate,
            "passthrough": passthrough,
            "web_correct": web_correct,
            "filter_supplement": filter_supplement,
            "generate": generate,
        }
    )

    await graph.ainvoke({"question": "q", "mode": "crag", "warnings": [], "timings_ms": {}})

    assert visited == ["retrieve", "evaluate", expected_node, "generate"]
