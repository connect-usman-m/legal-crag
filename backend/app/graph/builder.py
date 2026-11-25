from collections.abc import Callable
from functools import lru_cache, partial
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.core.config import Settings
from app.graph.nodes.cite import cite
from app.graph.nodes.evaluate import evaluate
from app.graph.nodes.filter_supplement import filter_and_supplement
from app.graph.nodes.generate import generate
from app.graph.nodes.passthrough import passthrough
from app.graph.nodes.retrieve import retrieve
from app.graph.nodes.web_correct import web_correct
from app.graph.state import CRAGState

Node = Callable[..., Any]


def route_after_evaluate(state: CRAGState) -> str:
    return {
        "CORRECT": "passthrough",
        "INCORRECT": "web_correct",
        "AMBIGUOUS": "filter_supplement",
    }[state["retrieval_decision"]]


def build_graph(
    settings: Settings | None = None,
    nodes: dict[str, Node] | None = None,
):
    config = settings or Settings()
    default_nodes: dict[str, Node] = {
        "retrieve": partial(retrieve, settings=config),
        "evaluate": partial(evaluate, settings=config),
        "passthrough": partial(passthrough, keep=config.keep_threshold),
        "web_correct": partial(web_correct, settings=config),
        "filter_supplement": partial(filter_and_supplement, settings=config),
        "generate": partial(generate, settings=config),
        "cite": partial(cite, settings=config),
    }
    chosen = nodes or default_nodes

    builder = StateGraph(CRAGState)
    for name, node in chosen.items():
        builder.add_node(name, node)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "evaluate")
    builder.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "passthrough": "passthrough",
            "web_correct": "web_correct",
            "filter_supplement": "filter_supplement",
        },
    )
    for branch in ("passthrough", "web_correct", "filter_supplement"):
        builder.add_edge(branch, "generate")
    if "cite" in chosen:
        builder.add_edge("generate", "cite")
        builder.add_edge("cite", END)
    else:
        builder.add_edge("generate", END)
    return builder.compile()


@lru_cache(maxsize=1)
def get_graph():
    return build_graph()
