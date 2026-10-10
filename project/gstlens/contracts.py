"""
GSTLens Core Domain Contracts and Pydantic Schemas.
Represents canonical invoice records, provenance, bounding boxes, candidates,
validation verdicts, and audit evidence.
"""
from decimal import Decimal
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class Provenance(str, Enum):
    READ = "read"
    REPAIRED = "repaired"
    DERIVED = "derived"
    HUMAN = "human_edited"

class ProcessingStatus(str, Enum):
    VERIFIED = "verified"
    REPAIRED = "repaired"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"

class BBox(BaseModel):
    page: int = 1
    x0: float = 0.0
    y0: float = 0.0
    x1: float = 1.0
    y1: float = 1.0

class Candidate(BaseModel):
    value: str
    reader: str
    view: str = "base"
    logprob: Optional[float] = None
    legible: bool = True

class FieldValue(BaseModel):
    path: str
    value: Optional[str] = None
    tier: str = "A"  # Tier A: provable, Tier B: partially checkable, Tier C: unverifiable
    confidence: float = 1.0
    provenance: Provenance = Provenance.READ
    bbox: Optional[BBox] = None
    candidates: List[Candidate] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    repair_history: List[str] = Field(default_factory=list)

class RuleResult(BaseModel):
    rule_id: int
    rule_name: str
    passed: bool
    severity: str = "hard"  # "hard" or "soft"
    implicated_fields: List[str] = Field(default_factory=list)
    message: str = ""
    expected_values: Dict[str, str] = Field(default_factory=dict)

class Supplier(BaseModel):
    name: Optional[str] = None
    gstin: Optional[str] = None
    state_code: Optional[str] = None
    address: Optional[str] = None

class Buyer(BaseModel):
    name: Optional[str] = None
    gstin: Optional[str] = None
    state_code: Optional[str] = None
    address: Optional[str] = None

class LineItem(BaseModel):
    item_index: int = 1
    description: Optional[str] = None
    hsn_sac: Optional[str] = None
    qty: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    discount: Optional[Decimal] = Decimal("0.00")
    taxable_value: Optional[Decimal] = None
    cgst_rate: Optional[Decimal] = Decimal("0.00")
    cgst_amt: Optional[Decimal] = Decimal("0.00")
    sgst_rate: Optional[Decimal] = Decimal("0.00")
    sgst_amt: Optional[Decimal] = Decimal("0.00")
    igst_rate: Optional[Decimal] = Decimal("0.00")
    igst_amt: Optional[Decimal] = Decimal("0.00")
    line_total: Optional[Decimal] = None

class Totals(BaseModel):
    taxable_amount: Optional[Decimal] = None
    cgst_amount: Optional[Decimal] = Decimal("0.00")
    sgst_amount: Optional[Decimal] = Decimal("0.00")
    igst_amount: Optional[Decimal] = Decimal("0.00")
    round_off: Optional[Decimal] = Decimal("0.00")
    grand_total: Optional[Decimal] = None
    amount_in_words: Optional[str] = None

class CanonicalInvoice(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    place_of_supply: Optional[str] = None
    is_reverse_charge: bool = False
    supplier: Supplier = Field(default_factory=Supplier)
    buyer: Buyer = Field(default_factory=Buyer)
    line_items: List[LineItem] = Field(default_factory=list)
    totals: Totals = Field(default_factory=Totals)

class InvoiceRecord(BaseModel):
    document_id: str
    filename: str = ""
    source_type: str = "unknown"  # "tabular", "digital_pdf", "scanned_image", "handwritten_image"
    status: str = "verified"      # "verified", "repaired", "needs_review"
    quality_score: float = 1.0
    invoice: CanonicalInvoice = Field(default_factory=CanonicalInvoice)
    fields: Dict[str, FieldValue] = Field(default_factory=dict)
    rules: List[RuleResult] = Field(default_factory=list)
    needs_review: List[str] = Field(default_factory=list)
    repair_log: List[Dict[str, Any]] = Field(default_factory=list)
    processing_stages: List[Dict[str, Any]] = Field(default_factory=list)
