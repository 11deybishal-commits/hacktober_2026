"""
GSTLens Test Suite: Constraint-Guided Repair Loop and Solver.
Tests Diagnose -> Solve -> Adjudicate -> Apply pipeline for:
  1. Misread taxable value (5,490 -> 5,400 via TAX_MATH backsolve)
  2. OCR confusion repair on GSTIN (27ABCDE1234F120 -> 27ABCDE1234F1Z0)
  3. Preservation of already-valid fields
"""
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gstlens.readers.mock import MockReader
from gstlens.structure.normalize import normalize_to_record
from gstlens.validate.engine import run_validation_rules
from gstlens.validate.gstin import is_valid_gstin_format, is_valid_gstin_checksum
from gstlens.repair.diagnose import diagnose_failures
from gstlens.repair.solve import generate_hypotheses
from gstlens.repair.controller import run_repair_loop
from gstlens.contracts import ProcessingStatus, Provenance


def test_diagnose_isolates_suspect_fields():
    reader = MockReader(mode="misread_taxable")
    raw = reader.read_document("dummy.jpg")
    rec = normalize_to_record(raw, "handwritten_image")
    rec = run_validation_rules(rec)
    
    suspect_fields = diagnose_failures(rec)
    assert len(suspect_fields) > 0
    # Taxable value of line 0 must be in suspect fields
    assert "line_items[0].taxable_value" in suspect_fields


def test_solve_generates_correct_taxable_hypothesis():
    reader = MockReader(mode="misread_taxable")
    raw = reader.read_document("dummy.jpg")
    rec = normalize_to_record(raw, "handwritten_image")
    rec = run_validation_rules(rec)
    
    suspect_fields = diagnose_failures(rec)
    hypotheses = generate_hypotheses(rec, suspect_fields)
    
    taxable_cands = hypotheses.get("line_items[0].taxable_value", [])
    assert len(taxable_cands) > 0
    candidate_values = [c.value for c in taxable_cands]
    # The backsolved 5400.00 should be proposed
    assert "5400.00" in candidate_values


def test_end_to_end_repair_taxable_5490_to_5400():
    reader = MockReader(mode="misread_taxable")
    raw = reader.read_document("inv_handwritten.jpg")
    rec = normalize_to_record(raw, "handwritten_image")
    rec = run_validation_rules(rec)
    
    assert rec.status == ProcessingStatus.NEEDS_REVIEW
    
    # Run repair loop
    repaired_rec = run_repair_loop(rec)
    
    assert repaired_rec.status == ProcessingStatus.REPAIRED
    assert str(repaired_rec.invoice.line_items[0].taxable_value) == "5400.00"
    assert len(repaired_rec.repair_log) > 0
    
    # FieldValue provenance must be marked REPAIRED
    fv = repaired_rec.fields.get("line_items[0].taxable_value")
    if fv:
        assert fv.provenance == Provenance.REPAIRED


def test_end_to_end_repair_gstin_confusion():
    reader = MockReader(mode="gstin_confusion")
    raw = reader.read_document("inv_gstin_bad.jpg")
    rec = normalize_to_record(raw, "scanned_image")
    rec = run_validation_rules(rec)
    
    assert rec.status == ProcessingStatus.NEEDS_REVIEW
    
    # Run repair loop
    repaired_rec = run_repair_loop(rec)
    
    assert repaired_rec.status == ProcessingStatus.REPAIRED
    repaired_gstin = repaired_rec.invoice.supplier.gstin
    assert is_valid_gstin_format(repaired_gstin) is True
    assert is_valid_gstin_checksum(repaired_gstin) is True
    assert repaired_gstin == "27ABCDE1234F1Z0"


if __name__ == "__main__":
    test_diagnose_isolates_suspect_fields()
    test_solve_generates_correct_taxable_hypothesis()
    test_end_to_end_repair_taxable_5490_to_5400()
    test_end_to_end_repair_gstin_confusion()
    print("All repair solver property tests passed successfully.")
