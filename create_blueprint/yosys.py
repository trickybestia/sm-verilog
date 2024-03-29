from subprocess import run
from pathlib import Path
from typing import Union

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
    result = "module SYNC_SR_LATCH(input C, input S, input R, output Q);\nendmodule\n\n"

    for name, cell in cells.items():
        result += f"module {name}({', '.join([f'input {input}' for input in cell.inputs] + [f'output {cell.output}'])});\n"

        result += "endmodule\n\n"

    return result


def _create_yosys_script(
    top_module: str,
    files: list[str],
    module_flowchart_prefix: Union[str, None],
    blueprints_path: Path,
) -> str:
    return f"""
read_verilog -sv {" ".join(f'"{file}"' for file in files)}

hierarchy -check -top {top_module}
proc
flatten
opt_expr
opt_clean
check
opt -nodffe -nosdff -full
fsm
opt -full
wreduce
peepopt
opt_clean
alumacc
share
opt -full
memory -nomap
opt_clean
opt -full
memory_map
opt -full
techmap; opt -full

dfflegalize -cell $_DFF_P_ x
opt -nodffe -nosdff -full
techmap -map resources/ff_map.sv
techmap; opt -full
abc -liberty resources/scrap_mechanic_cells.lib -dff
techmap -map resources/buf_map.sv
opt -full

{f"show -lib resources/scrap_mechanic_cells.sv -format dot -viewer none -stretch -prefix {module_flowchart_prefix} {top_module}" if module_flowchart_prefix is not None else ""}
write_json {blueprints_path / top_module / f"{top_module}.json"}
stat
"""


def compile(
    top_module: str,
    files: list[str],
    cells: dict[str, Cell],
    module_flowchart_prefix: Union[str, None],
    blueprints_path: Path,
) -> str:
    Path("resources/scrap_mechanic_cells.lib").write_text(_create_cells_liberty(cells))
    Path("resources/scrap_mechanic_cells.sv").write_text(_create_cells_verilog(cells))

    run(
        ["yosys", "-s", "-"],
        check=True,
        input=_create_yosys_script(
            top_module, files, module_flowchart_prefix, blueprints_path
        ).encode(),
    )

    return (blueprints_path / top_module / f"{top_module}.json").read_text()
