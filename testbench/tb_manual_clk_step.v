`timescale 1ns / 1ps

module tb_manual_clk_step;

    localparam integer DEBOUNCE_CYCLES = 4;

    reg clk = 1'b0;
    reg rst = 1'b1;
    reg step_button = 1'b0;

    wire step_enable;

    integer pulses = 0;
    integer failures = 0;

    // 100 MHz clock (10 ns period)
    always #5 clk = ~clk;

    // Device under test
    manual_clk_step #(
        .DEBOUNCE_CYCLES(DEBOUNCE_CYCLES)
    ) dut (
        .clk(clk),
        .rst(rst),
        .step_button(step_button),
        .step_enable(step_enable)
    );

    // Count generated step pulses
    always @(posedge clk) begin
        #1;

        if (step_enable === 1'b1)
            pulses = pulses + 1;
        else if (step_enable !== 1'b0) begin
            $display("FAIL: step_enable is unknown at %0t", $time);
            failures = failures + 1;
        end
    end

    // Wait for N clock cycles
    task wait_clocks;
        input integer n;
        integer k;

        begin
            for (k = 0; k < n; k = k + 1)
                @(negedge clk);
        end
    endtask

    // Verify pulse count
    task expect_pulses;
        input integer expected;

        begin
            if (pulses !== expected) begin
                $display(
                    "FAIL: expected %0d pulses, got %0d at %0t",
                    expected, pulses, $time
                );
                failures = failures + 1;
            end
        end
    endtask

    initial begin

        // Initialize and release reset
        wait_clocks(3);
        rst = 1'b0;

        wait_clocks(5);
        expect_pulses(0);

        // TEST 1: Button bouncing should not generate a step
        step_button = 1'b1;
        wait_clocks(1);

        step_button = 1'b0;
        wait_clocks(1);

        step_button = 1'b1;
        wait_clocks(1);

        step_button = 1'b0;
        wait_clocks(8);

        expect_pulses(0);

        // TEST 2: One valid press generates one pulse
        step_button = 1'b1;
        wait_clocks(12);

        expect_pulses(1);

        // TEST 3: Holding the button must not repeat pulses
        wait_clocks(20);

        expect_pulses(1);

        // TEST 4: Release and press again
        step_button = 1'b0;
        wait_clocks(12);

        expect_pulses(1);

        step_button = 1'b1;
        wait_clocks(12);

        expect_pulses(2);

        // TEST 5: Reset while button is pressed
        rst = 1'b1;
        wait_clocks(2);

        expect_pulses(2);

        rst = 1'b0;
        wait_clocks(12);

        expect_pulses(3);

        // Final result
        if (failures == 0) begin
            $display(
                "PASS: manual clock-step tests passed (%0d pulses)",
                pulses
            );
        end
        else begin
            $display(
                "FAIL: %0d manual clock-step checks failed",
                failures
            );

            $fatal(1, "Manual clock-step testbench failed");
        end

        $finish;
    end

endmodule