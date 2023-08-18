from typing import Union


class Net:
    input: Union[int, None]
    outputs: list[int]

    def __init__(self) -> None:
        self.input = None
        self.outputs = []
