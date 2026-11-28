# Implementation Build Order — Cache-Coherent Tiled Multicore

**THIS FILE IS THE CANONICAL BUILD ORDER.** Every other `BUILD_ORDER.md` in the repo
(root, `white_papers/final/`, `white_papers/final/build order/`) is a one-line pointer to it.
Machine-readable form: `docs/BUILD_ORDER.csv`.

**Source of truth:** `white_papers/final/FINAL_whitepaper_v3.0.md` (v3.0) + `white_papers/final/SPEC_SHEET.md` + `white_papers/final/WORK_BREAKDOWN_16.md` + approved LLD (`white_papers/final/Diagrams/LLD_2x2_mesh.pdf`).  
**Adjudicated Rulings:** B1 (13-round fairness bound, age threshold 5), B2 (conflict eviction prior to miss request over VC0), B4 (DMA 4×4 simulation-only, excluded from 2×2 FPGA target).

---

## 1. Scope & System Boundary Clarification

1. **Processor core RTL is strictly OUT OF SCOPE** (WP §1.2 line 49).
   - Core stimulus is driven via testbenches and the FPGA on-board JTAG bridge (§6.1 / §16.14).
   - The committed 2×2 budget (≈13–19k LUTs, 28–80 BRAM36) is for the **coherence fabric and memory hierarchy only**.
2. **Fabric & Infrastructure Modules Included**:
   - `mem_tap`: Behavioral backing store per CPU tile for its home slice (WP §3.9).
   - `cpu_tile`: Structural wrapper integrating L1, L2 bank, directory, NIC, router, mem_tap, and intra-tile mux.
   - `mesh_top`: N×N mesh interconnect with hardwired `TILE_ID` and corner port tie-offs.
   - `fpga_top`: Top-level wrapper targeting ZedBoard XC7Z020 with JTAG stimulus bridge and clock/reset synchronizer.
3. **DMA Tile**: Gated optional extension (WP §3.11, Ruling B4).
   - Evaluated exclusively at Week 8 in 4×4 simulation.
   - Completely excluded from the 2×2 FPGA design.

---

## 2. Verified Module Build Sequence (12 Modules)

| Build Order | Module Name | SystemVerilog File | Description / Function | Dependencies | Status / Gate |
|---|---|---|---|---|---|
| **0** | `tile_pkg` | `rtl/pkg/tile_pkg.sv` | Single source of truth: parameters, types, encodings, flit layouts | None | **✅ Done** |
| **1** | `l2_bank` | `rtl/l2/l2_bank.sv` | 2 KB data/tag array, `{valid, tag, dirty}` per-line word, Tree-PLRU, 512-bit bus | `tile_pkg` | Next |
| **2** | `l1_mesi_ctrl` | `rtl/l1/l1_mesi_ctrl.sv` | 9-state MESI FSM (4 stable, 5 transient), forward releases, conflict eviction (B2) | `tile_pkg`, `l2_bank` (interface) | Co-landed with Dir |
| **3** | `dir_ctrl` | `rtl/directory/dir_ctrl.sv` | 8-state Dir FSM, DTR, single-exit rule, bank-write, exclusive bit (B2/§16.2) | `tile_pkg`, `l2_bank`, `l1_mesi_ctrl` | Co-landed with L1 |
| **4** | `nic` | `rtl/nic/nic.sv` | Packetizer, flit framing, 4 VCs (depth 4), 4-bit credits, DATAFWD dirty bit [39] | `tile_pkg` | Baseline |
| **5** | `router` | `rtl/router/router.sv` | 5-port 4-stage (RC/VA/SA/ST), 5-round age escape, port-granular RR (B1: 13-round bound) | `tile_pkg` | Baseline |
| **6** | `mem_tap` | `rtl/mem_tap/mem_tap.sv` | Behavioral 1-cycle backing store for home slice (connects to L2/dir only) | `tile_pkg` | Baseline |
| **7** | `intra_tile_mux` | `rtl/tile/intra_tile_mux.sv` | Routes local misses directly to local L2/dir without traversing NIC/NoC | `tile_pkg` | Baseline |
| **8** | `cpu_tile` | `rtl/tile/cpu_tile.sv` | Integrates core stimulus port, L1, L2, Dir, NIC, Router, Tap, and Mux | Modules 1–7 | Baseline |
| **9** | `mesh_top` | `rtl/mesh/mesh_top.sv` | Instantiates N×N CPU tiles, ties off unused edge/corner ports & static TILE_ID | `cpu_tile` | Baseline |
| **10** | `fpga_top` | `syn/fpga/fpga_top.sv` | Top-level for ZedBoard XC7Z020, JTAG stimulus bridge, clk/rst constraints | `mesh_top` | Milestone 9 |
| **11** | `dma_tile` | `rtl/dma/dma_tile.sv` | Two-channel DMA engine + register file + L1-lite (no L2, no dir, no tap) | `nic`, `router` | **Gated (4×4 only)** |

