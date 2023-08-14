from pathlib import Path
from typing import Any, Tuple
from uuid import UUID, uuid4
import json

from .gate import Gate
from .shapes import ShapeId


class Blueprint:
    uuid: UUID
    name: str
    description: str
    blocks: list[dict[str, Any]]

    def __init__(self):
        self.uuid = uuid4()
        self.name = ""
        self.description = ""
        self.blocks = []

    def create_solid(
        self,
        shape_id: str,
        x: int,
        y: int,
        z: int,
        color: Tuple[str, None] = None,
        xaxis: Tuple[int, None] = None,
        zaxis: Tuple[int, None] = None,
    ):
        if xaxis is None:
            xaxis = -1
        if zaxis is None:
            zaxis = 2

        block = {
            "bounds": {"x": 1, "y": 1, "z": 1},
            "pos": {"x": x, "y": y, "z": z},
            "shapeId": shape_id,
            "xaxis": xaxis,
            "zaxis": zaxis,
        }

        if color is not None:
            block["color"] = color

        self.blocks.append(block)

    def create_switch(
        self,
        x: int,
        y: int,
        z: int,
        id: int,
        gate_id: int,
        color: Tuple[str, None] = None,
        xaxis: Tuple[int, None] = None,
        zaxis: Tuple[int, None] = None,
    ):
        if xaxis is None:
            xaxis = 1
        if zaxis is None:
            zaxis = -2

        block = {
            "controller": {
                "active": False,
                "id": id,
                "controllers": [{"id": gate_id}],
                "joints": None,
            },
            "pos": {"x": x - 1, "y": y + 1, "z": z},
            "shapeId": ShapeId.Switch,
            "xaxis": xaxis,
            "zaxis": zaxis,
        }

        if color is not None:
            block["color"] = color

        self.blocks.append(block)

    def create_gate(
        self,
        id: int,
        gate: Gate,
        x: int,
        y: int,
        z: int,
        color: Tuple[str, None] = None,
        xaxis: Tuple[int, None] = None,
        zaxis: Tuple[int, None] = None,
    ):
        if xaxis is None:
            xaxis = -1
        if zaxis is None:
            zaxis = 2

        block = {
            "pos": {"x": x, "y": y, "z": z},
            "controller": {
                "active": False,
                "id": id,
                "controllers": [{"id": output} for output in gate.outputs],
                "joints": None,
                "mode": int(gate.mode),
            },
            "shapeId": ShapeId.Gate,
            "xaxis": xaxis,
            "zaxis": zaxis,
        }

        if color is not None:
            block["color"] = color

        self.blocks.append(block)

    def save(self, path: Path):
        path /= str(self.uuid)

        path.mkdir(parents=True)

        (path / "description.json").write_text(
            json.dumps(
                {
                    "description": self.description,
                    "localId": str(self.uuid),
                    "name": self.name,
                    "type": "Blueprint",
                    "version": 0,
                }
            )
        )
        (path / "blueprint.json").write_text(
            json.dumps({"bodies": [{"childs": self.blocks}], "version": 4})
        )
