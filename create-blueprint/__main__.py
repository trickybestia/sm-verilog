from sys import argv
from pathlib import Path

from .cell import generate_cells

from .simple_block_placer import SimpleBlockPlacer
from .blueprint import Blueprint
from .block_placer import BlockPlacer
from .circuit import Circuit
from .yosys import compile

CELLS = generate_cells(10)
BLUEPRINTS_DIRECTORY = Path("./blueprints/")


def main():
    top_module = argv[1]
    verilog_files = [Path(arg) for arg in argv[2:]]

    (BLUEPRINTS_DIRECTORY / top_module).mkdir(parents=True, exist_ok=True)

    yosys_output = compile(top_module, verilog_files, CELLS, False)

    circuit = Circuit.from_yosys_output(CELLS, yosys_output)

    block_placer: BlockPlacer = SimpleBlockPlacer()

    blueprint: Blueprint = block_placer.place(circuit)

    blueprint.name = top_module

    blueprint.save(BLUEPRINTS_DIRECTORY / top_module)

    print(
        f'\n\nYour blueprint is "{BLUEPRINTS_DIRECTORY / top_module / str(blueprint.uuid)}"'
    )


main()
