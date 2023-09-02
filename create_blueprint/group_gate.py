from typing import Union

from .logic import LogicId
from .gate import Gate, GateMode


class GroupGate(Gate):
    _output_ready_time: Union[int, None]
    _group_gates: list["GroupGate"]

    def __init__(
        self, id: LogicId, group_gates: list["GroupGate"], mode: GateMode = GateMode.AND
    ) -> None:
        super().__init__(id, mode)

        self._output_ready_time = None
        self._group_gates = group_gates

    def _compute_output_ready_time_internal(self) -> int:
        if self._output_ready_time is None:
            self._output_ready_time = self._max_arrival_time(-1) + 1

        return self._output_ready_time

    def _compute_output_ready_time(self) -> Union[int, None]:
        return max(
            output._compute_output_ready_time_internal() for output in self._group_gates
        )
