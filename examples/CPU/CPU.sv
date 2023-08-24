`define OP_IO       2'd0
`define OP_MATH     2'd1
`define OP_IMM      2'd2
`define OP_JUMP     2'd3

`define IO_READ     1'b0
`define IO_WRITE    1'b1

`define MATH_OP_ADD 1'b0
`define MATH_OP_SUB 1'b1

module CPU
(
    input bit clk, rst,

    output reg halt,

    output reg [7:0] pc,

    (* rotate_to_inputs, stripe_width=8, override_x=1, override_y=1, override_z=3 *)
    input  bit [2*8-1:0] inputs,

    (* rotate_to_inputs, stripe_width=8, override_x=1, override_y=1, override_z=6 *)
    output reg [2*8-1:0] outputs,

    (* rotate_to_inputs, stripe_width=8, override_x=10, override_y=1, override_z=3 *)
    output reg [4*8-1:0] regs,

    input  bit [15:0]    mem_value,

    output reg [7:0]     mem_address
);
    bit [15:0] instruction = mem_value;
    
    bit [1:0]  opcode      = instruction[1:0];
    bit [1:0]  rs1         = instruction[3:2];
    bit [1:0]  rs2         = instruction[5:4];
    bit [1:0]  rd          = instruction[7:6];
    bit [7:0]  value       = instruction[15:8];

    bit        math_opcode = instruction[15];

    bit [7:0]  rs1_val     = regs[rs1*8+:8];
    bit [7:0]  rs2_val     = regs[rs2*8+:8];

    bit        io_opcode   = instruction[4];
    bit        io_target   = instruction[5];

    bit [7:0]  pc_result;
    bit [7:0]  rd_val;
    bit        write_rd;

    function bit [7:0] op_math();
        case (math_opcode)
            `MATH_OP_ADD: op_math = rs1_val + rs2_val;
            `MATH_OP_SUB: op_math = rs1_val - rs2_val;
        endcase
    endfunction

    always @(posedge clk) begin
        rd_val = 0;
        write_rd = 0;
        pc_result = 0;

        if (rst) begin
            pc = 0;
            outputs = 0;
            halt = 0;
            regs = 0;
            mem_address = 0;
        end else if (!halt) begin
            pc_result = pc + 1;

            case (opcode)
                `OP_IO: begin
                    case (io_opcode)
                        `IO_READ: begin
                            rd_val = inputs[io_target*8+:8];
                            write_rd = 1;
                        end
                        `IO_WRITE: begin
                            outputs[io_target*8+:8] = rs1_val;
                        end
                    endcase
                end
                `OP_MATH: begin
                    rd_val = op_math();
                    write_rd = 1;

                    pc_result = pc + 2;
                end
                `OP_IMM: begin
                    rd_val = value;
                    write_rd = 1;

                    pc_result = pc + 2;
                end
                `OP_JUMP: pc_result = value;
            endcase

            if (!halt) begin
                if (write_rd) regs[rd*8+:8] = rd_val;

                pc = pc_result;
                mem_address = pc;
            end
        end
    end
endmodule
