from .logic import Logic


class Timer(Logic):
    """
    Note that timer with 0 ticks still behaves like logic gate (has 1 tick delay).
    """

    ticks: int

    def __init__(self) -> None:
        super().__init__()

        self.ticks = 0

    def compute_output_ready_time(self, max_arrival_time: int):
        self.output_ready_time = max_arrival_time + self.ticks
