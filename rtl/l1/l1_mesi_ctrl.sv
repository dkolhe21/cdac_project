// l1_mesi_ctrl.sv — L1 MESI controller stub
// Stub. Not implemented.
`ifndef L1_MESI_CTRL_SV
`define L1_MESI_CTRL_SV

module l1_mesi_ctrl import tile_pkg::*; (
    input  logic        clk,
    input  logic        rst_n,
    // Core interface (stubbed)
    input  logic        core_req_valid,
    input  logic        core_req_is_write,
    input  logic [ADDR_W-1:0] core_req_addr,
    input  logic [LINE_BITS-1:0] core_req_wdata,
    output logic        core_rsp_valid,
    output logic [LINE_BITS-1:0] core_rsp_rdata,
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
    output logic        noc_req_valid,
    input  logic        noc_rsp_valid
);
    // Stub: all outputs tied to 0
    // Implementation lands in the next work order.
    always_comb begin
        core_rsp_valid    = 1'b0;
        core_rsp_rdata    = '0;
        bank_req_valid    = 1'b0;
        bank_req_is_write = 1'b0;
        bank_req_addr     = '0;
        bank_req_wdata    = '0;
        bank_req_wstrb    = '0;
        bank_req_source   = SRC_L1;
        noc_req_valid     = 1'b0;
    end

endmodule
`endif