`timescale 1ns / 1ps

module grayscale_rgb (
    input  wire [7:0] r_i,
    input  wire [7:0] g_i,
    input  wire [7:0] b_i,
    output wire [7:0] r_o,
    output wire [7:0] g_o,
    output wire [7:0] b_o
);
    assign r_o = r_i;
    assign g_o = g_i;
    assign b_o = b_i;
endmodule