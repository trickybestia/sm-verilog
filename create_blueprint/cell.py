from dataclasses import dataclass

from .gate import GateMode


@dataclass
class Cell:
    mode: GateMode
    inputs: list[str]
    output: str


def _input_name(i: int) -> str:
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXZabcdefghijklmnopqrstuvwxyz"

    if i == 0:
        return ALPHABET[0]

    result = ""

    while i != 0:
        result += ALPHABET[i % len(ALPHABET)]
        i //= len(ALPHABET)

    return result[::-1]


def generate_cells(inputs_count: int) -> dict[str, Cell]:
    result: dict[str, Cell] = {
        "NAND1": Cell(GateMode.NAND, [_input_name(0)], "Y"),
        "AND1": Cell(GateMode.AND, [_input_name(0)], "Y"),
    }

    for mode in (
        GateMode.AND,
        GateMode.OR,
        GateMode.XOR,
        GateMode.NAND,
        GateMode.NOR,
        GateMode.XNOR,
    ):
        for i in range(2, inputs_count + 1):
            result[f"{mode.name}{i}"] = Cell(
                mode, [_input_name(j) for j in range(i)], "Y"
            )

    return result
