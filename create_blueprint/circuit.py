from dataclasses import dataclass
from typing import Literal, Self, Tuple, TypeVar, Union
import json

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


class DFF:
    output: Union[Gate, None]
    not_data: Union[Gate, None]
    clk_and_data: Union[Gate, None]
    clk_and_not_data: Union[Gate, None]

    def __init__(self) -> None:
        self.output = None
        self.not_data = None
        self.clk_and_data = None
        self.clk_and_not_data = None


class Circuit:
    dffs: list[DFF]
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
                        gate = c._create_gate(None)

                        output.gates.append(gate)

                        match bit:
                            case "0":
                                ...
                            case "1":
                                gate.mode = GateMode.NAND

                                input_gate = c._create_gate("middle")

                                c._link(input_gate.id, gate.id)
                            case _:
                                get_net(bit).outputs_ids.append(gate.id)

        for cell in module["cells"].values():
            connections = cell["connections"]

            match cell["type"]:
                case "DFF":
                    dff = DFF()
                    c.dffs.append(dff)

                    dff.output = c._create_gate("middle", GateMode.NAND)
                    dff.clk_and_data = c._create_gate("middle", GateMode.AND)
                    dff.not_data = c._create_gate("middle", GateMode.NAND)
                    dff.clk_and_not_data = c._create_gate("middle", GateMode.AND)

                    c._link(dff.not_data.id, dff.clk_and_not_data.id)

                    get_net(connections["C"][0]).outputs_ids.extend(
                        (dff.clk_and_data.id, dff.clk_and_not_data.id)
                    )
                    get_net(connections["D"][0]).outputs_ids.extend(
                        (dff.clk_and_data.id, dff.not_data.id)
                    )
                    get_net(connections["Q"][0]).input_id = dff.output.id
                case _:
                    gate = c._create_gate("middle")

                    cell_info = cells[cell["type"]]

                    gate.mode = cell_info.mode
                    get_net(connections[cell_info.output][0]).input_id = gate.id

                    for input in cell_info.inputs:
                        get_net(connections[input][0]).outputs_ids.append(gate.id)

        for net in nets.values():
            for output_logic_id in net.outputs_ids:
                c._link(net.input_id, output_logic_id)

        return c

    def _connect_dffs(self):
        for dff in self.dffs:
            output_ready_time = max(
                dff.clk_and_data.output_ready_time,
                dff.clk_and_not_data.output_ready_time,
            )

            dff.clk_and_data.output_ready_time = output_ready_time
            dff.clk_and_not_data.output_ready_time = output_ready_time

            reset_loop_gate = self._create_gate("middle", GateMode.OR)
            set_loop_gate = self._create_gate("middle", GateMode.NOR)

            dff.output.output_ready_time = None

            self._link(dff.clk_and_data.id, set_loop_gate.id)
            self._link(dff.clk_and_not_data.id, reset_loop_gate.id)

            self._link(reset_loop_gate.id, dff.output.id)
            self._link(dff.output.id, set_loop_gate.id)
            self._link(set_loop_gate.id, reset_loop_gate.id)

    def _compute_output_ready_time(self):
        def get_output_ready_time(logic_id: LogicId) -> int:
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
                input_gate.output_ready_time = 0

        for logic_id in self.middle_logic:
            get_output_ready_time(logic_id)

        for output in self.outputs.values():
            for output_gate in output.gates:
                self.output_ready_time = max(
                    self.output_ready_time,
                    get_output_ready_time(output_gate.id),
                )

        for output in self.outputs.values():
            for output_gate in output.gates:
                output_gate.output_ready_time = self.output_ready_time

    def _insert_buffers(self):
        buffers: list[Logic] = []

        for gate_id, gate in self.all_logic.items():
            if gate.output_ready_time is None:
                continue

            outputs: list[Tuple[int, LogicId]] = sorted(
                (
                    self.all_logic[output_gate_id].output_ready_time
                    - gate.output_ready_time
                    - 1,
                    output_gate_id,
                )
                for output_gate_id in gate.outputs
                if self.all_logic[output_gate_id].output_ready_time is not None
            )

            last_buffer: Logic = gate
            last_buffer_total_delay = 0

            for required_delay, output_gate_id in outputs:
                self._unlink(gate_id, output_gate_id)

                new_buffer_delay = required_delay - last_buffer_total_delay

                if new_buffer_delay > 0:
                    buffer = Timer(self.id_generator.next(), new_buffer_delay - 1)

                    buffers.append(buffer)

                    last_buffer.outputs.append(buffer.id)
                    buffer.inputs.append(last_buffer.id)

                    last_buffer = buffer
                    last_buffer_total_delay = required_delay

                last_buffer.outputs.append(output_gate_id)
                self.all_logic[output_gate_id].inputs.append(last_buffer.id)

        for buffer in buffers:
            self.all_logic[buffer.id] = buffer
            self.middle_logic[buffer.id] = buffer

    def _create_gate(
        self,
        kind: Union[Literal["middle"], None],
        mode: GateMode = GateMode.AND,
    ) -> Gate:
        gate = Gate(self.id_generator.next(), mode)

        self.all_logic[gate.id] = gate

        match kind:
            case "middle":
                self.middle_logic[gate.id] = gate

        return gate

    def _link(self, input_id: LogicId, output_id: LogicId):
        self.all_logic[input_id].outputs.append(output_id)
        self.all_logic[output_id].inputs.append(input_id)

    def _unlink(self, input_id: LogicId, output_id: LogicId):
        self.all_logic[input_id].outputs.remove(output_id)
        self.all_logic[output_id].inputs.remove(input_id)
