`define OP_ADD 0'b00
`define OP_SUB 0'b01
`define OP_MUL 0'b10
`define OP_DIV 0'b11

module calculator #(parameter DATA_WIDTH = 16) (
    input bit [DATA_WIDTH-1:0] a,
    input bit [DATA_WIDTH-1:0] b,
    input bit [1:0]            op,

    output bit [DATA_WIDTH-1:0] result,
    output bit                  invalid_input
);
    always begin
        invalid_input = 0;
        result = 0;

        case (op)
            `OP_ADD: result = a + b;
            `OP_SUB: result = a - b;
            `OP_MUL: result = a * b;
            `OP_DIV: begin
                if (b == 0) invalid_input = 1;
                else result = a / b;
            end
        endcase
    end
endmodule
