module uart_tx #(
    parameter integer CLK_FREQ_HZ = 50_000_000,
    parameter integer BAUD_RATE   = 115_200
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] tx_data,
    input  wire       tx_start,
    output reg        txd,
    output reg        tx_busy
);

    localparam integer BAUD_DIV = (CLK_FREQ_HZ + (BAUD_RATE / 2)) / BAUD_RATE;
    localparam [1:0] ST_IDLE  = 2'd0;
    localparam [1:0] ST_START = 2'd1;
    localparam [1:0] ST_DATA  = 2'd2;
    localparam [1:0] ST_STOP  = 2'd3;

    reg [1:0]  state;
    reg [15:0] baud_cnt;
    reg [2:0]  bit_idx;
    reg [7:0]  shifter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= ST_IDLE;
            baud_cnt <= 16'd0;
            bit_idx  <= 3'd0;
            shifter  <= 8'd0;
            txd      <= 1'b1;
            tx_busy  <= 1'b0;
        end else begin
            case (state)
                ST_IDLE: begin
                    txd      <= 1'b1;
                    tx_busy  <= 1'b0;
                    baud_cnt <= 16'd0;
                    bit_idx  <= 3'd0;
                    if (tx_start) begin
                        shifter <= tx_data;
                        tx_busy <= 1'b1;
                        state   <= ST_START;
                    end
                end

                ST_START: begin
                    txd <= 1'b0;
                    if (baud_cnt == BAUD_DIV - 1) begin
                        baud_cnt <= 16'd0;
                        state    <= ST_DATA;
                    end else begin
                        baud_cnt <= baud_cnt + 16'd1;
                    end
                end

                ST_DATA: begin
                    txd <= shifter[0];
                    if (baud_cnt == BAUD_DIV - 1) begin
                        baud_cnt <= 16'd0;
                        shifter  <= {1'b0, shifter[7:1]};
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
                    txd <= 1'b1;
                    if (baud_cnt == BAUD_DIV - 1) begin
                        baud_cnt <= 16'd0;
                        tx_busy  <= 1'b0;
                        state    <= ST_IDLE;
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
