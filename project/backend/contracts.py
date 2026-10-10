"""
Re-export contracts from gstlens.contracts for backwards compatibility.
"""
from gstlens.contracts import (
    Provenance,
    ProcessingStatus,
    BBox,
    Candidate,
    FieldValue,
    RuleResult,
    Supplier,
    Buyer,
    LineItem,
    Totals,
    CanonicalInvoice,
    InvoiceRecord,
)

__all__ = [
    "Provenance",
    "ProcessingStatus",
    "BBox",
    "Candidate",
    "FieldValue",
    "RuleResult",
    "Supplier",
    "Buyer",
    "LineItem",
    "Totals",
    "CanonicalInvoice",
    "InvoiceRecord",
]
