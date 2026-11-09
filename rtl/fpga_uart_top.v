// UART-only board top: fixed 50 MHz clock, 9600 baud, 8N1.
module fpga_uart_top (
    input wire clk,
    input wire uart_rx,
    output wire uart_tx,
    output wire [7:0] led
);
// FPGA configuration initializes this startup-reset shift register.
reg [7:0] startup_reset = 8'hFF;
always @(posedge clk) begin
    startup_reset <= {startup_reset[6:0], 1'b0};
end
wire reset;
assign reset = startup_reset[7];
wire [175:0] tx_data;
wire [7:0] rx_data;
wire [7:0] input_A;
wire [7:0] input_B;
wire [7:0] input_C;
wire [7:0] input_D;
wire [7:0] final_value;
wire [7:0] adder_value;
wire [7:0] subtractor_value;
wire [7:0] multiplier_value;
wire rx_done;
wire tx_done;
wire tx_send;
wire busy;
wire done;
wire core_reset;
wire core_start;
wire core_step;
assign led = final_value;
uart_data_rx #(.DATA_WIDTH(8), .MSB_FIRST(1)) receiver (
    .clk(clk),
    .rst(!reset),
    .baud_set(3'd0),
    .uart_rx(uart_rx),
    .data(rx_data),
    .timeout_flag(),
    .rx_done(rx_done)
);
uart_data_tx #(.DATA_WIDTH(176), .MSB_FIRST(1)) transmitter (
    .clk(clk),
    .rst(!reset),
    .baud_set(3'd0),
    .data(tx_data),
    .send_en(tx_send),
    .uart_tx(uart_tx),
    .Tx_Done(tx_done),
    .uart_state()
);
uart_command controller (
    .clk(clk),
    .reset(reset),
    .rx_data(rx_data),
    .rx_done(rx_done),
    .tx_done(tx_done),
    .busy(busy),
    .done(done),
    .final_value(final_value),
    .adder_value(adder_value),
    .subtractor_value(subtractor_value),
    .multiplier_value(multiplier_value),
    .input_A(input_A),
    .input_B(input_B),
    .input_C(input_C),
    .input_D(input_D),
    .core_reset(core_reset),
    .core_start(core_start),
    .core_step(core_step),
    .tx_data(tx_data),
    .tx_send(tx_send)
);
generated_design #(.WIDTH(8)) core (
    .clk(clk),
    .reset(reset || core_reset),
    .start(core_start),
    .step(core_step),
    .busy(busy),
    .done(done),
    .in_A(input_A),
    .in_B(input_B),
    .in_C(input_C),
    .in_D(input_D),
    .final_result(final_value),
    .debug_adder(adder_value),
    .debug_subtractor(subtractor_value),
    .debug_multiplier(multiplier_value)
);
endmodule
