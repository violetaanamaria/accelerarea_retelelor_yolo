`timescale 1ns / 1ps

module nexys4ddr_yolo_preprocessor_top #(
    parameter integer CLK_FREQ_HZ = 100_000_000,
    parameter integer BAUD_RATE   = 921_600
)(
    input  wire        clk100mhz,
    input  wire        btnC,
    input  wire        uart_txd_in,
    output wire        uart_rxd_out,
    output wire [15:0] led
);

    wire rst;
    assign rst = btnC;

    wire [7:0] rx_data;
    wire       rx_valid;
    wire       rx_ferr;

    reg  [7:0] tx_data;
    reg        tx_start;
    wire       tx_busy;

    reg [7:0] r_byte;
    reg [7:0] g_byte;
    reg [7:0] b_byte;
    reg       pp_valid_in;

    wire [7:0] pp_r;
    wire [7:0] pp_g;
    wire [7:0] pp_b;
    wire       pp_valid_out;

    reg [15:0] frame_counter;
    reg [7:0]  err_counter;

    reg [7:0]  cmd;
    reg [31:0] len;
    reg [31:0] remaining;

    reg [7:0] checksum_calc;
    reg [7:0] checksum_resp;

    reg [1:0] byte_phase;

    localparam [4:0]
        WAIT_AA       = 5'd0,
        WAIT_55       = 5'd1,
        READ_CMD      = 5'd2,
        READ_LEN3     = 5'd3,
        READ_LEN2     = 5'd4,
        READ_LEN1     = 5'd5,
        READ_LEN0     = 5'd6,
        SEND_HDR_AA   = 5'd7,
        SEND_HDR_55   = 5'd8,
        SEND_RESP_CMD = 5'd9,
        SEND_LEN3     = 5'd10,
        SEND_LEN2     = 5'd11,
        SEND_LEN1     = 5'd12,
        SEND_LEN0     = 5'd13,
        READ_PAYLOAD  = 5'd14,
        WAIT_PROC     = 5'd15,
        SEND_OUT0     = 5'd16,
        SEND_OUT1     = 5'd17,
        SEND_OUT2     = 5'd18,
        READ_CHECKSUM = 5'd19,
        SEND_CHECKSUM = 5'd20,
        ERROR_STATE   = 5'd21;

    reg [4:0] state;

    assign led[7:0]  = frame_counter[7:0];
    assign led[15:8] = err_counter;

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

    image_preprocess_rgb U_PP (
        .clk(clk100mhz),
        .rst(rst),
        .r_i(r_byte),
        .g_i(g_byte),
        .b_i(b_byte),
        .pixel_valid_i(pp_valid_in),
        .r_o(pp_r),
        .g_o(pp_g),
        .b_o(pp_b),
        .pixel_valid_o(pp_valid_out)
    );

    always @(posedge clk100mhz) begin
        if (rst) begin
            state <= WAIT_AA;

            tx_data  <= 8'd0;
            tx_start <= 1'b0;

            r_byte <= 8'd0;
            g_byte <= 8'd0;
            b_byte <= 8'd0;
            pp_valid_in <= 1'b0;

            frame_counter <= 16'd0;
            err_counter   <= 8'd0;

            cmd <= 8'd0;
            len <= 32'd0;
            remaining <= 32'd0;

            checksum_calc <= 8'd0;
            checksum_resp <= 8'd0;

            byte_phase <= 2'd0;
        end else begin
            tx_start    <= 1'b0;
            pp_valid_in <= 1'b0;

            if (rx_ferr == 1'b1) begin
                err_counter <= err_counter + 8'd1;
                state <= WAIT_AA;
            end else begin

                case (state)

                    WAIT_AA: begin
                        if (rx_valid == 1'b1 && rx_data == 8'hAA) begin
                            state <= WAIT_55;
                        end
                    end

                    WAIT_55: begin
                        if (rx_valid == 1'b1) begin
                            if (rx_data == 8'h55) begin
                                checksum_calc <= 8'd0;
                                len <= 32'd0;
                                state <= READ_CMD;
                            end else begin
                                state <= WAIT_AA;
                            end
                        end
                    end

                    READ_CMD: begin
                        if (rx_valid == 1'b1) begin
                            cmd <= rx_data;
                            checksum_calc <= checksum_calc ^ rx_data;

                            if (rx_data == 8'h01) begin
                                state <= READ_LEN3;
                            end else begin
                                err_counter <= err_counter + 8'd1;
                                state <= ERROR_STATE;
                            end
                        end
                    end

                    READ_LEN3: begin
                        if (rx_valid == 1'b1) begin
                            len[31:24] <= rx_data;
                            checksum_calc <= checksum_calc ^ rx_data;
                            state <= READ_LEN2;
                        end
                    end

                    READ_LEN2: begin
                        if (rx_valid == 1'b1) begin
                            len[23:16] <= rx_data;
                            checksum_calc <= checksum_calc ^ rx_data;
                            state <= READ_LEN1;
                        end
                    end

                    READ_LEN1: begin
                        if (rx_valid == 1'b1) begin
                            len[15:8] <= rx_data;
                            checksum_calc <= checksum_calc ^ rx_data;
                            state <= READ_LEN0;
                        end
                    end

                    READ_LEN0: begin
                        if (rx_valid == 1'b1) begin
                            len[7:0] <= rx_data;
                            remaining <= {len[31:8], rx_data};

                            checksum_calc <= checksum_calc ^ rx_data;

                            checksum_resp <= 8'h81
                                           ^ len[31:24]
                                           ^ len[23:16]
                                           ^ len[15:8]
                                           ^ rx_data;

                            state <= SEND_HDR_AA;
                        end
                    end

                    // FIX: added "&& tx_start == 1'b0" to every send state.
                    //
                    // Root cause: uart_tx asserts busy_o one clock AFTER start_i
                    // goes high (registered output). Without the guard, the very next
                    // state fires in that 1-cycle window (tx_busy still 0), advances
                    // the state machine by one extra step, and the UART ignores the
                    // second start_i pulse (it is already in START_BIT). Result: every
                    // other byte is silently dropped - observed as "AA 81 00 LEN_LO"
                    // instead of "AA 55 81 00 00 LEN_HI LEN_LO".
                    // The guard uses tx_start's own registered output (= 1 for exactly
                    // one clock after a byte is queued) as a 1-cycle inhibit.

                    SEND_HDR_AA: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= 8'hAA;
                            tx_start <= 1'b1;
                            state <= SEND_HDR_55;
                        end
                    end

                    SEND_HDR_55: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= 8'h55;
                            tx_start <= 1'b1;
                            state <= SEND_RESP_CMD;
                        end
                    end

                    SEND_RESP_CMD: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= 8'h81;
                            tx_start <= 1'b1;
                            state <= SEND_LEN3;
                        end
                    end

                    SEND_LEN3: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= len[31:24];
                            tx_start <= 1'b1;
                            state <= SEND_LEN2;
                        end
                    end

                    SEND_LEN2: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= len[23:16];
                            tx_start <= 1'b1;
                            state <= SEND_LEN1;
                        end
                    end

                    SEND_LEN1: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= len[15:8];
                            tx_start <= 1'b1;
                            state <= SEND_LEN0;
                        end
                    end

                    SEND_LEN0: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= len[7:0];
                            tx_start <= 1'b1;
                            byte_phase <= 2'd0;
                            state <= READ_PAYLOAD;
                        end
                    end

                    READ_PAYLOAD: begin
                        if (remaining == 32'd0) begin
                            state <= READ_CHECKSUM;
                        end else if (rx_valid == 1'b1) begin
                            checksum_calc <= checksum_calc ^ rx_data;

                            if (byte_phase == 2'd0) begin
                                r_byte <= rx_data;
                                byte_phase <= 2'd1;
                                remaining <= remaining - 32'd1;
                            end else if (byte_phase == 2'd1) begin
                                g_byte <= rx_data;
                                byte_phase <= 2'd2;
                                remaining <= remaining - 32'd1;
                            end else begin
                                b_byte <= rx_data;
                                byte_phase <= 2'd0;
                                remaining <= remaining - 32'd1;

                                pp_valid_in <= 1'b1;
                                state <= WAIT_PROC;
                            end
                        end
                    end

                    WAIT_PROC: begin
                        if (pp_valid_out == 1'b1) begin
                            state <= SEND_OUT0;
                        end
                    end

                    SEND_OUT0: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= pp_r;
                            tx_start <= 1'b1;
                            checksum_resp <= checksum_resp ^ pp_r;
                            state <= SEND_OUT1;
                        end
                    end

                    SEND_OUT1: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= pp_g;
                            tx_start <= 1'b1;
                            checksum_resp <= checksum_resp ^ pp_g;
                            state <= SEND_OUT2;
                        end
                    end

                    SEND_OUT2: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= pp_b;
                            tx_start <= 1'b1;
                            checksum_resp <= checksum_resp ^ pp_b;
                            state <= READ_PAYLOAD;
                        end
                    end

                    READ_CHECKSUM: begin
                        if (rx_valid == 1'b1) begin
                            if (rx_data == checksum_calc) begin
                                frame_counter <= frame_counter + 16'd1;
                            end else begin
                                err_counter <= err_counter + 8'd1;
                            end

                            state <= SEND_CHECKSUM;
                        end
                    end

                    SEND_CHECKSUM: begin
                        if (tx_busy == 1'b0 && tx_start == 1'b0) begin
                            tx_data  <= checksum_resp;
                            tx_start <= 1'b1;
                            state <= WAIT_AA;
                        end
                    end

                    ERROR_STATE: begin
                        state <= WAIT_AA;
                    end

                    default: begin
                        state <= WAIT_AA;
                    end

                endcase
            end
        end
    end

endmodule