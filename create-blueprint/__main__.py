from json import loads, dumps
from sys import argv
from typing import Any, TypedDict
from uuid import uuid4
from pathlib import Path

from .cells import CELLS, GateMode
from .color_generator import ColorGenerator

# Type of buffer gate, which just passes signal through itself.
# Needed for inputs and outputs - doesn't do timings stuff.
BUFFER_GATE_MODE = GateMode.AND


class DependentController(TypedDict):
    id: int


controllers: dict[
    int, list[DependentController]
] = {}  # Controller ID -> dependent controllers IDs
nets: dict[int, list[int]] = {}  # Net ID -> dependent controllers IDs
nets_owners: dict[int, int] = {}  # Net ID -> Controller ID


def create_gate(
    mode: GateMode, x: int, y: int, z: int, id: int, color: str = "DF7F00"
) -> Any:
    dependent_controllers = []

    controllers[id] = dependent_controllers

    return {
        "color": color,
        "pos": {"x": x, "y": y, "z": z},
        "controller": {
            "active": False,
            "id": id,
            "controllers": dependent_controllers,
            "joints": None,
            "mode": int(mode),
        },
        "shapeId": "9f0f56e8-2c31-4d83-996c-d00a9b296c3f",
        "xaxis": -1,
        "zaxis": 2,
    }


def create_concrete(x: int, y: int, z: int) -> Any:
    return {
        "bounds": {"x": 1, "y": 1, "z": 1},
        "color": "8D8F89",
        "pos": {"x": x, "y": y, "z": z},
        "shapeId": "a6c6ce30-dd47-4587-b475-085d55c6a3b4",
        "xaxis": -1,
        "zaxis": 2,
    }


def create_switch(x: int, y: int, z: int, id: int, controller_id: int) -> Any:
    return {
        "color": "DF7F01",
        "controller": {
            "active": False,
            "controllers": [{"id": controller_id}],
            "id": id,
            "joints": None,
        },
        "pos": {"x": x - 1, "y": y + 1, "z": z},
        "shapeId": "7cf717d7-d167-4f2d-a6e7-6b2c70aa3986",
        "xaxis": 1,
        "zaxis": -2,
    }


def create_d_flip_flop(x: int, y: int, z: int, id: int) -> list[Any]:
    dependent_controllers = [{"id": id + 3}]

    controllers[id + 1] = dependent_controllers

    return [
        {  # D, C
            "color": "EEEEEE",
            "controller": {
                "active": False,
                "controllers": [{"id": id + 1}],
                "id": id,
                "joints": None,
                "mode": 0,
            },
            "pos": {"x": x, "y": y, "z": z},
            "shapeId": "9f0f56e8-2c31-4d83-996c-d00a9b296c3f",
            "xaxis": -1,
            "zaxis": 2,
        },
        {  # Q
            "color": "DF7F00",
            "controller": {
                "active": False,
                "controllers": dependent_controllers,
                "id": id + 1,
                "joints": None,
                "mode": 1,
            },
            "pos": {"x": x, "y": y, "z": z + 1},
            "shapeId": "9f0f56e8-2c31-4d83-996c-d00a9b296c3f",
            "xaxis": -1,
            "zaxis": 2,
        },
        {  # C
            "color": "222222",
            "controller": {
                "active": False,
                "controllers": [{"id": id + 1}],
                "id": id + 2,
                "joints": None,
                "mode": 4,
            },
            "pos": {"x": x, "y": y, "z": z + 2},
            "shapeId": "9f0f56e8-2c31-4d83-996c-d00a9b296c3f",
            "xaxis": -1,
            "zaxis": 2,
        },
        {
            "color": "DF7F00",
            "controller": {
                "active": True,
                "controllers": [{"id": id + 2}],
                "id": id + 3,
                "joints": None,
                "mode": 4,
            },
            "pos": {"x": x, "y": y, "z": z + 3},
            "shapeId": "9f0f56e8-2c31-4d83-996c-d00a9b296c3f",
            "xaxis": -1,
            "zaxis": 2,
        },
    ]


def main():
    source_path, blueprint_directory_path = (Path(arg) for arg in argv[1:3])
    blueprint_name = argv[3]

    source = loads(source_path.read_text())

    description = ""
    blueprint = []
    gate_id = 0

    modules = source["modules"]
    module = modules[blueprint_name]

    ports = module["ports"]
    cells = module["cells"]

    input_ports_offset = 0
    output_ports_offset = 0
    cells_offset = 0

    color_generator = ColorGenerator()

    description += "Inputs:\n\n"

    blueprint.append(create_concrete(0, -1, 0))

    for port_name in ports:
        port = ports[port_name]

        if port["direction"] == "input":
            color = color_generator.next_color()

            description += f"{port_name}: {color.name}\n"

            port_bits = port["bits"]

            for bit in port_bits:
                nets[bit] = []
                nets_owners[bit] = gate_id

                blueprint.append(
                    create_gate(
                        BUFFER_GATE_MODE, input_ports_offset, 0, 0, gate_id, color.hex
                    )
                )

                blueprint.append(create_concrete(input_ports_offset, -2, 0))
                blueprint.append(
                    create_switch(input_ports_offset, -2, 1, gate_id + 1, gate_id)
                )

                gate_id += 2
                input_ports_offset += 1

    for cell in cells.values():
        connections = cell["connections"]

        if cell["type"] == "DFF":
            net_id = connections["Q"][0]
            nets_owners[net_id] = gate_id + 1

            if net_id not in nets:
                nets[net_id] = []

            nets[connections["C"][0]].extend([gate_id, gate_id + 2])
            nets[connections["D"][0]].append(gate_id)

            blueprint.extend(create_d_flip_flop(cells_offset, 1, 0, gate_id))

            gate_id += 4
        else:
            gate_mode, inputs, outputs = CELLS[cell["type"]]

            for output in outputs:
                net_id = connections[output][0]
                nets[net_id] = []
                nets_owners[net_id] = gate_id

            blueprint.append(create_gate(gate_mode, cells_offset, 1, 0, gate_id))

            for input in inputs:
                if connections[input][0] not in nets:
                    nets[connections[input][0]] = []

                nets[connections[input][0]].append(gate_id)

            gate_id += 1

        cells_offset += 1

    color_generator.reset()

    description += "\nOutputs:\n\n"

    for port_name in ports:
        port = ports[port_name]

        if port["direction"] == "output":
            color = color_generator.next_color()

            description += f"{port_name}: {color.name}\n"

            port_bits = port["bits"]

            for bit in port_bits:
                blueprint.append(
                    create_gate(
                        BUFFER_GATE_MODE, output_ports_offset, 2, 0, gate_id, color.hex
                    )
                )

                if bit != "0":  # Looks like output is always equal to zero
                    nets[bit].append(gate_id)

                gate_id += 1
                output_ports_offset += 1

    for net in nets:
        owner = nets_owners[net]

        for dependent in nets[net]:
            controllers[owner].append({"id": dependent})

    blueprint = {"bodies": [{"childs": blueprint}], "version": 4}

    blueprint_uuid = uuid4()

    blueprint_directory_path /= str(blueprint_uuid)

    blueprint_directory_path.mkdir()

    (blueprint_directory_path / "blueprint.json").write_text(dumps(blueprint))
    (blueprint_directory_path / "description.json").write_text(
        dumps(
            {
                "description": description,
                "localId": str(blueprint_uuid),
                "name": blueprint_name,
                "type": "Blueprint",
                "version": 0,
            }
        )
    )

    print(f'Your blueprint is "{blueprint_directory_path}"')


main()
