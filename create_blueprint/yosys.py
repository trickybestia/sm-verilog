from subprocess import run
from pathlib import Path

from .gate import GateMode
from .cell import Cell


def _create_gate_formula(mode: GateMode, inputs: list[str]) -> str:
    match mode:
        case GateMode.AND:
            return " * ".join(inputs)
        case GateMode.OR:
            return " + ".join(inputs)
        case GateMode.XOR:
            return " ^ ".join(inputs)
        case GateMode.NAND:
            return f"!({' * '.join(inputs)})"
        case GateMode.NOR:
            return f"!({' + '.join(inputs)})"
        case GateMode.XNOR:
            return f"!({' ^ '.join(inputs)})"


def _create_cells_liberty(cells: dict[str, Cell]) -> str:
    result = """library(scrap_mechanic_cells) {
\tcell(DFF) {
\t\tff(IQ, IQN) { clocked_on: C; next_state: D; }
\t\tpin(C) { direction: input; clock: true; }
\t\tpin(D) { direction: input; }
\t\tpin(Q) { direction: output; function: "IQ"; }
\t}

"""

    for name, cell in cells.items():
        result += f"\tcell({name}) {{\n"

        for input in cell.inputs:
            result += f"\t\tpin({input}) {{ direction: input; }}\n"

        result += f'\t\tpin({cell.output}) {{ direction: output; function: "{_create_gate_formula(cell.mode, cell.inputs)}"; }}\n'

        result += "\t}\n\n"

    result += "}\n"

    return result


def _create_cells_verilog(cells: dict[str, Cell]) -> str:
    result = "module DFF(input C, input D, output reg Q);\nendmodule\n\n"

    for name, cell in cells.items():
        result += f"module {name}({', '.join([f'input {input}' for input in cell.inputs] + [f'output {cell.output}'])});\n"

        result += "endmodule\n\n"

    return result


def _create_yosys_script(
    top_module: str, files: list[Path], show: bool, blueprints_path: Path
) -> str:
    return f"""
read_verilog -sv {" ".join(f'"{file}"' for file in files)}
synth -flatten -top {top_module}
dfflibmap -liberty scrap_mechanic_cells.lib
abc -liberty scrap_mechanic_cells.lib
opt
{f"show -lib scrap_mechanic_cells.sv {top_module}" if show else ""}
write_json {blueprints_path / top_module / f"{top_module}.json"}
"""


def compile(
    top_module: str,
    files: list[str],
    cells: dict[str, Cell],
    show: bool,
    blueprints_path: Path,
) -> str:
    Path("scrap_mechanic_cells.lib").write_text(_create_cells_liberty(cells))
    Path("scrap_mechanic_cells.sv").write_text(_create_cells_verilog(cells))

    run(
        "yosys",
        check=True,
        input=_create_yosys_script(top_module, files, show, blueprints_path).encode(),
    )

    return (blueprints_path / top_module / f"{top_module}.json").read_text()
