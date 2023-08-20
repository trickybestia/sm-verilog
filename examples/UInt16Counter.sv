`include "types.sv"

module UInt16Counter(
    input bit clk, rst,
    output reg [15:0] counter
);
    always @(posedge clk) begin
        if (rst)
            counter = '0;
        else
            counter++;
    end
endmodule
