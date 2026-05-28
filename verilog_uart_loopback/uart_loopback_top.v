module uart_loopback_top #(
    parameter integer CLK_FREQ_HZ = 50_000_000,
    parameter integer BAUD_RATE   = 115_200
) (
    input  wire clk,
    input  wire rst_n,
    input  wire uart_rxd,
    output wire uart_txd
);

    wire [7:0] rx_data;
    wire       rx_valid;
    wire       tx_busy;
    wire [7:0] tx_data;

    reg        tx_start;
    reg [1:0]  fifo_count;
    reg [7:0]  fifo_data0;
    reg [7:0]  fifo_data1;

    wire fifo_empty = (fifo_count == 2'd0);
    wire fifo_full  = (fifo_count == 2'd2);
    wire do_send    = (!tx_busy && !fifo_empty);
    wire do_recv    = (rx_valid && !fifo_full);

    assign tx_data = fifo_data0;

    uart_rx #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .BAUD_RATE(BAUD_RATE)
    ) u_uart_rx (
        .clk(clk),
        .rst_n(rst_n),
        .rxd(uart_rxd),
        .rx_data(rx_data),
        .rx_valid(rx_valid)
    );

    uart_tx #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .BAUD_RATE(BAUD_RATE)
    ) u_uart_tx (
        .clk(clk),
        .rst_n(rst_n),
        .tx_data(tx_data),
        .tx_start(tx_start),
        .txd(uart_txd),
        .tx_busy(tx_busy)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_start <= 1'b0;
            fifo_count <= 2'd0;
            fifo_data0 <= 8'd0;
            fifo_data1 <= 8'd0;
        end else begin
            tx_start <= 1'b0;
            case (fifo_count)
                2'd0: begin
                    if (do_recv) begin
                        fifo_data0 <= rx_data;
                        fifo_count <= 2'd1;
                    end
                end

                2'd1: begin
                    if (do_send && do_recv) begin
                        tx_start   <= 1'b1;
                        fifo_data0 <= rx_data;
                        fifo_count <= 2'd1;
                    end else if (do_send) begin
                        tx_start   <= 1'b1;
                        fifo_count <= 2'd0;
                    end else if (do_recv) begin
                        fifo_data1 <= rx_data;
                        fifo_count <= 2'd2;
                    end
                end

                2'd2: begin
                    if (do_send && do_recv) begin
                        tx_start   <= 1'b1;
                        fifo_data0 <= fifo_data1;
                        fifo_data1 <= rx_data;
                        fifo_count <= 2'd2;
                    end else if (do_send) begin
                        tx_start   <= 1'b1;
                        fifo_data0 <= fifo_data1;
                        fifo_count <= 2'd1;
                    end
                end

                default: begin
                    fifo_count <= 2'd0;
                end
            endcase
        end
    end

endmodule
