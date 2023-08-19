from dataclasses import dataclass
from typing import Self, Tuple, Union
import json

from .timer import Timer
from .logic import Logic
from .cell import Cell
from .gate import Gate, GateMode
from .utils import get_or_insert, replace_first
from .gate_id_generator import GateIdGenerator
from .net import Net


@dataclass
class PortGate:
    bit: int
    gate_id: int
    gate: Gate


@dataclass
class Port:
    gates: list[PortGate]
    hide: bool
    rotate_to_inputs: bool
    stripe_width: int
    override_x: Union[int, None]
    override_y: Union[int, None]
    override_z: Union[int, None]


@dataclass
class Input(Port):
    attachment: Union[str, None]


@dataclass
class Output(Port):
    connect_to: Union[str, None]


class Circuit:
    all_logic: dict[int, Logic]  # Logic ID -> Logic
    middle_logic: dict[int, Logic]  # Logic ID -> Logic
    inputs: dict[str, Input]
    outputs: dict[str, Output]
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
        c._connect_outputs_to_inputs()

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
        netnames = module["netnames"]

        c = Circuit()
        nets: dict[int, Net] = {}

        def get_net(net_id: int) -> Net:
            return get_or_insert(nets, net_id, lambda: Net())

        for port_name in ports:
            port = ports[port_name]
            port_bits = port["bits"]

            hide = "hide" in netnames[port_name]["attributes"]
            rotate_to_inputs = "rotate_to_inputs" in netnames[port_name]["attributes"]
            stripe_width = len(port_bits)
            override_x: Union[int, None] = None
            override_y: Union[int, None] = None
            override_z: Union[int, None] = None

            if "stripe_width" in netnames[port_name]["attributes"]:
                stripe_width = int(netnames[port_name]["attributes"]["stripe_width"], 2)
            if "override_x" in netnames[port_name]["attributes"]:
                override_x = int(netnames[port_name]["attributes"]["override_x"], 2)
            if "override_y" in netnames[port_name]["attributes"]:
                override_y = int(netnames[port_name]["attributes"]["override_y"], 2)
            if "override_z" in netnames[port_name]["attributes"]:
                override_z = int(netnames[port_name]["attributes"]["override_z"], 2)

            match port["direction"]:
                case "input":
                    attachment: Union[str, None] = netnames[port_name][
                        "attributes"
                    ].get("attachment")

                    input = Input(
                        [],
                        hide,
                        rotate_to_inputs,
                        stripe_width,
                        override_x,
                        override_y,
                        override_z,
                        attachment,
                    )
                    c.inputs[port_name] = input

                    for bit in port_bits:
                        gate_id = c.id_generator.next_single()
                        gate = Gate()

                        gate.mode = GateMode.OR

                        c.all_logic[gate_id] = gate
                        input.gates.append(PortGate(bit, gate_id, gate))

                        get_net(bit).input = gate_id
                case "output":
                    connect_to: Union[str, None] = netnames[port_name][
                        "attributes"
                    ].get("connect_to")

                    output = Output(
                        [],
                        hide,
                        rotate_to_inputs,
                        stripe_width,
                        override_x,
                        override_y,
                        override_z,
                        connect_to,
                    )
                    c.outputs[port_name] = output

                    for bit in port_bits:
                        gate_id = c.id_generator.next_single()
                        gate = Gate()

                        c.all_logic[gate_id] = gate
                        output.gates.append(PortGate(bit, gate_id, gate))

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

    def _connect_outputs_to_inputs(self):
        for output_name, output in self.outputs.items():
            if output.connect_to:
                input = self.inputs[output.connect_to]

                if len(input.gates) != len(output.gates):
                    raise Exception(
                        f"input ({output.connect_to}) and output ({output_name}) bound via connect_to attribute must have same size"
                    )

                for i in range(len(input.gates)):
                    input.gates[i].gate.inputs.append(output.gates[i].gate_id)
                    output.gates[i].gate.outputs.append(input.gates[i].gate_id)

    def _compute_output_ready_time(self):
        def get_output_ready_time(logic_id: int) -> int:
            logic = self.all_logic[logic_id]

            if logic.output_ready_time is None:
                arrival_times = list(
                    map(
                        get_output_ready_time,
                        logic.inputs,
                    )
                )

                max_arrival_time = max(arrival_times) if len(arrival_times) != 0 else 0

                logic.compute_output_ready_time(max_arrival_time)

            return logic.output_ready_time

        for input in self.inputs.values():
            for input_gate in input.gates:
                input_gate.gate.output_ready_time = 0

        for logic_id in self.middle_logic:
            get_output_ready_time(logic_id)

        for output in self.outputs.values():
            for output_gate in output.gates:
                self.output_ready_time = max(
                    self.output_ready_time,
                    get_output_ready_time(output_gate.gate_id),
                )

        for output in self.outputs.values():
            for output_gate in output.gates:
                output_gate.gate.output_ready_time = self.output_ready_time

    def _insert_buffers(self):
        buffers: list[Tuple[int, Logic]] = []

        for gate_id, gate in self.all_logic.items():
            outputs: list[Tuple[int, int]] = sorted(
                map(
                    lambda output_gate_id: (
                        self.all_logic[output_gate_id].output_ready_time
                        - gate.output_ready_time
                        - 1,
                        output_gate_id,
                    ),
                    gate.outputs,
                )
            )

            last_buffer_id = gate_id
            last_buffer: Logic = gate
            last_buffer_total_delay = 0

            for required_delay, output_gate_id in outputs:
                gate.outputs.remove(output_gate_id)
                self.all_logic[output_gate_id].inputs.remove(gate_id)

                new_buffer_delay = required_delay - last_buffer_total_delay

                if new_buffer_delay != 0:
                    buffer_id = self.id_generator.next_single()
                    buffer: Logic

                    if new_buffer_delay == 1:
                        buffer = Gate()
                    else:
                        buffer = Timer()
                        buffer.ticks = new_buffer_delay - 1

                    buffers.append((buffer_id, buffer))

                    last_buffer.outputs.append(buffer_id)
                    buffer.inputs.append(last_buffer_id)

                    last_buffer = buffer
                    last_buffer_id = buffer_id
                    last_buffer_total_delay = required_delay

                last_buffer.outputs.append(output_gate_id)
                self.all_logic[output_gate_id].inputs.append(last_buffer_id)

        for buffer_id, buffer in buffers:
            self.all_logic[buffer_id] = buffer
            self.middle_logic[buffer_id] = buffer
