#!/usr/bin/env python3
"""check_rules.py - machine-check lint/coding_rules.json against the frozen RTL.

Usage:
  check_rules.py --verilator [--module NAME]   # rules CR1, CR2
  check_rules.py --iverilog [--module NAME]    # rule CR3
  check_rules.py                               # every rule

Exit 0 only when every selected rule passes on every selected module.
A failure prints the offending tool lines so the run is evidence, not a verdict.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

LINT_DIR = Path(__file__).resolve().parent
REPO = LINT_DIR.parents[1]          # tb_rtl_evidence/lint -> repo root


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def check_verilator(mod, cfg, results):
    flags = cfg["flags"]
    cmd = ["verilator", *flags, "--top-module", mod["name"], *mod["sources"]]
    rc, out = run(cmd, REPO)

    # CR1: lint exits 0 (with -Wno-fatal, warnings never fail the exit code,
    # so an error is a non-zero exit or a %Error line).
    errs = [l for l in out.splitlines() if "%Error" in l]
    if rc == 0 and not errs:
        results.append(("PASS", "CR1", mod["name"], "exit 0, no %Error"))
    else:
        results.append(("FAIL", "CR1", mod["name"],
                        f"exit {rc}; " + "; ".join(errs[:3] or out.splitlines()[:3])))

    # CR2: every warning class fired must be on the recorded allow-list.
    fired = sorted({m.group(1) for m in
                    re.finditer(r"%Warning-(\w+):", out)})
    allowed = set(cfg["allowed_warnings"])
    bad = [w for w in fired if w not in allowed]
    if bad:
        lines = [l for l in out.splitlines()
                 if any(f"%Warning-{w}:" in l for w in bad)]
        results.append(("FAIL", "CR2", mod["name"],
                        f"disallowed: {bad}; " + " | ".join(lines[:3])))
    else:
        results.append(("PASS", "CR2", mod["name"],
                        f"warnings fired: {fired or 'none'}"))


def check_iverilog(mod, cfg, results):
    flags = cfg["flags"]
    out_vvp = cfg.get("output", "/tmp/opencode/check_rules_iverilog.vvp")
    cmd = ["iverilog", *flags, "-o", out_vvp, *mod["sources"]]
    rc, out = run(cmd, REPO)
    # CR3: compile exits 0; Icarus 'sorry:' limitation notes are not violations.
    real = [l for l in out.splitlines()
            if l.strip() and not any(s in l for s in cfg.get("ignore_lines", []))]
    if rc == 0:
        results.append(("PASS", "CR3", mod["name"],
                        f"exit 0 ({len(real)} non-'sorry:' lines)"))
    else:
        results.append(("FAIL", "CR3", mod["name"],
                        f"exit {rc}; " + " | ".join(real[:3])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verilator", action="store_true")
    ap.add_argument("--iverilog", action="store_true")
    ap.add_argument("--module", default=None)
    args = ap.parse_args()
    do_v, do_i = args.verilator, args.iverilog
    if not do_v and not do_i:
        do_v = do_i = True

    cfg = json.loads((LINT_DIR / "coding_rules.json").read_text())
    mods = cfg["modules"]
    if args.module:
        mods = [m for m in mods if m["name"] == args.module]
        if not mods:
            print(f"unknown module: {args.module}")
            return 1

    results = []
    for mod in mods:
        if do_v:
            check_verilator(mod, cfg["verilator"], results)
        if do_i:
            check_iverilog(mod, cfg["iverilog"], results)

    for status, rid, name, detail in results:
        print(f"[{status}] {rid:<4} {name:<16} {detail}")
    nfail = sum(1 for s, *_ in results if s == "FAIL")
    print(f"RESULT: {'FAIL' if nfail else 'PASS'} - {len(results) - nfail}/{len(results)} "
          f"coding-rule checks passed")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
