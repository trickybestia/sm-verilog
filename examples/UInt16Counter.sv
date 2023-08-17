`include "types.sv"

module UInt16Counter(
    input UInt16 counter_i,
    input rst,
    (* connect_to="counter_i" *)
    output UInt16 counter
);
    always begin
        counter = counter_i;

        if (rst)
            counter = '0;
        else
            counter++;
    end
endmodule
