from typing import Tuple

from .circuit import GateMode


CELLS: dict[
    str, Tuple[GateMode, str, str]
] = {  # Cell name -> (gate_mode, cell_inputs, cell_outputs)
    "AND2": (GateMode.AND, "AB", "Y"),
    "AND3": (GateMode.AND, "ABC", "Y"),
    "AND4": (GateMode.AND, "ABCD", "Y"),
    "OR1": (GateMode.OR, "A", "Y"),
    "OR2": (GateMode.OR, "AB", "Y"),
    "OR3": (GateMode.OR, "ABC", "Y"),
    "OR4": (GateMode.OR, "ABCD", "Y"),
    "XOR2": (GateMode.XOR, "AB", "Y"),
    "XOR3": (GateMode.XOR, "ABC", "Y"),
    "XOR4": (GateMode.XOR, "ABCD", "Y"),
    "NAND2": (GateMode.NAND, "AB", "Y"),
    "NAND3": (GateMode.NAND, "ABC", "Y"),
    "NAND4": (GateMode.NAND, "ABCD", "Y"),
    "NOR1": (GateMode.NOR, "A", "Y"),
    "NOR2": (GateMode.NOR, "AB", "Y"),
    "NOR3": (GateMode.NOR, "ABC", "Y"),
    "NOR4": (GateMode.NOR, "ABCD", "Y"),
}
