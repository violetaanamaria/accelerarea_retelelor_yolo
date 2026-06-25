`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10.06.2026 09:03:33
// Design Name: 
// Module Name: image_preprocess_rgb
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



module image_preprocess_rgb(
    input  wire       clk,
    input  wire       rst,

    input  wire [7:0] r_i,
    input  wire [7:0] g_i,
    input  wire [7:0] b_i,
    input  wire       pixel_valid_i,

    output reg [7:0]  r_o,
    output reg [7:0]  g_o,
    output reg [7:0]  b_o,
    output reg        pixel_valid_o
);

    reg [15:0] acc;

    always @(posedge clk) begin
        if (rst) begin
            r_o           <= 8'd0;
            g_o           <= 8'd0;
            b_o           <= 8'd0;
            pixel_valid_o <= 1'b0;
            acc           <= 16'd0;
        end else begin
            pixel_valid_o <= pixel_valid_i;

            if (pixel_valid_i == 1'b1) begin
                // FIX: use 16-bit literals to prevent 8-bit multiplication overflow.
                // Without the cast, r_i*77 would be computed as 8-bit (truncated)
                // before being added to the 16-bit accumulator.
                acc = ({8'd0, r_i} * 16'd77)
                    + ({8'd0, g_i} * 16'd150)
                    + ({8'd0, b_i} * 16'd29);

                r_o <= acc[15:8];
                g_o <= acc[15:8];
                b_o <= acc[15:8];
            end
        end
    end

endmodule