---

## 3. Four-Item Green Criterion (Per Module)

An implementation row is marked **Green** if and only if all four conditions pass:
1. **RTL Unit Green**: SystemVerilog module compiles clean with zero warnings under Verilator (`-Wall`) — enforced by `python3 lint/check_rules.py --verilator` against the **canonical 25-rule set** in `lint/coding_rules.json` (CR01: no `%Error`; CR02: only the recorded style warning classes fire; CR03–CR25: the source-level synthesis/style rules) — and passes directed unit testbenches.
2. **SVA Category Clean**: All mapped SystemVerilog Assertions in categories A1–A8 pass Bounded Model Checking ($K = 64$) under SymbiYosys.
3. **Reference-Model Shadow Agrees**: The transaction-level shadow reference model (`pyuvm`/`cocotb`) achieves 0 data and state mismatches on the test suite.
4. **Verifier Gate Pass**: `python3 scripts/verify_patch_set.py --dir white_papers/final --build-script scripts/build_diagrams_html.py` returns **PASS - 134/134 checks**, guaranteeing zero specification regression.


---

## 4. Verified Parameters (2×2 vs 4×4)

| Parameter | 2×2 | 4×4 |
|---|---|---|
| `TILE_COUNT` | 4 | 16 |
| `TILE_ID_W` | 2 | 4 |
| `SHARER_W` | 4 | 16 |
| Directory entry (used) | 3 + 2 + 4 + 1 = **10 b** | 3 + 4 + 16 + 1 = **24 b** |
| L2 per-line word | **23 b** (21 b tag + valid + dirty) | **21 b** (19 b tag + valid + dirty) |
| L1 tag (`addr[31:8]`) | 24 b | 24 b |
| Home field | `addr[12:11]` | `addr[14:11]` |
| L2 set / L1 set | `addr[10:8]` / `addr[7:6]` | `addr[10:8]` / `addr[7:6]` |
| Flit width | 64 b | 64 b |
| VC count | 4 (VC0 REQ, VC1 FWD, VC2 RESP, VC3 INV) | 4 |
| Credit width | 4 b | 4 b |
| Age-escape threshold | 5 rounds (ruling B1) | 5 rounds |

**Not in the budget:** any processor core, instruction or data memory, CSR file, or performance
counter — the WP excludes processor-core RTL (§1.4); the FPGA estimate covers the coherence
fabric only. The core is an external stimulus source at the `l1_mesi_ctrl` `core_req` port.

---

## 5. Open Items Before Module #1 Is Accepted

- [x] `pkg/tile_pkg.sv` is the root of every other module and is checked by
      `python3 lint/check_rules.py --verilator`.
- [x] No RISC-V / processor-core subtree exists under `rtl/` (core RTL is out of scope; the
      boundary is the `core_req`/`core_rsp` port of `l1_mesi_ctrl`).
- [x] `dma_tile` is gated — 4×4 simulation only (ruling B4), excluded from the 2×2 build.
- [x] The stale Notion-export CSV link is gone; `docs/BUILD_ORDER.csv` is the machine-readable
      order.
