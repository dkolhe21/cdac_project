# 06 — Verification Plan & Methodology

## 1. Scope & Objective
Three-layer verification methodology guaranteeing cache coherence, protocol safety, deadlock freedom, and cycle-accurate functional correctness.

## 2. Verification Pillars
1. **Formal Verification (SymbiYosys / sby)**:
   - **Safety Properties**: 38 bound SystemVerilog Assertions (A1: MESI invariants, A2: directory consistency, A3: message protocol, A4: packet framing/credits, A6: data currency, A7: FSM legality, A8: unmapped addresses). Proven via Bounded Model Checking (BMC, K = 64).
   - **Bounded Liveness**: 4 assertions (A5: no orphan transients within $T=64$ cycles for 2×2, $T=150$ cycles for 4×4 under Premise F).
   - **Deadlock Freedom**: 3-layer proof (XY routing + VC preservation, message class hierarchy, credit bounds) confirmed by k-induction at $k=16$.
2. **Transaction-Level Reference Model (pyuvm / cocotb)**:
   - Python-based shadow model verifying per-tile L1, L2, directory, and tap contents.
   - Compares real data values (not just state tags) after every coherence transaction.
   - Covers directed tests 1–22 (including F1–F9 forward release suite).
3. **Directed & Constrained-Random Unit Testing**:
   - Component testbenches for `l1_mesi_ctrl`, `dir_ctrl`, `l2_bank`, `nic`, and `router`.
   - 238-term coverage cross: (9 L1 states + 8 Directory states) × 14 active messages.

## 3. Exit Criteria (Per Module)

A module is green only when **all four** hold:
1. RTL lint clean (`verilator --lint-only`); unit testbench pass.
2. 42 bound SVA assertions pass BMC K=64 in SymbiYosys.
3. TLM reference model shadow comparison: zero mismatches across directed tests.
4. `python3 pd/v1/verify_patch_set.py --dir cross-check-snapshot --build-script pd/v1/build_diagrams_html.py` → **130/130, exit 0**.

Directed test suites per module:
| Module | Tests | Covers |
|---|---|---|
| l2_bank | B1–B4 | PLRU eviction, dirty/clean hit/miss |
| l1_mesi_ctrl + dir_ctrl | F1–F9 | Forward release (F8 needs both co-landed) |
| nic | N1–N3 | Packetize/depacketize; credit flow |
| router | R1–R4 | XY routing; VC isolation; age escape |

## 4. Toolchain Verification (Criterion 1)

**Demonstrated via smoke test `tb/smoke/`:**

| Tool | Version |
|------|---------|
| cocotb | 2.1.0 |
| Icarus Verilog | 13.0 (stable) |

Smoke test: 4-bit ALU (add/sub/pass), single cocotb test asserting (2+3)==5 → **PASS**.

**Criterion 1 — demonstrated (smoke)**: ✅ `tb/smoke/` proves end-to-end toolchain.

## 5. Test Scaffolds

| Scaffold | Tests | Status |
|---|---|---|
| tb/smoke | ALU + DFF (async reset) | PASS (positive + 2 negative controls) |
| tb/l1_dir | F1 (forward release) | Scaffold only — positive FAILS against stub; 2 negative controls PASS |

