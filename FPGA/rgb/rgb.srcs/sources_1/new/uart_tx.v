`timescale 1ns / 1ps

module uart_tx #(
    parameter integer CLK_FREQ_HZ = 100_000_000,
    parameter integer BAUD_RATE   = 921_600
)(
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] data_i,
    input  wire       start_i,
    output reg        tx_o,
    output reg        busy_o
);

    localparam integer CLKS_PER_BIT = CLK_FREQ_HZ / BAUD_RATE;

    localparam [1:0]
        IDLE      = 2'd0,
        START_BIT = 2'd1,
        DATA_BITS = 2'd2,
        STOP_BIT  = 2'd3;

    reg [1:0] state = IDLE;

    reg [15:0] clk_count = 16'd0;
    reg [2:0]  bit_index = 3'd0;
    reg [7:0]  tx_data   = 8'd0;

    always @(posedge clk) begin
        if (rst) begin
            state     <= IDLE;
            clk_count <= 16'd0;
            bit_index <= 3'd0;
            tx_data   <= 8'd0;
            tx_o      <= 1'b1;
            busy_o    <= 1'b0;
        end else begin

            case (state)

                IDLE: begin
                    tx_o      <= 1'b1;
                    busy_o    <= 1'b0;
                    clk_count <= 16'd0;
                    bit_index <= 3'd0;

                    if (start_i == 1'b1) begin
                        tx_data <= data_i;
                        busy_o  <= 1'b1;
                        state   <= START_BIT;
                    end
                end

                START_BIT: begin
                    tx_o <= 1'b0;

                    if (clk_count == CLKS_PER_BIT - 1) begin
                        clk_count <= 16'd0;
                        state <= DATA_BITS;
                    end else begin
                        clk_count <= clk_count + 16'd1;
                    end
                end

                DATA_BITS: begin
                    tx_o <= tx_data[bit_index];

                    if (clk_count == CLKS_PER_BIT - 1) begin
                        clk_count <= 16'd0;

                        if (bit_index == 3'd7) begin
                            bit_index <= 3'd0;
                            state <= STOP_BIT;
                        end else begin
                            bit_index <= bit_index + 3'd1;
                        end
                    end else begin
                        clk_count <= clk_count + 16'd1;
                    end
                end

                STOP_BIT: begin
                    tx_o <= 1'b1;

                    if (clk_count == CLKS_PER_BIT - 1) begin
                        clk_count <= 16'd0;
                        state <= IDLE;
                    end else begin
                        clk_count <= clk_count + 16'd1;
                    end
                end

                default: begin
                    state <= IDLE;
                end

            endcase
        end
    end

endmodule