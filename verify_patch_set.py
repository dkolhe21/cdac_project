#!/usr/bin/env python3
"""
check_docs.py - deterministic gate for a hardware-design documentation suite.

Usage:
    python3 check_docs.py --docs docs
    python3 check_docs.py --docs docs --wp white_papers/FINAL_whitepaper_v3.0.md
    python3 check_docs.py --docs docs --build-order BUILD_ORDER.csv

Checks the ten-file suite: presence, section skeletons, decision-log shape, problem-log field
chain, coverage/count agreement with the spec, placeholder hygiene, and cross-links.

Exit code 0 only if there are no FAILs. WARNs do not fail the run.
"""
import argparse
import csv
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FILES = {
    "00_ARCHITECTURE.md": "Architecture",
    "01_DECISION_LOG.md": "Decision log",
    "02_PROBLEM_LOG.md": "Problem log",
    "03_CHANGELOG.md": "Changelog",
    "04_TECH_STACK.md": "Tech stack",
    "05_DATA_SAFETY.md": "Data safety",
    "06_VERIFICATION_PLAN.md": "Verification plan",
    "07_PHYSICAL_DESIGN.md": "Physical design",
    "08_PORTFOLIO_BIO.md": "Portfolio bio",
    "AI_SCRATCHPAD.md": "AI scratchpad",
}

# required heading fragments per file (case-insensitive substring)
REQUIRED = {
    "00_ARCHITECTURE.md": ["scope", "module map", "coherence"],
    "01_DECISION_LOG.md": ["contested", "ruling"],
    "02_PROBLEM_LOG.md": ["symptom", "root cause", "verification", "lesson"],
    "03_CHANGELOG.md": ["milestone", "added"],
    "04_TECH_STACK.md": ["tool", "version"],
    "05_DATA_SAFETY.md": ["ip", "secret"],
    "06_VERIFICATION_PLAN.md": ["assertion", "coverage", "exit criteria"],
    "07_PHYSICAL_DESIGN.md": ["resource budget", "timing", "clock"],
    "08_PORTFOLIO_BIO.md": ["talking point", "narrative"],
    "AI_SCRATCHPAD.md": ["next action", "open item"],
}

