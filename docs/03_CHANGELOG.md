# Changelog

> **Document Purpose**: Version-controlled chronicle of milestone completions, architectural refactorings, and module progress across the hardware engineering lifecycle.  
> **Writing Standard**: Formatted with explicit adherence to ~80% ASD-STE100 (Simplified Technical English) language standards — short itemized clauses, clear past-tense action verbs, and unambiguous component naming.

All notable changes and implementation iterations for the Cache-Coherent Tiled Multicore project will be documented here.

## Milestones

| Milestone | Target Date | Status |
|---|---|---|
| M0 — Spec package + gate 134/134 | Week 1 | ✅ Done (2026-11-04) |
| M1 — l2_bank + l2_ctrl green | Week 2 | Pending |
| M2 — l1_mesi_ctrl + dir_ctrl co-landed | Week 3-4 | Pending |
| M3 — nic + router + mem_tap green | Week 5 | Pending |
| M4 — cpu_tile + mesh_top + fpga_top | Week 6 | Pending |
| M5 — FPGA validation (JTAG bridge) | Week 7 | Pending |
| M6 — DMA tile (4×4, Week-8 gate) | Week 8 | Gated |

## [Unreleased] - 2026-11-04
### Added
- Created standardized project documentation structure (`docs/01_DECISION_LOG.md`, `02_PROBLEM_LOG.md`, `03_CHANGELOG.md`, `04_TECH_STACK.md`).
- Installed `doc-generator` skill into `.gemini/config/skills/` and workspace `.agents/skills/`.
- Created RTL folder hierarchy (`rtl/pkg`, `rtl/l1`, `rtl/l2`, `rtl/directory`, `rtl/nic`, `rtl/router`, `rtl/mem_tap`, `rtl/tile`, `rtl/mesh`).
- Created testbench hierarchy (`tb/directed`, `tb/sva`, `tb/ref_model`).
- Implemented `rtl/pkg/tile_pkg.sv` containing single source of truth for parameterised types, addresses, states, and messages.

## [2026-11-05] — Toolchain Verification & Bank Port Freeze
### Added
- **Toolchain verified**: cocotb 2.1.0 + Icarus Verilog 13.0 proven end-to-end via `tb/smoke/` (ALU combinational + DFF async reset with 2 negative controls).
- **Criterion 1 demonstrated**: Smoke test passes with positive + negative controls.
- **Doc checker hardened**: `check_docs.py` now has count-drift guard (EXPECTED_CHECKS=47); fails if any check silently skipped.
- **R3 — L2 bank port frozen**: Added `bank_src_e` enum (SRC_TAP, SRC_REMOTE, SRC_L1) and frozen port signature to `tile_pkg.sv`.
- **Created `rtl/l2/l2_bank.sv`**: Stub implementation (all outputs = 0) for port freeze.
- **L1/dir testbench scaffold** (`tb/l1_dir/`): Stubs for `l1_mesi_ctrl` + `dir_ctrl`, F1 positive test + 2 negative controls (both pass, proving scaffold has teeth).
- **Scaffold mutation-tested**: Original negatives passed vacuously against the zero stub; `test_f1_forward.py` restructured (negative controls now PASS only while their fault is present) and proven against 3 stub mutations — 9/9 expected outcomes, including positive rejecting a dirty DATAFWD.
- **R4 — cocotb 2.1.0 pinned**: Documented in decision log with migration notes.

