"""
Repair: Diagnoser.
Maps validation rule failures to suspect fields.
"""
from typing import List, Dict, Set
from gstlens.contracts import InvoiceRecord, RuleResult

def diagnose_failures(record: InvoiceRecord) -> List[str]:
    """Returns a unique list of field paths implicated in hard rule failures."""
    suspect_fields: Set[str] = set()
    for rule in record.rules:
        if not rule.passed and rule.severity == "hard":
            for field in rule.implicated_fields:
                suspect_fields.add(field)
    return list(suspect_fields)
