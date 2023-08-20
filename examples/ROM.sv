module ROM(
    input  bit  [7:0]     address,

    output bit [15:0]     read_value,

    (* attachment="sensor", stripe_width=8, override_x=1, override_y=1, override_z=3 *)
    input  bit [16*8-1:0] mem
);
    always begin
        read_value = mem[address*8+:16];
    end
endmodule
