module counter #(parameter COUNTER_WIDTH = 8) (
    input bit clk, rst,
    
    output reg [COUNTER_WIDTH-1:0] value
);
    always @(posedge clk) begin
        if (rst) value = '0;
        else value++;
    end
endmodule
