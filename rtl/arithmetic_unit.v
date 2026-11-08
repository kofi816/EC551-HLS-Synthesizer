`timescale 1ns / 1ps

module arithmetic_unit #(
    parameter WIDTH = 16
)(
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    input  wire [1:0]       op_sel,
    output reg  [WIDTH-1:0] result
);

    wire [WIDTH-1:0] add_result;
    wire [WIDTH-1:0] sub_result;
    wire [WIDTH-1:0] mul_result;

    // Addition
    adder #(.WIDTH(WIDTH)) u_adder (
        .a(a),
        .b(b),
        .result(add_result)
    );

    // Subtraction
    subtractor #(.WIDTH(WIDTH)) u_subtractor (
        .a(a),
        .b(b),
        .result(sub_result)
    );

    // Multiplication
    multiplier #(.WIDTH(WIDTH)) u_multiplier (
        .a(a),
        .b(b),
        .result(mul_result)
    );

    // Functional-unit output selection
    always @(*) begin
        case (op_sel)
            2'b00: result = add_result;
            2'b01: result = sub_result;
            2'b10: result = mul_result;
            default: result = {WIDTH{1'b0}};
        endcase
    end

endmodule