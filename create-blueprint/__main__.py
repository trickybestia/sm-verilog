from sys import argv
from pathlib import Path

from .line_block_placer import LineBlockPlacer
from .blueprint import Blueprint
from .block_placer import BlockPlacer
from .circuit import Circuit


def main():
    yosys_output_path, blueprint_directory_path = (Path(arg) for arg in argv[1:3])

    circuit = Circuit.from_yosys_output(yosys_output_path.read_text())

    block_placer: BlockPlacer = LineBlockPlacer()

    blueprint: Blueprint = block_placer.place(circuit)

    blueprint.name = argv[3]

    blueprint.save(blueprint_directory_path)

    print(f'\n\nYour blueprint is "{blueprint_directory_path / str(blueprint.uuid)}"')


main()
