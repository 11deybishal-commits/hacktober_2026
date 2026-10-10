"""
GSTLens Validation Engine.
Runs deterministic business rules against CanonicalInvoice records.
"""
from typing import List, Dict, Any
from gstlens.contracts import InvoiceRecord, RuleResult, ProcessingStatus

# Minimal mock implementation of the 12 rules for the engine.
# In a full build, each rule would be imported from validate.rules
def run_validation_rules(record: InvoiceRecord) -> InvoiceRecord:
    """Executes all active GST rules against the record and updates its status."""
    rules_run = []
    
    inv = record.invoice
    
    # Rule 1 & 2: GSTIN Format and Checksum
    from gstlens.validate.gstin import is_valid_gstin_format, is_valid_gstin_checksum
    
    for party, prefix in [(inv.supplier, "supplier"), (inv.buyer, "buyer")]:
        if party.gstin:
            is_fmt = is_valid_gstin_format(party.gstin)
            is_chk = is_valid_gstin_checksum(party.gstin)
            
            rules_run.append(RuleResult(
                rule_id=1, rule_name="GSTIN_FORMAT",
                passed=is_fmt, severity="hard",
                implicated_fields=[f"{prefix}.gstin"],
                message=f"{prefix.capitalize()} GSTIN format valid" if is_fmt else f"{prefix.capitalize()} GSTIN format invalid"
            ))
            
            if is_fmt:
                rules_run.append(RuleResult(
                    rule_id=2, rule_name="GSTIN_CHECKSUM",
                    passed=is_chk, severity="hard",
                    implicated_fields=[f"{prefix}.gstin"],
                    message=f"{prefix.capitalize()} GSTIN checksum passed" if is_chk else f"{prefix.capitalize()} GSTIN checksum failed"
                ))

    # Rule 6: Tax Math (taxable * rate = tax)
    # Rule 7: Sum Consistency
    tot_taxable = 0
    for i, line in enumerate(inv.line_items):
        if line.taxable_value is not None:
            tot_taxable += float(line.taxable_value)
            
            if line.cgst_rate and line.cgst_amt is not None:
                expected = float(line.taxable_value) * (float(line.cgst_rate) / 100.0)
                passed = abs(float(line.cgst_amt) - expected) <= 1.0
                rules_run.append(RuleResult(
                    rule_id=6, rule_name="TAX_MATH",
                    passed=passed, severity="hard",
                    implicated_fields=[f"line_items[{i}].taxable_value", f"line_items[{i}].cgst_amt"],
                    message="Tax math valid" if passed else f"Tax math mismatch. Expected ~{expected:.2f}, got {line.cgst_amt}",
                    expected_values={f"line_items[{i}].cgst_amt": str(round(expected, 2))}
                ))
    
    record.rules = rules_run
    
    # Determine Status
    failed_hard = [r for r in rules_run if not r.passed and r.severity == "hard"]
    if failed_hard:
        record.status = ProcessingStatus.NEEDS_REVIEW
        for f in failed_hard:
            for field in f.implicated_fields:
                if field not in record.needs_review:
                    record.needs_review.append(field)
    else:
        record.status = ProcessingStatus.VERIFIED if not record.repair_log else ProcessingStatus.REPAIRED

    return record
