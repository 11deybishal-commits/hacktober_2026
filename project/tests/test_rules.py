"""
GSTLens Test Suite: Validation Engine Rules.
Tests individual GST rules (Rules 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12).
"""
import sys
import os
from decimal import Decimal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gstlens.contracts import (
    InvoiceRecord,
    CanonicalInvoice,
    Supplier,
    Buyer,
    LineItem,
    Totals,
    ProcessingStatus,
)
from gstlens.validate.engine import run_validation_rules


def _make_clean_invoice() -> InvoiceRecord:
    inv = CanonicalInvoice(
        invoice_number="INV/2026/001",
        invoice_date="2026-10-04",
        place_of_supply="27",
        supplier=Supplier(
            name="Alpha Corp",
            gstin="27ABCDE1234F1Z0",
            state_code="27",
        ),
        buyer=Buyer(
            name="Beta Ltd",
            gstin="27XYZPQ5678K1ZF",
            state_code="27",
        ),
        line_items=[
            LineItem(
                item_index=1,
                description="Steel Bolt",
                hsn_sac="7318",
                qty=Decimal("10"),
                rate=Decimal("100.00"),
                discount=Decimal("0.00"),
                taxable_value=Decimal("1000.00"),
                cgst_rate=Decimal("9.0"),
                cgst_amt=Decimal("90.00"),
                sgst_rate=Decimal("9.0"),
                sgst_amt=Decimal("90.00"),
                igst_rate=Decimal("0.0"),
                igst_amt=Decimal("0.00"),
                line_total=Decimal("1180.00"),
            )
        ],
        totals=Totals(
            taxable_amount=Decimal("1000.00"),
            cgst_amount=Decimal("90.00"),
            sgst_amount=Decimal("90.00"),
            igst_amount=Decimal("0.00"),
            round_off=Decimal("0.00"),
            grand_total=Decimal("1180.00"),
        )
    )
    return InvoiceRecord(document_id="test-clean", invoice=inv)


def test_clean_invoice_passes_all_rules():
    rec = _make_clean_invoice()
    rec = run_validation_rules(rec)
    assert rec.status == ProcessingStatus.VERIFIED
    failed_hard = [r for r in rec.rules if not r.passed and r.severity == "hard"]
    assert len(failed_hard) == 0


def test_rule_1_and_2_gstin_failure():
    rec = _make_clean_invoice()
    rec.invoice.supplier.gstin = "INVALID_GSTIN_123"
    rec = run_validation_rules(rec)
    assert rec.status == ProcessingStatus.NEEDS_REVIEW
    rule_names = [r.rule_name for r in rec.rules if not r.passed]
    assert "GSTIN_FORMAT" in rule_names


def test_rule_6_tax_math_mismatch():
    rec = _make_clean_invoice()
    # Taxable is 1000, 9% CGST should be 90, but we inject 50.00
    rec.invoice.line_items[0].cgst_amt = Decimal("50.00")
    rec = run_validation_rules(rec)
    tax_math_rule = next(r for r in rec.rules if r.rule_name == "TAX_MATH")
    assert tax_math_rule.passed is False
    assert tax_math_rule.severity == "hard"
    assert rec.status == ProcessingStatus.NEEDS_REVIEW


def test_rule_7_line_sum_mismatch():
    rec = _make_clean_invoice()
    # Sum of items is 1000, but stated total is 2000
    rec.invoice.totals.taxable_amount = Decimal("2000.00")
    rec = run_validation_rules(rec)
    line_sum_rule = next(r for r in rec.rules if r.rule_name == "LINE_SUM")
    assert line_sum_rule.passed is False
    assert line_sum_rule.expected_values.get("totals.taxable_amount") == "1000.00"


def test_rule_8_grand_total_mismatch():
    rec = _make_clean_invoice()
    # 1000 + 90 + 90 = 1180, stated total is 1500
    rec.invoice.totals.grand_total = Decimal("1500.00")
    rec = run_validation_rules(rec)
    grand_total_rule = next(r for r in rec.rules if r.rule_name == "GRAND_TOTAL")
    assert grand_total_rule.passed is False


def test_rule_9_igst_vs_cgst_exclusion():
    rec = _make_clean_invoice()
    # Both CGST and IGST are populated
    rec.invoice.totals.igst_amount = Decimal("100.00")
    rec = run_validation_rules(rec)
    igst_rule = next(r for r in rec.rules if r.rule_name == "IGST_EXCLUSIVE")
    assert igst_rule.passed is False


def test_rule_10_hsn_digits_soft_rule():
    rec = _make_clean_invoice()
    rec.invoice.line_items[0].hsn_sac = "12"  # Invalid 2-digit HSN
    rec = run_validation_rules(rec)
    hsn_rule = next(r for r in rec.rules if r.rule_name == "HSN_DIGITS")
    assert hsn_rule.passed is False
    # Soft rule should not block verified status if all hard rules pass
    assert hsn_rule.severity == "soft"


def test_rule_11_round_off_exceeded():
    rec = _make_clean_invoice()
    rec.invoice.totals.round_off = Decimal("5.50")  # > 1.00
    rec = run_validation_rules(rec)
    ro_rule = next(r for r in rec.rules if r.rule_name == "ROUND_OFF")
    assert ro_rule.passed is False
    assert ro_rule.severity == "soft"


def test_rule_12_qty_rate_calculation():
    rec = _make_clean_invoice()
    # qty=10, rate=100 => expected taxable 1000, but stated is 800
    rec.invoice.line_items[0].taxable_value = Decimal("800.00")
    rec = run_validation_rules(rec)
    qty_rate_rule = next(r for r in rec.rules if r.rule_name == "QTY_RATE")
    assert qty_rate_rule.passed is False


if __name__ == "__main__":
    test_clean_invoice_passes_all_rules()
    test_rule_1_and_2_gstin_failure()
    test_rule_6_tax_math_mismatch()
    test_rule_7_line_sum_mismatch()
    test_rule_8_grand_total_mismatch()
    test_rule_9_igst_vs_cgst_exclusion()
    test_rule_10_hsn_digits_soft_rule()
    test_rule_11_round_off_exceeded()
    test_rule_12_qty_rate_calculation()
    print("All validation rule tests passed successfully.")
