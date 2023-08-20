from typing import Union


class GateIdGenerator:
    _id: int

    def __init__(self) -> None:
        self._id = 0

    def next(self, size: Union[int, None] = None) -> Union[int, range]:
        if size is None:
            result = self._id
            self._id += 1
        else:
            result = range(self._id, self._id + size)
            self._id += size

        return result
