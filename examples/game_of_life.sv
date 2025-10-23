module game_of_life #(
    parameter SIZE = 10
) (
    input bit clk,
    (* attachment="switch" *)
    input bit rst,

    output bit clk_out,

    (* attachment="switch", stripe_width=SIZE, stripes_orientation="vertical", override_x=SIZE + 3, override_y=1, override_z=3 *)
    input bit [SIZE * SIZE - 1:0] field_in,

    (* gate_rotation="backward", stripe_width=SIZE, stripes_orientation="vertical", override_x=1, override_y=1, override_z=3 *)
    output bit [SIZE * SIZE - 1:0] field
);

// Could use SystemVerilog 2D array there, but Icarus Verilog doesn't dump it to .vcd file,
// so using plain vector
bit [SIZE * SIZE * 4 - 1:0] neighbors_count;

assign clk_out = clk;

generate
    for (genvar x = 0; x != SIZE; x++) begin
        for (genvar y = 0; y != SIZE; y++) begin
            always_comb begin
                neighbors_count[(y * SIZE + x) * 4+:4] = 0;

                for (integer n_x = -1; n_x != 2; n_x++) begin
                    for (integer n_y = -1; n_y != 2; n_y++) begin
                        if ((n_x != 0 || n_y != 0) && x + n_x >= 0 && x + n_x < SIZE && y + n_y >= 0 && y + n_y < SIZE) begin
                            neighbors_count[(y * SIZE + x) * 4+:4] += field[(y + n_y) * SIZE + x + n_x];
                        end
                    end
                end
            end
            
            always_ff @(posedge clk) begin
                if (rst) begin
                    field[y * SIZE + x] <= field_in[y * SIZE + x];
                end else if (field[y * SIZE + x]) begin
                    if (neighbors_count[(y * SIZE + x) * 4+:4] != 2 && neighbors_count[(y * SIZE + x) * 4+:4] != 3) begin
                        field[y * SIZE + x] <= 0;
                    end
                end else if (neighbors_count[(y * SIZE + x) * 4+:4] == 3) begin
                    field[y * SIZE + x] <= 1;
                end
            end
        end
    end
endgenerate

endmodule
