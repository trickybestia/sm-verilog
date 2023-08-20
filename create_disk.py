import argparse
from pathlib import Path

from create_blueprint.blueprint import Blueprint
from create_blueprint.shapes import ShapeId

ZERO_BIT_COLOR = "222222"
ONE_BIT_COLOR = "EEEEEE"


def main():
    parser = argparse.ArgumentParser(
        "create_disk",
        description="Creates blueprint with rectangle with painted bits from specified file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("file", type=Path)
    parser.add_argument("-w", "--stripe-width", type=int)
    parser.add_argument(
        "-b",
        "--blueprints-path",
        help="path to a directory in which blueprints will be stored",
        type=Path,
        default="./blueprints/",
    )

    args = parser.parse_args()

    (args.blueprints_path / args.file.name).mkdir(parents=True, exist_ok=True)

    blueprint = Blueprint()

    blueprint.name = args.file.name

    blueprint.create_solid(ShapeId.Concrete, -1, 0, 0, color="D02525")

    bit_offset = 0

    bit_rows = []

    for byte in args.file.read_bytes():
        for _ in range(8):
            bit = byte & 1
            byte >>= 1

            block_color = ONE_BIT_COLOR if bit else ZERO_BIT_COLOR

            x = bit_offset
            z = 0

            if args.stripe_width is not None:
                x = bit_offset % args.stripe_width
                z = bit_offset // args.stripe_width

            blueprint.create_solid(ShapeId.Concrete, x, 0, z, color=block_color)

            if x == 0:
                bit_rows.append("")

            bit_rows[-1] += str(bit)

            bit_offset += 1

    blueprint.save(args.blueprints_path / args.file.name)

    print(*bit_rows[::-1], sep="\n")


main()
