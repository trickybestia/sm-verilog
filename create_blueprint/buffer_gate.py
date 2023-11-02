from .logic import LogicId
from .gate import Gate, GateMode


class BufferGate(Gate):
    def __init__(self, id: LogicId) -> None:
        super().__init__(id, GateMode.AND)
