module ClockGenerator (
    input bit clk, timer_output, work,
    output bit timer_input
);
    bit is_working = 0;
    bit is_starting = 0;

    always @(posedge clk) begin
        timer_input <= 0;

        if (!work) begin
            if (!timer_output) begin
                is_working <= 0;
                is_starting <= 0;
            end
        end else begin
            if (is_starting && timer_output) begin
                is_starting <= 0;
            end


        end
    end
endmodule
