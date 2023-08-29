`include "digit_display.sv"

module digit_selector #(parameter NUMBER_WIDTH = 16) (
    input bit [NUMBER_WIDTH-1:0] previous_number,
    input bit                    one, two, three, four, five, six, seven, eight, nine,

    output bit [NUMBER_WIDTH-1:0] new_number,
    output bit                    top_left, top, top_right, bottom_right, bottom, bottom_left, middle
);
    digit_t digit;

    digit_display digit_display(digit, top_left, top, top_right, bottom_right, bottom, bottom_left, middle);

    always begin
        new_number = 0;
        digit = 0;

        if (one + two + three + four + five + six + seven + eight + nine == 1) begin
            if (one)
                digit = 1;
            else if (two)
                digit = 2;
            else if (three)
                digit = 3;
            else if (four)
                digit = 4;
            else if (five)
                digit = 5;
            else if (six)
                digit = 6;
            else if (seven)
                digit = 7;
            else if (eight)
                digit = 8;
            else
                digit = 9;
        end
        
        new_number = previous_number * 10 + digit;
    end
endmodule
