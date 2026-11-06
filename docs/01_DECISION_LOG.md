# Architectural Decision Log (ADR)

> **Document Purpose**: Authoritative Architectural Decision Record (ADR) capturing formal protocol rulings, microarchitectural adjudications, and implementation contracts.  
> **Writing Standard**: Formatted with explicit adherence to ~80% ASD-STE100 (Simplified Technical English) language standards — direct active verbs, restricted synonym usage, unambiguous criteria, and strict clause brevity.

## Rulings

| ID | Topic | Ruling | Contested | Resolved by |
|---|---|---|---|---|
| B1 | Age-escape threshold | 5 rounds; bound 5+3+5=13; port-granular arbiter | No | Supervisor 2026-11-04 |
| B2 | Conflict eviction | Victim released before miss on VC0; sub-step of miss transient | No | Supervisor 2026-11-04 |
| B4 | DMA scope | 2×2 has 4 CPU tiles, 0 DMA; DMA is 4×4 sim-only Week-8 gated | No | Supervisor 2026-11-04 |
| R2 | Bank arbiter order | **Provisional**: tap > remote > L1 (see `BANK_ARB_TAP_FIRST` in `tile_pkg.sv`); spec §12 item 9 leaves order unspecified | **Yes — provisional** | Open (OI-4) |
| R3 | L2 bank port shape | Frozen per `tile_pkg.sv`: req {valid, is_write, addr, wdata, wstrb, source_sel}, rsp {valid, rdata, rstrb, rlast}, status {dtr_busy}. source_sel enum {TAP, REMOTE, L1} is the R2 input. | Provisional pending PLRU/write-logic impl | Open (R2/OI-4 arbiter) |
| R4 | cocotb major version | Pinned to 2.1.0 (installed via pipx; iverilog 13.0). Consequence: `dut.<sig>.value` returns LogicArray (not int); Timer signature; no `cocotb.binary`. Future tests must match 2.x. Revisit only if cocotb upgrade re-runs tb/smoke green. | No | 2026-11-04 |
| R5 | Formal scope: NIC backpressure | **Provisional:** `assume(!dir_oflow)` is a formal environment assumption standing in for NIC credit management (WP §16.9 not implemented). F1 formal results valid ONLY under this assumption. Re-run without the assumption when §16.9 lands. | Yes — provisional | Open until §16.9 implemented |

## Contested Decisions

*(None currently contested. Contested decisions are recorded here with open questions and resolution path.)*

## ADR-001: Baseline Unified Specification & Corrected 12-Module Build Order
- **Date:** 2026-11-04
- **Status:** Accepted
- **Context:** Correcting scope creep from old attached single-core SoC artifacts (`Build Order cf8a8428393d.md` / `Flat Table Database 2766ea9dcf5c.csv`). Establishing verified coherence-only fabric tree.
- **Decision:** 
  1. Processor core RTL is strictly **out of scope** (WP §1.2 line 49). Stimulus via testbench / on-board JTAG bridge.
  2. Implement in corrected dependency order: `tile_pkg` (Done) -> `l2_bank` (freeze bank/tag port) -> `l1_mesi_ctrl` + `dir_ctrl` (co-landed) -> `nic` -> `router` -> `mem_tap` -> `intra_tile_mux` -> `cpu_tile` -> `mesh_top` -> `fpga_top`.
  3. DMA Tile (`dma_tile.sv`) is strictly gated on Week 8 in 4×4 simulation only; 0 DMA tiles in 2×2 FPGA build (Ruling B4).
  4. Four-Item Green Criterion enforced per module: RTL clean lint/test + SVA BMC K=64 + TLM reference model zero mismatch + 130/130 `verify_patch_set.py` pass.

