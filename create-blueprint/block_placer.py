from abc import ABC, abstractmethod

from .blueprint import Blueprint
from .circuit import Circuit


class BlockPlacer(ABC):
    @abstractmethod
    def place(self, circuit: Circuit) -> Blueprint:
        ...
