from decimal import Decimal
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class Provenance(str, Enum):
    READ = "read"
    REPAIRED = "repaired"
    DERIVED = "derived"
    HUMAN = "human_edited"

class BBox(BaseModel):
    page: int
    x0: float
    y0: float
    x1: float
    y1: float

class Candidate(BaseModel):
    value: str
    reader: str
    view: str = "base"
    logprob: Optional[float] = None
    legible: bool = True

class FieldValue(BaseModel):
    path: str
    value: Optional[str]
    tier: str  # "A", "B", "C"
    confidence: float
    provenance: Provenance = Provenance.READ
    bbox: Optional[BBox] = None
    candidates: List[Candidate] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)

class RuleResult(BaseModel):
    rule_id: int
    rule_name: str
    passed: bool
    severity: str  # "hard" or "soft"
    implicated_fields: List[str]
    message: str
    expected_values: Dict[str, str] = Field(default_factory=dict)

class InvoiceRecord(BaseModel):
    document_id: str
    source_type: str
    status: str  # "verified", "repaired", "needs_review"
    fields: Dict[str, FieldValue] = Field(default_factory=dict)
    warnings: List[RuleResult] = Field(default_factory=list)

# Schema definitions for downstream canonical output
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
    item_index: int
    description: Optional[str] = None
    hsn_sac: Optional[str] = None
    qty: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    taxable_value: Optional[Decimal] = None
    cgst_rate: Optional[Decimal] = None
    cgst_amt: Optional[Decimal] = None
    sgst_rate: Optional[Decimal] = None
    sgst_amt: Optional[Decimal] = None
    igst_rate: Optional[Decimal] = None
    igst_amt: Optional[Decimal] = None
    line_total: Optional[Decimal] = None

class Totals(BaseModel):
    taxable_amount: Optional[Decimal] = None
    cgst_amount: Optional[Decimal] = None
    sgst_amount: Optional[Decimal] = None
    igst_amount: Optional[Decimal] = None
    round_off: Optional[Decimal] = None
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