PROBLEM_FIELDS = ["symptom", "reproduction", "root cause", "resolution", "verification", "lesson"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", required=True)
    ap.add_argument("--wp", default=None, help="spec file, to cross-check assertion counts")
    ap.add_argument("--build-order", default=None, help="BUILD_ORDER.csv, to cross-check modules")
    args = ap.parse_args()

    results = []

    def fail(pid, desc, detail=""):
        results.append(("FAIL", pid, desc, detail))

    def warn(pid, desc, detail=""):
        results.append(("WARN", pid, desc, detail))

    def ok(pid, desc, detail=""):
        results.append(("PASS", pid, desc, detail))

    # ---- 1. presence -------------------------------------------------------
    texts = {}
    for name in FILES:
        p = os.path.join(args.docs, name)
        if not os.path.exists(p):
            fail("F1", f"{name} exists", p)
            continue
        texts[name] = open(p, encoding="utf-8").read()
        ok("F1", f"{name} exists", "")

    # ---- 2. section skeletons ----------------------------------------------
    for name, txt in texts.items():
        low = txt.lower()
        missing = [h for h in REQUIRED.get(name, []) if h not in low]
        if missing:
            fail("F2", f"{name} carries its required sections", f"missing: {missing}")
        else:
            ok("F2", f"{name} carries its required sections", "")

    # ---- 3. decision log shape ---------------------------------------------
    if "01_DECISION_LOG.md" in texts:
        lines = [l for l in texts["01_DECISION_LOG.md"].splitlines() if l.strip().startswith("|")]
        if len(lines) < 2:
            fail("F3", "the decision log has a header and at least one ruling row", f"{len(lines)} table lines")
        else:
            hdr = [c.strip() for c in lines[0].strip("|").split("|")]
            hdr_l = [h.lower() for h in hdr]
            widths = {len([c for c in l.strip("|").split("|")]) for l in lines[1:]}
            if widths - {len(hdr)}:
                fail("F3", "every decision row has the same column count as the header",
                     f"header {len(hdr)} cols, rows {sorted(widths)}")
            else:
                ok("F3", "every decision row has the same column count as the header", "")
            labels = []
            for l in lines[1:]:
                cells = [c.strip() for c in l.strip("|").split("|")]
                if not cells or set(cells[0]) <= set("- :"):
                    continue
                labels.append(cells[0].strip(" *"))
                # locate the ruling column by its header, not by a fixed offset:
                # column order varies between ledgers (the basis column may sit last)
                ri = next((i for i, h in enumerate(hdr_l) if "ruling" in h or h.startswith("**ruling")), None)
                if ri is None:
                    ri = len(cells) - 2
                ruling = cells[ri] if ri < len(cells) else ""
                if not ruling.strip(" *"):
                    fail("F4", f"decision '{cells[0].strip()}' states a ruling",
                         f"column {ri} is empty")
            if len(labels) != len(set(labels)):
                dupes = [x for x in set(labels) if labels.count(x) > 1]
                fail("F5", "decision labels are unique", f"duplicates: {dupes}")
            else:
                ok("F5", "decision labels are unique", f"{len(labels)} decisions")

    # ---- 4. problem log field chain ----------------------------------------
    if "02_PROBLEM_LOG.md" in texts:
        txt = texts["02_PROBLEM_LOG.md"]
        entries = re.split(r"^##\s+(?=P-\d+)", txt, flags=re.M)[1:]
        if not entries:
            fail("F6", "the problem log has at least one entry", "")
        else:
            bad = []
            for e in entries:
                low = e.lower()
                miss = [f for f in PROBLEM_FIELDS if f not in low]
                if miss:
                    bad.append((e.splitlines()[0][:40], miss))
            if bad:
                fail("F6", "every problem entry carries the full field chain", str(bad[:3]))
            else:
                ok("F6", "every problem entry carries the full field chain", f"{len(entries)} entries")

    # ---- 5. assertion count agrees with the spec ---------------------------
    if args.wp and os.path.exists(args.wp) and "06_VERIFICATION_PLAN.md" in texts:
        wp = open(args.wp, encoding="utf-8").read()
        m = re.search(r"(\d+)\s+bound\s+SVA", wp) or re.search(r"(\d+)\s+(?:bound\s+)?assertions?\b", wp)
        if m:
            n = m.group(1)
            doc = texts["06_VERIFICATION_PLAN.md"]
            if n in doc:
                ok("F7", f"the verification plan quotes the spec's assertion count ({n})", "")
            else:
                fail("F7", "the verification plan quotes the spec's assertion count",
                     f"spec says {n}, not found in the plan")
        else:
            warn("F7", "the spec's assertion count could not be located", args.wp)
    elif "06_VERIFICATION_PLAN.md" in texts:
        warn("F7", "no spec given - the assertion count was not cross-checked", "")

    # ---- 6. physical-design budget shape -----------------------------------
    if "07_PHYSICAL_DESIGN.md" in texts:
        lines = [l for l in texts["07_PHYSICAL_DESIGN.md"].splitlines() if l.strip().startswith("|")]
        hdr = [c.strip().lower() for c in lines[0].strip("|").split("|")] if lines else []
        if not any(("target" in h) for h in hdr) or not any(("ceiling" in h or "max" in h) for h in hdr):
            fail("F8", "the resource budget separates target from ceiling", f"header: {hdr}")
        else:
            ok("F8", "the resource budget separates target from ceiling", "")
        rows = [l for l in lines[1:] if not set(l.strip()) <= set("|-: ")]
        if len(rows) < 3:
            fail("F8b", "the resource budget lists at least three resources", f"{len(rows)} rows")
        else:
            ok("F8b", "the resource budget lists at least three resources", f"{len(rows)} rows")

    # ---- 7. modules from the build order are documented ---------------------
    if args.build_order and os.path.exists(args.build_order):
        if "00_ARCHITECTURE.md" in texts:
            mods = []
            with open(args.build_order, encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    # accept any column whose name mentions "module" (Module, Module_Name, ...)
                    k = ""
                    for col, val in row.items():
                        if col and "module" in col.lower() and val and str(val).strip():
                            k = str(val).strip()
                            break
                    if k:
                        mods.append(k)
            arch = texts["00_ARCHITECTURE.md"]
            # the module must appear as a table row's first cell, not merely in prose
            row_keys = set()
            for l in arch.splitlines():
                if l.strip().startswith("|"):
                    cells = [c.strip() for c in l.strip().strip("|").split("|")]
                    if cells:
                        row_keys.add(cells[0].strip(" *`"))
            if not mods:
                # a cross-check that parsed nothing would vacuously pass - that is a false green
                fail("F9", "the build order yielded module names to cross-check",
                     "no column containing 'module' was found")
                mods = []
            missing = [m for m in mods if m not in row_keys]
            if missing:
                fail("F9", "every module in the build order appears in the architecture doc",
                     f"missing: {missing}")
            else:
                ok("F9", "every module in the build order appears in the architecture doc",
                   f"{len(mods)} modules")
        else:
            fail("F9", "the architecture doc exists to cross-check the build order", "")

    # ---- 8. placeholder hygiene --------------------------------------------
    for name, txt in texts.items():
        hits = []
        for pat in (r"\bTBD\b", r"\bTODO\b", r"\bXXX\b", r"\bFIXME\b", r"\?\?\?", r"\[insert[^\]]*\]",
                    r"\[Name\]", r"\[Member[^\]]*\]"):
            hits += [m.group(0) for m in re.finditer(pat, txt)]
        if hits:
            warn("F10", f"{name} has no leftover placeholders", f"{sorted(set(hits))[:5]}")
        else:
            ok("F10", f"{name} has no leftover placeholders", "")

    # ---- 9. cross-links resolve ---------------------------------------------
    known = set(FILES)
    for name, txt in texts.items():
        refs = {r for r in re.findall(r"\b(\d\d_[A-Z_]+\.md)\b", txt) if r not in known}
        if refs:
            fail("F11", f"{name} links only to files that exist", f"dangling: {sorted(refs)}")
        else:
            ok("F11", f"{name} links only to files that exist", "")

    # ---- report --------------------------------------------------------------
    width = max(len(d) for _, _, d, _ in results) + 2
    nfail = sum(1 for k, _, _, _ in results if k == "FAIL")
    nwarn = sum(1 for k, _, _, _ in results if k == "WARN")
    out = [f"[{k}] {pid:<6} {desc:<{width}} {detail}" for k, pid, desc, detail in results]
    print("\n".join([
        f"RESULT: {'FAIL' if nfail else 'PASS'} - {len(results) - nfail}/{len(results)} doc checks passed "
        f"({nfail} fail, {nwarn} warn)",
        "",
        *out,
    ]))
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
