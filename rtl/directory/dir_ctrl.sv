// dir_ctrl.sv — Directory controller stub
// Stub. Not implemented.
`ifndef DIR_CTRL_SV
`define DIR_CTRL_SV

module dir_ctrl import tile_pkg::*; (
    input  logic        clk,
    input  logic        rst_n,
    // L2 bank interface (R3 frozen)
    output logic        bank_req_valid,
    output logic        bank_req_is_write,
    output logic [ADDR_W-1:0]  bank_req_addr,
    output logic [LINE_BITS-1:0] bank_req_wdata,
    output logic [LINE_BITS/8-1:0] bank_req_wstrb,
    output bank_src_e         bank_req_source,
    input  logic        bank_rsp_valid,
    input  logic [LINE_BITS-1:0] bank_rsp_rdata,
    input  logic [LINE_BITS/8-1:0] bank_rsp_rstrb,
    input  logic        bank_rsp_rlast,
    // NoC interface (stubbed)
    input  logic        noc_req_valid,
    output logic        noc_rsp_valid,
    // Status
    output logic        dtr_busy
);
    // Stub: all outputs tied to 0
    // Implementation lands in the next work order.
    always_comb begin
        bank_req_valid    = 1'b0;
        bank_req_is_write = 1'b0;
        bank_req_addr     = '0;
        bank_req_wdata    = '0;
        bank_req_wstrb    = '0;
        bank_req_source   = SRC_REMOTE;
        noc_rsp_valid     = 1'b0;
        dtr_busy          = 1'b0;
    end

endmodule
`endif