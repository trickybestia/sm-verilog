class IdGenerator:
    _id: int

    def __init__(self) -> None:
        self._id = 0

    def next_range(self, size: int) -> range:
        result = range(self._id, self._id + size)

        self._id += size

        return result

    def next(self) -> int:
        result = self._id

        self._id += 1

        return result
