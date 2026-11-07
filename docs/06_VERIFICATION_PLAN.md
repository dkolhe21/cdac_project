# 06 — Verification Plan & Methodology

> **Document Purpose**: Formal verification and functional validation plan detailing the 42-assertion SVA suite, bounded model checking depths, transaction-level reference models, and exit criteria.  
> **Writing Standard**: Formatted with explicit adherence to ~80% ASD-STE100 (Simplified Technical English) language standards — direct test objectives, quantifiable pass/fail criteria, and structured technical specifications.

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
1. RTL lint clean — `python3 tb_rtl_evidence/lint/check_rules.py --verilator` passes CR1/CR2 against `tb_rtl_evidence/lint/coding_rules.json` (zero `%Error`; only the recorded style warning classes `UNUSEDSIGNAL`/`UNUSEDPARAM` fire); unit testbench pass.
2. 42 bound SVA assertions pass BMC K=64 in SymbiYosys — **anti-vacuity**: the run must report its live assertion count in the elaborated design (post-B6 slice: 36 `$check` cells = 32 asserts + 4 assumes) and the depth reached; a green log without both numbers is not a pass.
3. TLM reference model shadow comparison: zero mismatches across directed tests.
4. `python3 pd/v1/verify_patch_set.py --dir white_papers/final --build-script pd/v1/build_diagrams_html.py` → **132/132, exit 0**.

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
| tb/l1_dir | F1 (forward release) | Scaffold only — positive FAILS against stub; baseline vs zero-stub: neg1 PASS, neg2 FAIL. Discrimination proven by mutation test (3 stub mutations A/B/C, 9/9 expected outcomes) |

## 6. Ruling B5 — A2.2 Split & Sharer-Accuracy Verification

**The split (B5.1 — one assertion ID, §4.6 count stays 42):**
- **A2.2a — no missing bits (strict):** in `DIR_S`, every tile holding the line in `L1_S` has its sharer bit set. Never relaxed — a missing bit is the direction that allows two writers on one line.
- **A2.2b — bounded extra bits:** a sharer bit may remain set for a tile that has released the line **only while that tile's release notification (`PUTS`/`PUTM`) is in flight toward the home tile**, and it must clear within the bounded window **T = 64** cycles (§5.3: 40 cycles fabric + ≤ 24 cycles overhead). A BMC depth below T is unsound for this property.

**In-flight tracker:** the flight window is bounded by {release absorbed by the directory} — once the `PUTS`/`PUTM` is absorbed the bit must clear, and a bit still set T cycles after the release is an A2.2b failure. The TB samples `dir_state`, `dir_sharers`, `dir_owner`, `dir_valid` and the incoming message channels; `dir_ctrl` already exposes all of them (no port added, T2).

**Committed-set rule (B5.3):** on the `DIR_FWD_WAIT → DIR_S` exit the committed set is {requester} ∪ {owner} minus any tile whose release the directory has already absorbed. **B5.2:** the vector is a conservative superset of the actual holders, never a subset.

**Directed matrix (T3):** both arrival orders of the concurrent-owner-eviction case — (1) `UNBLOCK` (VC2) absorbed before the owner's `PUTS` (VC0): directory exits `DIR_FWD_WAIT` with the requester present, extra bit clears when `PUTS` is absorbed; (2) `PUTS` before `UNBLOCK`: baseline order. Golden result: `TESTS=2 PASS=2` (`tb_rtl_evidence/directed_owner_evict/evidence/`).

**Mutation / negative control:** `tb_rtl_evidence/directed_owner_evict/dir_ctrl_mut.sv` drops a **missing** bit (`sharers_d = sharers & ~(1 << req_tile)`, line 314) — the fault A2.2a exists to catch. Result: `PASS=0 FAIL=2`, fault present in the log (`A2_2A_FAIL t=24 missing=0001`). The control asserts the fault is present; a control that only showed the symptom absent would be a false pass.

