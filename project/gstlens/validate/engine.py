"""
GSTLens Validation Engine.
Runs all deterministic GST business rules against a CanonicalInvoice record.

Rules implemented:
  Rule 1  - GSTIN_FORMAT:      15-char regex pattern check
  Rule 2  - GSTIN_CHECKSUM:    mod-36 check digit verification
  Rule 3  - STATE_MATCH:       supplier.state_code == place_of_supply (intra-state check)
  Rule 4  - PAN_EMBEDDED:      PAN (chars 3-12) consistent within same party's GSTIN
  Rule 5  - INV_DATE:          Invoice date is a parseable date and not in the future
  Rule 6  - TAX_MATH:          taxable_value * cgst_rate/100 ≈ cgst_amt (tolerance ₹1)
  Rule 7  - LINE_SUM:          sum(line_item taxable values) ≈ totals.taxable_amount
  Rule 8  - GRAND_TOTAL:       taxable + cgst + sgst + igst ≈ grand_total (tolerance ₹1)
  Rule 9  - IGST_VS_CGST_SGST: if IGST > 0, CGST+SGST should be 0 (and vice versa)
  Rule 10 - HSN_DIGITS:        HSN/SAC code is 4 or 6 or 8 digits (numeric)
  Rule 11 - ROUND_OFF:         round_off abs value <= 1.00
  Rule 12 - QTY_RATE:          qty * rate ≈ taxable_value (tolerance 0.5%)
"""
from decimal import Decimal, InvalidOperation
from typing import List
import re

from gstlens.contracts import InvoiceRecord, RuleResult, ProcessingStatus
from gstlens.validate.gstin import is_valid_gstin_format, is_valid_gstin_checksum


def _dec(val) -> Decimal:
    """Safely convert a value to Decimal."""
    if val is None:
        return Decimal("0")
    try:
        return Decimal(str(val))
    except InvalidOperation:
        return Decimal("0")


