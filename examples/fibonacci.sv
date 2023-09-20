module fibonacci #(parameter COUNTER_WIDTH = 16) (
    input bit clk,
    input bit rst,
    
    output reg [COUNTER_WIDTH-1:0] value
);
    reg [COUNTER_WIDTH-1:0] a;
    reg [COUNTER_WIDTH-1:0] b;

    always @(posedge clk) begin
        if (rst) begin
            a = 'b0;
            b = 'b1;
            value = 'b0;
        end else begin
            if (a > b) begin
                b += a;
                value = b;
            end else begin
                a += b;
                value = a;
            end
        end
    end
endmodule
