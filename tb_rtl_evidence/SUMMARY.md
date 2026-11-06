# RTL Evidence Sweep Summary — 2026-11-06

> **Document Purpose**: Consolidated summary of overnight evidence tasks against frozen RTL (Slice 16.1).  
> **Writing Standard**: ~80% ASD-STE100 — direct active verbs, exact file references.

## Tasks Completed

| Task | Description | Status | Output |
|---|---|---|---|
| **1** | BMC K=64 on `rtl_frozen/` | **FAIL** | `tb_rtl_evidence/FORMAL_K64.md`, `FORMAL_FAILURES.md` |
| **2** | BMC K=128 on `rtl_frozen/` | **FAIL** | `tb_rtl_evidence/FORMAL_K128.md` |
| **3** | Static RTL-vs-spec audit | **COMPLETE** | `tb_rtl_evidence/AUDIT.md` |
| **4** | Lint sweep (iverilog + verilator) | **COMPLETE** | `tb_rtl_evidence/LINT.md` |
| **5** | Open items (R5, OI-8, OI-9) | **COMPLETE** | `docs/01_DECISION_LOG.md`, `docs/AI_SCRATCHPAD.md` |

## Tasks Failed / Blocked

| Task | Issue |
|---|---|
| **1, 2** | Both BMC runs failed on `a2_2` (Sharer accuracy) at step 48. Formal verdict conditional on `assume(!dir_oflow)` (R5). |

## Key Finding — Must Read First

**BMC FAILURE on `a2_2` (Sharer accuracy)**:
- **Location**: `rtl_frozen/directory/dir_ctrl.sv` lines 304–310 (DIR_FWD_WAIT → DIR_S transition)
- **Root cause**: Directory enters `DIR_S` on `UNBLOCK` from owner while requester is still in `SM_D` (transient, awaiting DATA). Sharers mask set to `{req_tile}` but requester not yet stable S.
- **Counterexample**: Step 48, directory state `DIR_S` with stale sharers while both L1s in `L1_SM_D`.
- **Fix required**: Clear `sharers_d = '0` on FWD_WAIT exit, let serving path add requester on DATA arrival — or delay DIR_S entry until requester reaches S.

> **Top 3 items for RTL author tomorrow**:
> 1. Fix `a2_2` sharer accuracy in `dir_ctrl.sv` lines 304–310
> 2. Clean up unused signals (`rx_data[511:448]`, `rx_we`, `conflict` in L1; `rx_data[511:448]` in Dir) — `tb_rtl_evidence/LINT.md`
> 3. Review UNUSEDPARAM scope (21 params from full-system package) — `tb_rtl_evidence/LINT.md`

## Evidence Inventory

All artifacts under `tb_rtl_evidence/`:
```
tb_rtl_evidence/
├── sby_k64/
│   ├── run_final.log          # Full sby output (4h 28m)
│   └── l1_dir/engine_0/
│       ├── trace.vcd          # Counterexample waveform
│       ├── trace_tb.v         # Verilog testbench
│       ├── trace.smtc         # Constraints
│       └── trace.yw           # Yosys witness
├── sby_k128/
│   ├── run_final.log          # Full sby output (4h 31m)
│   └── l1_dir/engine_0/
│       └── trace.vcd          # Counterexample waveform
├── lint/
│   ├── iverilog_l1.log
│   ├── iverilog_dir.log
│   ├── verilator_l1.log
│   └── verilator_dir.log
├── FORMAL_K64.md
├── FORMAL_K128.md
├── FORMAL_FAILURES.md
├── AUDIT.md
├── LINT.md
└── SUMMARY.md                 # (this file)
```

## Gate Status (on frozen RTL)

| Gate | Command | Result |
|---|---|---|
| Spec | `python3 pd/v1/verify_patch_set.py --dir white_papers/final --build-script pd/v1/build_diagrams_html.py` | **130/130 PASS** (exit 0) |
| Docs | `python3 ~/.skills/hw-design-docs/scripts/check_docs.py --docs docs --wp white_papers/final/FINAL_whitepaper_v3.0.md --build-order docs/BUILD_ORDER.csv` | **47/47 PASS** (exit 0) |
| Icarus 13 | `iverilog -g2012 -Wall` | exit 0 (21 "sorry" = Icarus limitation) |
| Verilator 5.054 | `verilator --lint-only -Wall -Wno-fatal` | exit 0 (4 real UNUSEDSIGNAL, 42 UNUSEDPARAM style) |
| BMC K=64 | `sby -f l1_dir.sby` | **FAIL** (a2_2 step 48) |
| BMC K=128 | `sby -f l1_dir.sby` | **FAIL** (a2_2 step 48) |

## Formal Scope Limitation (R5 / OI-8)

Both BMC results are **conditional on `assume(!dir_oflow)`** — an environment assumption modeling missing NIC credit management (§16.9 not implemented). Per R5: "F1 formal results valid ONLY under this assumption. Re-run without assumption when §16.9 lands."

## New Open Item (OI-9)

**Sharer accuracy failure on FWD_WAIT→DIR_S transition** — directory enters `DIR_S` with stale sharers while requester is `SM_D`. Requires RTL fix in `dir_ctrl.sv` lines 304–310.

---

*Generated 2026-11-06 05:45 UTC*