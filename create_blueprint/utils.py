from typing import Callable, TypeVar

from .gate import Gate
from .port import Port


K = TypeVar("K")
V = TypeVar("V")


def get_or_insert(d: dict[K, V], key: K, default: Callable[[], V]) -> V:
    if key not in d:
        d[key] = default()

    return d[key]


def port_gate_render_name(gate: Gate, port: Port) -> str:
    if len(port.gates) == 1:
        return port.name

    return f"{port.name}[{port.gates.index(gate)}]"
