`include "digit.sv"

localparam bit [11*7-1:0] DIGITS_PATTERNS = {
    7'b0000000, // empty_digit
    7'b1111101, // 9
    7'b1111111, // 8
    7'b0111000, // 7
    7'b1101111, // 6
    7'b1101101, // 5
    7'b1011001, // 4
    7'b0111101, // 3
    7'b0110111, // 2
    7'b0011000, // 1
    7'b1111110  // 0
};

function bit [6:0] digit_pattern(digit_t digit);
    digit_t effective_digit;

    if (digit > empty_digit) effective_digit = empty_digit;
    else effective_digit = digit;
    
    digit_pattern = DIGITS_PATTERNS[7*effective_digit+:7];
endfunction

module digit_display(
    input  digit_t digit,

    output bit top_left, top, top_right, bottom_right, bottom, bottom_left, middle
);
    always begin
        {top_left, top, top_right, bottom_right, bottom, bottom_left, middle} = digit_pattern(digit);
    end
endmodule
