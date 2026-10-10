"""
Repair: State Machine Controller.
Orchestrates the repair loop: Diagnose → Solve → Adjudicate → Apply → Re-validate.

The loop runs a maximum of MAX_LOOPS iterations. On each pass:
  1. Diagnose:   Identify fields implicated in hard rule failures
  2. Solve:      Generate candidate corrections for each suspect field
  3. Adjudicate: Pick the best candidate (by reader priority and logprob)
  4. Apply:      Patch both the FieldValue dict AND the underlying CanonicalInvoice model
  5. Re-validate: Re-run all rules to check if the fix was sufficient
"""
import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional

from gstlens.contracts import InvoiceRecord, ProcessingStatus, Provenance
from gstlens.repair.diagnose import diagnose_failures
from gstlens.repair.solve import generate_hypotheses
from gstlens.validate.engine import run_validation_rules

MAX_LOOPS = 3

# Reader priority order: higher = more trusted
_READER_PRIORITY = {
    "solver_gstin_confusion":     10,
    "solver_tax_math_backsolve":  9,
    "solver_line_sum_backsolve":  8,
    "qwen_vl_crop":               7,
    "vlm_paddle_hf":              6,
}


def _best_candidate(candidates):
    """Pick the best candidate: prioritise by reader trust, then by logprob."""
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda c: (
            _READER_PRIORITY.get(c.reader, 0),
            c.logprob if c.logprob is not None else -999
        )
    )


def run_repair_loop(record: InvoiceRecord) -> InvoiceRecord:
    """Runs up to MAX_LOOPS repair iterations, re-validating after each pass."""
    for loop_count in range(MAX_LOOPS):
        # 1. Diagnose
        suspect_fields = diagnose_failures(record)
        if not suspect_fields:
            break

        # 2. Solve
        hypotheses = generate_hypotheses(record, suspect_fields)

        # 3+4. Adjudicate and Apply
        repairs_made = 0
        for field, candidates in hypotheses.items():
            if not candidates:
                continue
            best = _best_candidate(candidates)
            if not best:
                continue

            old_val = record.fields[field].value if field in record.fields else None

            # Update FieldValue provenance trail
            if field in record.fields:
                record.fields[field].value = best.value
                record.fields[field].provenance = Provenance.REPAIRED
                record.fields[field].candidates.append(best)
                record.fields[field].repair_history.append(
                    f"Loop {loop_count}: {old_val!r} → {best.value!r} via {best.reader}"
                )

            # Patch the underlying CanonicalInvoice model
            _apply_to_invoice_model(record, field, best.value)

            record.repair_log.append({
                "loop": loop_count,
                "field": field,
                "old_value": old_val,
                "applied": best.value,
                "reader": best.reader,
            })
            repairs_made += 1

        if repairs_made == 0:
            break  # Nothing more to try

        # 5. Re-validate
        record = run_validation_rules(record)

    # Final status
    if diagnose_failures(record):
        record.status = ProcessingStatus.NEEDS_REVIEW
    else:
        record.status = (
            ProcessingStatus.REPAIRED if record.repair_log else ProcessingStatus.VERIFIED
        )

    return record


def _apply_to_invoice_model(record: InvoiceRecord, field_path: str, value: str):
    """
    Applies a repaired value to both the FieldValue dict and the CanonicalInvoice model.
    Supports: supplier.gstin, buyer.gstin, totals.*, line_items[N].*
    """
    try:
        inv = record.invoice

        # ── Supplier / Buyer GSTIN ───────────────────────────────────────────
        if field_path == "supplier.gstin":
            inv.supplier.gstin = value
            if len(value) >= 2:
                inv.supplier.state_code = value[:2]
            return

        if field_path == "buyer.gstin":
            inv.buyer.gstin = value
            if len(value) >= 2:
                inv.buyer.state_code = value[:2]
            return

        # ── Totals ───────────────────────────────────────────────────────────
        totals_map = {
            "totals.taxable_amount": "taxable_amount",
            "totals.cgst_amount":    "cgst_amount",
            "totals.sgst_amount":    "sgst_amount",
            "totals.igst_amount":    "igst_amount",
            "totals.grand_total":    "grand_total",
            "totals.round_off":      "round_off",
        }
        if field_path in totals_map:
            setattr(inv.totals, totals_map[field_path], Decimal(value))
            return

        # ── Line Items ───────────────────────────────────────────────────────
        m = re.match(r"line_items\[(\d+)\]\.(.+)", field_path)
        if m:
            idx  = int(m.group(1))
            attr = m.group(2)
            if idx >= len(inv.line_items):
                return

            # Decimal fields
            decimal_fields = {
                "qty", "rate", "discount", "taxable_value",
                "cgst_rate", "cgst_amt", "sgst_rate", "sgst_amt",
                "igst_rate", "igst_amt", "line_total"
            }
            if attr in decimal_fields:
                setattr(inv.line_items[idx], attr, Decimal(value))
            else:
                setattr(inv.line_items[idx], attr, value)
            return

    except (InvalidOperation, ValueError, AttributeError, IndexError):
        # Non-fatal: field patch failed, repair_log still records the attempt
        pass
