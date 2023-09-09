from dataclasses import dataclass
from typing import Union

from .port import Port
from .logic import Logic, LogicId
from .timer import Timer
from .gate import Gate
from .shapes import ShapeId
from .color_generator import Color, ColorGenerator
from .blueprint import Blueprint
from .circuit import Circuit


@dataclass
class BlockPlacerOptions:
    height: Union[int, None]
    compact: bool
    rotate_middle_gates_to_input: bool
    auto_height: bool
    default_attachment: Union[str, None]
    cubic: bool


class BlockPlacer:
    _circuit: Circuit
    _blueprint: Blueprint
    _options: BlockPlacerOptions
    _height: int
    _middle_gates_offset: int

    def __init__(
        self, circuit: Circuit, blueprint: Blueprint, options: BlockPlacerOptions
    ) -> None:
        super().__init__()

        self._circuit = circuit
        self._blueprint = blueprint
        self._options = options
        self._middle_gates_offset = 0

        if options.auto_height:
            self.height = int(len(circuit.middle_logic) ** 0.5)
        elif options.cubic:
            self.height = int(len(circuit.middle_logic) ** (1 / 3))
        elif options.height is not None:
            self.height = options.height
        else:
            self.height = 1

    @classmethod
    def place(cls, circuit: Circuit, options: BlockPlacerOptions) -> Blueprint:
        placer = cls(circuit, Blueprint(), options)

        color_generator = ColorGenerator()

        placer._blueprint.description += "Inputs (first is left):\n\n"

        input_gates_offset = 0

        for name, input in circuit.inputs.items():
            color = color_generator.next()
            placer._blueprint.description += f"{name}: {color.name}\n"

            start_x = input_gates_offset
            start_y = 0
            start_z = 0

            if input.override_x is not None:
                start_x = input.override_x
            if input.override_y is not None:
                start_y = input.override_y
            if input.override_z is not None:
                start_z = input.override_z

            attachment = input.attachment

            if attachment is None:
                attachment = placer._options.default_attachment

            port_width = placer._place_port(
                input, start_x, start_y, start_z, color, attachment
            )

            if input.override_x is None:
                input_gates_offset += port_width

        color_generator.reset()

        placer._blueprint.description += "\nOutputs (first is left):\n\n"

        output_gates_offset = 0

        for name, output in circuit.outputs.items():
            color = color_generator.next()
            placer._blueprint.description += f"{name}: {color.name}\n"

            start_x = output_gates_offset
            start_y = 1
            start_z = 0

            if output.override_x is not None:
                start_x = output.override_x
            if output.override_y is not None:
                start_y = output.override_y
            if output.override_z is not None:
                start_z = output.override_z

            port_width = placer._place_port(
                output, start_x, start_y, start_z, color, None
            )

            if output.override_x is None:
                output_gates_offset += port_width

        for logic in circuit.middle_logic.values():
            placer._place_middle_logic(logic)

        return placer._blueprint

    def _place_middle_logic(self, logic: Logic):
        layer_offset = 0

        if self._options.cubic:
            layer_offset = self._middle_gates_offset // (self.height**2)

        middle_gates_offset_in_layer = (
            self._middle_gates_offset - layer_offset * self.height**2
        )

        x = middle_gates_offset_in_layer // self.height
        y = 2 + layer_offset
        z = middle_gates_offset_in_layer % self.height

        if self._options.rotate_middle_gates_to_input:
            z += 1

            if middle_gates_offset_in_layer % self.height == 0:
                self._blueprint.create_solid(ShapeId.Concrete, x, y, 0)

        if isinstance(logic, Gate):
            self._create_gate(
                logic, x, y, z, self._options.rotate_middle_gates_to_input
            )
        elif isinstance(logic, Timer):
            self._blueprint.create_timer(logic, x, y, z)

        if not self._options.compact:
            self._middle_gates_offset += 1

    def _create_attachment(
        self,
        gate_id: LogicId,
        gate_x: int,
        gate_y: int,
        gate_z: int,
        attachment: str,
        color: Union[str, None] = None,
    ):
        attachment_id = self._circuit.id_generator.next()

        match attachment:
            case "switch":
                self._blueprint.create_switch(
                    gate_x,
                    gate_y,
                    gate_z,
                    attachment_id,
                    gate_id,
                    color=color,
                )
            case "sensor":
                self._blueprint.create_sensor(
                    gate_x - 1,
                    gate_y,
                    gate_z + 1,
                    attachment_id,
                    gate_id,
                    color=color,
                )
            case _:
                raise ValueError(f"attachment with name {attachment} doesn't exist")

    def _create_gate(
        self,
        gate: Gate,
        x: int,
        y: int,
        z: int,
        rotate_to_inputs: bool,
        color: Union[str, None] = None,
        attachment: Union[str, None] = None,
    ):
        xaxis = None
        zaxis = None

        if rotate_to_inputs:
            y += 1
            xaxis = -1
            zaxis = 0

        self._blueprint.create_gate(
            gate, x, y, z, color=color, xaxis=xaxis, zaxis=zaxis
        )

        if attachment is not None:
            self._create_attachment(gate.id, x, y, z, attachment, color)

    def _place_port(
        self,
        port: Port,
        start_x: int,
        start_y: int,
        start_z: int,
        color: Color,
        attachment: Union[str, None] = None,
    ) -> int:
        match port.stripes_orientation:
            case "horizontal":
                for i, gate in enumerate(port.gates):
                    self._create_gate(
                        gate,
                        start_x + i % port.stripe_width,
                        start_y,
                        start_z + i // port.stripe_width,
                        port.rotate_to_inputs,
                        color=color.hex,
                        attachment=attachment,
                    )

                return min(port.stripe_width, len(port.gates))
            case "vertical":
                for i, gate in enumerate(port.gates):
                    self._create_gate(
                        gate,
                        start_x + i // port.stripe_width,
                        start_y,
                        start_z + i % port.stripe_width,
                        port.rotate_to_inputs,
                        color=color.hex,
                        attachment=attachment,
                    )

                return len(port.gates) // port.stripe_width
