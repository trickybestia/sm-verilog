from enum import IntEnum
from typing import Union

from .logic import Logic, LogicId


class GateMode(IntEnum):
    """
    Magic numbers taken from Scrap Mechanic blueprint files.
    """

    AND = 0
    OR = 1
    XOR = 2
    NAND = 3
    NOR = 4
    XNOR = 5


class Gate(Logic):
    mode: GateMode

    def __init__(self, id: LogicId, mode: GateMode = GateMode.AND) -> None:
        super().__init__(id)

        self.mode = mode

    def _compute_output_ready_time(self) -> Union[int, None]:
        return self._max_arrival_time(-1) + 1
