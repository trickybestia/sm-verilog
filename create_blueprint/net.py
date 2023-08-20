from typing import Union


class Net:
    input_logic_id: Union[int, None]
    output_logic_ids: list[int]

    def __init__(self) -> None:
        self.input_logic_id = None
        self.output_logic_ids = []
