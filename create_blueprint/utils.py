from typing import Callable, TypeVar
from bitstring import BitArray

from .gate import Gate
from .port import Port


K = TypeVar("K")
V = TypeVar("V")


def get_or_insert(d: dict[K, V], key: K, default: Callable[[], V]) -> V:
    if key not in d:
        d[key] = default()

    return d[key]


def port_gate_render_name(gate: Gate, port: Port) -> str:
    result = ""

    if len(port.gates) == 1:
        result += port.name
    else:
        result += f"{port.name}[{port.gates.index(gate)}]"

    result += f"\n{gate.mode.name}"

    return result


def parse_yosys_attribute_value(value: str) -> int:
    return BitArray(bin=value).int
