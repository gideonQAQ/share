module uart_rx #(
    parameter integer CLK_FREQ_HZ = 50_000_000,
    parameter integer BAUD_RATE   = 115_200
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       rxd,
    output reg  [7:0] rx_data,
    output reg        rx_valid
);

    localparam integer BAUD_DIV      = CLK_FREQ_HZ / BAUD_RATE;
    localparam integer HALF_BAUD_DIV = BAUD_DIV / 2;
    localparam [1:0] ST_IDLE  = 2'd0;
    localparam [1:0] ST_START = 2'd1;
    localparam [1:0] ST_DATA  = 2'd2;
    localparam [1:0] ST_STOP  = 2'd3;

    reg [1:0]  state;
    reg [15:0] baud_cnt;
    reg [2:0]  bit_idx;
    reg [7:0]  shifter;
    reg [1:0]  rxd_sync;

    wire rxd_s = rxd_sync[1];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rxd_sync <= 2'b11;
        end else begin
            rxd_sync <= {rxd_sync[0], rxd};
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= ST_IDLE;
            baud_cnt <= 16'd0;
            bit_idx  <= 3'd0;
            shifter  <= 8'd0;
            rx_data  <= 8'd0;
            rx_valid <= 1'b0;
        end else begin
            rx_valid <= 1'b0;
            case (state)
                ST_IDLE: begin
                    baud_cnt <= 16'd0;
                    bit_idx  <= 3'd0;
                    if (!rxd_s) begin
                        state <= ST_START;
                    end
                end

                ST_START: begin
                    if (baud_cnt == HALF_BAUD_DIV - 1) begin
                        baud_cnt <= 16'd0;
                        if (!rxd_s) begin
                            state <= ST_DATA;
                        end else begin
                            state <= ST_IDLE;
                        end
                    end else begin
                        baud_cnt <= baud_cnt + 16'd1;
                    end
                end

                ST_DATA: begin
                    if (baud_cnt == BAUD_DIV - 1) begin
                        baud_cnt <= 16'd0;
                        shifter  <= {rxd_s, shifter[7:1]};
                        if (bit_idx == 3'd7) begin
                            bit_idx <= 3'd0;
                            state   <= ST_STOP;
                        end else begin
                            bit_idx <= bit_idx + 3'd1;
                        end
                    end else begin
                        baud_cnt <= baud_cnt + 16'd1;
                    end
                end

                ST_STOP: begin
                    if (baud_cnt == BAUD_DIV - 1) begin
                        baud_cnt <= 16'd0;
                        state    <= ST_IDLE;
                        if (rxd_s) begin
                            rx_data  <= shifter;
                            rx_valid <= 1'b1;
                        end
                    end else begin
                        baud_cnt <= baud_cnt + 16'd1;
                    end
                end

                default: begin
                    state <= ST_IDLE;
                end
            endcase
        end
    end

endmodule
