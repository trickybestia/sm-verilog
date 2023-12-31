`include "mem_defines.sv"

module rv32i_cpu_ram (
    (* override_y=-11 *)
    input  bit clk,
    (* override_y=-11 *)
    input  bit rst,

    (* override_y=-10 *)
    output bit clk_out,

    (* gate_rotation="backward", stripe_width=8, override_x=10, override_y=1, override_z=3, ignore_timings *)
    output bit [SIZE*8-1:0] display,

    (* override_y=-11 *)
    input  bit [1:0]            mode,

    (* override_y=-11 *)
    input  bit [ADDR_WIDTH-1:0] address,

    (* override_y=-11 *)
    input  bit [31:0]           write_value,

    (* override_x=2, override_y=-10 *)
    output reg [31:0]           value
);
    localparam SIZE = 32;
    localparam ADDR_WIDTH = 5;

    reg [7:0] ram [SIZE-1:0];
    bit [2:0] write_size;

    assign clk_out = clk;

    function bit [31:0] read(bit [ADDR_WIDTH-1:0] address);
        read = {ram[address], ram[address + 1], ram[address + 2], ram[address + 3]};
    endfunction

    function void write(bit [ADDR_WIDTH-1:0] address, bit [31:0] value, integer width);
        for (integer i = 0; i != width; i++) begin
            ram[address + i] = value;
            
            value >>= 8;
        end
    endfunction

    always @(posedge clk) begin
        if (rst) begin
            for (integer i = 0; i != SIZE; i++) begin
                ram[i] = 0;
            end
        end

        value = '0;
        case (mode)
            `MEM_READ:       value = read(address);
            `MEM_WRITE_WORD: write(address, write_value, 4);
            `MEM_WRITE_HALF: write(address, write_value, 2);
            `MEM_WRITE_BYTE: write(address, write_value, 1);
        endcase

        for (integer i = 0; i != SIZE; i++) display[i*8+:8] <= ram[i];
    end
endmodule
