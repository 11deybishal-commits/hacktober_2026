"""
Repair: Solver.
Generates candidate fixes for suspect fields using:
  - Arithmetic constraint back-calculation (L0: no model calls needed)
  - OCR confusion pattern substitution for GSTINs (mod-36 guided)
  - Second-reader re-read via the VLM reader (L1: crop re-read)
"""
from typing import List, Dict, Any
from gstlens.contracts import InvoiceRecord, Candidate


def generate_hypotheses(record: InvoiceRecord, suspect_fields: List[str]) -> Dict[str, List[Candidate]]:
    """
    Generates candidate fixes for each suspect field.
    
    Priority order:
      1. GSTIN confusion candidates (format/checksum repair via mod-36 exhaustive search)
      2. TAX_MATH arithmetic back-calculation (trust printed tax, back-derive taxable)
      3. LINE_SUM arithmetic back-calculation (re-sum from line items)
    """
    hypotheses: Dict[str, List[Candidate]] = {field: [] for field in suspect_fields}

    # ── Strategy 1: GSTIN confusion candidates ───────────────────────────────
    from gstlens.validate.gstin import generate_gstin_confusion_candidates
    for field in suspect_fields:
        if "gstin" in field.lower():
            # Get the current (bad) GSTIN value from the record
            fv = record.fields.get(field)
            val = fv.value if fv else None
            if not val:
                # Try to get from invoice model
                if "supplier" in field:
                    val = record.invoice.supplier.gstin
                elif "buyer" in field:
                    val = record.invoice.buyer.gstin
            if val:
                candidates = generate_gstin_confusion_candidates(val)
                for fix in candidates:
                    hypotheses[field].append(Candidate(
                        value=fix,
                        reader="solver_gstin_confusion",
                        view="derived",
                        legible=True
                    ))

    # ── Strategy 2: TAX_MATH back-calculation ───────────────────────────────
    # Find the TAX_MATH rule failures and use their expected_values
    import re
    from decimal import Decimal
    for rule in record.rules:
        if not rule.passed and rule.rule_name == "TAX_MATH" and rule.expected_values:
            for field_path, expected_val in rule.expected_values.items():
                if field_path in hypotheses:
                    # Consistency check (WORKING.md §4.1 & §4.4):
                    # Verify expected_val converges with qty * rate if both exist.
                    # An invoice arithmetic error on paper (writer's slip) must not be silently forced.
                    m = re.match(r"line_items\[(\d+)\]\.taxable_value", field_path)
                    if m:
                        idx = int(m.group(1))
                        if idx < len(record.invoice.line_items):
                            li = record.invoice.line_items[idx]
                            if li.qty and li.rate:
                                qr_val = Decimal(str(li.qty)) * Decimal(str(li.rate))
                                if abs(qr_val - Decimal(str(expected_val))) > Decimal("1.00"):
                                    # Contradiction: qty*rate contradicts tax backsolve.
                                    # Paper itself disagrees; do not hallucinate an unproven number.
                                    continue
                    hypotheses[field_path].append(Candidate(
                        value=expected_val,
                        reader="solver_tax_math_backsolve",
                        view="derived",
                        legible=True
                    ))

    # ── Strategy 3: LINE_SUM back-calculation ────────────────────────────────
    # If totals.taxable_amount is suspect, recompute from line items
    for rule in record.rules:
        if not rule.passed and rule.rule_name == "LINE_SUM":
            from decimal import Decimal
            sum_taxable = sum(
                Decimal(str(li.taxable_value))
                for li in record.invoice.line_items
                if li.taxable_value is not None
            )
            if "totals.taxable_amount" in hypotheses:
                hypotheses["totals.taxable_amount"].append(Candidate(
                    value=str(sum_taxable),
                    reader="solver_line_sum_backsolve",
                    view="derived",
                    legible=True
                ))

    # ── Strategy 4: TAX_SYMMETRY back-calculation ────────────────────────────
    for rule in record.rules:
        if not rule.passed and rule.rule_name == "TAX_SYMMETRY" and rule.expected_values:
            for field_path, expected_val in rule.expected_values.items():
                if field_path in hypotheses and expected_val:
                    hypotheses[field_path].append(Candidate(
                        value=expected_val,
                        reader="solver_tax_symmetry_backsolve",
                        view="derived",
                        legible=True
                    ))

    return hypotheses
