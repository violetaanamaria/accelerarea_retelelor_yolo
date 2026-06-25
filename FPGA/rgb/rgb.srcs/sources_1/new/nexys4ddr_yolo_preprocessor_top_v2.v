`timescale 1ns / 1ps


module nexys4ddr_yolo_preprocessor_top_v2 #(
    parameter integer CLK_FREQ_HZ = 100_000_000,
    parameter integer BAUD_RATE   = 921_600
) (
    input  wire        clk100mhz,
    input  wire        btnC,
    input  wire        uart_txd_in,
    output wire        uart_rxd_out,
    output wire [15:0] led
);
    wire rst = btnC;

    wire [7:0] rx_data;
    wire       rx_valid;
    wire       rx_ferr;

    uart_rx #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .BAUD_RATE(BAUD_RATE)
    ) U_RX (
        .clk(clk100mhz),
        .rst(rst),
        .rx_i(uart_txd_in),
        .data_o(rx_data),
        .valid_o(rx_valid),
        .framing_error_o(rx_ferr)
    );

    wire       tx_start;
    wire [7:0] tx_data;
    wire       tx_busy;

    uart_tx #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .BAUD_RATE(BAUD_RATE)
    ) U_TX (
        .clk(clk100mhz),
        .rst(rst),
        .data_i(tx_data),
        .start_i(tx_start),
        .tx_o(uart_rxd_out),
        .busy_o(tx_busy)
    );

    wire [15:0] frame_counter;
    wire [7:0]  err_counter;
    wire [3:0]  status_led;

    frame_engine U_ENGINE (
        .clk(clk100mhz),
        .rst(rst),
        .rx_data(rx_data),
        .rx_valid(rx_valid),
        .rx_framing_error(rx_ferr),
        .tx_start(tx_start),
        .tx_data(tx_data),
        .tx_busy(tx_busy),
        .frame_counter(frame_counter),
        .err_counter(err_counter),
        .status_led(status_led)
    );

    assign led[7:0]  = frame_counter[7:0];
    assign led[15:8] = {4'b0000, status_led};
endmodule