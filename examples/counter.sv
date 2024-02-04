module counter #(parameter COUNTER_WIDTH = 8) (
    input bit clk,
    input bit rst,

    output bit clk_out,
    output reg [COUNTER_WIDTH-1:0] value
);
    assign clk_out = clk;

    always @(posedge clk) begin
        if (rst) value = '0;
        else value++;
    end
endmodule
