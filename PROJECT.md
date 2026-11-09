# Project: Clean-Room Multi-Core Cache Hierarchy RTL Verification

## Architecture
- **Target DUT**: Multi-core cache hierarchy slice 16.1 (`rtl/pkg/tile_pkg.sv`, `rtl/l1/l1_mesi_ctrl.sv`, `rtl/directory/dir_ctrl.sv`).
- **Clean-Room Boundary**: Completely isolated workspace at `~/teamwork_projects/clean_room_verification`.
- **Authoritative Specifications**:
  - `white_papers/final/FINAL_whitepaper_v3.0.md`
  - `white_papers/final/SLICE_16_1.md`
  - `white_papers/final/WORK_BREAKDOWN_16.md`
  - `white_papers/final/RULINGS_B1_B2_B4.md`
  - `docs/01_DECISION_LOG.md`
  - `docs/04_TECH_STACK.md`
  - `BUILD_ORDER.md`
- **Isolation Constraint**: The team must NOT read or inspect test source code from `tb/`, `tb_self_test/`, `tb/l1_dir/`, or scratch test suites. The frozen RTL is a read-only black box. RTL under test must NEVER be modified.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Setup & Isolation Script (`WAKE_UP.sh`) | Automates verification of `pd/v1/verify_patch_set.py` md5, snapshotting RTL to `rtl_frozen/`, quarantining `tb/l1_dir` to `tb_self_test/l1_dir`, generating `tb_self_test/README.md` | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Clean-Room Workspace Setup | Creates `~/teamwork_projects/clean_room_verification`, copies only authorized specs and `rtl_frozen/`, verifies `md5sum -c rtl_frozen/FROZEN.md5` | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Directed Tests F1-F8 (`tb_acceptance/l1_dir/`) | Cocotb 2.1.0 + iverilog 13.0 directed testbenches verifying Slice 16.1 forward release (clean/dirty FWD_GETS/FWD_GETM, silent upgrades, evict races) | M2 | SLICE_16_1.md §5, ORIGINAL_REQUEST §R2 |
| 4 | Python Shadow Reference Model (`tb_acceptance/ref_model/`) | Cycle-by-cycle / transaction shadow model implementing Slice Rules 1–11, reporting mismatch count (target: 0) | M2 | SLICE_16_1.md §4, ORIGINAL_REQUEST §R2 |
| 5 | SystemVerilog Assertions Suite (`tb_acceptance/sva/`) | SVA assertions A1.1 (SWMR), A1.2 (Exclusivity), A1.3 (Shared validity), A2.2 (Sharer precision), A2.6 (Owner in sharers), A3.1 (VC preservation), A7.x (FSM single-exit & determinism) | M3 | RULINGS_B1_B2_B4.md, ORIGINAL_REQUEST §R2 |
| 6 | Formal BMC K=64 with SymbiYosys | SymbiYosys configuration running Boolector/Z3 at depth K=64 with `read_slang` on frozen RTL | M3 | SLICE_16_1.md §5 (F9), ORIGINAL_REQUEST §R2 |
| 7 | Spec-Derived Mutation Suite (`tb_acceptance/mutations/`) | Independent mutation testing suite evaluating positive control, structural fault (`neg1`), and data fault (`neg2`) | M4 | ORIGINAL_REQUEST §R2, §R3 |
| 8 | Unified Test Runner (`tb_acceptance/run_all.py`) | Executes all directed tests, ref model, SVA BMC, and mutations, outputting test matrix: `test name \| PASS/FAIL \| spec clause it verifies` | M5 | ORIGINAL_REQUEST §R2 |
| 9 | Defect Citation & Verification Report (`README.md`) | Comprehensive report quoting exact spec line violations for any RTL failures, mutation matrix, BMC outputs, mismatch counts | M5 | ORIGINAL_REQUEST §R3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Setup & Isolation | Create `WAKE_UP.sh`, snapshot RTL into `rtl_frozen/`, quarantine `tb/l1_dir`, create `tb_self_test/README.md`, setup `~/teamwork_projects/clean_room_verification` | none | DONE |
| M2 | Directed Tests & Ref Model | Implement `tb_acceptance/l1_dir/` (F1-F8 with cocotb 2.1.0/iverilog) and `tb_acceptance/ref_model/` (Slice Rules 1-11) | M1 | DONE |
| M3 | SVA & Formal BMC K=64 | Implement `tb_acceptance/sva/` assertions A1.1-A7.x and `sby` BMC at depth K=64 | M1 | BLOCKED: Forensic Audit Integrity Violation (Vacuous formal harness & A3.1 framing defect) |
| M4 | Mutation Testing Suite | Implement `tb_acceptance/mutations/` matrix and qualification harnesses | M2, M3 | PLANNED |
| M5 | Unified Runner & Reporting | Implement `tb_acceptance/run_all.py` and final clean-room verification `README.md` | M2, M3, M4 | PLANNED |

