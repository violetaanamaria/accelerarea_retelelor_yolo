`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10.06.2026 08:42:41
// Design Name: 
// Module Name: frame_engine
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



// Protocol host<->FPGA:
//   Host -> FPGA: [AA 55] [01] [LEN:4B BE] [RGB payload] [XOR checksum]
//   FPGA -> Host: [AA 55] [81] [LEN:4B BE] [RGB Y,Y,Y] [XOR checksum]
//
// Faza 1: primeste tot payload-ul in BRAM.
// Faza 2: proceseaza si transmite raspunsul.
module frame_engine #(
    parameter integer MAX_BYTES = 57600   // 160 x 120 x 3
) (
    input  wire        clk,
    input  wire        rst,

    input  wire [7:0]  rx_data,
    input  wire        rx_valid,
    input  wire        rx_framing_error,

    output reg         tx_start,
    output reg  [7:0]  tx_data,
    input  wire        tx_busy,

    output wire [15:0] frame_counter,
    output wire [7:0]  err_counter,
    output wire [3:0]  status_led
);
    localparam [7:0] MAGIC0 = 8'hAA;
    localparam [7:0] MAGIC1 = 8'h55;
    localparam [7:0] CMD_RX = 8'h01;
    localparam [7:0] CMD_TX = 8'h81;

    localparam [4:0]
        ST_WAIT_AA     = 5'd0,
        ST_WAIT_55     = 5'd1,
        ST_RX_CMD      = 5'd2,
        ST_RX_LEN3     = 5'd3,
        ST_RX_LEN2     = 5'd4,
        ST_RX_LEN1     = 5'd5,
        ST_RX_LEN0     = 5'd6,
        ST_RX_PAYLOAD  = 5'd7,
        ST_RX_CHECKSUM = 5'd8,
        ST_TX_HDR      = 5'd9,
        ST_TX_PIXEL    = 5'd10,
        ST_TX_CHECKSUM = 5'd11,
        ST_ERROR       = 5'd12;

    reg [4:0] state;

    reg [7:0]  cmd_byte;
    reg [31:0] frame_len;
    reg [31:0] rx_remaining;
    reg [31:0] rx_addr;
    reg [31:0] tx_addr;
    reg [2:0]  tx_hdr_idx;
    reg [1:0]  tx_chan_idx;
    reg [7:0]  rx_checksum;
    reg [7:0]  tx_checksum;
    reg [7:0]  tx_y;

    reg [15:0] frames_ok;
    reg [7:0]  errors;

    (* ram_style = "block" *) reg [7:0] frame_mem [0:MAX_BYTES-1];

    reg [7:0] bram_r;
    reg [7:0] bram_g;
    reg [7:0] bram_b;

    wire [7:0] gray_r;
    wire [7:0] gray_g;
    wire [7:0] gray_b;

    grayscale_rgb u_gray (
        .r_i(bram_r),
        .g_i(bram_g),
        .b_i(bram_b),
        .r_o(gray_r),
        .g_o(gray_g),
        .b_o(gray_b)
    );

    assign frame_counter = frames_ok;
    assign err_counter   = errors;

    assign status_led[0] = (state == ST_WAIT_AA);
    assign status_led[1] = (state == ST_RX_PAYLOAD);
    assign status_led[2] = (state == ST_TX_HDR || state == ST_TX_PIXEL);
    assign status_led[3] = (state == ST_ERROR);

    function automatic [7:0] hdr_byte;
        input [2:0] idx;
        begin
            case (idx)
                3'd0: hdr_byte = MAGIC0;
                3'd1: hdr_byte = MAGIC1;
                3'd2: hdr_byte = CMD_TX;
                3'd3: hdr_byte = frame_len[31:24];
                3'd4: hdr_byte = frame_len[23:16];
                3'd5: hdr_byte = frame_len[15:8];
                3'd6: hdr_byte = frame_len[7:0];
                default: hdr_byte = 8'h00;
            endcase
        end
    endfunction

    task automatic tx_byte;
        input [7:0] value;
        begin
            tx_data  = value;
            tx_start = 1'b1;
        end
    endtask

    always @(posedge clk) begin
        if (rst) begin
            state        <= ST_WAIT_AA;
            cmd_byte     <= 8'd0;
            frame_len    <= 32'd0;
            rx_remaining <= 32'd0;
            rx_addr      <= 32'd0;
            tx_addr      <= 32'd0;
            tx_hdr_idx   <= 3'd0;
            tx_chan_idx  <= 2'd0;
            rx_checksum  <= 8'd0;
            tx_checksum  <= 8'd0;
            tx_y         <= 8'd0;
            frames_ok    <= 16'd0;
            errors       <= 8'd0;
            tx_start     <= 1'b0;
            tx_data      <= 8'd0;
            bram_r       <= 8'd0;
            bram_g       <= 8'd0;
            bram_b       <= 8'd0;
        end else begin
            tx_start <= 1'b0;

            if (rx_framing_error) begin
                errors <= errors + 8'd1;
                state  <= ST_WAIT_AA;
            end else begin
                case (state)
                    ST_WAIT_AA: begin
                        if (rx_valid && rx_data == MAGIC0)
                            state <= ST_WAIT_55;
                    end

                    ST_WAIT_55: begin
                        if (rx_valid) begin
                            if (rx_data == MAGIC1) begin
                                rx_checksum <= 8'd0;
                                state       <= ST_RX_CMD;
                            end else if (rx_data == MAGIC0) begin
                                state <= ST_WAIT_55;
                            end else begin
                                state <= ST_WAIT_AA;
                            end
                        end
                    end

                    ST_RX_CMD: begin
                        if (rx_valid) begin
                            cmd_byte    <= rx_data;
                            rx_checksum <= rx_checksum ^ rx_data;

                            if (rx_data == CMD_RX)
                                state <= ST_RX_LEN3;
                            else begin
                                errors <= errors + 8'd1;
                                state  <= ST_ERROR;
                            end
                        end
                    end

                    ST_RX_LEN3: begin
                        if (rx_valid) begin
                            frame_len[31:24] <= rx_data;
                            rx_checksum      <= rx_checksum ^ rx_data;
                            state            <= ST_RX_LEN2;
                        end
                    end

                    ST_RX_LEN2: begin
                        if (rx_valid) begin
                            frame_len[23:16] <= rx_data;
                            rx_checksum      <= rx_checksum ^ rx_data;
                            state            <= ST_RX_LEN1;
                        end
                    end

                    ST_RX_LEN1: begin
                        if (rx_valid) begin
                            frame_len[15:8] <= rx_data;
                            rx_checksum     <= rx_checksum ^ rx_data;
                            state           <= ST_RX_LEN0;
                        end
                    end

                    ST_RX_LEN0: begin
                        if (rx_valid) begin
                            frame_len[7:0] <= rx_data;
                            rx_checksum    <= rx_checksum ^ rx_data;
                            rx_remaining   <= {frame_len[31:8], rx_data};
                            rx_addr        <= 32'd0;

                            if ({frame_len[31:8], rx_data} == 32'd0 ||
                                {frame_len[31:8], rx_data} > MAX_BYTES) begin
                                errors <= errors + 8'd1;
                                state  <= ST_ERROR;
                            end else begin
                                state <= ST_RX_PAYLOAD;
                            end
                        end
                    end

                    ST_RX_PAYLOAD: begin
                        if (rx_remaining == 32'd0) begin
                            state <= ST_RX_CHECKSUM;
                        end else if (rx_valid) begin
                            frame_mem[rx_addr[17:0]] <= rx_data;
                            rx_checksum              <= rx_checksum ^ rx_data;
                            rx_addr                  <= rx_addr + 32'd1;
                            rx_remaining             <= rx_remaining - 32'd1;
                        end
                    end

                    ST_RX_CHECKSUM: begin
                        if (rx_valid) begin
                            if (rx_data == rx_checksum) begin
                                tx_addr     <= 32'd0;
                                tx_hdr_idx  <= 3'd0;
                                tx_chan_idx <= 2'd0;
                                tx_checksum <= CMD_TX
                                             ^ frame_len[31:24]
                                             ^ frame_len[23:16]
                                             ^ frame_len[15:8]
                                             ^ frame_len[7:0];
                                bram_r      <= frame_mem[0];
                                bram_g      <= frame_mem[1];
                                bram_b      <= frame_mem[2];
                                state       <= ST_TX_HDR;
                            end else begin
                                errors <= errors + 8'd1;
                                state  <= ST_ERROR;
                            end
                        end
                    end

                    ST_TX_HDR: begin
                        if (!tx_busy) begin
                            tx_byte(hdr_byte(tx_hdr_idx));

                            if (tx_hdr_idx == 3'd6) begin
                                tx_hdr_idx  <= 3'd0;
                                tx_chan_idx <= 2'd0;
                                state       <= ST_TX_PIXEL;
                            end else begin
                                tx_hdr_idx <= tx_hdr_idx + 3'd1;
                            end
                        end
                    end

                    ST_TX_PIXEL: begin
                        if (!tx_busy) begin
                            case (tx_chan_idx)
                                2'd0: begin
                                    tx_y        <= gray_r;
                                    tx_byte(gray_r);
                                    tx_checksum <= tx_checksum ^ gray_r;
                                    tx_chan_idx <= 2'd1;
                                end

                                2'd1: begin
                                    tx_byte(gray_g);
                                    tx_checksum <= tx_checksum ^ gray_g;
                                    tx_chan_idx <= 2'd2;
                                end

                                2'd2: begin
                                    tx_byte(gray_b);
                                    tx_checksum <= tx_checksum ^ gray_b;
                                    tx_addr     <= tx_addr + 32'd3;
                                    tx_chan_idx <= 2'd0;

                                    if (tx_addr + 32'd3 >= frame_len) begin
                                        state <= ST_TX_CHECKSUM;
                                    end else begin
                                        bram_r <= frame_mem[tx_addr + 32'd3];
                                        bram_g <= frame_mem[tx_addr + 32'd4];
                                        bram_b <= frame_mem[tx_addr + 32'd5];
                                    end
                                end

                                default: tx_chan_idx <= 2'd0;
                            endcase
                        end
                    end

                    ST_TX_CHECKSUM: begin
                        if (!tx_busy) begin
                            tx_byte(tx_checksum);
                            frames_ok <= frames_ok + 16'd1;
                            state     <= ST_WAIT_AA;
                        end
                    end

                    ST_ERROR: begin
                        state <= ST_WAIT_AA;
                    end

                    default: state <= ST_WAIT_AA;
                endcase
            end
        end
    end
endmodule
