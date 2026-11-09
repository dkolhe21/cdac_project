#!/usr/bin/env bash
set -euo pipefail

# WAKE_UP.sh — 4-Step Clean-Room Reset Script
# Automates environment verification, RTL snapshotting, and test quarantine.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "========================================================"
echo "Starting Clean-Room Reset Protocol (WAKE_UP.sh)"
echo "Working directory: $REPO_ROOT"
echo "========================================================"

# Step 1: Verify pd/v1/verify_patch_set.py checksum
echo "[Step 1/4] Verifying pd/v1/verify_patch_set.py checksum..."
VERIFIER="pd/v1/verify_patch_set.py"
EXPECTED_VERIFIER_MD5="4c4370f50882e82399b65076147bf112"

if [ ! -f "$VERIFIER" ]; then
    echo "ERROR: Verifier script '$VERIFIER' not found!" >&2
    exit 1
fi

ACTUAL_VERIFIER_MD5=$(md5sum "$VERIFIER" | awk '{print $1}')
if [ "$ACTUAL_VERIFIER_MD5" != "$EXPECTED_VERIFIER_MD5" ]; then
    echo "ERROR: Checksum mismatch for $VERIFIER!" >&2
    echo "  Expected: $EXPECTED_VERIFIER_MD5" >&2
    echo "  Actual:   $ACTUAL_VERIFIER_MD5" >&2
    exit 1
fi
echo "Step 1 PASS: $VERIFIER matches $EXPECTED_VERIFIER_MD5"

# Step 2: Validate source RTL against golden baseline hashes and snapshot into rtl_frozen/
echo "[Step 2/4] Validating source RTL against golden baseline hashes..."
GOLDEN_TILE_PKG_MD5="b6ece1864f1ce6ddf5b6976775d34485"
GOLDEN_L1_MESI_CTRL_MD5="d63be56146cfd7f2c9f3682caf918809"
GOLDEN_DIR_CTRL_MD5="4b8cca8381166c83ee61440ee2e45220"

RTL_CHECKS=(
    "rtl/pkg/tile_pkg.sv:$GOLDEN_TILE_PKG_MD5"
    "rtl/l1/l1_mesi_ctrl.sv:$GOLDEN_L1_MESI_CTRL_MD5"
    "rtl/directory/dir_ctrl.sv:$GOLDEN_DIR_CTRL_MD5"
)

RTL_ERRORS=0
for entry in "${RTL_CHECKS[@]}"; do
    src_file="${entry%%:*}"
    expected_md5="${entry##*:}"

    if [ ! -f "$src_file" ]; then
        echo "ERROR: Source RTL file '$src_file' not found!" >&2
        RTL_ERRORS=$((RTL_ERRORS + 1))
        continue
    fi

    actual_md5=$(md5sum "$src_file" | awk '{print $1}')
    if [ "$actual_md5" != "$expected_md5" ]; then
        echo "ERROR: Checksum mismatch for source RTL '$src_file'!" >&2
        echo "  Expected (golden baseline): $expected_md5" >&2
        echo "  Actual:                    $actual_md5" >&2
        RTL_ERRORS=$((RTL_ERRORS + 1))
    else
        echo "  Validated $src_file matches golden baseline ($actual_md5)"
    fi
done

if [ "$RTL_ERRORS" -ne 0 ]; then
    echo "ERROR: Source RTL validation failed against golden baseline ($RTL_ERRORS error(s))." >&2
    echo "RTL under test must NEVER be modified. Snapshot aborted!" >&2
    exit 1
fi

echo "Snapshotting RTL under test into rtl_frozen/..."
mkdir -p rtl_frozen/pkg rtl_frozen/l1 rtl_frozen/directory

# Copy hierarchical structure
cp -p rtl/pkg/tile_pkg.sv rtl_frozen/pkg/tile_pkg.sv
cp -p rtl/l1/l1_mesi_ctrl.sv rtl_frozen/l1/l1_mesi_ctrl.sv
cp -p rtl/directory/dir_ctrl.sv rtl_frozen/directory/dir_ctrl.sv

# Also copy flat files to support flat directory layouts
cp -p rtl/pkg/tile_pkg.sv rtl_frozen/tile_pkg.sv
cp -p rtl/l1/l1_mesi_ctrl.sv rtl_frozen/l1_mesi_ctrl.sv
cp -p rtl/directory/dir_ctrl.sv rtl_frozen/dir_ctrl.sv

# Generate rtl_frozen/FROZEN.md5
md5sum rtl_frozen/pkg/tile_pkg.sv rtl_frozen/l1/l1_mesi_ctrl.sv rtl_frozen/directory/dir_ctrl.sv > rtl_frozen/FROZEN.md5
echo "Generated rtl_frozen/FROZEN.md5:"
cat rtl_frozen/FROZEN.md5
echo "Step 2 PASS: RTL snapshot created and verified against golden baseline."

# Step 3: Quarantine existing self-tests
echo "[Step 3/4] Quarantining existing self-tests into tb_self_test/..."
mkdir -p tb_self_test
if [ -d "tb/l1_dir" ]; then
    mv tb/l1_dir tb_self_test/l1_dir
    echo "Moved tb/l1_dir -> tb_self_test/l1_dir"
elif [ -d "tb_self_test/l1_dir" ]; then
    echo "tb_self_test/l1_dir already quarantined."
else
    echo "Notice: Neither tb/l1_dir nor tb_self_test/l1_dir found."
fi

cat <<'EOF' > tb_self_test/README.md
# Quarantined Self-Tests

This directory contains quarantined legacy self-tests moved from `tb/l1_dir`.

## Clean-Room Isolation Protocol
Under clean-room verification rules:
- Engineers and verification agents MUST NOT read, inspect, or copy test source code from this directory (`tb_self_test/`) or any prior test suites.
- Acceptance tests must be independently developed from authoritative specification documents alone.
- RTL under test in `rtl_frozen/` is treated strictly as a read-only black box.
EOF
echo "Step 3 PASS: Quarantine complete and tb_self_test/README.md created."

# Step 4: Verify md5sum -c rtl_frozen/FROZEN.md5
echo "[Step 4/4] Validating frozen RTL checksums..."
md5sum -c rtl_frozen/FROZEN.md5
echo "Step 4 PASS: Checksum validation succeeded."

echo "========================================================"
echo "WAKE_UP: 4-step reset cleanly completed."
echo "========================================================"
