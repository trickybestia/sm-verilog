from dataclasses import dataclass
from typing import Union

from .utils import port_gate_render_name
from .logic import LogicId
from .port import Port
from .gate import Gate, GateMode


@dataclass
class Input(Port):
    attachment: Union[str, None]


class InputGate(Gate):
    _input: Input

    def __init__(self, id: LogicId, input: Input) -> None:
        super().__init__(id, GateMode.OR)

        self._input = input

    def _render_name(self) -> str:
        return port_gate_render_name(self, self._input)
