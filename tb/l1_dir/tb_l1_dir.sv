// tb_l1_dir.sv — Testbench top for L1 MESI + Directory scaffold
// Instantiates stub l1_mesi_ctrl and stub dir_ctrl
`ifndef TB_L1_DIR_SV
`define TB_L1_DIR_SV

module tb_l1_dir import tile_pkg::*; (
    input  logic        clk,
    input  logic        rst_n,
    // Core 0 interface (requester)
    input  logic        core0_req_valid,
    input  logic        core0_req_is_write,
    input  logic [ADDR_W-1:0] core0_req_addr,
    input  logic [LINE_BITS-1:0] core0_req_wdata,
    output logic        core0_rsp_valid,
    output logic [LINE_BITS-1:0] core0_rsp_rdata,
    // Core 1 interface (owner)
    input  logic        core1_req_valid,
    input  logic        core1_req_is_write,
    input  logic [ADDR_W-1:0] core1_req_addr,
    input  logic [LINE_BITS-1:0] core1_req_wdata,
    output logic        core1_rsp_valid,
    output logic [LINE_BITS-1:0] core1_rsp_rdata,
    // L2 bank interface (shared, R3 frozen)
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
    // NoC between L1 and Directory (stubbed)
    output logic        noc_l1_dir_valid,
    output logic [63:0] noc_l1_dir_flit,
    input  logic        noc_dir_l1_valid,
    input  logic [63:0] noc_dir_l1_flit,
    // Status
    output logic        dtr_busy
);

    // L1 MESI controller instance (core 0 - requester)
    logic l1_0_core_rsp_valid;
    logic [LINE_BITS-1:0] l1_0_core_rsp_rdata;
    logic l1_0_bank_req_valid, l1_0_bank_req_is_write;
    logic [ADDR_W-1:0] l1_0_bank_req_addr;
    logic [LINE_BITS-1:0] l1_0_bank_req_wdata;
    logic [LINE_BITS/8-1:0] l1_0_bank_req_wstrb;
    bank_src_e l1_0_bank_req_source;
    logic l1_0_noc_req_valid;
    logic [63:0] l1_0_noc_req_flit;
    logic l1_0_noc_rsp_valid;
    logic [63:0] l1_0_noc_rsp_flit;

    l1_mesi_ctrl l1_0 (
        .clk            (clk),
        .rst_n          (rst_n),
        .core_req_valid (core0_req_valid),
        .core_req_is_write (core0_req_is_write),
        .core_req_addr  (core0_req_addr),
        .core_req_wdata (core0_req_wdata),
        .core_rsp_valid (l1_0_core_rsp_valid),
        .core_rsp_rdata (l1_0_core_rsp_rdata),
        .bank_req_valid (l1_0_bank_req_valid),
        .bank_req_is_write (l1_0_bank_req_is_write),
        .bank_req_addr  (l1_0_bank_req_addr),
        .bank_req_wdata (l1_0_bank_req_wdata),
        .bank_req_wstrb (l1_0_bank_req_wstrb),
        .bank_req_source (l1_0_bank_req_source),
        .bank_rsp_valid (bank_rsp_valid),
        .bank_rsp_rdata (bank_rsp_rdata),
        .bank_rsp_rstrb (bank_rsp_rstrb),
        .bank_rsp_rlast (bank_rsp_rlast),
        .noc_req_valid  (l1_0_noc_req_valid),
        .noc_rsp_valid  (l1_0_noc_rsp_valid)
    );

    // L1 MESI controller instance (core 1 - owner)
    logic l1_1_core_rsp_valid;
    logic [LINE_BITS-1:0] l1_1_core_rsp_rdata;
    logic l1_1_bank_req_valid, l1_1_bank_req_is_write;
    logic [ADDR_W-1:0] l1_1_bank_req_addr;
    logic [LINE_BITS-1:0] l1_1_bank_req_wdata;
    logic [LINE_BITS/8-1:0] l1_1_bank_req_wstrb;
    bank_src_e l1_1_bank_req_source;
    logic l1_1_noc_req_valid;
    logic [63:0] l1_1_noc_req_flit;
    logic l1_1_noc_rsp_valid;
    logic [63:0] l1_1_noc_rsp_flit;

    l1_mesi_ctrl l1_1 (
        .clk            (clk),
        .rst_n          (rst_n),
        .core_req_valid (core1_req_valid),
        .core_req_is_write (core1_req_is_write),
        .core_req_addr  (core1_req_addr),
        .core_req_wdata (core1_req_wdata),
        .core_rsp_valid (l1_1_core_rsp_valid),
        .core_rsp_rdata (l1_1_core_rsp_rdata),
        .bank_req_valid (l1_1_bank_req_valid),
        .bank_req_is_write (l1_1_bank_req_is_write),
        .bank_req_addr  (l1_1_bank_req_addr),
        .bank_req_wdata (l1_1_bank_req_wdata),
        .bank_req_wstrb (l1_1_bank_req_wstrb),
        .bank_req_source (l1_1_bank_req_source),
        .bank_rsp_valid (bank_rsp_valid),
        .bank_rsp_rdata (bank_rsp_rdata),
        .bank_rsp_rstrb (bank_rsp_rstrb),
        .bank_rsp_rlast (bank_rsp_rlast),
        .noc_req_valid  (l1_1_noc_req_valid),
        .noc_rsp_valid  (l1_1_noc_rsp_valid)
    );

    // Directory controller instance
    logic dir_bank_req_valid, dir_bank_req_is_write;
    logic [ADDR_W-1:0] dir_bank_req_addr;
    logic [LINE_BITS-1:0] dir_bank_req_wdata;
    logic [LINE_BITS/8-1:0] dir_bank_req_wstrb;
    bank_src_e dir_bank_req_source;
    logic dir_noc_req_valid;
    logic [63:0] dir_noc_req_flit;
    logic dir_noc_rsp_valid;
    logic [63:0] dir_noc_rsp_flit;
    logic dir_dtr_busy;

    dir_ctrl dir_0 (
        .clk            (clk),
        .rst_n          (rst_n),
        .bank_req_valid (dir_bank_req_valid),
        .bank_req_is_write (dir_bank_req_is_write),
        .bank_req_addr  (dir_bank_req_addr),
        .bank_req_wdata (dir_bank_req_wdata),
        .bank_req_wstrb (dir_bank_req_wstrb),
        .bank_req_source (dir_bank_req_source),
        .bank_rsp_valid (bank_rsp_valid),
        .bank_rsp_rdata (bank_rsp_rdata),
        .bank_rsp_rstrb (bank_rsp_rstrb),
        .bank_rsp_rlast (bank_rsp_rlast),
        .noc_req_valid  (dir_noc_req_valid),
        .noc_rsp_valid  (dir_noc_rsp_valid),
        .dtr_busy       (dir_dtr_busy)
    );

    // Tie-offs for stub outputs
    always_comb begin
        core0_rsp_valid = l1_0_core_rsp_valid;
        core0_rsp_rdata = l1_0_core_rsp_rdata;
        core1_rsp_valid = l1_1_core_rsp_valid;
        core1_rsp_rdata = l1_1_core_rsp_rdata;

        // Bank request mux (priority: L1_0 > L1_1 > DIR)
        bank_req_valid    = l1_0_bank_req_valid | l1_1_bank_req_valid | dir_bank_req_valid;
        bank_req_is_write = l1_0_bank_req_is_write | l1_1_bank_req_is_write | dir_bank_req_is_write;
        bank_req_addr     = l1_0_bank_req_valid ? l1_0_bank_req_addr :
                            l1_1_bank_req_valid ? l1_1_bank_req_addr :
                                                  dir_bank_req_addr;
        bank_req_wdata    = l1_0_bank_req_valid ? l1_0_bank_req_wdata :
                            l1_1_bank_req_valid ? l1_1_bank_req_wdata :
                                                  dir_bank_req_wdata;
        bank_req_wstrb    = l1_0_bank_req_valid ? l1_0_bank_req_wstrb :
                            l1_1_bank_req_valid ? l1_1_bank_req_wstrb :
                                                  dir_bank_req_wstrb;
        bank_req_source   = bank_src_e'(l1_0_bank_req_valid ? l1_0_bank_req_source :
                            l1_1_bank_req_valid ? l1_1_bank_req_source :
                                                  dir_bank_req_source);

        // NoC connections (stubbed through)
        noc_l1_dir_valid  = l1_0_noc_req_valid | l1_1_noc_req_valid;
        noc_l1_dir_flit   = l1_0_noc_req_valid ? l1_0_noc_req_flit : l1_1_noc_req_flit;

        l1_0_noc_rsp_valid = noc_dir_l1_valid;
        l1_0_noc_rsp_flit  = noc_dir_l1_flit;
        l1_1_noc_rsp_valid = noc_dir_l1_valid;
        l1_1_noc_rsp_flit  = noc_dir_l1_flit;

        dir_noc_req_valid  = noc_l1_dir_valid;
        dir_noc_req_flit   = noc_l1_dir_flit;
        // dir_noc_rsp_valid and dir_noc_rsp_flit are driven by dir_ctrl instance

        dtr_busy = dir_dtr_busy;
    end

endmodule
`endif