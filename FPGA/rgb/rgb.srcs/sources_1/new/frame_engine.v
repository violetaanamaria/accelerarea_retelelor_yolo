`timescale 1ns / 1ps


module frame_engine #(
    parameter integer MAX_BYTES  = 57600, // 160 x 120 x 3
    parameter integer MAX_PIXELS = 19200  // MAX_BYTES / 3
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

    reg [31:0] frame_len;
    reg [31:0] rx_remaining;
    reg [14:0] rx_pixel;        // pixel index during RX (increments each RGB triplet)
    reg [1:0]  rx_chan;         // channel during RX: 0=R 1=G 2=B
    reg [14:0] tx_pixel;        // pixel index during TX
    reg [14:0] tx_pixels_total; // total pixels = frame_len/3, stored at end of RX
    reg [2:0]  tx_hdr_idx;
    reg [1:0]  tx_chan_idx;
    reg [7:0]  rx_checksum;
    reg [7:0]  tx_checksum;

    reg [15:0] frames_ok;
    reg [7:0]  errors;

    // Single read address driven by FSM.
    // A single variable ensures Vivado sees ONE read port per BRAM array.
    reg [14:0] bram_rd_pixel;

    // Three BRAM arrays - one per colour channel.
    (* ram_style = "block" *) reg [7:0] frame_r [0:MAX_PIXELS-1];
    (* ram_style = "block" *) reg [7:0] frame_g [0:MAX_PIXELS-1];
    (* ram_style = "block" *) reg [7:0] frame_b [0:MAX_PIXELS-1];

    // BRAM output registers - driven ONLY by the read always blocks below.
    reg [7:0] bram_r;
    reg [7:0] bram_g;
    reg [7:0] bram_b;

    // -----------------------------------------------------------------------
    // Simple dual-port BRAM inference (UG901 pattern):
    //   Write port: FSM always block (below)
    //   Read port:  these three separate always blocks
    // Each array has ONE read address (bram_rd_pixel) -> single read port ->
    // Vivado can infer each array as a separate RAMB18/RAMB36 block.
    // -----------------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) bram_r <= 8'd0;
        else     bram_r <= frame_r[bram_rd_pixel];
    end

    always @(posedge clk) begin
        if (rst) bram_g <= 8'd0;
        else     bram_g <= frame_g[bram_rd_pixel];
    end

    always @(posedge clk) begin
        if (rst) bram_b <= 8'd0;
        else     bram_b <= frame_b[bram_rd_pixel];
    end

    // -----------------------------------------------------------------------
    // Grayscale: Y = (77R + 150G + 29B) >> 8, replicated on R/G/B outputs
    // -----------------------------------------------------------------------
    wire [7:0] gray_r;
    wire [7:0] gray_g;
    wire [7:0] gray_b;

    grayscale_rgb u_gray (
        .r_i(bram_r), .g_i(bram_g), .b_i(bram_b),
        .r_o(gray_r), .g_o(gray_g), .b_o(gray_b)
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
            tx_data  <= value;
            tx_start <= 1'b1;
        end
    endtask

    // -----------------------------------------------------------------------
    // FSM always block.
    // Contains WRITE ports for frame_r/g/b (ST_RX_PAYLOAD case).
    // Does NOT contain any frame_r/g/b reads - only drives bram_rd_pixel.
    // -----------------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            state           <= ST_WAIT_AA;
            frame_len       <= 32'd0;
            rx_remaining    <= 32'd0;
            rx_pixel        <= 15'd0;
            rx_chan         <= 2'd0;
            tx_pixel        <= 15'd0;
            tx_pixels_total <= 15'd0;
            bram_rd_pixel   <= 15'd0;
            tx_hdr_idx      <= 3'd0;
            tx_chan_idx     <= 2'd0;
            rx_checksum     <= 8'd0;
            tx_checksum     <= 8'd0;
            frames_ok       <= 16'd0;
            errors          <= 8'd0;
            tx_start        <= 1'b0;
            tx_data         <= 8'd0;
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
                            rx_pixel       <= 15'd0;
                            rx_chan        <= 2'd0;

                            if ({frame_len[31:8], rx_data} == 32'd0 ||
                                {frame_len[31:8], rx_data} > MAX_BYTES) begin
                                errors <= errors + 8'd1;
                                state  <= ST_ERROR;
                            end else begin
                                state <= ST_RX_PAYLOAD;
                            end
                        end
                    end

                    // WRITE port for all three BRAMs.
                    // Writes are distributed by rx_chan: 0=R 1=G 2=B.
                    // rx_pixel is the shared address for all three arrays.
                    ST_RX_PAYLOAD: begin
                        if (rx_remaining == 32'd0) begin
                            state <= ST_RX_CHECKSUM;
                        end else if (rx_valid) begin
                            case (rx_chan)
                                2'd0: frame_r[rx_pixel] <= rx_data;
                                2'd1: frame_g[rx_pixel] <= rx_data;
                                2'd2: frame_b[rx_pixel] <= rx_data;
                                default: ;
                            endcase
                            rx_checksum  <= rx_checksum ^ rx_data;
                            rx_remaining <= rx_remaining - 32'd1;
                            if (rx_chan == 2'd2) begin
                                rx_pixel <= rx_pixel + 15'd1;
                                rx_chan  <= 2'd0;
                            end else begin
                                rx_chan <= rx_chan + 2'd1;
                            end
                        end
                    end

                    ST_RX_CHECKSUM: begin
                        if (rx_valid) begin
                            if (rx_data == rx_checksum) begin
                                tx_pixel        <= 15'd0;
                                // rx_pixel holds frame_len/3 (no divider needed)
                                tx_pixels_total <= rx_pixel;
                                tx_hdr_idx      <= 3'd0;
                                tx_chan_idx     <= 2'd0;
                                tx_checksum     <= CMD_TX
                                                ^ frame_len[31:24]
                                                ^ frame_len[23:16]
                                                ^ frame_len[15:8]
                                                ^ frame_len[7:0];
                                // Point read address at pixel 0.
                                // BRAM read always block will latch frame_r/g/b[0]
                                // on the NEXT cycle - valid well before ST_TX_PIXEL
                                // (7 header bytes x ~1082 cycles = ~7574 cycles away).
                                bram_rd_pixel <= 15'd0;
                                state         <= ST_TX_HDR;
                            end else begin
                                errors <= errors + 8'd1;
                                state  <= ST_ERROR;
                            end
                        end
                    end

                    ST_TX_HDR: begin
                        if (!tx_busy && !tx_start) begin
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
                        if (!tx_busy && !tx_start) begin
                            case (tx_chan_idx)
                                2'd0: begin
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
                                    tx_chan_idx <= 2'd0;
                                    if (tx_pixel + 15'd1 >= tx_pixels_total) begin
                                        state <= ST_TX_CHECKSUM;
                                    end else begin
                                        // Advance read address to next pixel.
                                        // BRAM latches new data on next cycle;
                                        // uart_tx takes ~1082 cycles to finish B,
                                        // so gray_r/g/b are valid before
                                        // tx_chan_idx=0 fires for the next pixel.
                                        bram_rd_pixel <= tx_pixel + 15'd1;
                                        tx_pixel      <= tx_pixel + 15'd1;
                                    end
                                end
                                default: tx_chan_idx <= 2'd0;
                            endcase
                        end
                    end

                    ST_TX_CHECKSUM: begin
                        if (!tx_busy && !tx_start) begin
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