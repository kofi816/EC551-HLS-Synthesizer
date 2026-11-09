// Generated unsigned arithmetic datapath and control FSM.
// Inputs are captured on start while idle; outputs remain valid until overwritten.
// done stays high until reset or the next accepted start.
module generated_design #(parameter WIDTH = 8) (
    input wire clk,
    input wire reset,
    input wire start,
    input wire step,
    output reg busy,
    output reg done,
    output reg [WIDTH-1:0] debug_fu_0,
    output reg [WIDTH-1:0] debug_fu_1,
    output reg [WIDTH-1:0] debug_fu_2,
    input wire [WIDTH-1:0] in_A,
    input wire [WIDTH-1:0] in_B,
    input wire [WIDTH-1:0] in_C,
    input wire [WIDTH-1:0] in_D,
    output wire [WIDTH-1:0] final_result,
    output reg [WIDTH-1:0] debug_adder,
    output reg [WIDTH-1:0] debug_subtractor,
    output reg [WIDTH-1:0] debug_multiplier,
    output wire [WIDTH-1:0] out_X_1,
    output wire [WIDTH-1:0] out_Y_1,
    output wire [WIDTH-1:0] out_Z_1,
    output wire [WIDTH-1:0] out_W_1,
    output wire [WIDTH-1:0] out_OUT_1
);
localparam IDLE = 0;
localparam FINISH = 6;
reg [2:0] state;
reg [WIDTH-1:0] input_0;
reg [WIDTH-1:0] input_1;
reg [WIDTH-1:0] input_2;
reg [WIDTH-1:0] input_3;
reg [WIDTH-1:0] value_0;
reg [WIDTH-1:0] value_1;
reg [WIDTH-1:0] value_2;
reg [WIDTH-1:0] value_3;
reg [WIDTH-1:0] value_4;
assign final_result = value_4;
assign out_X_1 = value_0;
assign out_Y_1 = value_1;
assign out_Z_1 = value_2;
assign out_W_1 = value_3;
assign out_OUT_1 = value_4;
reg [WIDTH-1:0] fu_0_a;
reg [WIDTH-1:0] fu_0_b;
wire [WIDTH-1:0] fu_0_result;
hls_adder #(.WIDTH(WIDTH)) fu_0 (
    .a(fu_0_a), .b(fu_0_b), .result(fu_0_result));
reg [WIDTH-1:0] fu_1_a;
reg [WIDTH-1:0] fu_1_b;
wire [WIDTH-1:0] fu_1_result;
hls_multiplier #(.WIDTH(WIDTH)) fu_1 (
    .a(fu_1_a), .b(fu_1_b), .result(fu_1_result));
reg [WIDTH-1:0] fu_2_a;
reg [WIDTH-1:0] fu_2_b;
wire [WIDTH-1:0] fu_2_result;
hls_subtractor #(.WIDTH(WIDTH)) fu_2 (
    .a(fu_2_a), .b(fu_2_b), .result(fu_2_result));

// FSM-controlled operand multiplexers.
always @(*) begin
    fu_0_a = 0;
    fu_0_b = 0;
    fu_1_a = 0;
    fu_1_b = 0;
    fu_2_a = 0;
    fu_2_b = 0;
    case (state)
        1: begin
            fu_0_a = input_0;
            fu_0_b = input_1;
        end
        2: begin
            fu_0_a = input_2;
            fu_0_b = input_3;
        end
        3: begin
            fu_1_a = value_0;
            fu_1_b = value_1;
        end
        4: begin
            fu_2_a = value_2;
            fu_2_b = value_0;
        end
        5: begin
            fu_0_a = value_3;
            fu_0_b = value_1;
        end
        default: begin end
    endcase
end

// State-dependent assignments provide register write enables.
always @(posedge clk) begin
    if (reset) begin
        state <= IDLE;
        busy <= 0;
        done <= 0;
        input_0 <= 0;
        input_1 <= 0;
        input_2 <= 0;
        input_3 <= 0;
        value_0 <= 0;
        value_1 <= 0;
        value_2 <= 0;
        value_3 <= 0;
        value_4 <= 0;
        debug_fu_0 <= 0;
        debug_fu_1 <= 0;
        debug_fu_2 <= 0;
        debug_adder <= 0;
        debug_subtractor <= 0;
        debug_multiplier <= 0;
    end else begin
        case (state)
            IDLE: begin
                if (start) begin
                    busy <= 1;
                    done <= 0;
                    state <= 1;
                    input_0 <= in_A;
                    input_1 <= in_B;
                    input_2 <= in_C;
                    input_3 <= in_D;
                    debug_fu_0 <= 0;
                    debug_fu_1 <= 0;
                    debug_fu_2 <= 0;
                    debug_adder <= 0;
                    debug_subtractor <= 0;
                    debug_multiplier <= 0;
                end
            end
            1: if (step) begin
                value_0 <= fu_0_result;
                debug_fu_0 <= fu_0_result;
                debug_adder <= fu_0_result;
                state <= 2;
            end
            2: if (step) begin
                value_1 <= fu_0_result;
                debug_fu_0 <= fu_0_result;
                debug_adder <= fu_0_result;
                state <= 3;
            end
            3: if (step) begin
                value_2 <= fu_1_result;
                debug_fu_1 <= fu_1_result;
                debug_multiplier <= fu_1_result;
                state <= 4;
            end
            4: if (step) begin
                value_3 <= fu_2_result;
                debug_fu_2 <= fu_2_result;
                debug_subtractor <= fu_2_result;
                state <= 5;
            end
            5: if (step) begin
                value_4 <= fu_0_result;
                debug_fu_0 <= fu_0_result;
                debug_adder <= fu_0_result;
                busy <= 0;
                done <= 1;
                state <= 6;
            end
            FINISH: begin
                busy <= 0;
                done <= 1;
                if (!start) state <= IDLE;
            end
            default: begin
                state <= IDLE;
                busy <= 0;
                done <= 0;
            end
        endcase
    end
end
endmodule
