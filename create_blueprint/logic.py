from typing import Union
from abc import ABC, abstractmethod

LogicId = int


class Logic(ABC):
    id: LogicId
    inputs: list[LogicId]
    outputs: list[LogicId]
    output_ready_time: Union[int, None]

    def __init__(self, id: LogicId) -> None:
        self.id = id
        self.inputs = []
        self.outputs = []
        self.output_ready_time = None

    @abstractmethod
    def compute_output_ready_time(self, max_arrival_time: int):
        ...