## Interface Contracts
### Directed Testbench (`tb_acceptance/l1_dir`) ↔ DUT
- Toolchain: Python 3.14 + cocotb 2.1.0 + iverilog 13.0
- Clocks: 100 MHz (`clk`), active-low reset (`rst_n`)
- Signals: Header and Flit formats conform to `rtl/pkg/tile_pkg.sv`:
  - Flit: `[63:0]` width
  - Header fields: `Dest[63:56], Src[55:48], Msg[47:44], VC[43:42], Head[41], Tail[40], WE/Dirty[39], Excl[38], Len[37:32], Addr[31:0]`
  - VCs: `VC_REQ=2'd0, VC_FWD=2'd1, VC_RESP=2'd2, VC_INV=2'd3`

### Shadow Reference Model (`tb_acceptance/ref_model`) ↔ DUT
- Compares transaction by transaction / cycle by cycle:
  - L1 state: Stable (I, S, E, M) and Transient (IS_D, IM_AD, IM_A, SM_A, MI_A, EI_A)
  - Directory state: Stable (DIR_I, DIR_S, DIR_E, DIR_M) and Transient (DIR_MEM_WAIT, DIR_FWD_WAIT, DIR_INV_WAIT, DIR_EVICT)
  - Single-Exit rule: `DIR_FWD_WAIT` exits only on `UNBLOCK`.
  - Mismatch reporting: mismatch count integer, target = 0.

### Formal SVA (`tb_acceptance/sva`) ↔ SymbiYosys
- Parser: Yosys with Slang frontend (`read_slang`)
- Engines: `smtbmc boolector` and `smtbmc z3`
- Bounds: `depth = 64`
- Properties: A1.1 (SWMR), A1.2 (Exclusivity), A1.3 (Shared validity), A2.2 (Sharer precision), A2.6 (Owner in sharers), A3.1 (VC preservation), A7.x (Single exit on UNBLOCK & Determinism).

## Code Layout
```
/mnt/Code/visualstudio/Design-arch_multi-core/
├── WAKE_UP.sh                         # Automated 4-step reset script
├── rtl_frozen/                        # Read-only snapshot of RTL under test
│   ├── tile_pkg.sv
│   ├── l1_mesi_ctrl.sv
│   ├── dir_ctrl.sv
│   └── FROZEN.md5
└── tb_self_test/                      # Quarantined original self-tests
    ├── l1_dir/
    └── README.md

~/teamwork_projects/clean_room_verification/
├── README.md                          # Acceptance report and defect citations
├── white_papers/final/                # Authorized specifications
├── docs/                              # Authorized design docs
├── BUILD_ORDER.md                     # Authorized build order
├── rtl_frozen/                        # Verified frozen RTL snapshot
└── tb_acceptance/                     # Clean-room acceptance test suite
    ├── l1_dir/                        # Directed tests F1-F8 (cocotb + iverilog)
    ├── sva/                           # Formal SVA & sby BMC K=64
    ├── ref_model/                     # Python shadow reference model (Rules 1-11)
    ├── mutations/                     # Spec-derived mutation testing
    └── run_all.py                     # Unified test runner & matrix generator
```
