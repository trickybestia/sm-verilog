from dataclasses import dataclass
from typing import Self
import json

from .cell import Cell
from .gate import Gate, GateMode
from .utils import get_or_insert
from .gate_id_generator import GateIdGenerator
from .net import Net


@dataclass
class PortData:
    bit: int
    gate_id: int
    gate: Gate


class Circuit:
    middle_gates: dict[int, Gate]  # Gate ID -> Gate
    input_gates: dict[str, list[PortData]]
    output_gates: dict[str, list[PortData]]
    id_generator: GateIdGenerator

    @classmethod
    def from_yosys_output(
        cls,
        cells: dict[str, Cell],
        yosys_output: str,
        top_module: str,
    ) -> Self:
        json_yosys_output = json.loads(yosys_output)

        module = json_yosys_output["modules"][top_module]

        ports = module["ports"]

        c = Circuit()
        all_gates: dict[int, Gate] = {}
        nets: dict[int, Net] = {}

        def _net(net_id: int) -> Net:
            return get_or_insert(nets, net_id, lambda: Net())

        for port_name in ports:
            port = ports[port_name]
            port_bits = port["bits"]

            match port["direction"]:
                case "input":
                    for bit in port_bits:
                        gate_id = c.id_generator.next_single()
                        gate = Gate()

                        all_gates[gate_id] = gate
                        get_or_insert(c.input_gates, port_name, lambda: []).append(
                            PortData(bit, gate_id, gate)
                        )

                        _net(bit).input = gate_id
                case "output":
                    for bit in port_bits:
                        gate_id = c.id_generator.next_single()
                        gate = Gate()

                        all_gates[gate_id] = gate
                        get_or_insert(c.output_gates, port_name, lambda: []).append(
                            PortData(bit, gate_id, gate)
                        )

                        match bit:
                            case "0":
                                ...
                            case "1":
                                gate.mode = GateMode.NAND

                                input_gate_id = c.id_generator.next_single()
                                input_gate = Gate()

                                all_gates[input_gate_id] = input_gate
                                c.middle_gates[input_gate_id] = input_gate

                                input_gate.outputs.append(gate_id)
                            case _:
                                _net(bit).outputs.append(gate_id)

        for cell in module["cells"].values():
            gate_id = c.id_generator.next_single()
            gate = Gate()

            all_gates[gate_id] = gate
            c.middle_gates[gate_id] = gate

            connections = cell["connections"]

            cell_info = cells[cell["type"]]

            gate.mode = cell_info.mode
            _net(connections[cell_info.output][0]).input = gate_id

            for input in cell_info.inputs:
                _net(connections[input][0]).outputs.append(gate_id)

        for net in nets.values():
            for output in net.outputs:
                all_gates[net.input].outputs.append(output)

        return c

    def __init__(self) -> None:
        self.middle_gates = {}
        self.input_gates = {}
        self.output_gates = {}
        self.id_generator = GateIdGenerator()
