`include "types.sv"

/*
1 - jump (addr)
2 - store (value) // a = value
3 - add // a = a + b
4 - sub // a = a - b
5 - read_i1 // a = i1
6 - read_i2 // a = i2
7 - write_o1 // o1 = a
8 - write_o2 // o2 = a
9 - swap // a, b = b, a
*/

module CPU
(
    (* hide *)
    input UInt8 i_ptr_i, a_i, b_i, o1_i, o2_i,
    (* hide *)
    input bit halt_i,
    input UInt8 i1, i2,
    input bit [63:0] i_mem,
    input rst,
    (* connect_to="i_ptr_i" *)
    output UInt8 i_ptr,
    (* connect_to="a_i" *)
    output UInt8 a,
    (* connect_to="b_i" *)
    output UInt8 b,
    (* connect_to="o1_i" *)
    output UInt8 o1,
    (* connect_to="o2_i" *)
    output UInt8 o2,
    (* connect_to="halt_i" *)
    output bit halt
);
    always begin
        i_ptr = i_ptr_i;
        a = a_i;
        b = b_i;
        o1 = o1_i;
        o2 = o2_i;
        halt = halt_i;

        if (rst) begin
            i_ptr = 0;
            a = 0;
            b = 0;
            o1 = 0;
            o2 = 0;
            halt = 0;
        end else if (!halt)       
            case (i_mem[i_ptr*8+:8])
                1: i_ptr = i_mem[(i_ptr+1)*8+:8];
                2: begin
                    a = i_mem[(i_ptr+1)*8+:8];

                    i_ptr += 2;
                end
                3: begin
                    a += b;

                    i_ptr++;
                end
                4: begin
                    a -= b;

                    i_ptr++;
                end
                5: begin
                    a = i1;

                    i_ptr++;
                end
                6: begin
                    a = i2;

                    i_ptr++;
                end
                7: begin
                    o1 = a;

                    i_ptr++;
                end
                8: begin
                    o2 = a;

                    i_ptr++;
                end
                9: begin
                    {a, b} = {b, a};

                    i_ptr++;
                end
                default: begin
                    halt = 1;
                end
            endcase
    end
endmodule
