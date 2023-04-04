module UInt16Counter(
    input clk,
    output reg [15:0] counter
);
    always @(posedge clk) begin
        counter <= counter + 1;
    end
endmodule
