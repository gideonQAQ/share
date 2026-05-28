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
    reg        rd_ptr;
    reg        wr_ptr;
    reg [1:0]  fifo_count;
    reg [7:0]  fifo_data0;
    reg [7:0]  fifo_data1;

    wire fifo_empty = (fifo_count == 2'd0);
    wire fifo_full  = (fifo_count == 2'd2);
    wire do_send    = (!tx_busy && !fifo_empty);
    wire do_recv    = (rx_valid && !fifo_full);

    assign tx_data = rd_ptr ? fifo_data1 : fifo_data0;

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
            rd_ptr    <= 1'b0;
            wr_ptr    <= 1'b0;
            fifo_count <= 2'd0;
            fifo_data0 <= 8'd0;
            fifo_data1 <= 8'd0;
        end else begin
            tx_start <= 1'b0;

            if (do_send) begin
                tx_start <= 1'b1;
                rd_ptr   <= ~rd_ptr;
            end

            if (do_recv) begin
                if (!wr_ptr) begin
                    fifo_data0 <= rx_data;
                end else begin
                    fifo_data1 <= rx_data;
                end
                wr_ptr <= ~wr_ptr;
            end

            case ({do_recv, do_send})
                2'b10: fifo_count <= fifo_count + 2'd1;
                2'b01: fifo_count <= fifo_count - 2'd1;
                default: fifo_count <= fifo_count;
            endcase
        end
    end

endmodule
