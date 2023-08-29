module rom #(parameter ADDR_WIDTH = 8, parameter MEM_SIZE = 32) (
    input  bit  [ADDR_WIDTH-1:0] address,

    (* attachment="sensor", stripe_width=8, override_x=1, override_y=1, override_z=3 *)
    input  bit  [MEM_SIZE*8-1:0] mem,

    output bit [15:0]     read_value
);
    always begin
        read_value = mem[address*8+:16];
    end
endmodule
