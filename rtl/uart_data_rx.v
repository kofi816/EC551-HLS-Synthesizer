`timescale 1ns / 1ps
// Whole-byte words. rst is active low, matching the supplied UART modules.
module uart_data_rx #(
    parameter DATA_WIDTH = 16,
    parameter MSB_FIRST = 1
) (
    input wire clk,
    input wire rst,
    input wire uart_rx,
    input wire [2:0] baud_set,
    output reg rx_done,
    output reg timeout_flag,
    output reg [DATA_WIDTH-1:0] data
);
localparam BYTE_COUNT = DATA_WIDTH / 8;
reg [DATA_WIDTH-1:0] data_r;
reg [DATA_WIDTH-1:0] assembled;
integer byte_count;
reg [19:0] timeout_cnt;
wire [7:0] data_byte;
wire byte_rx_done;
wire [19:0] timeout_cycles;
assign timeout_cycles = (baud_set == 0) ? 20'd182291 :
                        (baud_set == 1) ? 20'd91145 :
                        (baud_set == 2) ? 20'd45572 :
                        (baud_set == 3) ? 20'd30381 : 20'd15190;
uart_byte_rx receiver (
    .clk(clk), .rst_n(rst), .baud_set(baud_set), .uart_rx(uart_rx),
    .data_byte(data_byte), .rx_done(byte_rx_done)
);
always @(*) begin
    assembled = data_r;
    if (MSB_FIRST) assembled = (data_r << 8) | data_byte;
    else assembled[byte_count*8 +: 8] = data_byte;
end
always @(posedge clk or negedge rst) begin
    if (!rst) begin
        data_r <= 0;
        data <= 0;
        byte_count <= 0;
        timeout_cnt <= 0;
        rx_done <= 0;
        timeout_flag <= 0;
    end else begin
        rx_done <= 0;
        timeout_flag <= 0;
        if (byte_rx_done) begin
            timeout_cnt <= 0;
            if (byte_count == BYTE_COUNT-1) begin
                data <= assembled;
                rx_done <= 1;
                byte_count <= 0;
                data_r <= 0;
            end else begin
                data_r <= assembled;
                byte_count <= byte_count + 1;
            end
        end else if (byte_count != 0) begin
            if (timeout_cnt >= timeout_cycles) begin
                timeout_flag <= 1;
                byte_count <= 0;
                data_r <= 0;
                timeout_cnt <= 0;
            end else timeout_cnt <= timeout_cnt + 1'b1;
        end else timeout_cnt <= 0;
    end
end
endmodule
