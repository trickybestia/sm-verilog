from enum import IntEnum


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


class Gate:
    mode: GateMode
    outputs: list[int]

    def __init__(self) -> None:
        self.mode = GateMode.AND
        self.outputs = []
