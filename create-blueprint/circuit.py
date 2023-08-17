from dataclasses import dataclass
from typing import Self, Tuple
import json

from .timer import Timer
from .logic import Logic
from .cell import Cell
from .gate import Gate, GateMode
from .utils import get_or_insert, replace_first
from .gate_id_generator import GateIdGenerator
from .net import Net


@dataclass
class PortData:
    bit: int
    gate_id: int
    gate: Gate


class Circuit:
    all_logic: dict[int, Logic]  # Logic ID -> Logic
    middle_logic: dict[int, Logic]  # Logic ID -> Logic
    inputs: dict[str, list[PortData]]
    outputs: dict[str, list[PortData]]
    id_generator: GateIdGenerator
    output_ready_time: int

    @classmethod
    def from_yosys_output(
        cls,
        cells: dict[str, Cell],
        yosys_output: str,
        top_module: str,
    ) -> Self:
        c = cls._from_yosys_output(cells, yosys_output, top_module)

        c._compute_output_ready_time()
        c._insert_buffers()

        return c

    def __init__(self) -> None:
        self.all_logic = {}
        self.middle_logic = {}
        self.inputs = {}
        self.outputs = {}
        self.id_generator = GateIdGenerator()
        self.output_ready_time = 0

    @classmethod
    def _from_yosys_output(
        cls, cells: dict[str, Cell], yosys_output: str, top_module: str
    ) -> Self:
        json_yosys_output = json.loads(yosys_output)

        module = json_yosys_output["modules"][top_module]

        ports = module["ports"]

        c = Circuit()
        nets: dict[int, Net] = {}

        def get_net(net_id: int) -> Net:
            return get_or_insert(nets, net_id, lambda: Net())

        for port_name in ports:
            port = ports[port_name]
            port_bits = port["bits"]

            match port["direction"]:
                case "input":
                    for bit in port_bits:
                        gate_id = c.id_generator.next_single()
                        gate = Gate()

                        gate.mode = GateMode.OR

                        c.all_logic[gate_id] = gate
                        get_or_insert(c.inputs, port_name, lambda: []).append(
                            PortData(bit, gate_id, gate)
                        )

                        get_net(bit).input = gate_id
                case "output":
                    for bit in port_bits:
                        gate_id = c.id_generator.next_single()
                        gate = Gate()

                        c.all_logic[gate_id] = gate
                        get_or_insert(c.outputs, port_name, lambda: []).append(
                            PortData(bit, gate_id, gate)
                        )

                        match bit:
                            case "0":
                                ...
                            case "1":
                                gate.mode = GateMode.NAND

                                input_gate_id = c.id_generator.next_single()
                                input_gate = Gate()

                                c.all_logic[input_gate_id] = input_gate
                                c.middle_logic[input_gate_id] = input_gate

                                input_gate.outputs.append(gate_id)
                            case _:
                                get_net(bit).outputs.append(gate_id)

        for cell in module["cells"].values():
            gate_id = c.id_generator.next_single()
            gate = Gate()

            c.all_logic[gate_id] = gate
            c.middle_logic[gate_id] = gate

            connections = cell["connections"]

            cell_info = cells[cell["type"]]

            gate.mode = cell_info.mode
            get_net(connections[cell_info.output][0]).input = gate_id

            for input in cell_info.inputs:
                get_net(connections[input][0]).outputs.append(gate_id)

        for net in nets.values():
            for output in net.outputs:
                c.all_logic[output].inputs.append(net.input)
                c.all_logic[net.input].outputs.append(output)

        return c

    def _compute_output_ready_time(self):
        def get_output_ready_time(gate_id: int) -> int:
            logic = self.all_logic[gate_id]

            if logic.output_ready_time is None:
                arrival_times = map(
                    get_output_ready_time,
                    logic.inputs,
                )

                logic.compute_output_ready_time(max(arrival_times))

            return logic.output_ready_time

        for input in self.inputs.values():
            for input_port_data in input:
                input_port_data.gate.output_ready_time = 0

        for output in self.outputs.values():
            for output_port_data in output:
                self.output_ready_time = max(
                    self.output_ready_time,
                    get_output_ready_time(output_port_data.gate_id),
                )

        for output in self.outputs.values():
            for output_port_data in output:
                output_port_data.gate.output_ready_time = self.output_ready_time

    def _insert_buffers(self):
        buffers: list[Tuple[int, Logic]] = []

        for gate_id, gate in self.all_logic.items():
            for input_gate_id in gate.inputs:
                input_gate = self.all_logic[input_gate_id]

                buffer_delay = gate.output_ready_time - input_gate.output_ready_time - 1

                if buffer_delay == 0:
                    continue

                buffer_id = self.id_generator.next_single()
                buffer: Logic

                if buffer_delay == 1:
                    buffer = Gate()
                else:
                    buffer = Timer()
                    buffer.ticks = buffer_delay - 1

                buffers.append((buffer_id, buffer))

                self._insert_logic_between_others(
                    buffer_id, buffer, input_gate_id, input_gate, gate_id, gate
                )

        for buffer_id, buffer in buffers:
            self.all_logic[buffer_id] = buffer
            self.middle_logic[buffer_id] = buffer

    def _insert_logic_between_others(
        self,
        middle_logic_id: int,
        middle_logic: Logic,
        input_logic_id: int,
        input_logic: Logic,
        output_logic_id: int,
        output_logic: Logic,
    ):
        replace_first(input_logic.outputs, output_logic_id, middle_logic_id)
        replace_first(output_logic.inputs, input_logic_id, middle_logic_id)

        middle_logic.inputs.append(input_logic_id)
        middle_logic.outputs.append(output_logic_id)
