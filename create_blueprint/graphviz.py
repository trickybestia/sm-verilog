from typing import Iterable
from graphviz import Digraph

from .port import Port
from .circuit import Circuit


def render_circuit(circuit: Circuit) -> str:
    graph = Digraph()

    graph.attr(rankdir="LR")
    graph.attr("node", shape="box")

    _render_ports(graph, circuit.inputs.values(), "source")
    _render_ports(graph, circuit.outputs.values(), "sink")

    for logic in circuit.all_logic.values():
        logic.render(graph)

    return graph.source


def _render_ports(graph: Digraph, ports: Iterable[Port], rank: str):
    for port in ports:
        if len(port.gates) == 1:
            graph.node(port.gates[0].render_id(), rank=rank)
        else:
            subgraph = Digraph(f"cluster_{port.name}")

            subgraph.attr(rank=rank)

            for i, gate in enumerate(port.gates):
                subgraph.node(gate.render_id())

                if i != 0:
                    subgraph.edge(
                        port.gates[i - 1].render_id(),
                        gate.render_id(),
                        style="invis",
                    )

            graph.subgraph(subgraph)
