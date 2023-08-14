module AND2(A, B, Y);
    input A, B;
    output Y = A & B;
endmodule

module AND3(A, B, C, Y);
    input A, B, C;
    output Y = A & B & C;
endmodule

module AND4(A, B, C, D, Y);
    input A, B, C, D;
    output Y = A & B & C & D;
endmodule


module OR2(A, B, Y);
    input A, B;
    output Y = A | B;
endmodule

module OR3(A, B, C, Y);
    input A, B, C;
    output Y = A | B | C;
endmodule

module OR4(A, B, C, D, Y);
    input A, B, C, D;
    output Y = A | B | C | D;
endmodule


module XOR2(A, B, Y);
    input A, B;
    output Y = A ^ B;
endmodule

module XOR3(A, B, C, Y);
    input A, B, C;
    output Y = A ^ B ^ C;
endmodule

module XOR4(A, B, C, D, Y);
    input A, B, C, D;
    output Y = A ^ B ^ C ^ D;
endmodule


module NAND2(A, B, Y);
    input A, B;
    output Y = !(A & B);
endmodule

module NAND3(A, B, C, Y);
    input A, B, C;
    output Y = !(A & B & C);
endmodule

module NAND4(A, B, C, D, Y);
    input A, B, C, D;
    output Y = !(A & B & C & D);
endmodule


module NOR1(A, Y);
    input A;
    output Y = !A;
endmodule

module NOR2(A, B, Y);
    input A, B;
    output Y = !(A | B);
endmodule

module NOR3(A, B, C, Y);
    input A, B, C;
    output Y = !(A | B | C);
endmodule

module NOR4(A, B, C, D, Y);
    input A, B, C, D;
    output Y = !(A | B | C | D);
endmodule
