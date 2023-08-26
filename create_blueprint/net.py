from typing import Union

from .logic import LogicId


class Net:
    input_id: Union[LogicId, None]
    outputs_ids: list[LogicId]

    def __init__(self) -> None:
        self.input_id = None
        self.outputs_ids = []
