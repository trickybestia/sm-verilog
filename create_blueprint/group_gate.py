from typing import Union

from .logic import LogicId
from .gate import Gate, GateMode


class GroupGate(Gate):
    _output_ready_time: int
    _group_gates: list["GroupGate"]

    def __init__(
        self, id: LogicId, group_gates: list["GroupGate"], mode: GateMode = GateMode.AND
    ) -> None:
        super().__init__(id, mode)

        self._output_ready_time = 0
        self._group_gates = group_gates

    def _compute_output_ready_time(self) -> Union[int, None]:
        self._output_ready_time = self._max_arrival_time(-1) + 1

        return max(output._output_ready_time for output in self._group_gates)
