from subprocess import run, PIPE, STDOUT
from pathlib import Path

from .gate import GateMode

from .cell import Cell


def _create_gate_formula(
    mode: GateMode, inputs: list[str], and_sign: str, or_sign: str
) -> str:
    match mode:
        case GateMode.AND:
            return and_sign.join(inputs)
        case GateMode.OR:
            return or_sign.join(inputs)
        case GateMode.XOR:
            return " ^ ".join(inputs)
        case GateMode.NAND:
            return f"!({and_sign.join(inputs)})"
        case GateMode.NOR:
            return f"!({or_sign.join(inputs)})"
        case GateMode.XNOR:
            return f"!({' ^ '.join(inputs)})"


def _create_cells_liberty(cells: dict[str, Cell]) -> str:
    result = "library(scrap_mechanic_cells) {\n"

    for name, cell in cells.items():
        result += f"\tcell({name}) {{\n"

        for input in cell.inputs:
            result += f"\t\tpin({input}) {{ direction: input; }}\n"

        result += f"\t\tpin({cell.output}) {{ direction: output; function: \"{_create_gate_formula(cell.mode, cell.inputs, ' * ', ' + ')}\"; }}\n"

        result += "\t}\n\n"

    result += "}\n"

    return result


def _create_cells_verilog(cells: dict[str, Cell]) -> str:
    result = ""

    for name, cell in cells.items():
        result += f"module {name}({', '.join(cell.inputs + [cell.output])});\n"

        result += f"\tinput {', '.join(cell.inputs)};\n"

        result += f"\toutput {cell.output} = {_create_gate_formula(cell.mode, cell.inputs, ' & ', ' | ')};\n"

        result += "endmodule\n\n"

    return result


def _create_yosys_script(top_module: str, files: list[str], show: bool) -> str:
    return f"""
read -sv {" ".join(f'"{file}"' for file in files)}
synth -flatten -top {top_module}
abc -liberty scrap_mechanic_cells.lib
opt
{"" if show else "#"}show -lib scrap_mechanic_cells.sv {top_module}
write_json ./blueprints/{top_module}/{top_module}.json
"""


def compile(
    top_module: str, files: list[str], cells: dict[str, Cell], show: bool
) -> str:
    Path("scrap_mechanic_cells.lib").write_text(_create_cells_liberty(cells))
    Path("scrap_mechanic_cells.sv").write_text(_create_cells_verilog(cells))

    run(
        "yosys",
        check=True,
        input=_create_yosys_script(top_module, files, show).encode(),
    )

    print("pog")

    return Path(f"./blueprints/{top_module}/{top_module}.json").read_text()
