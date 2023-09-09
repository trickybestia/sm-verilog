from functools import cached_property
from typing import Union

from .logic import LogicId
from .gate import Gate, GateMode


class GroupGate(Gate):
    _group_gates: list["GroupGate"]

    @cached_property
    def _output_ready_time(self) -> int:
        return self._max_arrival_time(-1) + 1

    @property
    def requires_inputs_buffering(self) -> bool:
        return True

    def __init__(
        self, id: LogicId, group_gates: list["GroupGate"], mode: GateMode = GateMode.AND
    ) -> None:
        super().__init__(id, mode)

        self._group_gates = group_gates

    def _compute_output_ready_time(self) -> Union[int, None]:
        return max((gate._output_ready_time for gate in self._group_gates), default=0)
