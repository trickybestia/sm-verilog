`include "UInt16DigitDisplay.sv"

module UInt16NumberDisplay(
    input UInt16 number,
    output UInt16 remaining_number,
    output bit top_left, top, top_right, bottom_right, bottom, bottom_left, middle
);
    Digit digit;

    UInt16DigitDisplay digit_display(digit, top_left, top, top_right, bottom_right, bottom, bottom_left, middle);

    always begin
        digit <= EmptyDigit;
        remaining_number <= 0;

        if (number != 0) begin
            remaining_number <= number / 10;
            digit <= number % 10;
        end
    end
endmodule
