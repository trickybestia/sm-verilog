from typing import Union
from abc import ABC, abstractmethod


class Logic(ABC):
    inputs: list[int]
    outputs: list[int]
    output_ready_time: Union[int, None]

    def __init__(self) -> None:
        self.inputs = []
        self.outputs = []
        self.output_ready_time = None

    @abstractmethod
    def compute_output_ready_time(self, max_arrival_time: int):
        ...
