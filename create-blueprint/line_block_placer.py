from .shapes import ShapeId
from .color_generator import ColorGenerator
from .blueprint import Blueprint
from .circuit import Circuit
from .block_placer import BlockPlacer


class LineBlockPlacer(BlockPlacer):
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
                blueprint.create_solid(ShapeId.Concrete, input_gates_offset, -2, 0)
                blueprint.create_switch(
                    input_gates_offset,
                    -2,
                    1,
                    circuit.id_generator.next_single(),
                    data.gate_id,
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
                    data.gate_id, data.gate, output_gates_offset, 2, 0, color.hex
                )

                output_gates_offset += 1

        middle_gates_offset = 0

        for gate_id, gate in circuit.middle_gates.items():
            blueprint.create_gate(gate_id, gate, middle_gates_offset, 1, 0)

            middle_gates_offset += 1

        return blueprint
