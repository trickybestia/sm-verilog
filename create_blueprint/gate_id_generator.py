class GateIdGenerator:
    _id: int

    def __init__(self) -> None:
        self._id = 0

    def next(self, size: int) -> range:
        result = range(self._id, self._id + size)

        self._id += size

        return result

    def next_single(self) -> int:
        return self.next(1)[0]
