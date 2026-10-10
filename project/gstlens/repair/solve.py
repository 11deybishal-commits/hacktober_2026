"""
Repair: Solver.
Generates candidate fixes for suspect fields using arithmetic constraints
and OCR confusion patterns.
"""
from typing import List, Dict
from gstlens.contracts import InvoiceRecord, Candidate

def generate_hypotheses(record: InvoiceRecord, suspect_fields: List[str]) -> Dict[str, List[Candidate]]:
    """Generates L0 deterministic candidate fixes without calling models."""
    hypotheses: Dict[str, List[Candidate]] = {field: [] for field in suspect_fields}
    
    # 1. GSTIN Checksum Confusions
    from gstlens.validate.gstin import generate_gstin_confusion_candidates
    for field in suspect_fields:
        if "gstin" in field:
            val = record.fields[field].value
            if val:
                fixes = generate_gstin_confusion_candidates(val)
                for fix in fixes:
                    hypotheses[field].append(Candidate(
                        value=fix,
                        reader="solver_gstin_confusion",
                        view="derived",
                        legible=True
                    ))
                    
    # 2. Arithmetic Constraint Solver (Rule 6 Tax Math)
    for rule in record.rules:
        if not rule.passed and rule.rule_name == "TAX_MATH" and rule.expected_values:
            for field, expected_val in rule.expected_values.items():
                if field in hypotheses:
                    hypotheses[field].append(Candidate(
                        value=expected_val,
                        reader="solver_tax_math",
                        view="derived",
                        legible=True
                    ))
                    
    return hypotheses
