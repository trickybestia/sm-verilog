`include "digit_display.sv"

module number_display #(parameter NUMBER_WIDTH = 16) (
    input bit [NUMBER_WIDTH-1:0] number,

    output bit [NUMBER_WIDTH-1:0] remaining_number,
    output bit                    top_left, top, top_right, bottom_right, bottom, bottom_left, middle
);
    digit_t digit;

    digit_display digit_display(digit, top_left, top, top_right, bottom_right, bottom, bottom_left, middle);

    always begin
        digit = empty_digit;
        remaining_number = 0;

        if (number != 0) begin
            remaining_number = number / 10;
            digit = number % 10;
        end
    end
endmodule
