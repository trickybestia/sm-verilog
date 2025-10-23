// run testbench with following command using Icarus Verilog and GTKWave:
// cd examples &&  iverilog -g2005-sv -s game_of_life_tb -o game_of_life_tb.out game_of_life_tb.sv game_of_life.sv && ./game_of_life_tb.out && gtkwave game_of_life_tb.vcd

`timescale 1ns / 1ps

module game_of_life_tb;

logic clk;
logic rst;

logic [3:0] debug;

logic [24:0] field_in;
logic [24:0] field;

always begin
    clk = 1'b0;
    #5;
    clk = 1'b1;
    #5;
end

game_of_life #(
    .SIZE (5)
) uut (
    .clk      (clk),
    .rst      (rst),
    .field_in (field_in),
    .field    (field)
);

initial begin
    $dumpfile("game_of_life_tb.vcd");
    $dumpvars;

    rst      = 0;
    field_in = '0;

    @(posedge clk);
    @(posedge clk);
    @(posedge clk);

    rst          <= 1;
    field_in[7]  <= 1;
    field_in[12] <= 1;
    field_in[17] <= 1;
    @(posedge clk);
    rst      <= 0;
    field_in <= '0;
    @(posedge clk);

    @(posedge clk);
    @(posedge clk);
    @(posedge clk);
    @(posedge clk);
    @(posedge clk);

    $finish;
end

endmodule
