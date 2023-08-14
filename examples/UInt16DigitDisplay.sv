`include "types.sv"

module UInt16DigitDisplay(
    input Digit digit,
    output bit top_left, top, top_right, bottom_right, bottom, bottom_left, middle
);
    always begin
        top_left <= 0;
        top <= 0;
        top_right <= 0;
        bottom_right <= 0;
        bottom <= 0;
        bottom_left <= 0;
        middle <= 0;

        if (digit != EmptyDigit) begin
            top_left <= digit == 0 || digit == 4 || digit == 5 || digit == 6 || digit == 8 || digit == 9;
            top <= digit == 0 || digit == 2 || digit == 3 || digit == 5 || digit == 6 || digit == 7 || digit == 8 || digit == 9;
            top_right <= digit == 0 || digit == 1 || digit == 2 || digit == 3 || digit == 4 || digit == 7 || digit == 8 || digit == 9;
            bottom_right <= digit == 0 || digit == 1 || digit == 3 || digit == 4 || digit == 5 || digit == 6 || digit == 7 || digit == 8 || digit == 9;
            bottom <= digit == 0 || digit == 2 || digit == 3 || digit == 5 || digit == 6 || digit == 8 || digit == 9;
            bottom_left <= digit == 0 || digit == 2 || digit == 6 || digit == 8;
            middle <= digit == 2 || digit == 3 || digit == 4 || digit == 5 || digit == 6 || digit == 8 || digit == 9;
        end
    end
endmodule