**Anti-vacuity requirement:** every BMC run reported as evidence must state (a) the **live assertion count** in the elaborated design — counted as `$check` cells in the flattened design (post-B6: 36 = 32 asserts + 4 assumes) — and (b) the **depth reached**. A run that reports neither, or reports zero live assertions, is vacuous regardless of the log colour. This requirement exists because Task 0 found the SVA instance wrapped in `` `ifdef FORMAL `` with `FORMAL` never defined and depth lowered 64→32: 0 of 35 assertions live, still marked green.

**Open:** §12 item 12 (Lemma L1 versus a mid-miss tile) is not covered by B5 — A2.2a is vacuously true while no tile holds the line in S. B5 stays open until the Task 0 K=64 BMC run and the depth-128 trace analysis report their evidence.

## 7. Ruling B6 — Same-Line INV Abort (Concurrent-Upgrade Race)

**Abort mechanism (v4 Task 1):** `rtl/l1/l1_mesi_ctrl.sv` — on `MSG_INV` dispatched while the state is `IS_D`/`IM_D`/`SM_D` and `rx_addr == addr_q`, the sequential block invalidates `data_q` and pulses `abort_o` for one cycle, staying in the same transient (Appendix A row 1007: same-state self-edge — no new FSM state, `A7 a7_*_data` untouched). `INVACK` was already sent combinationally and unconditionally on every INV (comb dispatch); the parked access is re-driven by the DATA-install path; no `GETM` re-send. Lint 6/6; yosys elaboration clean.

**Formal assumption (v4 Task 0):** `env_unblk_installed` in `tb_rtl_evidence/sby_k64/fml_l1_dir.sv` (and the `tb/sva/` copy) — when the directory receives `MSG_UNBLOCK` whose source is `dir_req_tile`, that tile's L1 state is in `{S,E,M}`. This is a **state-space restriction, not a proof**: the real L1 sends `UNBLOCK` only after installing DATA (the depth-128 counterexample's harness-driven `UNBLOCK` from a requester that never received DATA is excluded). Live count after adding it: 36 `$check` = 32 asserts + 4 assumes (`env_dir_credit`, `env_dir_rx_msg`, `env_dir_dst`, `env_unblk_installed`).

**New directed test (v4 Task 3):** `tb_rtl_evidence/directed_upgrade_race/` — three phases: (A) tile 1 `GETS` → `DIR_E` owner=1; (B) tile 0 `GETS` → `DIR_S` sharers=0b11; (C) both stores issued in the same cycle → both S-store-hits send `GETM` → the directory pops one and sends a same-line INV to the other sharer, which is in `L1_SM_D`. Four properties: **B6.1** the race is exercised (INV delivered to a mid-miss tile — anti-vacuity: the hazard must occur, not be assumed); **B6.2** that tile aborts (`abort_o` within 8 cycles of the INV, `INVACK` within 12 — never deferred); **B6.3** both stores complete within 600 cycles; **B6.4** exactly one `M` at the end (single-writer).

**Negative control:** `l1_mesi_ctrl_defer_inv.sv` (same-name replacement, pattern of `dir_ctrl_mut.sv`) holds a same-line INV while the miss is open — the B6-forbidden behaviour. Expected and observed: B6.1 passes (the fault is present — the INV reaches the mid-miss tile), B6.2 fails with `DEFER-INV FAULT PRESENT` (no `abort_o`, no `INVACK`). The control asserts the fault is present; it never asserts that the symptom is absent.

**Current golden result (recorded, not fixed):** B6.1 ✓ (t=8), B6.2 ✓ (`abort_o` t=10, `INVACK` t=11), **B6.3 ✗** — the directory stalls in `DIR_INV_WAIT` with `rxq` head = the second `GETM` and the `INVACK` behind it (`RXQ cnt=2 head_msg=GETM`), because `DIR_INV_WAIT` has no `GETM` pop branch and the slice's rxq is arrival-ordered. Escalated as a challenge in the v4 report §8: the WP specifies VC priority inside the router (§3.5 line 287, RESP > INV > FWD > REQ) but not the directory controller's per-VC RX pop order, and the directed slice's round-robin merge models neither. Logs: `tb_rtl_evidence/directed_upgrade_race/golden_run.log`, `mutant_run.log`.

