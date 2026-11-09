// End-to-end serial test for the current five-equation constrained-ASAP example.
`timescale 1ns/1ps
module tb_fpga_uart_top;
reg clk = 0;
always #10 clk = ~clk;
reg uart_rx = 1;
wire uart_tx;
wire [7:0] led;
localparam BIT_NS = 104160;
reg [175:0] response;
reg [7:0] received;
integer i;
reg [7:0] expected_hundreds, expected_tens, expected_ones;
fpga_uart_top dut (
    .clk(clk),
    .uart_rx(uart_rx),
    .uart_tx(uart_tx),
    .led(led)
);

task send_byte;
    input [7:0] value;
    integer bit_index;
    begin
        uart_rx = 0;
        #(BIT_NS);
        for (bit_index=0; bit_index<8; bit_index=bit_index+1) begin
            uart_rx = value[bit_index];
            #(BIT_NS);
        end
        uart_rx = 1;
        #(BIT_NS);
    end
endtask

task receive_byte;
    output [7:0] value;
    integer bit_index;
    begin
        @(negedge uart_tx);
        #(BIT_NS/2);
        if (uart_tx !== 0) $fatal(1, "Invalid start bit");
        for (bit_index=0; bit_index<8; bit_index=bit_index+1) begin
            #(BIT_NS);
            value[bit_index] = uart_tx;
        end
        #(BIT_NS);
        if (uart_tx !== 1) $fatal(1, "Invalid stop bit");
    end
endtask

task get_reply;
    integer byte_index;
    begin
        response = 0;
        for (byte_index=0; byte_index<22; byte_index=byte_index+1) begin
            receive_byte(received);
            response = {response[167:0], received};
        end
        #(BIT_NS*2);
    end
endtask

task input_command;
    input [7:0] name;
    input [23:0] digits;
    begin
        send_byte(name);
        #(BIT_NS);
        send_byte(digits[23:16]);
        #(BIT_NS);
        send_byte(digits[15:8]);
        #(BIT_NS);
        fork
            send_byte(digits[7:0]);
            get_reply;
        join
    end
endtask

task set_input;
    input [7:0] name;
    input [7:0] value;
    begin
        input_command(name, dut.controller.decimal_text(value));
        if (response[175:168] !== "+") $fatal(1, "Input rejected");
    end
endtask

task command_byte;
    input [7:0] command;
    begin
        // UART is full duplex: the FPGA can begin replying during the stop bit.
        fork
            send_byte(command);
            get_reply;
        join
    end
endtask

initial begin
    // Exhaustively check decimal conversion across the entire 8-bit range.
    for (i=0; i<256; i=i+1) begin
        expected_hundreds = 48 + i/100;
        expected_tens = 48 + (i/10)%10;
        expected_ones = 48 + i%10;
        if (dut.controller.decimal_text(i) !==
            {expected_hundreds, expected_tens, expected_ones})
            $fatal(1, "Decimal conversion failed for %0d", i);
    end
    #(BIT_NS*3);
    command_byte("R");
    set_input("A", 0);
    if (dut.input_A !== 0) $fatal(1, "Zero input failed");
    set_input("A", 10);
    if (dut.input_A !== 10) $fatal(1, "Decimal input failed");
    set_input("A", 100);
    if (dut.input_A !== 100) $fatal(1, "Hundreds input failed");
    set_input("A", 255);
    if (dut.input_A !== 255) $fatal(1, "Maximum input failed");
    input_command("A", "256");
    if (response[175:168] !== "!" || dut.input_A !== 255) $fatal(1, "Overflow accepted");
    input_command("A", "999");
    if (response[175:168] !== "!" || dut.input_A !== 255) $fatal(1, "Overflow wrapped");
    input_command("A", "00F");
    if (response[175:168] !== "!" || dut.input_A !== 255) $fatal(1, "Nondecimal input accepted");
    set_input("A", 1);
    set_input("B", 2);
    set_input("C", 3);
    set_input("D", 4);
    command_byte("G");
    if (response !== {"+ 025 025 018 021 01", 8'h0D, 8'h0A}) $fatal(1, "Unexpected final reply: %s", response);
    if (led !== 25) $fatal(1, "Incorrect LED result");
    command_byte("R");
    set_input("A", 1);
    set_input("B", 2);
    set_input("C", 3);
    set_input("D", 4);
    command_byte("S");
    input_command("A", "099");
    if (response[175:168] !== "!" || dut.input_A !== 1) $fatal(1, "Busy input accepted");
    for (i=0; i<5; i=i+1) begin
        command_byte("S");
    end
    if (response !== {"+ 025 025 018 021 01", 8'h0D, 8'h0A}) $fatal(1, "Manual stepping failed");
    command_byte("?");
    if (response !== {"+ 025 025 018 021 01", 8'h0D, 8'h0A}) $fatal(1, "Status failed");
    $display("PASS: decimal input boundaries, invalid input, busy rejection, UART loading, run, reset, manual step, status");
    $finish;
end

initial begin
    #1000000000;
    $fatal(1, "UART simulation timeout");
end
endmodule
