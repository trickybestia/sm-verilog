// Taken from https://github.com/Redcrafter/verilog2factorio and modified under terms of GPL-3.0 license.

`include "mem_defines.sv"

// instructions
// I-type LOAD
`define OP_LOAD      7'b0000011
`define F3_LB        3'b000
`define F3_LH        3'b001
`define F3_LW        3'b010
`define F3_LBU       3'b100
`define F3_LHU       3'b101

// S-type STORE
`define OP_STORE     7'b0100011
`define F3_SB        3'b000
`define F3_SH        3'b001
`define F3_SW        3'b010

// I-type OP-IMM
`define OP_IMM       7'b0010011
`define F3_ADDI      3'b000
`define F3_SLTI      3'b010
`define F3_SLTIU     3'b011
`define F3_XORI      3'b100
`define F3_ORI       3'b110
`define F3_ANDI      3'b111

`define F3_SLLI      3'b001
`define F3_SRLI_SRAI 3'b101

// U-type
`define OP_LUI       7'b0110111
`define OP_AUIPC     7'b0010111

// R-type
`define OP_OP        7'b0110011
`define F3_ADD       3'b000
`define F3_SUB       3'b000
`define F3_SLT       3'b010
`define F3_SLTU      3'b011
`define F3_XOR       3'b100
`define F3_OR        3'b110
`define F3_AND       3'b111
`define F3_SLL       3'b001
`define F3_SRL       3'b101
`define F3_SRA       3'b101

`define F7_30_0      7'b0000000
`define F7_30_1      7'b0100000

// J-type
`define OP_JAL       7'b1101111

// I-type JALR
`define OP_JALR      7'b1100111

// B-type
`define OP_BRANCH    7'b1100011
`define F3_BEQ       3'b000
`define F3_BNE       3'b001
`define F3_BLT       3'b100
`define F3_BGE       3'b101
`define F3_BLTU      3'b110
`define F3_BGEU      3'b111

