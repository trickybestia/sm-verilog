module Counter #(parameter COUNTER_WIDTH = 8) (
    input bit clk, rst,
    
    output reg [COUNTER_WIDTH-1:0] counter
);
    always @(posedge clk) begin
        if (rst) counter = '0;
        else counter++;
    end
endmodule