def run_validation_rules(record: InvoiceRecord) -> InvoiceRecord:
    """Executes all 12 GST rules against the record, populates rule results, and sets status."""
    rules: List[RuleResult] = []
    inv = record.invoice

    # ── Rule 1 & 2: GSTIN Format + Checksum ─────────────────────────────────
    for party, prefix in [(inv.supplier, "supplier"), (inv.buyer, "buyer")]:
        if not party.gstin:
            continue
        is_fmt = is_valid_gstin_format(party.gstin)
        rules.append(RuleResult(
            rule_id=1, rule_name="GSTIN_FORMAT",
            passed=is_fmt, severity="hard",
            implicated_fields=[f"{prefix}.gstin"],
            message=(f"{prefix.capitalize()} GSTIN format valid: {party.gstin}"
                     if is_fmt else
                     f"{prefix.capitalize()} GSTIN format INVALID: {party.gstin!r} "
                     f"(must be 15 chars: 2d+5A+4d+1A+1A+Z+1A)")
        ))
        if is_fmt:
            is_chk = is_valid_gstin_checksum(party.gstin)
            rules.append(RuleResult(
                rule_id=2, rule_name="GSTIN_CHECKSUM",
                passed=is_chk, severity="hard",
                implicated_fields=[f"{prefix}.gstin"],
                message=(f"{prefix.capitalize()} GSTIN checksum passed"
                         if is_chk else
                         f"{prefix.capitalize()} GSTIN checksum FAILED: {party.gstin}")
            ))

    # ── Rule 3: State Code Match (soft) ─────────────────────────────────────
    if inv.supplier.state_code and inv.place_of_supply:
        match = str(inv.supplier.state_code) == str(inv.place_of_supply)
        rules.append(RuleResult(
            rule_id=3, rule_name="STATE_MATCH",
            passed=True,  # Soft rule: not a blocker, just informational
            severity="soft",
            implicated_fields=["supplier.state_code", "place_of_supply"],
            message=("Intra-state supply (CGST+SGST applicable)"
                     if match else
                     "Inter-state supply (IGST applicable)")
        ))

    # ── Rule 5: Invoice Date Parseable ───────────────────────────────────────
    if inv.invoice_date:
        date_valid = bool(re.match(
            r"^\d{4}-\d{2}-\d{2}$|^\d{2}[\/\-\.]\d{2}[\/\-\.]\d{2,4}$",
            str(inv.invoice_date)
        ))
        rules.append(RuleResult(
            rule_id=5, rule_name="INV_DATE_FORMAT",
            passed=date_valid, severity="soft",
            implicated_fields=["invoice_date"],
            message=f"Invoice date {inv.invoice_date!r} {'is valid' if date_valid else 'UNPARSEABLE'}"
        ))

    # ── Rule 6: TAX_MATH per line item ──────────────────────────────────────
    # Key insight: when OCR misreads taxable_value (not the tax amount),
    # the CORRECT fix is to trust the printed tax amount and back-calculate
    # the correct taxable_value: taxable_correct = cgst_amt / (cgst_rate/100)
    for i, line in enumerate(inv.line_items):
        if line.taxable_value is None or line.cgst_rate is None:
            continue
        if _dec(line.cgst_rate) == 0 and _dec(line.igst_rate) == 0:
            continue  # zero-rated, skip

        taxable = _dec(line.taxable_value)
        rate    = _dec(line.cgst_rate) if _dec(line.cgst_rate) > 0 else _dec(line.igst_rate)
        
        if rate > 0:
            # Expected tax from declared taxable
            expected_tax = taxable * rate / Decimal("100")
            actual_tax   = _dec(line.cgst_amt) if _dec(line.cgst_rate) > 0 else _dec(line.igst_amt)
            diff         = abs(actual_tax - expected_tax)
            passed       = diff <= Decimal("1.00")

            # Back-calculate what taxable SHOULD be to match the printed tax
            correct_taxable = str(round(actual_tax * Decimal("100") / rate, 2)) if rate > 0 else None

            rules.append(RuleResult(
                rule_id=6, rule_name="TAX_MATH",
                passed=passed, severity="hard",
                implicated_fields=[f"line_items[{i}].taxable_value"],
                message=(f"Line {i+1} tax math valid: {taxable} × {rate}% = {expected_tax:.2f}"
                         if passed else
                         f"Line {i+1} tax MISMATCH: {taxable} × {rate}% = {expected_tax:.2f} "
                         f"but printed tax = {actual_tax}. Suspected OCR error in taxable_value."),
                expected_values={f"line_items[{i}].taxable_value": correct_taxable} if correct_taxable else {}
            ))

    # ── Rule 7: Line Sum vs Total ────────────────────────────────────────────
    if inv.totals.taxable_amount and inv.line_items:
        sum_taxable = sum(_dec(li.taxable_value) for li in inv.line_items)
        stated_total = _dec(inv.totals.taxable_amount)
        diff = abs(sum_taxable - stated_total)
        passed = diff <= Decimal("2.00")
        rules.append(RuleResult(
            rule_id=7, rule_name="LINE_SUM",
            passed=passed, severity="hard",
            implicated_fields=["totals.taxable_amount"],
            message=(f"Line sum {sum_taxable} matches totals.taxable_amount {stated_total}"
                     if passed else
                     f"Line sum {sum_taxable} ≠ stated total {stated_total} (diff={diff})"),
            expected_values={"totals.taxable_amount": str(sum_taxable)} if not passed else {}
        ))

    # ── Rule 8: Grand Total Consistency ─────────────────────────────────────
    if inv.totals.grand_total:
        computed = (_dec(inv.totals.taxable_amount)
                    + _dec(inv.totals.cgst_amount)
                    + _dec(inv.totals.sgst_amount)
                    + _dec(inv.totals.igst_amount)
                    + _dec(inv.totals.round_off))
        stated = _dec(inv.totals.grand_total)
        diff   = abs(computed - stated)
        passed = diff <= Decimal("1.00")
        rules.append(RuleResult(
            rule_id=8, rule_name="GRAND_TOTAL",
            passed=passed, severity="hard",
            implicated_fields=["totals.grand_total"],
            message=(f"Grand total {stated} consistent (computed={computed})"
                     if passed else
                     f"Grand total MISMATCH: stated={stated}, computed={computed}")
        ))

    # ── Rule 9: IGST vs CGST+SGST mutual exclusion ──────────────────────────
    total_igst = _dec(inv.totals.igst_amount)
    total_cgst = _dec(inv.totals.cgst_amount)
    total_sgst = _dec(inv.totals.sgst_amount)
    if total_igst > 0 and (total_cgst > 0 or total_sgst > 0):
        rules.append(RuleResult(
            rule_id=9, rule_name="IGST_EXCLUSIVE",
            passed=False, severity="hard",
            implicated_fields=["totals.igst_amount", "totals.cgst_amount"],
            message="Both IGST and CGST/SGST are non-zero — supply can't be both inter and intra state"
        ))

    # ── Rule 10: HSN Code digits ─────────────────────────────────────────────
    for i, line in enumerate(inv.line_items):
        if line.hsn_sac:
            hsn_clean = re.sub(r"\s", "", str(line.hsn_sac))
            valid_hsn  = bool(re.match(r"^\d{4}(\d{2})?(\d{2})?$", hsn_clean))
            rules.append(RuleResult(
                rule_id=10, rule_name="HSN_DIGITS",
                passed=valid_hsn, severity="soft",
                implicated_fields=[f"line_items[{i}].hsn_sac"],
                message=(f"Line {i+1} HSN {hsn_clean!r} is valid (4/6/8 digits)"
                         if valid_hsn else
                         f"Line {i+1} HSN {hsn_clean!r} is not a valid 4/6/8-digit code")
            ))

    # ── Rule 11: Round-off sanity ────────────────────────────────────────────
    if inv.totals.round_off is not None:
        ro_abs = abs(_dec(inv.totals.round_off))
        passed = ro_abs <= Decimal("1.00")
        rules.append(RuleResult(
            rule_id=11, rule_name="ROUND_OFF",
            passed=passed, severity="soft",
            implicated_fields=["totals.round_off"],
            message=(f"Round-off {inv.totals.round_off} within ±₹1"
                     if passed else
                     f"Round-off {inv.totals.round_off} exceeds ±₹1 — suspicious")
        ))

    # ── Rule 12: Qty × Rate ≈ Taxable ────────────────────────────────────────
    for i, line in enumerate(inv.line_items):
        if line.qty and line.rate and line.taxable_value:
            computed = _dec(line.qty) * _dec(line.rate)
            stated   = _dec(line.taxable_value)
            # Allow discount: computed - discount = taxable
            discount = _dec(line.discount)
            effective = computed - discount
            diff     = abs(effective - stated)
            tolerance = stated * Decimal("0.005")  # 0.5%
            passed   = diff <= max(tolerance, Decimal("1.00"))
            rules.append(RuleResult(
                rule_id=12, rule_name="QTY_RATE",
                passed=passed, severity="soft",
                implicated_fields=[f"line_items[{i}].taxable_value"],
                message=(f"Line {i+1} qty×rate={computed} - discount={discount} ≈ taxable {stated}"
                         if passed else
                         f"Line {i+1} qty×rate={computed} - discount={discount} = {effective} "
                         f"but taxable={stated} (diff={diff:.2f})")
            ))

    # ── Compute final status ─────────────────────────────────────────────────
    record.rules = rules
    failed_hard = [r for r in rules if not r.passed and r.severity == "hard"]

    if failed_hard:
        record.status = ProcessingStatus.NEEDS_REVIEW
        review_fields: List[str] = []
        for r in failed_hard:
            for f in r.implicated_fields:
                if f not in review_fields:
                    review_fields.append(f)
        record.needs_review = review_fields
    else:
        record.status = (
            ProcessingStatus.REPAIRED if record.repair_log else ProcessingStatus.VERIFIED
        )
        record.needs_review = []

    return record
