from enum import IntEnum

from .logic import Logic


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

    def __init__(self) -> None:
        super().__init__()

        self.mode = GateMode.AND

    def compute_output_ready_time(self, max_arrival_time: int):
        self.output_ready_time = max_arrival_time + 1
