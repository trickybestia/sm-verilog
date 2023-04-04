from enum import IntEnum


class GateMode(IntEnum):
    AND = 0  # magic numbers from Scrap Mechanic blueprint files
    OR = 1
    XOR = 2
    NAND = 3
    NOR = 4
    XNOR = 5
