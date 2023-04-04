`include "types.sv"

module UInt16RAM(
    input clk,
    input UInt16 address,
    input bit read, write,
    input UInt16 input_data,
    output UInt16 output_data
);
    UInt16 data [32];

    always @(posedge clk) begin
        output_data = 0;

        if (read) begin
            output_data = data[address[4:0]];
        end else if (write) begin
            data[address[4:0]] = input_data;
        end
    end
endmodule
