"""The default cache key must accept hashable keys that are not orderable."""

from enum import Enum

from langgraph.cache.memory import InMemoryCache

from langgraph._internal._cache import _freeze, default_cache_key
from langgraph.func import entrypoint, task
from langgraph.types import CachePolicy


class Color(Enum):
    RED = 1
    BLUE = 2


def test_cache_key_accepts_unorderable_mapping_keys() -> None:
    mapping = {Color.RED: "r", Color.BLUE: "b"}
    assert default_cache_key(x=mapping) == default_cache_key(
        x=dict(reversed(list(mapping.items())))
    )


def test_cache_key_accepts_heterogeneous_mapping_keys() -> None:
    assert default_cache_key(x={1: "one", "two": 2})
    assert default_cache_key(x={None: 0, "a": 1})


def test_cache_key_keeps_natural_order_for_sortable_mapping_keys() -> None:
    # Mappings whose keys are comparable keep the canonical form they had
    # before this fix, so cache entries persisted by earlier versions stay
    # valid.
    assert _freeze({"b": 1, "aa": 2}) == (("aa", 2), ("b", 1))


def test_cached_task_with_unorderable_mapping_keys_runs_once() -> None:
    runs: list[int] = []

    @task(cache_policy=CachePolicy())
    def count(x: dict) -> int:
        runs.append(1)
        return len(x)

    @entrypoint(cache=InMemoryCache())
    def workflow(reverse: bool) -> int:
        items = [(Color.RED, "r"), (Color.BLUE, "b")]
        if reverse:
            items.reverse()
        return count(x=dict(items)).result()

    assert workflow.invoke(False) == 2
    assert runs == [1]
    # Reversing the insertion order must still hit the cached entry.
    assert workflow.invoke(True) == 2
    assert runs == [1]
