from dataclasses import dataclass
from typing import Literal, Self, Tuple, Union
import json

from .group_gate import GroupGate
from .dff_output import DffOutput
from .timer import Timer
from .logic import Logic, LogicId
from .cell import Cell
from .gate import Gate, GateMode
from .utils import get_or_insert
from .id_generator import IdGenerator
from .net import Net


@dataclass
class Port:
    gates: list[Gate]
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
    ...


class Circuit:
    dffs: list[DffOutput]
    all_logic: dict[LogicId, Logic]
    middle_logic: dict[LogicId, Logic]
    inputs: dict[str, Input]
    outputs: dict[str, Output]
    id_generator: IdGenerator
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

        if len(c.dffs) != 0:
            c._connect_dffs()
            c._insert_buffers()

        return c

    def __init__(self) -> None:
        self.dffs = []
        self.all_logic = {}
        self.middle_logic = {}
        self.inputs = {}
        self.outputs = {}
        self.id_generator = IdGenerator()
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
        all_outputs: list[GroupGate] = []
        always_zero_gate: Union[Gate, None] = None

        def get_net(net_id: int) -> Net:
            return get_or_insert(nets, net_id, lambda: Net())

        for port_name in ports:
            port = ports[port_name]
            port_bits = port["bits"]

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
                        rotate_to_inputs,
                        stripe_width,
                        override_x,
                        override_y,
                        override_z,
                        attachment,
                    )
                    c.inputs[port_name] = input

                    for bit in port_bits:
                        gate = c._create_gate(None, GateMode.OR)

                        input.gates.append(gate)

                        get_net(bit).input_id = gate.id
                case "output":
                    output = Output(
                        [],
                        rotate_to_inputs,
                        stripe_width,
                        override_x,
                        override_y,
                        override_z,
                    )
                    c.outputs[port_name] = output

                    for bit in port_bits:
                        match bit:
                            case "0":
                                output.gates.append(c._create_gate(None))
                            case "1":
                                if always_zero_gate is None:
                                    always_zero_gate = c._create_gate("middle")

                                gate = c._create_gate(None, GateMode.NAND)

                                _link(always_zero_gate, gate)
                            case _:
                                gate = GroupGate(c.id_generator.next(), all_outputs)

                                c._register_logic(gate, None)
                                all_outputs.append(gate)
                                output.gates.append(gate)

                                get_net(bit).outputs_ids.append(gate.id)

        for cell in module["cells"].values():
            connections = cell["connections"]

            match cell["type"]:
                case "DFF":
                    dff = DffOutput(c.id_generator.next())
                    c.dffs.append(dff)
                    c._register_logic(dff, "middle")

                    dff.not_data = c._create_gate("middle", GateMode.NAND)

                    dff_inputs: list[GroupGate] = []

                    dff.clk_and_data = GroupGate(
                        c.id_generator.next(), dff_inputs, GateMode.AND
                    )
                    c._register_logic(dff.clk_and_data, "middle")
                    dff.clk_and_not_data = GroupGate(
                        c.id_generator.next(), dff_inputs, GateMode.AND
                    )
                    c._register_logic(dff.clk_and_not_data, "middle")

                    dff_inputs.extend((dff.clk_and_data, dff.clk_and_not_data))

                    _link(dff.not_data, dff.clk_and_not_data)

                    get_net(connections["C"][0]).outputs_ids.extend(
                        (dff.clk_and_data.id, dff.clk_and_not_data.id)
                    )
                    get_net(connections["D"][0]).outputs_ids.extend(
                        (dff.clk_and_data.id, dff.not_data.id)
                    )
                    get_net(connections["Q"][0]).input_id = dff.id
                case _:
                    gate = c._create_gate("middle")

                    cell_info = cells[cell["type"]]

                    gate.mode = cell_info.mode
                    get_net(connections[cell_info.output][0]).input_id = gate.id

                    for input in cell_info.inputs:
                        get_net(connections[input][0]).outputs_ids.append(gate.id)

        for net in nets.values():
            for output_logic_id in net.outputs_ids:
                _link(c.all_logic[net.input_id], c.all_logic[output_logic_id])

        return c

    def _connect_dffs(self):
        for dff in self.dffs:
            reset_loop_gate = self._create_gate("middle", GateMode.OR)
            set_loop_gate = self._create_gate("middle", GateMode.NOR)

            _link(dff.clk_and_data, set_loop_gate)
            _link(dff.clk_and_not_data, reset_loop_gate)

            _link(reset_loop_gate, dff)
            _link(dff, set_loop_gate)
            _link(set_loop_gate, reset_loop_gate)

    def _compute_output_ready_time(self):
        for output in self.outputs.values():
            for output_gate in output.gates:
                self.output_ready_time = max(
                    self.output_ready_time,
                    output_gate.output_ready_time(),
                )

    def _insert_buffers(self):
        buffers: list[Logic] = []

        for gate in self.all_logic.values():
            if gate.output_ready_time() is None:
                continue

            outputs: list[Tuple[int, Logic]] = [
                (
                    output_gate.output_ready_time() - gate.output_ready_time() - 1,
                    output_gate,
                )
                for output_gate in gate.outputs
                if output_gate.output_ready_time() is not None
            ]

            outputs.sort(key=lambda t: t[0])

            last_buffer: Logic = gate
            last_buffer_total_delay = 0

            for required_delay, output_gate in outputs:
                _unlink(gate, output_gate)

                new_buffer_delay = required_delay - last_buffer_total_delay

                if new_buffer_delay > 0:
                    buffer = Timer(self.id_generator.next(), new_buffer_delay - 1)

                    buffers.append(buffer)

                    _link(last_buffer, buffer)

                    last_buffer = buffer
                    last_buffer_total_delay = required_delay

                _link(last_buffer, output_gate)

        for buffer in buffers:
            self.all_logic[buffer.id] = buffer
            self.middle_logic[buffer.id] = buffer

    def _register_logic(self, logic: Logic, kind: Union[Literal["middle"], None]):
        self.all_logic[logic.id] = logic

        match kind:
            case "middle":
                self.middle_logic[logic.id] = logic

    def _create_gate(
        self,
        kind: Union[Literal["middle"], None],
        mode: GateMode = GateMode.AND,
    ) -> Gate:
        gate = Gate(self.id_generator.next(), mode)

        self._register_logic(gate, kind)

        return gate


def _link(input: Logic, output: Logic):
    input.outputs.append(output)
    output.inputs.append(input)


def _unlink(input: Logic, output: Logic):
    input.outputs.remove(output)
    output.inputs.remove(input)
