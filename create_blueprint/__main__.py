import argparse
from pathlib import Path

from .block_placer import BlockPlacer
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
        "-s",
        "--show",
        help="show generated flowchart",
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
    parser.add_argument(
        "-r",
        "--rotate-middle-gates-to-input",
        help="rotate middle gates to make their lights visible",
        action="store_true",
    )
    parser.add_argument(
        "-a",
        "--default-attachment",
        help="attach this attachment if input doesn't already has an attachment",
        choices=("switch", "sensor"),
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

    args = parser.parse_args()

    CELLS = generate_cells(args.cell_max_inputs)

    (args.blueprints_path / args.top).mkdir(parents=True, exist_ok=True)

    yosys_output = compile(args.top, args.files, CELLS, args.show, args.blueprints_path)

    circuit = Circuit.from_yosys_output(CELLS, yosys_output, args.top)

    block_placer = BlockPlacer()

    if args.height is not None:
        block_placer.height = args.height
    block_placer.auto_height = args.auto_height
    block_placer.compact = args.compact
    block_placer.rotate_middle_gates_to_input = args.rotate_middle_gates_to_input
    block_placer.default_attachment = args.default_attachment

    blueprint: Blueprint = block_placer.place(circuit)

    blueprint.name = args.top

    blueprint.save(args.blueprints_path / args.top)

    print()
    print()
    print(f"Circuit delay is {circuit.output_ready_time} ticks.")
    print()
    print(
        f'Your blueprint is "{args.blueprints_path / args.top / str(blueprint.uuid)}"'
    )


main()
