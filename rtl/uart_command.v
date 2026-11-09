// ASCII commands: Addd/Bddd/Cddd/Dddd (three decimal digits, 000-255), S=start/step, G=run, R=reset, ?=status.
// Wait for one response before sending another command. Whitespace is ignored.
module uart_command (
    input wire clk,
    input wire reset,
    input wire [7:0] rx_data,
    input wire rx_done,
    input wire tx_done,
    input wire busy,
    input wire done,
    input wire [7:0] final_value,
    input wire [7:0] adder_value,
    input wire [7:0] subtractor_value,
    input wire [7:0] multiplier_value,
    output reg [7:0] input_A,
    output reg [7:0] input_B,
    output reg [7:0] input_C,
    output reg [7:0] input_D,
    output reg core_reset,
    output reg core_start,
    output reg core_step,
    output reg [175:0] tx_data,
    output reg tx_send
);
reg [1:0] parse_state;
reg [1:0] selected_input;
reg [9:0] decimal_accumulator;
reg auto_run;
reg run_started;
reg reply_pending;
reg reply_error;
reg [2:0] settle_count;
reg tx_active;
wire decimal_valid;
wire [3:0] decimal_digit;
wire [9:0] decimal_value;
assign decimal_valid = rx_data >= "0" && rx_data <= "9";
assign decimal_digit = rx_data - "0";
assign decimal_value = decimal_accumulator * 10'd10 + decimal_digit;

// Fixed-width unsigned decimal text, including leading zeroes (000 through 255).
function [23:0] decimal_text;
    input [7:0] value;
    reg [7:0] hundreds, tens, ones;
    begin
        hundreds = 8'd48 + value / 100;
        tens = 8'd48 + (value / 10) % 10;
        ones = 8'd48 + value % 10;
        decimal_text = {hundreds, tens, ones};
    end
endfunction

always @(posedge clk) begin
    if (reset) begin
        input_A <= 0;
        input_B <= 0;
        input_C <= 0;
        input_D <= 0;
        core_reset <= 0;
        core_start <= 0;
        core_step <= 0;
        tx_data <= 0;
        tx_send <= 0;
        parse_state <= 0;
        selected_input <= 0;
        decimal_accumulator <= 0;
        auto_run <= 0;
        run_started <= 0;
        reply_pending <= 0;
        reply_error <= 0;
        settle_count <= 0;
        tx_active <= 0;
    end else begin
        core_reset <= 0;
        core_start <= 0;
        core_step <= 0;
        tx_send <= 0;

        if (tx_done) tx_active <= 0;

        // Automatic mode advances the same FSM that manual S commands step.
        if (auto_run) begin
            if (busy) begin
                core_step <= 1;
                run_started <= 1;
            end
            if (run_started && !busy && done) begin
                auto_run <= 0;
                run_started <= 0;
                reply_pending <= 1;
                settle_count <= 3;
            end
        end

        // Ignore terminal CR/LF and spaces, and accept commands only between replies.
        if (rx_done && !auto_run && !reply_pending && !tx_active) begin
            if (rx_data != 8'h0D && rx_data != 8'h0A && rx_data != " ") begin
                if (parse_state != 0) begin
                    if (!decimal_valid) begin
                        parse_state <= 0;
                        reply_error <= 1;
                        reply_pending <= 1;
                        settle_count <= 3;
                    end else if (parse_state < 3) begin
                        decimal_accumulator <= decimal_value;
                        parse_state <= parse_state + 1'b1;
                    end else begin
                        if (!busy && decimal_value <= 10'd255) begin
                            case (selected_input)
                                0: input_A <= decimal_value[7:0];
                                1: input_B <= decimal_value[7:0];
                                2: input_C <= decimal_value[7:0];
                                3: input_D <= decimal_value[7:0];
                            endcase
                        end
                        reply_error <= busy || decimal_value > 10'd255;
                        parse_state <= 0;
                        reply_pending <= 1;
                        settle_count <= 3;
                    end
                end else begin
                    reply_error <= 0;
                    case (rx_data)
                        "A", "B", "C", "D": begin
                            selected_input <= rx_data - "A";
                            decimal_accumulator <= 0;
                            parse_state <= 1;
                        end
                        "S": begin
                            if (busy) core_step <= 1;
                            else core_start <= 1;
                            reply_pending <= 1;
                            settle_count <= 3;
                        end
                        "G": begin
                            if (!busy) core_start <= 1;
                            auto_run <= 1;
                            run_started <= busy;
                        end
                        "R": begin
                            core_reset <= 1;
                            input_A <= 0;
                            input_B <= 0;
                            input_C <= 0;
                            input_D <= 0;
                            reply_pending <= 1;
                            settle_count <= 3;
                        end
                        "?": begin
                            reply_pending <= 1;
                            settle_count <= 3;
                        end
                        default: begin
                            reply_error <= 1;
                            reply_pending <= 1;
                            settle_count <= 3;
                        end
                    endcase
                end
            end
        end

        // Snapshot results after the core has consumed its control pulse.
        if (reply_pending) begin
            if (settle_count != 0) settle_count <= settle_count - 1'b1;
            else begin
                tx_data <= {reply_error ? 8'h21 : 8'h2B, 8'h20,
                    decimal_text(final_value), 8'h20,
                    decimal_text(adder_value), 8'h20,
                    decimal_text(subtractor_value), 8'h20,
                    decimal_text(multiplier_value), 8'h20,
                    busy ? 8'h31 : 8'h30, done ? 8'h31 : 8'h30, 8'h0D, 8'h0A};
                tx_send <= 1;
                tx_active <= 1;
                reply_pending <= 0;
            end
        end

    end
end
endmodule
