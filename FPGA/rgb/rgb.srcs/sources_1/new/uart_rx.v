`timescale 1ns / 1ps

module uart_rx #(
    parameter integer CLK_FREQ_HZ = 100_000_000,
    parameter integer BAUD_RATE   = 921_600
)(
    input  wire       clk,
    input  wire       rst,
    input  wire       rx_i,
    output reg [7:0]  data_o,
    output reg        valid_o,
    output reg        framing_error_o
);

    localparam integer CLKS_PER_BIT = CLK_FREQ_HZ / BAUD_RATE;

    localparam [2:0]
        IDLE      = 3'd0,
        START_BIT = 3'd1,
        DATA_BITS = 3'd2,
        STOP_BIT  = 3'd3,
        CLEANUP   = 3'd4;

    reg [2:0] state = IDLE;

    reg [15:0] clk_count = 16'd0;
    reg [2:0]  bit_index = 3'd0;
    reg [7:0]  rx_data   = 8'd0;

    reg rx_sync_0 = 1'b1;
    reg rx_sync_1 = 1'b1;

    always @(posedge clk) begin
        rx_sync_0 <= rx_i;
        rx_sync_1 <= rx_sync_0;
    end

    always @(posedge clk) begin
        if (rst) begin
            state           <= IDLE;
            clk_count       <= 16'd0;
            bit_index       <= 3'd0;
            rx_data         <= 8'd0;
            data_o          <= 8'd0;
            valid_o         <= 1'b0;
            framing_error_o <= 1'b0;
        end else begin
            valid_o         <= 1'b0;
            framing_error_o <= 1'b0;

            case (state)

                IDLE: begin
                    clk_count <= 16'd0;
                    bit_index <= 3'd0;

                    if (rx_sync_1 == 1'b0) begin
                        state <= START_BIT;
                    end
                end

                START_BIT: begin
                    if (clk_count == (CLKS_PER_BIT - 1) / 2) begin
                        if (rx_sync_1 == 1'b0) begin
                            clk_count <= 16'd0;
                            state <= DATA_BITS;
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        clk_count <= clk_count + 16'd1;
                    end
                end

                DATA_BITS: begin
                    if (clk_count == CLKS_PER_BIT - 1) begin
                        clk_count <= 16'd0;
                        rx_data[bit_index] <= rx_sync_1;

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
                    if (clk_count == CLKS_PER_BIT - 1) begin
                        clk_count <= 16'd0;

                        if (rx_sync_1 == 1'b1) begin
                            data_o <= rx_data;
                            valid_o <= 1'b1;
                        end else begin
                            framing_error_o <= 1'b1;
                        end

                        state <= CLEANUP;
                    end else begin
                        clk_count <= clk_count + 16'd1;
                    end
                end

                CLEANUP: begin
                    state <= IDLE;
                end

                default: begin
                    state <= IDLE;
                end

            endcase
        end
    end

endmodule