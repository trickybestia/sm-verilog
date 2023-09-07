from typing import Union

from .logic import LogicId
from .gate import Gate, GateMode


class DffOutput(Gate):
    not_data: Union[Gate, None]
    clk_and_data: Union[Gate, None]
    clk_and_not_data: Union[Gate, None]

    def __init__(self, id: LogicId) -> None:
        super().__init__(id, GateMode.NAND)

        self.not_data = None
        self.clk_and_data = None
        self.clk_and_not_data = None

    def _render_name(self) -> str:
        return f"DFF output ({super()._render_name()})"

    def _compute_output_ready_time(self) -> Union[int, None]:
        return None
