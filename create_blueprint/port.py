from dataclasses import dataclass
from typing import Tuple, Union
from enum import StrEnum

from .gate import Gate


class GateRotation(StrEnum):
    FORWARD = "forward"
    BACKWARD = "backward"
    TOP = "top"


class StripesOrientation(StrEnum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


class AttachmentRotation(StrEnum):
    FORWARD = "forward"
    BACKWARD = "backward"


class AttachmentName(StrEnum):
    SWITCH = "switch"
    SENSOR = "sensor"


Attachment = Union[Tuple[AttachmentName, AttachmentRotation], None]


@dataclass
class Port:
    name: str
    gates: list[Gate]
    gate_rotation: GateRotation
    attachment: Attachment
    stripe_width: int
    stripes_orientation: StripesOrientation
    override_x: Union[int, None]
    override_y: Union[int, None]
    override_z: Union[int, None]
