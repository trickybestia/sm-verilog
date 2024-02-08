module \$_DFF_P_ (input D, input C, output reg Q);
    wire SET   = D;
    wire RESET = !D;

    SYNC_SR_LATCH _TECHMAP_REPLACE (
        .C(C),
        .S(SET),
        .R(RESET),
        .Q(Q)
    );
endmodule
