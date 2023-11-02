from functools import cached_property
from typing import Literal, Self, Tuple, Union, cast
import json

from .port import (
    Attachment,
    AttachmentName,
    AttachmentRotation,
    GateRotation,
    StripesOrientation,
)
from .output_gate import Output, OutputGate
from .input_gate import Input, InputGate
from .group_gate import GroupGate
from .sync_sr_latch_output import SyncSRLatchOutput
from .timer import Timer
from .logic import Logic, LogicId
from .cell import Cell
from .gate import Gate, GateMode
from .utils import (
    get_or_insert,
    get_yosys_integer_attribute,
    get_yosys_str_enum_attribute,
)
from .id_generator import IdGenerator
from .net import Net


class Circuit:
    latch_inputs: list[GroupGate]
    latches: list[SyncSRLatchOutput]
    all_logic: dict[LogicId, Logic]
    middle_logic: dict[LogicId, Logic]
    inputs: dict[str, Input]
    outputs: dict[str, Output]
    id_generator: IdGenerator

    @cached_property
    def output_ready_time(self) -> int:
        return max(logic.output_ready_time for logic in self.all_logic.values())

    @classmethod
    def from_yosys_output(
        cls,
        cells: dict[str, Cell],
        yosys_output: str,
        top_module: str,
    ) -> Self:
        c = cls._from_yosys_output(cells, yosys_output, top_module)

        if len(c.latches) != 0:
            c._connect_dffs()
            c._insert_buffers()

        c._handle_ingore_timings_outputs()

        return c

    def __init__(self) -> None:
        self.latch_inputs = []
        self.latches = []
        self.all_logic = {}
        self.middle_logic = {}
        self.inputs = {}
        self.outputs = {}
        self.id_generator = IdGenerator()

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
            attributes = netnames[port_name]["attributes"]
            port = ports[port_name]
            port_bits = port["bits"]

            stripe_width = get_yosys_integer_attribute(
                attributes, "stripe_width", len(port_bits)
            )
            override_x = get_yosys_integer_attribute(attributes, "override_x", None)
            override_y = get_yosys_integer_attribute(attributes, "override_y", None)
            override_z = get_yosys_integer_attribute(attributes, "override_z", None)

            stripes_orientation = get_yosys_str_enum_attribute(
                attributes,
                "stripes_orientation",
                StripesOrientation,
                StripesOrientation.HORIZONTAL,
            )
            attachment_name = get_yosys_str_enum_attribute(
                attributes, "attachment", AttachmentName, None
            )
            attachment_rotation = get_yosys_str_enum_attribute(
                attributes,
                "attachment_rotation",
                AttachmentRotation,
                AttachmentRotation.BACKWARD,
            )
            gate_rotation = get_yosys_str_enum_attribute(
                attributes, "gate_rotation", GateRotation, GateRotation.TOP
            )

            attachment: Attachment = None

            if attachment_name is not None:
                attachment = (attachment_name, attachment_rotation)

            match port["direction"]:
                case "input":
                    input = Input(
                        port_name,
                        [],
                        gate_rotation,
                        attachment,
                        stripe_width,
                        stripes_orientation,
                        override_x,
                        override_y,
                        override_z,
                    )
                    c.inputs[port_name] = input

                    for bit in port_bits:
                        gate = InputGate(c.id_generator.next(), input)
                        c._register_logic(gate, None)

                        input.gates.append(gate)

                        get_net(bit).input_id = gate.id
                case "output":
                    ignore_timings = "ignore_timings" in attributes

                    output = Output(
                        port_name,
                        [],
                        gate_rotation,
                        attachment,
                        stripe_width,
                        stripes_orientation,
                        override_x,
                        override_y,
                        override_z,
                        ignore_timings,
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
                            case _:
                                gate = OutputGate(
                                    c.id_generator.next(), volatile_outputs, output
                                )
                                c._register_logic(gate, None)

                                volatile_outputs.append(gate)

                                get_net(bit).outputs_ids.append(gate.id)

                        output.gates.append(gate)

        for cell in module["cells"].values():
            connections = cell["connections"]

            match cell["type"]:
                case "SYNC_SR_LATCH":
                    clk_and_set = GroupGate(
                        c.id_generator.next(), c.latch_inputs, GateMode.AND
                    )
                    c._register_logic(clk_and_set, "middle")
                    clk_and_reset = GroupGate(
                        c.id_generator.next(), c.latch_inputs, GateMode.AND
                    )
                    c._register_logic(clk_and_reset, "middle")

                    c.latch_inputs.extend((clk_and_set, clk_and_reset))

                    get_net(connections["C"][0]).outputs_ids.extend(
                        (clk_and_set.id, clk_and_reset.id)
                    )
                    get_net(connections["S"][0]).outputs_ids.append(clk_and_set.id)
                    get_net(connections["R"][0]).outputs_ids.append(clk_and_reset.id)

                    latch = SyncSRLatchOutput(
                        c.id_generator.next(), clk_and_set, clk_and_reset
                    )
                    c.latches.append(latch)
                    c._register_logic(latch, "middle")

                    get_net(connections["Q"][0]).input_id = latch.id
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
        for latch in self.latches:
            reset_loop_gate = self._create_gate("middle", GateMode.OR)
            set_loop_gate = self._create_gate("middle", GateMode.NOR)

            _link(latch.clk_and_set, set_loop_gate)
            _link(latch.clk_and_reset, reset_loop_gate)

            _link(reset_loop_gate, latch)
            _link(latch, set_loop_gate)
            _link(set_loop_gate, reset_loop_gate)

    def _insert_buffers(self):
        buffers: list[Logic] = []

        for gate in self.all_logic.values():
            outputs: list[Tuple[int, Logic]] = [
                (
                    output_gate.output_ready_time - gate.output_ready_time - 1,
                    output_gate,
                )
                for output_gate in gate.outputs
            ]

            outputs.sort(key=lambda t: t[0])

            last_buffer: Logic = gate
            last_buffer_total_delay = 0

            for required_delay, output_gate in outputs:
                if (
                    not output_gate.requires_inputs_buffering
                    or output_gate.depends_on_latch != gate.depends_on_latch
                ):
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

    def _handle_ingore_timings_outputs(self):
        for output in self.outputs.values():
            for i, gate in enumerate(output.gates):
                if (
                    len(gate.inputs) == 1
                    and isinstance(gate.inputs[0], Gate)
                    and not gate.requires_inputs_buffering
                    and gate.inputs[0].id in self.middle_logic
                ):
                    del self.middle_logic[gate.inputs[0].id]

                    del self.all_logic[gate.id]

                    output.gates[i] = gate.inputs[0]

                    _unlink(gate.inputs[0], gate)

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
