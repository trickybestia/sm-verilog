from .logic import LogicId
from .gate import Gate, GateMode


class SyncSRLatchOutput(Gate):
    clk_and_set: Gate
    clk_and_reset: Gate

    @property
    def depends_on_latch(self) -> bool:
        return True

    def __init__(self, id: LogicId, clk_and_set: Gate, clk_and_reset: Gate) -> None:
        super().__init__(id, GateMode.NAND)

        self.clk_and_set = clk_and_set
        self.clk_and_reset = clk_and_reset

    def _render_name(self) -> str:
        return f"SYNC_SR_LATCH output ({super()._render_name()})"

    def _compute_output_ready_time(self) -> int:
        return self.clk_and_set.output_ready_time + 3
