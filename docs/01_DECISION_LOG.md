# Architectural Decision Log (ADR)

> **Document Purpose**: Authoritative Architectural Decision Record (ADR) capturing formal protocol rulings, microarchitectural adjudications, and implementation contracts.  
> **Writing Standard**: Formatted with explicit adherence to ~80% ASD-STE100 (Simplified Technical English) language standards — direct active verbs, restricted synonym usage, unambiguous criteria, and strict clause brevity.

## Rulings

| ID | Topic | Ruling | Contested | Resolved by |
|---|---|---|---|---|
| B1 | Age-escape threshold | 5 rounds; bound 5+3+5=13; port-granular arbiter | No | Supervisor 2026-11-04 |
| B2 | Conflict eviction | Victim released before miss on VC0; sub-step of miss transient | No | Supervisor 2026-11-04 |
| B4 | DMA scope | 2×2 has 4 CPU tiles, 0 DMA; DMA is 4×4 sim-only Week-8 gated | No | Supervisor 2026-11-04 |
| B5 | Sharer accuracy (A2.2) | A2.2 becomes two clauses under one ID: **a** — no missing bits (strict, never relaxed); **b** — extra bits allowed only while `PUTS`/`PUTM` is in flight, cleared within T = 64. Sharer vector is a conservative **superset**, never a subset. On `DIR_FWD_WAIT → DIR_S` the committed set excludes an already-released tile. **No RTL change** for the Case-C bookkeeping lag. **B5 is NOT closed** (§12 item 12 open; needs live K=64 BMC + mid-miss directed test) | No | Specification owner (MCode) 2026-11-06 — full text in `docs/RULINGS_B5.md` |
| B6 | Same-line INV during an outstanding miss | A same-line INV in `IS_D`/`IM_D`/`SM_D` **aborts the outstanding miss**: the L1 invalidates its copy, answers INVACK immediately, and re-issues the access. Deferral is forbidden (it deadlocks the one-outstanding-transaction-per-bank directory). Lemma L1 restated; the formal harness may not drive UNBLOCK before the requester installed the data. §12 item 12 closed | No | Specification owner (MCode) 2026-11-07 — row AH in WP §13 |
| R2 | Bank arbiter order | **Provisional**: tap > remote > L1 (see `BANK_ARB_TAP_FIRST` in `tile_pkg.sv`); spec §12 item 9 leaves order unspecified | **Yes — provisional** | Open (OI-4) |
| R3 | L2 bank port shape | Frozen per `tile_pkg.sv`: req {valid, is_write, addr, wdata, wstrb, source_sel}, rsp {valid, rdata, rstrb, rlast}, status {dtr_busy}. source_sel enum {TAP, REMOTE, L1} is the R2 input. | Provisional pending PLRU/write-logic impl | Open (R2/OI-4 arbiter) |
| R4 | cocotb major version | Pinned to 2.1.0 (installed via pipx; iverilog 13.0). Consequence: `dut.<sig>.value` returns LogicArray (not int); Timer signature; no `cocotb.binary`. Future tests must match 2.x. Revisit only if cocotb upgrade re-runs tb/smoke green. | No | 2026-11-04 |
| R5 | Formal scope: NIC backpressure | **Provisional:** `assume(!dir_oflow)` is a formal environment assumption standing in for NIC credit management (WP §16.9 not implemented). F1 formal results valid ONLY under this assumption. Re-run without the assumption when §16.9 lands. | Yes — provisional | Open until §16.9 implemented |

## Adjudication Ledger — Row AG (verbatim copy from WP §13)

*Quoted verbatim from `white_papers/final/FINAL_whitepaper_v3.0.md` §13 (row `| **AG** |`). Both copies are edited together or not at all, so they cannot drift.*

> | # | Contested point | Q | M | X | G | E | D | **Ruling (v3.0)** | Deciding basis |
> |---|---|---|---|---|---|---|---|---|---|
> | **AG** | Sharer accuracy under a concurrent owner eviction (ruling B5) | — | — | — | — | — | — | **A2.2 restated as two clauses under one assertion ID: A2.2a “no missing bits” (strict — every tile holding the line in S has its bit set) and A2.2b “bounded extra bits” (a stale bit is permitted only while that tile's release notification is in flight, and must clear within *T* = 64 cycles). The committed sharer set on the DIR_FWD_WAIT exit excludes a tile that has already released the line. The directory's sharer vector is a conservative superset of the actual holders, never a subset. **No RTL change is required for the Case-C bookkeeping lag**; the K = 64 BMC run with assertions live, and a directed test of the depth-128 trace scenario, must confirm that before B5 is closed (§12 item 12)** | Ruling B5: the verification team reproduced — by directed test and by a BMC counterexample — the case where the owner evicts while a forward is outstanding. The owner's PUTS travels on VC0 and the requester's UNBLOCK on VC2, and no FIFO order relates them, so the directory may exit DIR_FWD_WAIT while a sharer bit still names a tile that has already released. That transient is inherent to an asynchronous release notification, not an RTL defect: the directory absorbs the PUTS, clears the bit and self-corrects, and data integrity is unaffected. The previous wording (“sharers equal the S-mask exactly, no stale bits”) assumed instantaneous message delivery and is therefore unachievable per cycle. The correct restatement is one-sided: the missing-bit direction, which is what prevents two writers on one line, stays strict, and the extra-bit direction is bounded by the release flight time. Rejected: routing PUTS on VC1 (breaks invariant I2, VC = class) and adding PUTACK to S-state evictions (extra round trip, deadlock risk). |

## Adjudication Ledger — Row AH (verbatim copy from WP §13)

*Quoted verbatim from `white_papers/final/FINAL_whitepaper_v3.0.md` §13 (row `| **AH** |`). Both copies are edited together or not at all, so they cannot drift.*

> | # | Contested point | Q | M | X | G | E | D | **Ruling (v3.0)** | Deciding basis |
> |---|---|---|---|---|---|---|---|---|---|
> | **AH** | Same-line INV during an outstanding miss (ruling B6) | — | — | — | — | — | — | **A same-line INV aborts the L1's outstanding miss: the L1 invalidates its copy, answers INVACK immediately, and re-issues the access. Deferral is forbidden — it deadlocks against the one-outstanding-transaction-per-bank directory. Lemma L1 is restated from "no same-line message" to "no same-line message is serviced", with the abort as the single exception** | Ruling B6: the verification team's directed test of the concurrent-upgrade race found the directory issuing an INV to a tile in `L1_SM_D` on the same line — a case §3.3 rule 6 and Lemma L1 (§4.6) both declared impossible, so the §4.6 deadlock-freedom proof rested on a false premise. The fix is in the protocol, not in the assertion set: the abort path is the standard MESI resolution and costs no extra message. The formal harness must also be constrained: it may not drive an UNBLOCK from a requester that has not installed the data (the real L1 never does), which was the cause of the depth-128 counterexample. |

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
  4. Four-Item Green Criterion enforced per module: RTL clean lint/test + SVA BMC K=64 + TLM reference model zero mismatch + 132/132 `verify_patch_set.py` pass.

