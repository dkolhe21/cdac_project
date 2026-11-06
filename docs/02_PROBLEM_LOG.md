# Problem Log

> **Document Purpose**: Systematic post-mortem ledger recording every hardware defect, reproduction method, root cause analysis, resolution patch, verification proof, and engineering lesson learned.  
> **Writing Standard**: Formatted with explicit adherence to ~80% ASD-STE100 (Simplified Technical English) language standards — structured 6-field chain, direct causal analysis, and unambiguous technical vocabulary.

Format: Symptom → Reproduction → Root cause → Resolution → Verification → Lesson

## P-001: L1_TAG_W computed as 26 b instead of 24 b

**Symptom**: `L1_TAG_W = ADDR_W - L1_SET_LO` evaluates to 32-6=26, but WP §3.6 states the stored L1 tag is addr[31:8] = 24 bits.

**Reproduction**: Read `rtl/pkg/tile_pkg.sv` line 42. The comment says "24 always" but the expression yields 26 because `L1_SET_LO = 6` is the low bit of the *index*, not one past the high bit.

**Root cause**: The L1 set index occupies bits [7:6] (two bits). The tag starts at bit 8, so width = ADDR_W - (L1_SET_HI + 1) = 32 - 8 = 24. Using `L1_SET_LO` instead of `L1_SET_HI + 1` double-counted the index bits.

**Resolution**: Changed expression to `ADDR_W - (L1_SET_HI + 1)` where `L1_SET_HI = 7`. Comment updated to `// 24 always: stored tag = addr[31:8]`.

**Verification**: `verilator --lint-only -Wno-UNUSEDPARAM -Wno-DECLFILENAME rtl/pkg/tile_pkg.sv` exits 0 clean after the fix.

**Lesson**: When deriving a field width from an address map, use the *high* bit position of the excluded field plus 1, not the low bit position.

## P-002: WP Appendix C VC ID row cited wrong invariant (I3 instead of I2)

**Symptom**: Appendix C header-flit table row [43:42] reads "formal invariant I3" for the VC check. I3 is the credit invariant. The VC check is I2.

**Reproduction**: `grep "43:42" white_papers/final/FINAL_whitepaper_v3.0.md` shows "formal invariant I3". §5.3 line 648 of the WP lists: "I1 XY path; I2 flit.VC==class(flit.msg); I3 credit invariant".

**Root cause**: Copy-paste error when writing the Appendix C table; I3 was used where I2 was intended.

**Resolution**: Changed "invariant I3" to "invariant I2" in that row only. Re-rendered `diagrams_rendered.html` via `pd/v1/build_diagrams_html.py`. Updated `cross-check-snapshot/`.

**Verification**: `python3 pd/v1/verify_patch_set.py --dir cross-check-snapshot --build-script pd/v1/build_diagrams_html.py` → RESULT: PASS 130/130, exit 0.

**Lesson**: Invariant cross-references must be checked against the numbered list in §5.3 at the time of writing, not assumed from memory.

