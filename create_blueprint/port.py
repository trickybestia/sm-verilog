from dataclasses import dataclass
from typing import Literal, Union

from .gate import Gate


@dataclass
class Port:
    name: str
    gates: list[Gate]
    rotate_to_inputs: bool
    stripe_width: int
    stripes_orientation: Union[Literal["vertical"], Literal["horizontal"]]
    override_x: Union[int, None]
    override_y: Union[int, None]
    override_z: Union[int, None]
