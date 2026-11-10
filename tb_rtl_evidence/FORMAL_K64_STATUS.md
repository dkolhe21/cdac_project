# BMC K=64 — v7 run status on the landed RTL (`rtl/`)

> **Document Purpose:** the observed state of the K=64 BMC run against the **landed**
> RTL tree (`rtl/`, md5-identical to the clean-room's pre-B6 snapshot — see R1).
> The v4 run against `rtl_frozen/` is recorded separately in `FORMAL_K64.md` and
> is history; this file is the current run.

## What is being checked

The formal item is *"BMC over the **declared assertion subset**, under the
**documented assumptions**"*. The subset is published as an **ID list**, not a
count, in `tb_rtl_evidence/FORMAL_SCOPE.md` (32 asserts + 4 assumptions = 36
`$check` cells, each traced to a harness source line).

## Command

```bash
export PATH="$HOME/.local/oss-cad-suite/bin:$PATH"
cd tb_rtl_evidence/sby_k64 && sby -f l1_dir.sby
```

The run is executed as a **systemd user unit** (`systemctl --user status bmc_k64`)
so that a machine restart does not kill it — the v6 run was lost twice to server
restarts.

## The RTL the run reads

`l1_dir.sby` copies the sources at start; the copy is byte-identical to the
tracked tree:

| file | md5 (copy in `l1_dir/src/`) | md5 (`rtl/`) |
|---|---|---|
| `tile_pkg.sv` | `b6ece1864f1ce6ddf5b6976775d34485` | `b6ece1864f1ce6ddf5b6976775d34485` |
| `l1_mesi_ctrl.sv` | `0bc0d48f4c830ca1a1b6c45a29077c4c` | `0bc0d48f4c830ca1a1b6c45a29077c4c` |
| `dir_ctrl.sv` | `8e44ed1da9543a62e52bc448f7d899fe` | `8e44ed1da9543a62e52bc448f7d899fe` |

## Live counts (from the elaborated design, not from prose)

```bash
cd tb_rtl_evidence/sby_k64/l1_dir
grep -c 'cell \$check' model/design.il                    # 36
grep -c 'parameter \\FLAVOR "assert"' model/design.il      # 32
grep -c 'parameter \\FLAVOR "assume"' model/design.il      # 4
```

**36 live cells = 32 asserts + 4 assumes.** No assertion was weakened, removed
or disabled to reach this number.

## Observed state

**The run is still going.** The solver is grinding through the depth; the state
below is what the log actually says at the time of writing — not a target.

| Quantity | Observed |
|---|---|
| Depth target | 64 (from `l1_dir.sby`) |
| Depth reached | **29** (`Checking assertions in step 29`, the last step entered) |
| Live assert cells | 32 |
| Live assume cells | 4 |
| Violations so far | 0 (no `Assert failed` line in the log) |
| Failing step | none so far — no assertion has failed |
| Failing signals | n/a — no counterexample exists yet |
| Wall clock | 0:21:02 at the last logged step |

Raw tail of the live run:

```
SBY 16:21:03 [l1_dir] engine_0: ##   0:16:02  Checking assertions in step 29..
SBY 16:22:03 [l1_dir] engine_0: ##   0:17:02  waiting for solver (1 minute)
SBY 16:26:03 [l1_dir] engine_0: ##   0:21:02  waiting for solver (5 minutes)
```

## Status of the formal item

**OPEN — not green.** Per the supervisor decision, the item stays open until
K=64 completes; the depth is reported as actually reached and is never rounded
up. Until the run finishes, no statement is made about the properties beyond
depth 29.

Two facts are recorded here regardless of how the run ends:

- The scope is the **declared subset** (`FORMAL_SCOPE.md`), not the 42 bound
  properties of the specification; the gap is itemised there.
- The result is **conditional on the four assumptions** — `assume(!dir_oflow)`
  (R5 / open item 8, the NIC credit gap) and the UNBLOCK-after-DATA harness
  assumption, plus the two environment-shape assumptions. What becomes
  unproven if each is false is stated in `FORMAL_SCOPE.md` §2.
