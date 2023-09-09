from typing import Union

from .logic import LogicId
from .gate import Gate, GateMode


class DffOutput(Gate):
    clk_and_data: Gate
    clk_and_not_data: Gate

    @property
    def depends_on_dff(self) -> bool:
        return True

    def __init__(self, id: LogicId, clk_and_data: Gate, clk_and_not_data: Gate) -> None:
        super().__init__(id, GateMode.NAND)

        self.clk_and_data = clk_and_data
        self.clk_and_not_data = clk_and_not_data

    def _render_name(self) -> str:
        return f"DFF output ({super()._render_name()})"

    def _compute_output_ready_time(self) -> int:
        return self.clk_and_data.output_ready_time() + 3
