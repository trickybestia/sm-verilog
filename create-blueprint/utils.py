from typing import Callable, TypeVar


K = TypeVar("K")
V = TypeVar("V")


def get_or_insert(d: dict[K, V], key: K, default: Callable[[], V]) -> V:
    if key not in d:
        d[key] = default()

    return d[key]
