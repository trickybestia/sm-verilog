from typing import Union

from .logic import Logic
from .timer import Timer
from .gate import Gate
from .shapes import ShapeId
from .color_generator import ColorGenerator
from .blueprint import Blueprint
from .circuit import Circuit, Port


class BlockPlacer:
    height: Union[int, None]
    compact: bool
    rotate_middle_gates_to_input: bool
    auto_height: bool

    def __init__(self) -> None:
        super().__init__()

        self.height = None
        self.auto_height = True
        self.compact = False
        self.rotate_middle_gates_to_input = True

    def place(self, circuit: Circuit) -> Blueprint:
        blueprint = Blueprint()
        color_generator = ColorGenerator()

        if self.auto_height:
            self.height = int(len(circuit.middle_logic) ** 0.5)

        middle_gates_offset = 0

        def create_gate(
            gate_id: int,
            gate: Gate,
            x: int,
            y: int,
            z: int,
            rotate_to_inputs: bool,
            color: Union[str, None] = None,
        ):
            xaxis = None
            zaxis = None

            if rotate_to_inputs:
                y += 1
                xaxis = -1
                zaxis = 0

            blueprint.create_gate(
                gate_id, gate, x, y, z, color=color, xaxis=xaxis, zaxis=zaxis
            )

        def place_middle_logic(logic_id: int, logic: Logic, rotate_to_inputs: bool):
            nonlocal middle_gates_offset

            x = middle_gates_offset // self.height
            y = 2
            z = middle_gates_offset % self.height

            if rotate_to_inputs:
                z += 1

                if middle_gates_offset % self.height == 0:
                    blueprint.create_solid(ShapeId.Concrete, x, y, 0)

            if isinstance(logic, Gate):
                create_gate(logic_id, logic, x, y, z, rotate_to_inputs)
            elif isinstance(logic, Timer):
                blueprint.create_timer(logic_id, logic, x, y, z)

            if not self.compact:
                middle_gates_offset += 1

        def place_port_in_middle(port: Port):
            for port_gate in port.gates:
                place_middle_logic(
                    port_gate.gate_id, port_gate.gate, self.rotate_middle_gates_to_input
                )

        blueprint.description += "Inputs (first is left):\n\n"

        input_gates_offset = 0

        for name, input in circuit.inputs.items():
            if input.hide:
                place_port_in_middle(input)

                continue

            color = color_generator.next()
            blueprint.description += f"{name}: {color.name}\n"

            for input_gate in input.gates:
                blueprint.create_gate(
                    input_gate.gate_id,
                    input_gate.gate,
                    input_gates_offset,
                    0,
                    0,
                    color.hex,
                )
                blueprint.create_solid(
                    ShapeId.Concrete, input_gates_offset, -2, 0, color.hex
                )
                blueprint.create_switch(
                    input_gates_offset,
                    -2,
                    1,
                    circuit.id_generator.next_single(),
                    input_gate.gate_id,
                    color.hex,
                )

                input_gates_offset += 1

        if input_gates_offset != 0:
            blueprint.create_solid(ShapeId.Concrete, 0, -1, 0)

        color_generator.reset()

        blueprint.description += "\nOutputs (first is left):\n\n"

        output_gates_offset = 0

        for name, output in circuit.outputs.items():
            if output.hide:
                place_port_in_middle(output)

                continue

            color = color_generator.next()
            blueprint.description += f"{name}: {color.name}\n"

            start_x = output_gates_offset
            start_z = 0

            if output.override_x is not None:
                start_x = output.override_x
            else:
                output_gates_offset += output.stripe_width
            if output.override_z is not None:
                start_z = output.override_z

            for i, output_gate in enumerate(output.gates):
                create_gate(
                    output_gate.gate_id,
                    output_gate.gate,
                    start_x + i % output.stripe_width,
                    1,
                    start_z + i // output.stripe_width,
                    output.rotate_to_inputs,
                    color=color.hex,
                )

        for logic_id, logic in circuit.middle_logic.items():
            place_middle_logic(logic_id, logic, self.rotate_middle_gates_to_input)

        return blueprint
