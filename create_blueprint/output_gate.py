from dataclasses import dataclass

from .utils import port_gate_render_name
from .gate import GateMode
from .logic import LogicId
from .port import Port
from .group_gate import GroupGate


@dataclass
class Output(Port):
    ...


class OutputGate(GroupGate):
    _output: Output

    def __init__(
        self,
        id: LogicId,
        group_gates: list[GroupGate],
        output: Output,
        mode: GateMode = GateMode.AND,
    ) -> None:
        super().__init__(id, group_gates, mode)

        self._output = output

    def _render_name(self) -> str:
        return port_gate_render_name(self, self._output)
