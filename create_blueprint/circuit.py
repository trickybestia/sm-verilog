from typing import Literal, Self, Tuple, Union, cast
import json

from .output_gate import Output, OutputGate
from .input_gate import Input, InputGate
from .group_gate import GroupGate
from .dff_output import DffOutput
from .timer import Timer
from .logic import Logic, LogicId
from .cell import Cell
from .gate import Gate, GateMode
from .utils import get_or_insert
from .id_generator import IdGenerator
from .net import Net


class Circuit:
    dff_inputs: list[GroupGate]
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
        self.dff_inputs = []
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
        volatile_outputs: list[GroupGate] = []
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

            stripes_orientation = netnames[port_name]["attributes"].get(
                "stripes_orientation", "horizontal"
            )

            if stripes_orientation not in ("horizontal", "vertical"):
                raise ValueError(
                    f'invalid value "{stripes_orientation}" for attribute "stripes_orientation"'
                )

            match port["direction"]:
                case "input":
                    attachment: Union[str, None] = netnames[port_name][
                        "attributes"
                    ].get("attachment")

                    input = Input(
                        port_name,
                        [],
                        rotate_to_inputs,
                        stripe_width,
                        stripes_orientation,
                        override_x,
                        override_y,
                        override_z,
                        attachment,
                    )
                    c.inputs[port_name] = input

                    for bit in port_bits:
                        gate = InputGate(c.id_generator.next(), input)
                        c._register_logic(gate, None)

                        input.gates.append(gate)

                        get_net(bit).input_id = gate.id
                case "output":
                    output = Output(
                        port_name,
                        [],
                        rotate_to_inputs,
                        stripe_width,
                        stripes_orientation,
                        override_x,
                        override_y,
                        override_z,
                    )
                    c.outputs[port_name] = output

                    for bit in port_bits:
                        match bit:
                            case "0":
                                gate = OutputGate(c.id_generator.next(), [], output)
                                c._register_logic(gate, None)
                            case "1":
                                if always_zero_gate is None:
                                    always_zero_gate = c._create_gate("middle")

                                gate = OutputGate(
                                    c.id_generator.next(), [], output, GateMode.NAND
                                )
                                c._register_logic(gate, None)

                                _link(always_zero_gate, gate)

                                output.gates.append(gate)
                            case _:
                                gate = OutputGate(
                                    c.id_generator.next(), volatile_outputs, output
                                )
                                c._register_logic(gate, None)

                                volatile_outputs.append(gate)
                                output.gates.append(gate)

                                get_net(bit).outputs_ids.append(gate.id)

        for cell in module["cells"].values():
            connections = cell["connections"]

            match cell["type"]:
                case "DFF":
                    not_data = c._create_gate("middle", GateMode.NAND)

                    clk_and_data = GroupGate(
                        c.id_generator.next(), c.dff_inputs, GateMode.AND
                    )
                    c._register_logic(clk_and_data, "middle")
                    clk_and_not_data = GroupGate(
                        c.id_generator.next(), c.dff_inputs, GateMode.AND
                    )
                    c._register_logic(clk_and_not_data, "middle")

                    c.dff_inputs.extend((clk_and_data, clk_and_not_data))

                    _link(not_data, clk_and_not_data)

                    get_net(connections["C"][0]).outputs_ids.extend(
                        (clk_and_data.id, clk_and_not_data.id)
                    )
                    get_net(connections["D"][0]).outputs_ids.extend(
                        (clk_and_data.id, not_data.id)
                    )

                    dff = DffOutput(
                        c.id_generator.next(), clk_and_data, clk_and_not_data
                    )
                    c.dffs.append(dff)
                    c._register_logic(dff, "middle")

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
                _link(
                    c.all_logic[cast(int, net.input_id)], c.all_logic[output_logic_id]
                )

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
                    cast(int, output_gate.output_ready_time()),
                )

    def _insert_buffers(self):
        buffers: list[Logic] = []

        for gate in self.all_logic.values():
            if gate.output_ready_time() is None:
                continue

            outputs: list[Tuple[int, Logic]] = [
                (
                    cast(int, output_gate.output_ready_time())
                    - cast(int, gate.output_ready_time())
                    - 1,
                    output_gate,
                )
                for output_gate in gate.outputs
                if output_gate.output_ready_time() is not None
            ]

            outputs.sort(key=lambda t: t[0])

            last_buffer: Logic = gate
            last_buffer_total_delay = 0

            for required_delay, output_gate in outputs:
                if not output_gate.requires_inputs_buffering:
                    continue

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
