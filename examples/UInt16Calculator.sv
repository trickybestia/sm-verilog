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

        if (add + subtract + divide + multiply != 1)
            invalid_input <= 1;
        else if (add)
            result <= a + b;
        else if (subtract)
            result <= a - b;
        else if (divide)
            if (b == 0)
                invalid_input <= 1;
            else
                result <= a / b;
        else
            result <= a * b;
    end
endmodule
