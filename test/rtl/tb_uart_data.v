`timescale 1ns/1ps
// Loopback both byte orders, repeated words, and partial-word timeout recovery.
module tb_uart_data;
reg clk=0;
always #10 clk=~clk;
reg rst=0;
reg send=0;
reg [31:0] value=0;
wire [1:0] serial, tx_done, rx_done, timeout_flag;
wire [31:0] received [1:0];
reg [1:0] seen=0;
reg [1:0] timed_out=0;
reg [1:0] cut=0;
genvar mode;
generate for(mode=0; mode<2; mode=mode+1) begin: orders
    uart_data_tx #(.DATA_WIDTH(32), .MSB_FIRST(mode)) tx (
        .clk(clk), .rst(rst), .baud_set(3'd4), .send_en(send), .data(value),
        .uart_tx(serial[mode]), .uart_state(), .Tx_Done(tx_done[mode]));
    uart_data_rx #(.DATA_WIDTH(32), .MSB_FIRST(mode)) rx (
        .clk(clk), .rst(rst), .baud_set(3'd4),
        .uart_rx(cut[mode] ? 1'b1 : serial[mode]),
        .data(received[mode]), .rx_done(rx_done[mode]), .timeout_flag(timeout_flag[mode]));
    always @(posedge clk) begin
        if(rx_done[mode]) begin
            if(received[mode] !== value) $fatal(1,"Byte order mismatch");
            seen[mode] <= 1;
        end
        if(timeout_flag[mode]) timed_out[mode] <= 1;
    end
end endgenerate

task transmit;
    input [31:0] word;
    begin
        @(negedge clk); value=word; seen=0; send=1;
        @(negedge clk); send=0;
        wait (&tx_done);
        repeat(20) @(negedge clk);
        if(seen !== 2'b11) $fatal(1,"Missing receive completion");
    end
endtask
initial begin
    repeat(10) @(negedge clk); rst=1;
    transmit(32'h12345678);
    transmit(32'hA500FF81);
    // Deliver one byte, then suppress the remainder of this word.
    @(negedge clk); send=1;
    @(negedge clk); send=0;
    wait(orders[0].rx.byte_rx_done && orders[1].rx.byte_rx_done);
    repeat(4) @(negedge clk); cut=3;
    wait(&tx_done);
    repeat(20000) @(negedge clk);
    if(timed_out !== 3) $fatal(1,"Missing partial-word timeout");
    cut=0;
    transmit(32'h89ABCDEF);
    $display("PASS: multibyte byte orders, repeated words, timeout recovery");
    $finish;
end
initial begin
    #20000000;
    $fatal(1,"Multibyte test timeout");
end
endmodule
