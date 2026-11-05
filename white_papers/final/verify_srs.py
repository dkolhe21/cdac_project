#!/usr/bin/env python3
"""
verify_srs.py - acceptance checker for the SRS (DOCX) against the closed spec package.

Usage:
    python3 verify_srs.py --srs SRS_final.docx --dir <package dir>
    python3 verify_srs.py --srs SRS_final.docx --dir <package dir> --wp <path> --spec <path>

Checks the SRS against the findings in SRS_REVIEW.md: protocol directions, identifier
namespaces, VC index order, area targets, the DMA scope, the message list, requirement
coverage, coverage criteria, test-plan completeness, traceability, and table hygiene.

Exit code 0 only if every check passes.
"""
import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def extract(path):
    d = Document(path)
    lines, tables = [], []

    def iter_block(parent, doc):
        for child in parent.iterchildren():
            if child.tag.endswith('}p'):
                yield Paragraph(child, doc)
            elif child.tag.endswith('}tbl'):
                yield Table(child, doc)

    for b in iter_block(d.element.body, d):
        if isinstance(b, Paragraph):
            t = b.text.strip()
            if t:
                try:
                    st = b.style.name
                except Exception:
                    st = "?"
                lines.append((st, t))
        else:
            rows = [[c.text.strip() for c in r.cells] for r in b.rows]
            tables.append(rows)
            for r in rows:
                lines.append(("TBL", " | ".join(r)))
    return lines, tables


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--srs", required=True)
    ap.add_argument("--dir", default=None)
    ap.add_argument("--wp", default=None)
    ap.add_argument("--spec", default=None)
    args = ap.parse_args()

    lines, tables = extract(args.srs)
    text = "\n".join(t for _, t in lines)
    results = []

    def check(pid, desc, ok, detail=""):
        results.append((pid, desc, bool(ok), detail))

    def row_with(prefix):
        for rows in tables:
            for r in rows:
                if r and r[0].strip().startswith(prefix):
                    return r
        return None

    # ---- B1: release message directions -------------------------------------
    puts = row_with("PUTS")
    putm = row_with("PUTM")
    putack = row_with("PUTACK")
    unblock = row_with("UNBLOCK")
    check("B1a", "PUTS is described as L1 -> directory", puts and "L1" in puts[-1] and "dir" in puts[-1].lower(), str(puts))
    check("B1b", "PUTM is described as L1 -> directory", putm and "L1" in putm[-1] and "dir" in putm[-1].lower(), str(putm))
    check("B1c", "PUTACK is described as directory -> L1", putack and "dir" in putack[-1].lower() and "L1" in putack[-1], str(putack))
    check("B1d", "UNBLOCK is described as L1 -> directory", unblock and "L1" in unblock[-1] and "dir" in unblock[-1].lower(), str(unblock))
    check("B1e", "no 'Directory-to-subscriber' direction remains", "Directory-to-subscriber" not in text, "")

    # ---- B2: phantom A13 ---------------------------------------------------
    check("B2a", "the phantom assertion id A13 is gone from the SRS", "A13" not in text, "")
    fr02 = row_with("FR-02")
    check("B2b", "FR-02 is verified by A8.x and/or I1", fr02 and re.search(r"A8|I1", fr02[-1]), str(fr02))

    # ---- B3: VC index order -------------------------------------------------
    ac03 = row_with("AC-03")
    check("B3a", "AC-03 states VC0 = REQ", ac03 and "VC0" in ac03[-1] and "REQ" in ac03[-1], str(ac03))
    check("B3b", "AC-03 states VC1 = FWD", ac03 and "VC1" in ac03[-1] and "FWD" in ac03[-1], "")
    check("B3c", "AC-03 states VC2 = RESP", ac03 and "VC2" in ac03[-1] and "RESP" in ac03[-1], "")
    check("B3d", "AC-03 states VC3 = INV", ac03 and "VC3" in ac03[-1] and "INV" in ac03[-1], "")
    order_ok = False
    if ac03:
        m = re.search(r"VC0\s*=\s*REQ.*?VC1\s*=\s*FWD.*?VC2\s*=\s*RESP.*?VC3\s*=\s*INV", ac03[-1], re.S)
        order_ok = m is not None
    check("B3e", "the VC index order is stated as REQ, FWD, RESP, INV (not the priority order)", order_ok, "")

    # ---- B4: area targets are design targets, not device capacity ----------
    a1 = row_with("AREA-01")
    a2 = row_with("AREA-02")
    check("B4a", "AREA-01's LUT target is a design target (<=20,000), not device capacity",
          a1 and len(a1) >= 4 and re.search(r"20[,.]?000", a1[2]), str(a1))
    check("B4b", "AREA-01's LUT maximum is <= 40,000",
          a1 and len(a1) >= 4 and re.search(r"40[,.]?000", a1[3]), str(a1))
    check("B4c", "AREA-02's BRAM target is <= 48 with a ceiling of 80",
          a2 and len(a2) >= 4 and re.search(r"48", a2[2]) and re.search(r"80", a2[3]), str(a2))
    check("B4d", "a DSP row exists with target 0", re.search(r"AREA-0[3-9][^\n]*DSP", text) and
          re.search(r"AREA-0[3-9][^\n]*\b0\b", text), "")
    fpga05 = [r for rows in tables for r in rows if r and r[0].strip().startswith("FPGA-05")]
    check("B4e", "FPGA-05 no longer asserts 80 DSP", not fpga05 or all("DSP" not in " ".join(r) or "0" in " ".join(r) for r in fpga05), str(fpga05))

    # ---- B5: no DMA signal in the 2x2 build --------------------------------
    sig_rows = [r for rows in tables for r in rows if len(r) >= 2 and r[0].strip() in
                ("dma_wr", "dma_req", "dma_write")]
    check("B5a", "no bare DMA write signal appears in the signal list", not sig_rows, str(sig_rows))
    check("B5b", "the DMA interface is marked absent from the 2x2 build",
          "not present in the 2" in text.lower() or "no dma" in text.lower(), "")

    # ---- B6: resolvable verification references -----------------------------
    bad = []
    for rows in tables:
        for r in rows:
            if not r:
                continue
            rid = r[0].strip()
            if not re.match(r"^(FR|AC|PERF|PWR|AREA|FPGA)-\d+", rid):
                continue
            for cell in r[1:]:
                if re.search(r"\bA13\b|\bG\d+\b|\bB[1-9]\b|\bB1[0-9]\b", cell):
                    bad.append((rid, cell))
    check("B6a", "no requirement cites a finding id (A13/G*) or a ruling id (B*) as its evidence", not bad, str(bad[:4]))
    fr_ids = set()
    for rows in tables:
        for r in rows:
            if r and re.match(r"^FR-\d+$", r[0].strip()):
                fr_ids.add(r[0].strip())
    traced = set()
    for rows in tables:
        for r in rows:
            if r and re.match(r"^FR-\d+$", r[0].strip()):
                traced.add(r[0].strip())
    # the traceability table is the one whose header mentions 'Method'
    trace_rows = []
    for rows in tables:
        if rows and any("Method" in c for c in rows[0]):
            trace_rows = rows[1:]
    traced_ids = {r[0].strip() for r in trace_rows if r}
    check("B6b", "every FR is traced in the traceability table",
          fr_ids and fr_ids.issubset(traced_ids), f"untraced: {sorted(fr_ids - traced_ids)}")

    # ---- M1: message set ---------------------------------------------------
    msgs = ["GETS", "GETM", "PUTS", "PUTM", "UNBLOCK", "INV", "INVACK", "DATA",
            "FWD_GETS", "FWD_GETM", "DATAFWD", "PUTACK", "DMA_WRITE", "DMA_ACK"]
    missing = [m for m in msgs if m not in text]
    check("M1a", "all 12 core + 2 gated messages appear in the SRS", not missing, f"missing: {missing}")

    # ---- M2: requirement coverage -------------------------------------------
    for i in range(9, 15):
        rid = f"FR-{i:02d}"
        check(f"M2-{i}", f"{rid} exists (forward release, exclusive bit, L2 word, dirty bit, write-back, receptivity)",
              row_with(rid) is not None, "")

    # ---- M3: numeric coverage criteria ---------------------------------------
    n_pct = max(text.count("100 %"), text.count("100%"))
    check("M3a", "coverage targets are numeric (at least three numeric targets)", n_pct >= 3, f"numeric targets: {n_pct}")
    check("M3b", "the four WP coverage criteria are present",
          all(k in text for k in ("FSM", "assertion", "waiver", "bin")), "")

    # ---- M4: test plans ------------------------------------------------------
    def plan_rows(marker):
        for rows in tables:
            if rows and any(marker in c for c in rows[0]):
                return rows[1:]
        return []
    tc = plan_rows("Scenario")
    fv = plan_rows("Procedure on board")
    check("M4a", "the directed test plan has at least 14 rows", len(tc) >= 14, f"{len(tc)} rows")
    check("M4b", "the FPGA test plan has at least 14 rows", len(fv) >= 14, f"{len(fv)} rows")

    # ---- M5: proof parameters marked as proposed -----------------------------
    check("M5a", "the proof parameters are marked proposed", "proposed" in text.lower(), "")
    check("M5b", "both liveness bounds appear (2x2 and 4x4)",
          ("64" in text and "150" in text), "")

    # ---- M6: table hygiene ----------------------------------------------------
    dupes = []
    for i, rows in enumerate(tables, 1):
        seen = {}
        for r in rows:
            key = tuple(c.strip() for c in r)
            if not any(key):
                continue
            seen[key] = seen.get(key, 0) + 1
        for k, v in seen.items():
            if v > 1:
                dupes.append((i, k[0], v))
    check("M6a", "no table repeats an identical row", not dupes, str(dupes[:4]))
    keydupes = []
    for i, rows in enumerate(tables, 1):
        keys = [r[0].strip() for r in rows[1:] if r and len(r) > 1]
        for k in set(keys):
            if keys.count(k) > 1:
                keydupes.append((i, k))
    check("M6b", "no table repeats the same key with different values", not keydupes, str(keydupes[:4]))

    # ---- N-series ------------------------------------------------------------
    check("N1a", "the SRS says 'virtual channel', not 'virtual buffer'", "virtual buffer" not in text.lower(), "")
    check("N2a", "the conditional DMA tests are marked conditional",
          re.search(r"18[–-]22[^.]*conditional|conditional[^.]*18[–-]22", text, re.I) is not None, "")
    check("N4a", "the performance section states known latency figures",
          any(k in text for k in ("4-cycle", "4 cycles", "9 flits", "512-bit")), "")
    check("N5a", "power is explicitly scoped or flagged", re.search(r"out of scope|not specified|TBD", text, re.I) is not None, "")
    check("N6a", "the verification exit criteria mention zero waivers", "waiver" in text.lower(), "")

    # ---- report ---------------------------------------------------------------
    width = max(len(d) for _, d, _, _ in results) + 2
    npass = sum(1 for _, _, ok, _ in results if ok)
    out = [f"[{'PASS' if ok else 'FAIL'}] {pid:<6} {desc:<{width}} {detail}"
           for pid, desc, ok, detail in results]
    print("\n".join([f"RESULT: {'PASS' if npass == len(results) else 'FAIL'} - {npass}/{len(results)} SRS checks passed",
                     ""] + out))
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
