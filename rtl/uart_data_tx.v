`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company:
// Engineer:
//
// Create Date: 2026/05/26 02:22:53
// Design Name:
// Module Name: uart_data_tx
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


module uart_data_tx #(
    parameter DATA_WIDTH = 8,
    parameter MSB_FIRST = 1
    )
    (
    input clk,
    input rst,
    input [2:0] baud_set,
    input send_en,
    input [DATA_WIDTH - 1 : 0] data,
    output uart_tx,
    output uart_state,
    output reg Tx_Done
    );

    reg [8:0] cnt;
    reg [DATA_WIDTH - 1 : 0] data_r;
    reg [7:0] data_byte;
    wire byte_tx_done; //byte module tx done
    reg byte_send_en;

    uart_byte_tx uart_byte_tx(
        .clk(clk),
        .rst_n(rst),
        .data_byte(data_byte),
        .send_en(byte_send_en),
        .baud_set(baud_set),
        .uart_tx(uart_tx),
        .tx_done(byte_tx_done),
        .uart_state(uart_state)
    );

    localparam S0 = 0;
    localparam S1 = 1;
    localparam S2 = 2;
    localparam S3 = 3;

    reg [1:0] state, n_state;

    always @(posedge clk or negedge rst) begin
        if(!rst)
            state <= S0;
        else
            state <= n_state;
    end

    always @(*) begin
        n_state = state;
        case(state)
            S0: begin
                if(send_en)
                    n_state = S1;
                else
                    n_state = S0;
            end
            S1: begin
                n_state = S2;
            end
            S2: begin
                if(byte_tx_done)
                    n_state = S3;
                else
                    n_state = S2;
            end
            S3: begin
                if(cnt >= DATA_WIDTH)
                    n_state = S0;
                else
                    n_state = S1;
            end
        endcase
    end

    always @(posedge clk or negedge rst) begin
        if(!rst)begin
            cnt <= 0;
            Tx_Done <= 0;
            data_r <= 0;
            data_byte <= 8'b0;
            byte_send_en <= 0;
        end
        else begin
            byte_send_en <= 0;
            Tx_Done <= 0;
            data_byte <= data_byte;
            data_r <= data_r;
            cnt <= cnt;

            case(state)
                S0: begin
                    if(send_en)begin
                        data_r <= data;
                        cnt <= 0;
                    end
                end
                S1: begin

                    byte_send_en <= 1'b1;

                    if(MSB_FIRST == 1) begin
                        data_byte <= data_r[DATA_WIDTH - 1 : DATA_WIDTH - 8];
                        data_r <= data_r << 8; //move data_r so that operation above is still valid
                    end
                    else begin
                        data_byte <= data_r[7:0];
                        data_r <= data_r >> 8;
                    end
                end
                S2: begin
                    if(byte_tx_done)begin
                        cnt <= cnt + 9'd8;
                    end
                end
                S3: begin
                    if(cnt >= DATA_WIDTH) begin
                        Tx_Done <= 1;
                    end
                end
            endcase
        end
    end
endmodule
