from pathlib import Path
from typing import Any, Union
from uuid import UUID, uuid4
import json

from .port import AttachmentRotation, GateRotation
from .logic import LogicId
from .timer import Timer
from .gate import Gate
from .shapes import ShapeId

_DEFAULT_COLOR = "222222"


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
        color: Union[str, None] = None,
    ):
        if color is None:
            color = _DEFAULT_COLOR

        block = {
            "bounds": {"x": 1, "y": 1, "z": 1},
            "pos": {"x": x, "y": y, "z": z},
            "shapeId": shape_id,
            "xaxis": -1,
            "zaxis": 2,
            "color": color,
        }

        self.blocks.append(block)

    def create_sensor(
        self,
        x: int,
        y: int,
        z: int,
        id: LogicId,
        gate_id: LogicId,
        rotation: AttachmentRotation,
        color: Union[str, None] = _DEFAULT_COLOR,
    ):
        match rotation:
            case AttachmentRotation.BACKWARD:
                x -= 1
                y += 1
                z += 1

                xaxis = -3
                zaxis = -2
            case AttachmentRotation.FORWARD:
                z += 1

                xaxis = -3
                zaxis = 2

        if color is None:
            color = _DEFAULT_COLOR

        block = {
            "controller": {
                "audioEnabled": False,
                "buttonMode": True,
                "colorMode": True,
                "color": "EEEEEE",
                "range": 1,
                "id": id,
                "controllers": [{"id": gate_id}],
                "joints": None,
            },
            "pos": {"x": x, "y": y, "z": z},
            "shapeId": ShapeId.Sensor,
            "xaxis": xaxis,
            "zaxis": zaxis,
            "color": color,
        }

        self.blocks.append(block)

    def create_switch(
        self,
        x: int,
        y: int,
        z: int,
        id: LogicId,
        gate_id: LogicId,
        rotation: AttachmentRotation,
        color: Union[str, None] = None,
    ):
        match rotation:
            case AttachmentRotation.BACKWARD:
                y += 1

                xaxis = -1
                zaxis = 0
            case AttachmentRotation.FORWARD:
                x -= 1

                xaxis = 1
                zaxis = 3

        if color is None:
            color = _DEFAULT_COLOR

        block = {
            "controller": {
                "active": False,
                "id": id,
                "controllers": [{"id": gate_id}],
                "joints": None,
            },
            "pos": {"x": x, "y": y, "z": z},
            "shapeId": ShapeId.Switch,
            "xaxis": xaxis,
            "zaxis": zaxis,
            "color": color,
        }

        self.blocks.append(block)

    def create_timer(
        self,
        timer: Timer,
        x: int,
        y: int,
        z: int,
        color: Union[str, None] = None,
        xaxis: Union[int, None] = None,
        zaxis: Union[int, None] = None,
    ):
        if timer.ticks > 2400:
            raise ValueError(f"timer.ticks ({timer.ticks}) must be < 2400")

        if xaxis is None:
            xaxis = -1
        if zaxis is None:
            zaxis = 2
        if color is None:
            color = _DEFAULT_COLOR

        block = {
            "pos": {"x": x, "y": y, "z": z},
            "controller": {
                "active": False,
                "id": timer.id,
                "controllers": [{"id": output.id} for output in timer.outputs],
                "joints": None,
                "seconds": timer.ticks // 40,
                "ticks": timer.ticks % 40,
            },
            "shapeId": ShapeId.Timer,
            "xaxis": xaxis,
            "zaxis": zaxis,
            "color": color,
        }

        self.blocks.append(block)

    def create_gate(
        self,
        gate: Gate,
        x: int,
        y: int,
        z: int,
        rotation: GateRotation,
        color: Union[str, None] = None,
    ):
        match rotation:
            case GateRotation.TOP:
                xaxis = -1
                zaxis = 2
            case GateRotation.BACKWARD:
                y += 1

                xaxis = -1
                zaxis = 0
            case GateRotation.FORWARD:
                x -= 1

                xaxis = 1
                zaxis = 0

        if color is None:
            color = _DEFAULT_COLOR

        block = {
            "pos": {"x": x, "y": y, "z": z},
            "controller": {
                "active": False,
                "id": gate.id,
                "controllers": [{"id": output.id} for output in gate.outputs],
                "joints": None,
                "mode": int(gate.mode),
            },
            "shapeId": ShapeId.Gate,
            "xaxis": xaxis,
            "zaxis": zaxis,
            "color": color,
        }

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
