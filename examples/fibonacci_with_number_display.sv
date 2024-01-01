`include "number_display.sv"
`include "fibonacci.sv"

module fibonacci_with_number_display #(parameter NUMBER_WIDTH = 16) (
    input bit clk,
    input bit rst,

    (* gate_rotation="backward", stripe_width=5, stripes_orientation="vertical", override_x=1, override_y=1, override_z=3 *)
    output bit [15*DIGITS_COUNT+5*(DIGITS_COUNT-1)-1:0] display
);
    localparam DIGITS_COUNT = $rtoi($ceil(NUMBER_WIDTH * $log10(2))); // TODO: file an issue in yosys that it is impossible to use instantiated module localparam

    bit [NUMBER_WIDTH-1:0] value;

    number_display #(.NUMBER_WIDTH(NUMBER_WIDTH)) number_display(
        .value,
        .display
    );
    fibonacci #(.COUNTER_WIDTH(NUMBER_WIDTH)) fibonacci(
        .clk,
        .rst,
        .value
    );
endmodule
