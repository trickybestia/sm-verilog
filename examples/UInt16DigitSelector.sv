`include "types.sv"

module UInt16DigitSelector(
    input bit zero, one, two, three, four, five, six, seven, eight, nine,
    input UInt16 previous_number,
    output UInt16 new_number,
    output bit invalid_input,
    output bit top_left, top, top_right, bottom_right, bottom, bottom_left, middle
);
    Digit digit;

    UInt16DigitDisplay digit_display(digit, top_left, top, top_right, bottom_right, bottom, bottom_left, middle);

    always begin
        new_number <= 0;
        invalid_input <= 0;
        digit <= 0;

        if (zero + one + two + three + four + five + six + seven + eight + nine != 1) begin
            invalid_input <= 1;
        end else begin
            if (zero) begin
                digit <= 0;
            end else if (one) begin
                digit <= 1;
            end else if (two) begin
                digit <= 2;
            end else if (three) begin
                digit <= 3;
            end else if (four) begin
                digit <= 4;
            end else if (five) begin
                digit <= 5;
            end else if (six) begin
                digit <= 6;
            end else if (seven) begin
                digit <= 7;
            end else if (eight) begin
                digit <= 8;
            end else begin
                digit <= 9;
            end

            new_number <= previous_number * 10 + digit;
        end
    end
endmodule
