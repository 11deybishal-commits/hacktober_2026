"""
GSTLens End-to-End Test Suite.
Tests all three pipeline scenarios:
  1. Perfect invoice → should be VERIFIED, zero repairs
  2. misread_taxable → should be REPAIRED (taxable_value fixed via TAX_MATH backsolve)
  3. gstin_confusion → should be REPAIRED (GSTIN fixed via confusion candidates)
"""
import sys
sys.path.insert(0, "project")

from gstlens.readers.mock import MockReader, _SUPPLIER_GSTIN_GOOD, _SUPPLIER_GSTIN_BAD, _BUYER_GSTIN_GOOD
from gstlens.structure.normalize import normalize_to_record
from gstlens.validate.engine import run_validation_rules
from gstlens.validate.gstin import is_valid_gstin_format, is_valid_gstin_checksum
from gstlens.repair.controller import run_repair_loop

PASS = "✓ PASS"
FAIL = "✗ FAIL"

print("=" * 65)
print(" GSTLens End-to-End Test Suite")
print("=" * 65)

# ── GSTIN sanity checks ──────────────────────────────────────────────────────
print("\n── GSTIN Sanity ──")
for label, gstin in [("Supplier GOOD", _SUPPLIER_GSTIN_GOOD),
                      ("Supplier BAD ", _SUPPLIER_GSTIN_BAD),
                      ("Buyer GOOD   ", _BUYER_GSTIN_GOOD)]:
    fmt = is_valid_gstin_format(gstin)
    chk = is_valid_gstin_checksum(gstin) if fmt else "N/A"
    tag = PASS if (fmt and chk is True) else (PASS if label.endswith("BAD ") and not fmt else FAIL)
    print(f"  {tag} | {label}: {gstin} | format={fmt} checksum={chk}")

# ── Test 1: Perfect mode ─────────────────────────────────────────────────────
print("\n── Test 1: Perfect Invoice ──")
m = MockReader(mode="perfect")
raw = m.read_document("dummy.jpg")
rec = normalize_to_record(raw, "scanned_image", filename="inv_perfect.jpg")
rec = run_validation_rules(rec)
tag = PASS if rec.status == "verified" else FAIL
print(f"  {tag} | Status: {rec.status}")
failed = [r.rule_name for r in rec.rules if not r.passed and r.severity == "hard"]
print(f"  Hard failures: {failed if failed else 'none'}")

# ── Test 2: Misread taxable ──────────────────────────────────────────────────
print("\n── Test 2: Misread Taxable (5490 → should repair to 5400) ──")
m2 = MockReader(mode="misread_taxable")
raw2 = m2.read_document("inv_hand.jpg")
rec2 = normalize_to_record(raw2, "handwritten_image", filename="inv_hand.jpg")
rec2 = run_validation_rules(rec2)
print(f"  Pre-repair status: {rec2.status}")
pre_failed = [r.rule_name for r in rec2.rules if not r.passed and r.severity == "hard"]
print(f"  Hard failures pre-repair: {pre_failed}")

rec2 = run_repair_loop(rec2)
tag = PASS if rec2.status in ("repaired", "verified") else FAIL
print(f"  {tag} | Post-repair status: {rec2.status}")
repaired_val = rec2.invoice.line_items[0].taxable_value
print(f"  Repaired line_items[0].taxable_value: {repaired_val} (expected 5400.00)")
tag2 = PASS if str(repaired_val) == "5400.00" else FAIL
print(f"  {tag2} | Taxable value correct: {repaired_val == 5400}")
print(f"  Repair log entries: {len(rec2.repair_log)}")

# ── Test 3: GSTIN confusion ──────────────────────────────────────────────────
print("\n── Test 3: GSTIN Confusion (Z→2 at pos 13) ──")
m3 = MockReader(mode="gstin_confusion")
raw3 = m3.read_document("inv_gstin.jpg")
rec3 = normalize_to_record(raw3, "scanned_image", filename="inv_gstin.jpg")
rec3 = run_validation_rules(rec3)
print(f"  Pre-repair supplier GSTIN: {rec3.invoice.supplier.gstin}")
pre_failed3 = [r.rule_name for r in rec3.rules if not r.passed and r.severity == "hard"]
print(f"  Hard failures pre-repair: {pre_failed3}")

rec3 = run_repair_loop(rec3)
tag3 = PASS if rec3.status in ("repaired", "verified") else FAIL
print(f"  {tag3} | Post-repair status: {rec3.status}")
repaired_gstin = rec3.invoice.supplier.gstin
fmt_ok = is_valid_gstin_format(repaired_gstin)
chk_ok = is_valid_gstin_checksum(repaired_gstin)
print(f"  Repaired GSTIN: {repaired_gstin} | format={fmt_ok} checksum={chk_ok}")
tag4 = PASS if fmt_ok and chk_ok else FAIL
print(f"  {tag4} | GSTIN passes all checks")

# ── Test 4: Export ───────────────────────────────────────────────────────────
print("\n── Test 4: Export ──")
from gstlens.export.json_csv import export_to_json, export_to_csv
try:
    j = export_to_json(rec2)
    c = export_to_csv(rec2)
    import json
    parsed = json.loads(j)
    assert "invoice" in parsed
    assert len(c.splitlines()) >= 2
    print(f"  {PASS} | JSON export OK ({len(j)} bytes)")
    print(f"  {PASS} | CSV export OK ({len(c.splitlines())} rows)")
except Exception as e:
    print(f"  {FAIL} | Export error: {e}")

# ── Test 5: Router ───────────────────────────────────────────────────────────
print("\n── Test 5: Router ──")
from gstlens.router import route_file, PipelineRoute
import tempfile, os

# Create temp files with known extensions
for ext, expected_route in [(".csv", PipelineRoute.TABULAR), (".xlsx", PipelineRoute.TABULAR),
                              (".jpg", PipelineRoute.SCANNED_IMAGE), (".png", PipelineRoute.SCANNED_IMAGE)]:
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(b"dummy content for routing test")
        tmp = f.name
    decision = route_file(tmp)
    os.unlink(tmp)
    tag = PASS if decision.route == expected_route else FAIL
    print(f"  {tag} | {ext} → {decision.route} (expected {expected_route})")

print("\n" + "=" * 65)
print(" All tests completed.")
print("=" * 65)
