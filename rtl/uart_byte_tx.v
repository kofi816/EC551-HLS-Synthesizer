`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company:
// Engineer:
//
// Create Date: 2026/05/20 22:20:53
// Design Name:
// Module Name: uart_byte_tx
// Project Name:
// Target Devices:
// Tool Versions:
// Description:
//
// Dependencies:
//
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
//
//////////////////////////////////////////////////////////////////////////////////


module uart_byte_tx(
    input clk,
    input rst_n,
    input [7:0] data_byte,
    input send_en,
    input [2:0] baud_set,
    output reg uart_tx,
    output reg tx_done,
    output reg uart_state
    );

    wire reset = ~rst_n;
    localparam START_BIT = 1'b0;
	localparam STOP_BIT = 1'b1;

    reg bps_clk;
	reg [15:0]div_cnt;  //divider counter -- from 0 to bps_DR
	reg [15:0]bps_DR;   //maximum value for counter
	reg [3:0]bps_cnt;
	reg [7:0]data_byte_reg;

    //state transition
    always@(posedge clk or posedge reset)begin
        if(reset)
            uart_state <= 1'b0;
        else if(send_en)
            uart_state <= 1'b1;
        else if(bps_cnt == 4'd11)
            uart_state <= 1'b0;
        else
            uart_state <= uart_state;
    end

    //internal data byte resigter
    always@(posedge clk or posedge reset)begin
        if(reset)
            data_byte_reg <= 8'b0;
        else if(send_en)
            data_byte_reg <= data_byte;
        else
            data_byte_reg <= data_byte_reg;
    end

    //baud rate setting
    always@(posedge clk or posedge reset) begin
        if(reset)
            bps_DR <= 16'd5207;
        else
            case(baud_set)
                0:bps_DR <= 16'd5207;//9600
                1:bps_DR <= 16'd2603;//19200
                2:bps_DR <= 16'd1301;//38400
                3:bps_DR <= 16'd867;//57600
                4:bps_DR <= 16'd433;//115200
                default:bps_DR <= 16'd5207;
            endcase
    end

    //counter setting
    always@(posedge clk or posedge reset) begin
        if(reset)
            div_cnt <= 16'b0;
        else if(uart_state)begin
            if(div_cnt == bps_DR)
                div_cnt <= 16'b0;
            else
                div_cnt <= div_cnt + 1'b1;
        end
        else
            div_cnt <= 16'b0;
    end

    //baud clk (pulse)
    always @(posedge clk or posedge reset) begin
        if(reset)
            bps_clk <= 1'b0;
        else if(div_cnt == 16'b1)
            bps_clk <= 1'b1;
        else
            bps_clk <= 1'b0;
    end

    //bps counter
    always @(posedge clk or posedge reset) begin
        if(reset)
            bps_cnt <= 4'b0;
        else if (bps_cnt == 4'd11)
            bps_cnt <= 4'b0;
        else if(bps_clk)
            bps_cnt <= bps_cnt + 1'b1;
        else
            bps_cnt <= bps_cnt;
    end

    always @(posedge clk or posedge reset) begin
        if(reset)
            tx_done <= 1'b0;
        else if(bps_cnt == 4'd11)
            tx_done <= 1'b1;
        else
            tx_done <= 1'b0;
    end

    always @(posedge clk or posedge reset) begin
        if(reset)
            uart_tx <= 1'b1;
        else begin
            case(bps_cnt)
                0:uart_tx <= 1'b1;
                1:uart_tx <= START_BIT;
                2:uart_tx <= data_byte_reg[0];
                3:uart_tx <= data_byte_reg[1];
                4:uart_tx <= data_byte_reg[2];
                5:uart_tx <= data_byte_reg[3];
                6:uart_tx <= data_byte_reg[4];
                7:uart_tx <= data_byte_reg[5];
                8:uart_tx <= data_byte_reg[6];
                9:uart_tx <= data_byte_reg[7];
                10:uart_tx <= STOP_BIT;
                default:uart_tx <= 1'b1;
            endcase
        end
    end


endmodule
