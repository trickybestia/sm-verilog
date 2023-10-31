`include "digit.sv"

localparam bit [11*15-1:0] DIGITS_PATTERNS = {
    15'b000000000000000, // empty_digit
    15'b111111010111101, // 9
    15'b111111010111111, // 8
    15'b111111000010000, // 7
    15'b101111010111111, // 6
    15'b101111010111101, // 5
    15'b111110010011100, // 4
    15'b111111010110101, // 3
    15'b111011010110111, // 2
    15'b111110000000000, // 1
    15'b111111000111111  // 0
};

function bit [14:0] digit_pattern(digit_t digit);
    digit_t effective_digit;

    if (digit > empty_digit) effective_digit = empty_digit;
    else effective_digit = digit;
    
    digit_pattern = DIGITS_PATTERNS[15*effective_digit+:15];
endfunction

module number_display #(parameter NUMBER_WIDTH = 8) (
    input bit [NUMBER_WIDTH-1:0] number,

    (* gate_rotation="backward", stripe_width=5, stripes_orientation="vertical", override_x=1, override_y=1, override_z=3 *)
    output bit [15*DIGITS_COUNT+5*(DIGITS_COUNT-1)-1:0] display
);
    localparam DIGITS_COUNT = $rtoi($ceil(NUMBER_WIDTH * $log10(2)));
    
    digit_t digits [DIGITS_COUNT];
    bit [NUMBER_WIDTH-1:0] remaining_number;
    
    always begin
        display = '0;

        remaining_number = number;

        for (integer i = 0; i != DIGITS_COUNT; i++) begin
            if (remaining_number == '0) begin
                digits[DIGITS_COUNT - i - 1] = empty_digit;
            end else begin
                digits[DIGITS_COUNT - i - 1] = remaining_number % 10;
                remaining_number /= 10;
            end
        end

        if (digits[DIGITS_COUNT - 1] == empty_digit) digits[DIGITS_COUNT - 1] = 0;

        for (integer i = 0; i != DIGITS_COUNT; i++) begin
            display[(15+5)*i+:15] = digit_pattern(digits[i]);
        end
    end
endmodule
