from abc import ABC, abstractmethod
from functools import cached_property
from graphviz import Digraph

LogicId = int


class Logic(ABC):
    id: LogicId
    inputs: list["Logic"]
    outputs: list["Logic"]

    @cached_property
    def output_ready_time(self) -> int:
        return self._compute_output_ready_time()

    @property
    def requires_inputs_buffering(self) -> bool:
        return False

    @cached_property
    def depends_on_dff(self) -> bool:
        if len(self.inputs) == 0:
            return False

        return all(input.depends_on_dff for input in self.inputs)

    def __init__(self, id: LogicId) -> None:
        self.id = id
        self.inputs = []
        self.outputs = []

    def render(self, graph: Digraph):
        graph.node(self.render_id(), self._render_label())

        self._render_link_outputs(graph)

    def _render_link_outputs(self, graph: Digraph):
        for output in self.outputs:
            graph.edge(self.render_id(), output.render_id())

    def _render_label(self) -> str:
        return f"{self._render_name()}\n{self._render_description()}"

    def _render_name(self) -> str:
        return self.render_id()

    def _render_description(self) -> str:
        return f"arrival: {self._max_arrival_time(0)} ticks\nready: {self.output_ready_time} ticks"

    def render_id(self) -> str:
        return f"logic_{self.id}"

    @abstractmethod
    def _compute_output_ready_time(self) -> int:
        ...

    def _max_arrival_time(self, default: int) -> int:
        return max(
            (
                input.output_ready_time
                for input in self.inputs
                if input.depends_on_dff == self.depends_on_dff
            ),
            default=default,
        )
