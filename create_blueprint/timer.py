from .logic import Logic, LogicId


class Timer(Logic):
    """
    Note that timer with 0 ticks still behaves like logic gate (has 1 tick delay).
    """

    ticks: int

    def __init__(self, id: LogicId, ticks: int = 0) -> None:
        super().__init__(id)

        self.ticks = ticks

    def compute_output_ready_time(self, max_arrival_time: int):
        self.output_ready_time = max_arrival_time + self.ticks
