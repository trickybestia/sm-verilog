from enum import StrEnum
from typing import Callable, TypeVar, Union
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


D = TypeVar("D")


def get_yosys_integer_attribute(
    attributes: dict[str, str], name: str, default: D
) -> Union[int, D]:
    if name not in attributes:
        return default

    return BitArray(bin=attributes[name]).int


E = TypeVar("E", bound=StrEnum)
D = TypeVar("D")


def get_yosys_str_enum_attribute(
    attributes: dict[str, str], name: str, enum: type[E], default: D
) -> Union[E, D]:
    if name not in attributes:
        return default

    str_value = attributes[name]

    try:
        value = enum(str_value)
    except ValueError:
        raise ValueError(f'invalid value "{str_value}" for attribute "{name}"')

    return value
