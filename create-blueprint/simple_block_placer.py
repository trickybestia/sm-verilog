from .shapes import ShapeId
from .color_generator import ColorGenerator
from .blueprint import Blueprint
from .circuit import Circuit
from .block_placer import BlockPlacer


class SimpleBlockPlacer(BlockPlacer):
    height: int
    compact: bool
    rotate_middle_gates_to_input: bool
    auto_height: bool

    def __init__(self) -> None:
        super().__init__()

        self.height = 1
        self.auto_height = True
        self.compact = False
        self.rotate_middle_gates_to_input = True

    def place(self, circuit: Circuit) -> Blueprint:
        blueprint = Blueprint()
        color_generator = ColorGenerator()

        if len(circuit.input_gates) != 0:
            blueprint.create_solid(ShapeId.Concrete, 0, -1, 0)

        blueprint.description += "Inputs (first is left):\n\n"

        input_gates_offset = 0

        for name, data_list in circuit.input_gates.items():
            color = color_generator.next()
            blueprint.description += f"{name}: {color.name}\n"

            for data in data_list:
                blueprint.create_gate(
                    data.gate_id, data.gate, input_gates_offset, 0, 0, color.hex
                )
                blueprint.create_solid(
                    ShapeId.Concrete, input_gates_offset, -2, 0, color.hex
                )
                blueprint.create_switch(
                    input_gates_offset,
                    -2,
                    1,
                    circuit.id_generator.next_single(),
                    data.gate_id,
                    color.hex,
                )

                input_gates_offset += 1

        color_generator.reset()

        blueprint.description += "\nOutputs (first is left):\n\n"

        output_gates_offset = 0

        for name, data_list in circuit.output_gates.items():
            color = color_generator.next()
            blueprint.description += f"{name}: {color.name}\n"

            for data in data_list:
                blueprint.create_gate(
                    data.gate_id, data.gate, output_gates_offset, 1, 0, color.hex
                )

                output_gates_offset += 1

        if self.auto_height:
            self.height = int(len(circuit.middle_gates) ** 0.5)

        middle_gates_offset = 0

        for gate_id, gate in circuit.middle_gates.items():
            x = middle_gates_offset // self.height
            y = 2
            z = middle_gates_offset % self.height
            xaxis = None
            zaxis = None

            if self.rotate_middle_gates_to_input:
                if middle_gates_offset % self.height == 0:
                    blueprint.create_solid(ShapeId.Concrete, x, y, 0)

                y += 1
                z += 1
                xaxis = -1
                zaxis = 0

            blueprint.create_gate(
                gate_id,
                gate,
                x,
                y,
                z,
                xaxis=xaxis,
                zaxis=zaxis,
            )

            if not self.compact:
                middle_gates_offset += 1

        return blueprint
