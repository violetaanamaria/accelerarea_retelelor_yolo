`timescale 1ns / 1ps

// RGB -> grayscale: Y = (77R + 150G + 29B) / 256, replicat pe 3 canale.
module grayscale_rgb (
    input  wire [7:0] r_i,
    input  wire [7:0] g_i,
    input  wire [7:0] b_i,
    output wire [7:0] r_o,
    output wire [7:0] g_o,
    output wire [7:0] b_o
);
    wire [15:0] acc = (r_i * 8'd77) + (g_i * 8'd150) + (b_i * 8'd29);
    wire [7:0]  y   = acc[15:8];

    assign r_o = y;
    assign g_o = y;
    assign b_o = y;
endmodule