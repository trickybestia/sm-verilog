from abc import ABC, abstractmethod
from typing import Union

LogicId = int


class Logic(ABC):
    id: LogicId
    inputs: list["Logic"]
    outputs: list["Logic"]
    requires_inputs_buffering: bool
    _computed_output_ready_time: Union[int, None]

    def __init__(self, id: LogicId) -> None:
        self.id = id
        self.inputs = []
        self.outputs = []
        self.requires_inputs_buffering = False
        self._computed_output_ready_time = None

    def output_ready_time(self) -> Union[int, None]:
        if self._computed_output_ready_time is None:
            self._computed_output_ready_time = self._compute_output_ready_time()

        return self._computed_output_ready_time

    @abstractmethod
    def _compute_output_ready_time(self) -> Union[int, None]:
        ...

    def _max_arrival_time(self, default: int) -> int:
        return max(
            (
                input.output_ready_time()
                for input in self.inputs
                if input.output_ready_time() is not None
            ),
            default=default,
        )
