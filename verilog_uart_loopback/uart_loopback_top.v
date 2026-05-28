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

    reg        tx_start;
    reg [7:0]  tx_data;
    reg        pending_full;
    reg [7:0]  pending_data;

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
            tx_data  <= 8'd0;
            pending_full <= 1'b0;
            pending_data <= 8'd0;
        end else begin
            tx_start <= 1'b0;

            if (!tx_busy && pending_full) begin
                tx_data      <= pending_data;
                tx_start     <= 1'b1;
                pending_full <= 1'b0;
                if (rx_valid) begin
                    pending_data <= rx_data;
                    pending_full <= 1'b1;
                end
            end else if (rx_valid) begin
                if (!tx_busy) begin
                    tx_data  <= rx_data;
                    tx_start <= 1'b1;
                end else if (!pending_full) begin
                    pending_data <= rx_data;
                    pending_full <= 1'b1;
                end
            end
        end
    end

endmodule
