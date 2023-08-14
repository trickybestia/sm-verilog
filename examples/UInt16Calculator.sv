`include "types.sv"

module UInt16Calculator(
    input UInt16 a,
    input UInt16 b,
    input bit add,
    input bit subtract,
    input bit divide,
    input bit multiply,
    output UInt16 result,
    output bit invalid_input
);
    always begin
        invalid_input <= 0;
        result <= 0;

        if (add + subtract + divide + multiply != 1) begin
            invalid_input <= 1;
        end else begin
            if (add) begin
                result <= a + b;
            end else if (subtract) begin
                result <= a - b;
            end else if (divide) begin
                result <= a / b;
            end else begin
                result <= a * b;
            end
        end 
    end
endmodule
