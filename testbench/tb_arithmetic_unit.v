`timescale 1ns / 1ps

module tb_arithmetic_unit;

    parameter WIDTH = 16;

    reg  [WIDTH-1:0] a, b;
    reg  [1:0] op_sel;
    wire [WIDTH-1:0] result;

    integer tests;
    integer failures;
    integer i;

    // Instantiate the arithmetic unit
    arithmetic_unit #(.WIDTH(WIDTH)) uut (
        .a(a),
        .b(b),
        .op_sel(op_sel),
        .result(result)
    );

    // Test one operation
    task check;
        input [WIDTH-1:0] input_a;
        input [WIDTH-1:0] input_b;
        input [1:0] operation;

        reg [WIDTH-1:0] expected;

        begin
            a = input_a;
            b = input_b;
            op_sel = operation;

            case (operation)
                2'b00: expected = input_a + input_b;
                2'b01: expected = input_a - input_b;
                2'b10: expected = input_a * input_b;
                default: expected = {WIDTH{1'b0}};
            endcase

            #1;

            tests = tests + 1;

            if (result !== expected) begin
                $display(
                    "FAIL: op=%b a=%h b=%h got=%h expected=%h",
                    op_sel, a, b, result, expected
                );
                failures = failures + 1;
            end
        end
    endtask

    // Test all four operation selections
    task check_all_operations;
        input [WIDTH-1:0] input_a;
        input [WIDTH-1:0] input_b;

        begin
            check(input_a, input_b, 2'b00);
            check(input_a, input_b, 2'b01);
            check(input_a, input_b, 2'b10);
            check(input_a, input_b, 2'b11);
        end
    endtask

    initial begin
        tests = 0;
        failures = 0;

        a = 0;
        b = 0;
        op_sel = 0;

        // Directed tests
        check_all_operations(16'd0,    16'd0);
        check_all_operations(16'd0,    16'd123);
        check_all_operations(16'd123,  16'd0);
        check_all_operations(16'd5,    16'd3);
        check_all_operations(16'd5,    16'd10);
        check_all_operations(16'd100,  16'd25);
        check_all_operations(16'hFFFF, 16'd1);
        check_all_operations(16'hFFFF, 16'hFFFF);
        check_all_operations(16'd300,  16'd300);
        check_all_operations(16'h8000, 16'd2);
        check_all_operations(16'hAAAA, 16'h5555);

        // Random tests
        for (i = 0; i < 100; i = i + 1) begin
            check_all_operations($random, $random);
        end

        // Final results
        if (failures == 0) begin
            $display(
                "PASS: %0d arithmetic-unit checks passed",
                tests
            );
        end
        else begin
            $display(
                "FAIL: %0d of %0d arithmetic-unit checks failed",
                failures, tests
            );

            $fatal(1, "Arithmetic-unit testbench failed");
        end

        $finish;
    end

endmodule