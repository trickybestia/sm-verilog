from typing import Union

from .logic import Logic, LogicId


class Timer(Logic):
    """
    Note that timer with 0 ticks still behaves like logic gate (has 1 tick delay).
    """

    ticks: int

    def __init__(self, id: LogicId, ticks: int = 0) -> None:
        super().__init__(id)

        self.ticks = ticks

    def _render_name(self) -> str:
        return f"Timer: {self.ticks} ticks"

    def _compute_output_ready_time(self) -> Union[int, None]:
        return self._max_arrival_time(-self.ticks - 1) + self.ticks + 1
