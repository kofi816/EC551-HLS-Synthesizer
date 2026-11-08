`timescale 1ns / 1ps

module manual_clk_step #(
    parameter integer DEBOUNCE_CYCLES = 1_000_000
)(
    input  wire clk,
    input  wire rst,
    input  wire step_button,
    output reg  step_enable
);

    // Synchronize the asynchronous push button
    reg button_meta = 1'b0;
    reg button_sync = 1'b0;

    // Debounce counter
    localparam integer COUNT_WIDTH =
        (DEBOUNCE_CYCLES < 2) ? 1 : $clog2(DEBOUNCE_CYCLES);

    reg [COUNT_WIDTH-1:0] stable_count = 0;

    reg debounced_button = 1'b0;
    reg debounced_prev = 1'b0;

    always @(posedge clk) begin
        if (rst) begin
            button_meta <= 1'b0;
            button_sync <= 1'b0;
            stable_count <= 0;
            debounced_button <= 1'b0;
            debounced_prev <= 1'b0;
            step_enable <= 1'b0;
        end
        else begin

            // Two-stage synchronization
            button_meta <= step_button;
            button_sync <= button_meta;

            // Debounce logic
            if (button_sync == debounced_button) begin
                stable_count <= 0;
            end
            else if (stable_count == DEBOUNCE_CYCLES - 1) begin
                debounced_button <= button_sync;
                stable_count <= 0;
            end
            else begin
                stable_count <= stable_count + 1'b1;
            end

            // Detect rising edge of debounced button
            debounced_prev <= debounced_button;

            step_enable <= debounced_button && !debounced_prev;
        end
    end

endmodule