`include "cpu.sv"
`include "rom.sv"

module motherboard # (parameter MEM_ADDR_WIDTH = 4) (
    input bit clk,
    input bit rst,

    (* attachment="sensor", stripe_width=8, override_x=1, override_y=1, override_z=3 *)
    input  bit [(2**MEM_ADDR_WIDTH)*8-1:0] mem,

    (* gate_rotation="backward", stripe_width=8, override_x=10, override_y=1, override_z=3 *)
    input  bit [2*8-1:0] inputs,

    output bit           halt,
    output bit [7:0]     pc,

    (* gate_rotation="backward", stripe_width=8, override_x=10, override_y=1, override_z=6 *)
    output bit [2*8-1:0] outputs,

    (* gate_rotation="backward", stripe_width=8, override_x=10, override_y=1, override_z=9 *)
    output bit [4*8-1:0] regs
);
    bit [7:0] address;
    bit [15:0] rom_value;

    cpu cpu(
        .clk(clk),
        .rst(rst),
        .halt(halt),
        .inputs(inputs),
        .outputs(outputs),
        .pc(pc),
        .regs(regs),
        .mem_value(rom_value),
        .mem_address(address)
    );
    rom #(.ADDR_WIDTH(MEM_ADDR_WIDTH)) rom(
        .address(address[MEM_ADDR_WIDTH-1:0]),
        .read_value(rom_value),
        .mem(mem));
endmodule
