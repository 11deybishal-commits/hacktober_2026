"""
Repair: State Machine Controller.
Orchestrates the repair loop: Diagnose -> Solve -> Re-read -> Adjudicate -> Validate.
"""
from typing import Dict, Any
from gstlens.contracts import InvoiceRecord, ProcessingStatus, Provenance
from gstlens.repair.diagnose import diagnose_failures
from gstlens.repair.solve import generate_hypotheses
from gstlens.validate.engine import run_validation_rules

def run_repair_loop(record: InvoiceRecord) -> InvoiceRecord:
    """Runs a maximum of 2 repair loops to fix validation failures."""
    max_loops = 2
    loop_count = 0
    
    while loop_count < max_loops:
        # 1. Diagnose
        suspect_fields = diagnose_failures(record)
        if not suspect_fields:
            break # All fixed!
            
        # 2. Solve (Hypothesize)
        hypotheses = generate_hypotheses(record, suspect_fields)
        
        # 3. Adjudicate (Simplified for mock: Apply hypotheses if they exist)
        repairs_made = 0
        for field, cands in hypotheses.items():
            if cands and field in record.fields:
                best_cand = cands[0]
                record.fields[field].value = best_cand.value
                record.fields[field].provenance = Provenance.REPAIRED
                record.fields[field].repair_history.append(f"Applied candidate {best_cand.value} from {best_cand.reader}")
                record.repair_log.append({
                    "loop": loop_count,
                    "field": field,
                    "applied": best_cand.value,
                    "reason": best_cand.reader
                })
                # Apply to invoice model
                _apply_to_invoice_model(record, field, best_cand.value)
                repairs_made += 1
                
        if repairs_made == 0:
            break # No fixes could be proposed
            
        # 4. Re-validate
        record = run_validation_rules(record)
        loop_count += 1
        
    # Final status check
    if diagnose_failures(record):
        record.status = ProcessingStatus.NEEDS_REVIEW
    else:
        record.status = ProcessingStatus.REPAIRED if record.repair_log else ProcessingStatus.VERIFIED
        
    return record

def _apply_to_invoice_model(record: InvoiceRecord, field_path: str, value: str):
    """Updates the underlying Pydantic model with the repaired value."""
    try:
        from decimal import Decimal
        inv = record.invoice
        if "gstin" in field_path:
            if "supplier" in field_path:
                inv.supplier.gstin = value
            elif "buyer" in field_path:
                inv.buyer.gstin = value
        elif "taxable_amount" in field_path:
            inv.totals.taxable_amount = Decimal(value)
        elif "cgst_amount" in field_path:
            inv.totals.cgst_amount = Decimal(value)
        # Apply to line items
        elif field_path.startswith("line_items["):
            import re
            m = re.match(r"line_items\[(\d+)\]\.(.+)", field_path)
            if m:
                idx = int(m.group(1))
                attr = m.group(2)
                if idx < len(inv.line_items):
                    if "amt" in attr or "value" in attr or "rate" in attr or "qty" in attr:
                        setattr(inv.line_items[idx], attr, Decimal(value))
                    else:
                        setattr(inv.line_items[idx], attr, value)
    except Exception:
        pass
