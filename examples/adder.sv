module adder (
    (* attachment="switch" *) // other attachment is "sensor"
    input bit [7:0] a, b,     // you also can rotate attachments
    // using attachment_rotation attribute values are "forward"
    // and "backward" (default). You can rotate gate using
    // gate_rotation, values are "forward", "backward",
    // and "top" (default).
    
    output bit [8:0] sum
);
    always begin
        sum = a + b;
    end
endmodule
