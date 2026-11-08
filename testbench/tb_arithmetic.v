`timescale 1ns / 1ps

module tb_arithmetic;

    parameter WIDTH = 16;

    reg  [WIDTH-1:0] a, b;

    wire [WIDTH-1:0] add_result;
    wire [WIDTH-1:0] sub_result;
    wire [WIDTH-1:0] mul_result;

    integer tests;
    integer failures;
    integer i;

    // Instantiate the arithmetic units.

    adder #(.WIDTH(WIDTH)) uut_add (
        .a(a),
        .b(b),
        .result(add_result)
    );

    subtractor #(.WIDTH(WIDTH)) uut_sub (
        .a(a),
        .b(b),
        .result(sub_result)
    );

    multiplier #(.WIDTH(WIDTH)) uut_mul (
        .a(a),
        .b(b),
        .result(mul_result)
    );

    // Test all three operations for the given inputs.

    task check;
        input [WIDTH-1:0] input_a;
        input [WIDTH-1:0] input_b;

        reg [WIDTH-1:0] expected_add;
        reg [WIDTH-1:0] expected_sub;
        reg [WIDTH-1:0] expected_mul;

        begin
            a = input_a;
            b = input_b;

            expected_add = input_a + input_b;
            expected_sub = input_a - input_b;
            expected_mul = input_a * input_b;

            #1;

            tests = tests + 1;

            if (add_result !== expected_add) begin
                $display(
                    "FAIL ADD: a=%h b=%h got=%h expected=%h",
                    a, b, add_result, expected_add
                );
                failures = failures + 1;
            end

            tests = tests + 1;

            if (sub_result !== expected_sub) begin
                $display(
                    "FAIL SUB: a=%h b=%h got=%h expected=%h",
                    a, b, sub_result, expected_sub
                );
                failures = failures + 1;
            end

            tests = tests + 1;

            if (mul_result !== expected_mul) begin
                $display(
                    "FAIL MUL: a=%h b=%h got=%h expected=%h",
                    a, b, mul_result, expected_mul
                );
                failures = failures + 1;
            end
        end
    endtask

    initial begin

        tests = 0;
        failures = 0;

        a = 0;
        b = 0;

        // Basic arithmetic.
        check(16'd0,    16'd0);
        check(16'd0,    16'd123);
        check(16'd123,  16'd0);
        check(16'd5,    16'd3);
        check(16'd5,    16'd10);
        check(16'd100,  16'd25);

        // Overflow and underflow.
        check(16'hFFFF, 16'd1);
        check(16'hFFFF, 16'hFFFF);

        // Multiplication truncation.
        check(16'd300,  16'd300);
        check(16'h8000, 16'd2);

        // Additional bit patterns.
        check(16'hAAAA, 16'h5555);

        // Random test cases.
        for (i = 0; i < 100; i = i + 1) begin
            check($random, $random);
        end

        // Final result.
        if (failures == 0) begin
            $display(
                "PASS: %0d arithmetic checks passed",
                tests
            );
        end
        else begin
            $display(
                "FAIL: %0d of %0d arithmetic checks failed",
                failures, tests
            );

            $fatal(1, "Arithmetic testbench failed");
        end

        $finish;

    end

endmodule