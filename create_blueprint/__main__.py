import argparse
from pathlib import Path

from .graphviz import render_circuit
from .block_placer import BlockPlacer, BlockPlacerOptions
from .cell import generate_cells
from .blueprint import Blueprint
from .circuit import Circuit
from .yosys import compile


def positive_int(s: str) -> int:
    i = int(s)

    if i <= 0:
        raise ValueError(f'"{i}" must be > 0')

    return i


def existing_path(s: str) -> Path:
    path = Path(s)

    if not path.exists():
        raise ValueError(f'"{path}" does not exist')

    return path


def main():
    parser = argparse.ArgumentParser(
        prog="create_blueprint",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "files",
        metavar="file",
        help="SystemVerilog file to be compiled",
        nargs="+",
        type=existing_path,
    )
    parser.add_argument(
        "-m",
        "--module-flowchart",
        help="generate module flowchart",
        action="store_true",
    )
    parser.add_argument(
        "-g",
        "--gates-flowchart",
        help="generate gates flowchart",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--top",
        help="specify top module name",
        required=True,
    )
    parser.add_argument(
        "-i",
        "--cell-max-inputs",
        help="use gates with less or equal count of inputs",
        type=int,
        default=10,
    )
    parser.add_argument(
        "-b",
        "--blueprints-path",
        help="path to a directory in which blueprints will be stored",
        type=Path,
        default="./blueprints/",
    )

    block_placer_arguments_parser = parser.add_mutually_exclusive_group(required=True)
    block_placer_arguments_parser.add_argument(
        "--height",
        help="height of middle gates layer",
        type=positive_int,
    )
    block_placer_arguments_parser.add_argument(
        "--auto-height",
        help="automatically calculate middle gates layer height to make it look like square",
        action="store_true",
    )
    block_placer_arguments_parser.add_argument(
        "-c",
        "--compact",
        help="compact middle gates layer to one block",
        action="store_true",
    )
    block_placer_arguments_parser.add_argument(
        "--cubic",
        help="give middle gates layer shape of cube",
        action="store_true",
    )

    args = parser.parse_args()

    CELLS = generate_cells(args.cell_max_inputs)

    (args.blueprints_path / args.top).mkdir(parents=True, exist_ok=True)

    module_flowchart_prefix = None

    if args.module_flowchart:
        module_flowchart_prefix = args.blueprints_path / args.top / f"module"

    yosys_output = compile(
        args.top, args.files, CELLS, module_flowchart_prefix, args.blueprints_path
    )

    circuit = Circuit.from_yosys_output(CELLS, yosys_output, args.top)

    block_placer_options = BlockPlacerOptions(
        args.height,
        args.compact,
        args.auto_height,
        args.cubic,
    )

    blueprint: Blueprint = BlockPlacer.place(circuit, block_placer_options)

    blueprint.name = args.top

    blueprint.save(args.blueprints_path / args.top)

    print("\n")

    if args.module_flowchart:
        print(f'Module flowchart is "{module_flowchart_prefix}.dot"\n')

    if args.gates_flowchart:
        path = args.blueprints_path / args.top / "gates.dot"
        dot = render_circuit(circuit)

        path.write_text(dot)

        print(f'Gates flowchart is "{path}"\n')

    print(f"Circuit delay is {circuit.output_ready_time} ticks.\n")

    blocks_count = {}

    for block in blueprint.blocks:
        block_count = blocks_count.get(block["shapeId"], 0)

        blocks_count[block["shapeId"]] = block_count + 1

    print("Blocks count:")

    for shape_id, block_count in sorted(
        blocks_count.items(), key=lambda item: item[1], reverse=True
    ):
        print(f"\t{shape_id.name}: {block_count}")

    print(f"\n\tTotal: {len(blueprint.blocks)}\n")

    print(
        f'Your blueprint is "{args.blueprints_path / args.top / str(blueprint.uuid)}"'
    )


main()
