`timescale 1ns / 1ps

module subtractor #(
    parameter WIDTH = 16
)(
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] result
);

    assign result = a - b;

endmodule