`define OP_MISC_MEM  7'b0001111
`define FENCE        3'b000
`define FENCE_I      3'b001

// TODO:
`define OP_SYSTEM    7'b1110011
`define ECALL_EBREAK 3'b000
`define CSRRW        3'b001
`define CSRRS        3'b010
`define CSRRC        3'b011
`define CSRRWI       3'b101
`define CSRRSI       3'b110
`define CSRRCI       3'b111

// States
`define STATE_READY  2'b00
`define STATE_LOAD   2'b01
`define STATE_STORE  2'b10
`define STATE_HALT   2'b11

module rv32i_cpu (
    (* override_y=10 *)
    input  bit clk,
    (* override_y=10 *)
    input  bit rst,

    (* override_y=11 *)
    output bit clk_out,
    (* override_y=11 *)
    output bit rst_out,

    (* gate_rotation="backward", override_x=1, override_y=1, override_z=3, ignore_timings *)
    output reg [1:0]        state,
    (* gate_rotation="backward", stripe_width=32, override_x=1, override_y=1, override_z=7, ignore_timings *)
    output bit [32*32-1:32] regs_display,
    (* gate_rotation="backward", override_x=1, override_y=1, override_z=5, ignore_timings *)
    output reg [7:0]        pc,

    (* override_y=10 *)
    input  bit [31:0]       mem_value,
    (* override_y=11 *)
    output reg [1:0]        mem_mode,
    (* override_y=11 *)
    output reg [7:0]        mem_address,
    (* override_y=11 *)
    output reg [31:0]       mem_write_value
);
    reg [31:0] regs [31:1];
    reg [4:0]  load_rd;
    reg [2:0]  load_funct3;

    assign     clk_out = clk;
    assign     rst_out = rst;

    bit [31:0] instruction = mem_value;

    /* instruction decoding wiring
     *
     * Some ranges are overlapped given that different instruction types use different instruction formats.
     */
    bit [6:0]  opcode = instruction[6:0];
    bit [4:0]  rd     = instruction[11:7];                           // destination register
    bit [2:0]  funct3 = instruction[14:12];                          // operation selector
    bit [4:0]  rs1    = instruction[19:15];                          // source register 1
    bit [4:0]  rs2    = instruction[24:20];                          // source register 2
    bit [6:0]  funct7 = instruction[31:25];                          // operation selector

    bit [31:0] i_imm  = $signed(instruction[31:20]);                 // I-type immediate (OP-IMM)
    bit [31:0] u_imm  = {instruction[31:12], 12'b0};                 // U-type immediate (LUI, AUIPC)
    bit [31:0] j_imm  = $signed({instruction[31], instruction[19:12], instruction[20], instruction[30:21], 1'b0 }); // J-type immediate offset (JAL)
    bit [31:0] b_imm  = $signed({instruction[31], instruction[7],  instruction[30:25], instruction[11:8] , 1'b0 }); // B-type immediate offset (BRANCH)
    bit [31:0] s_imm  = $signed({instruction[31:25], instruction[11:7]});     // S-type immediate (STORE)

    bit [31:0] rs1_val = rs1 == 0 ? 0 : regs[rs1];
    bit [31:0] rs2_val = rs2 == 0 ? 0 : regs[rs2];

    bit [31:0] result;
    bit        write_result;
    bit [7:0]  pc_result;

    function bit jump_cond();
        case (funct3)
            `F3_BEQ:  jump_cond = rs1_val == rs2_val;
            `F3_BNE:  jump_cond = rs1_val != rs2_val;
            `F3_BLT:  jump_cond = $signed(rs1_val) < $signed(rs2_val);
            `F3_BGE:  jump_cond = $signed(rs1_val) >= $signed(rs2_val);
            `F3_BLTU: jump_cond = rs1_val < rs2_val;
            `F3_BGEU: jump_cond = rs1_val >= rs2_val;
            default:  state = `STATE_HALT;
        endcase
    endfunction

    function bit [31:0] imm_math();
        case (funct3)
            `F3_ADDI:  imm_math = rs1_val + i_imm;
            `F3_SLTI:  imm_math = $signed(rs1_val) < $signed(i_imm);
            `F3_SLTIU: imm_math = rs1_val < i_imm;
            `F3_XORI:  imm_math = rs1_val ^ i_imm;
            `F3_ORI:   imm_math = rs1_val | i_imm;
            `F3_ANDI:  imm_math = rs1_val & i_imm;
            `F3_SLLI:  imm_math = rs1_val << i_imm[4:0];
            `F3_SRLI_SRAI: begin
                if (i_imm[10]) imm_math = $signed(rs1_val) >>> i_imm[4:0];
                else           imm_math = rs1_val >> i_imm[4:0];
            end
            default: state = `STATE_HALT;
        endcase
    endfunction

    function bit [31:0] op_math();
        case({funct7, funct3})
            {`F7_30_0, `F3_ADD}:  op_math = rs1_val + rs2_val;
            {`F7_30_0, `F3_SLT}:  op_math = $signed(rs1_val) < $signed(rs2_val);
            {`F7_30_0, `F3_SLTU}: op_math = rs1_val < rs2_val;
            {`F7_30_0, `F3_XOR}:  op_math = rs1_val ^ rs2_val;
            {`F7_30_0, `F3_OR}:   op_math = rs1_val | rs2_val;
            {`F7_30_0, `F3_AND}:  op_math = rs1_val & rs2_val;
            {`F7_30_0, `F3_SLL}:  op_math = rs1_val << rs2_val[4:0];
            {`F7_30_0, `F3_SRL}:  op_math = rs1_val >> rs2_val[4:0];
            {`F7_30_1, `F3_SUB}:  op_math = $signed(rs1_val) - $signed(rs2_val);
            {`F7_30_1, `F3_SRA}:  op_math = $signed(rs1_val) >>> rs2_val[4:0];
            default:              state = `STATE_HALT;
        endcase
    endfunction

    always @(posedge clk) begin
        result = '0;
        write_result = '0;
        pc_result = pc + 4;

        if (rst) begin
            pc = '0;
            state = `STATE_READY;
            load_rd = '0;
            load_funct3 = '0;
            for (integer i = 1; i != 32; i++) regs[i] = '0;

            mem_mode = `MEM_READ;
            mem_address = '0;
            mem_write_value = '0;
        end else begin
            case (state)
                `STATE_READY: begin
                    case (opcode)
                        `OP_LOAD: begin
                            case (funct3)
                                `F3_LB, `F3_LH, `F3_LW, `F3_LBU, `F3_LHU: begin
                                    mem_mode = `MEM_READ;
                                    mem_address = rs1_val + i_imm;
                                    load_funct3 = funct3;
                                    load_rd = rd;
                                    state = `STATE_LOAD;
                                end
                                default: state = `STATE_HALT;
                            endcase
                        end
                        `OP_STORE: begin
                            case (funct3)
                                `F3_SB: mem_mode = `MEM_WRITE_BYTE;
                                `F3_SH: mem_mode = `MEM_WRITE_HALF;
                                `F3_SW: mem_mode = `MEM_WRITE_WORD;
                                default: state = `STATE_HALT;
                            endcase

                            if (state != `STATE_HALT) begin
                                state = `STATE_STORE;
                                mem_address = rs1_val + $signed(s_imm);
                                mem_write_value = rs2_val;
                            end
                        end
                        `OP_IMM: begin
                            result = imm_math();
                            write_result = 1;
                        end
                        `OP_LUI: begin
                            result = u_imm;
                            write_result = 1;
                        end
                        `OP_AUIPC: begin
                            result = u_imm + pc;
                            write_result = 1;
                        end
                        `OP_OP: begin
                            result = op_math();
                            write_result = 1;
                        end
                        `OP_JAL: begin
                            result = pc + 4;
                            write_result = 1;
                            pc_result = pc + j_imm;
                        end
                        `OP_JALR: begin
                            result = pc + 4;
                            write_result = 1;
                            pc_result = (rs1_val + i_imm) & 32'b11111111111111111111111111111110;
                        end
                        `OP_BRANCH: if (jump_cond()) pc_result = pc + b_imm;
                        default: state = `STATE_HALT;
                    endcase

                    if (state != `STATE_HALT) begin
                        pc = pc_result;

                        if (state == `STATE_READY) mem_address = pc;
                        if (write_result && rd != 0) regs[rd] = result;
                    end
                end
                `STATE_LOAD: begin
                    if (load_rd != 0) case (load_funct3)
                        `F3_LB:  regs[load_rd] = $signed(mem_value[7:0]);
                        `F3_LH:  regs[load_rd] = $signed(mem_value[15:0]);
                        `F3_LW:  regs[load_rd] = mem_value;
                        `F3_LBU: regs[load_rd] = mem_value[7:0];
                        `F3_LHU: regs[load_rd] = mem_value[15:0];
                        default: /* never */ ;
                    endcase;

                    state = `STATE_READY;
                    mem_address = pc;
                end
                `STATE_STORE: begin
                    state = `STATE_READY;
                    mem_mode = `MEM_READ;
                    mem_write_value = '0;
                    mem_address = pc;
                end
                `STATE_HALT: ;
            endcase
        end

        for (integer i = 1; i != 32; i++) regs_display[i*32+:32] = regs[i];
    end
endmodule
