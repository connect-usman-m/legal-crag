import operator
from typing import get_args, get_type_hints

from app.graph.state import CRAGState

hints = get_type_hints(CRAGState, include_extras=True)


def test_warnings_use_append_reducer():
    metadata = get_args(hints["warnings"])[1:]

    assert operator.add in metadata


def test_timings_use_merge_reducer():
    metadata = get_args(hints["timings_ms"])[1:]
    merge = next(item for item in metadata if callable(item) and item is not operator.add)

    assert merge({"retrieve": 1}, {"evaluate": 2}) == {"retrieve": 1, "evaluate": 2}
