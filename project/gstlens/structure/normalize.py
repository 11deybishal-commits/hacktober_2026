"""
Structuring: Normalizer.
Converts raw parsed outputs from perception modules into canonical CanonicalInvoice
and InvoiceRecord structures with field paths and candidates.
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
import uuid

from gstlens.contracts import (
    CanonicalInvoice,
    Supplier,
    Buyer,
    LineItem,
    Totals,
    InvoiceRecord,
    FieldValue,
    Candidate,
    Provenance,
    BBox
)

def to_decimal(val: Any) -> Optional[Decimal]:
    if val is None or val == "":
        return None
    try:
        clean = str(val).replace(",", "").replace("/-", "").strip()
        return Decimal(clean)
    except Exception:
        return None

def normalize_to_record(
    raw_dict: Dict[str, Any],
    source_type: str,
    document_id: Optional[str] = None,
    filename: str = "",
    quality_score: float = 1.0,
    reader_name: str = "primary_reader"
) -> InvoiceRecord:
    """Normalizes raw dictionary into a complete InvoiceRecord."""
    doc_id = document_id or str(uuid.uuid4())
    
    # 1. Supplier and Buyer
    raw_sup = raw_dict.get("supplier", {})
    raw_buy = raw_dict.get("buyer", {})
    
    supplier = Supplier(
        name=raw_sup.get("name"),
        gstin=raw_sup.get("gstin"),
        state_code=raw_sup.get("state_code") or (raw_sup.get("gstin")[:2] if raw_sup.get("gstin") and len(raw_sup.get("gstin")) >= 2 else None),
        address=raw_sup.get("address")
    )
    
    buyer = Buyer(
        name=raw_buy.get("name"),
        gstin=raw_buy.get("gstin"),
        state_code=raw_buy.get("state_code") or (raw_buy.get("gstin")[:2] if raw_buy.get("gstin") and len(raw_buy.get("gstin")) >= 2 else None),
        address=raw_buy.get("address")
    )

    # 2. Line Items
    line_items: List[LineItem] = []
    raw_items = raw_dict.get("line_items", [])
    
    for idx, item_data in enumerate(raw_items, start=1):
        item = LineItem(
            item_index=idx,
            description=item_data.get("description", f"Item {idx}"),
            hsn_sac=item_data.get("hsn_sac"),
            qty=to_decimal(item_data.get("qty")),
            rate=to_decimal(item_data.get("rate")),
            discount=to_decimal(item_data.get("discount")) or Decimal("0.00"),
            taxable_value=to_decimal(item_data.get("taxable_value")),
            cgst_rate=to_decimal(item_data.get("cgst_rate")) or Decimal("0.00"),
            cgst_amt=to_decimal(item_data.get("cgst_amt")) or Decimal("0.00"),
            sgst_rate=to_decimal(item_data.get("sgst_rate")) or Decimal("0.00"),
            sgst_amt=to_decimal(item_data.get("sgst_amt")) or Decimal("0.00"),
            igst_rate=to_decimal(item_data.get("igst_rate")) or Decimal("0.00"),
            igst_amt=to_decimal(item_data.get("igst_amt")) or Decimal("0.00"),
            line_total=to_decimal(item_data.get("line_total"))
        )
        line_items.append(item)

    # 3. Totals
    raw_totals = raw_dict.get("totals", {})
    totals = Totals(
        taxable_amount=to_decimal(raw_totals.get("taxable_amount")),
        cgst_amount=to_decimal(raw_totals.get("cgst_amount")) or Decimal("0.00"),
        sgst_amount=to_decimal(raw_totals.get("sgst_amount")) or Decimal("0.00"),
        igst_amount=to_decimal(raw_totals.get("igst_amount")) or Decimal("0.00"),
        round_off=to_decimal(raw_totals.get("round_off")) or Decimal("0.00"),
        grand_total=to_decimal(raw_totals.get("grand_total")),
        amount_in_words=raw_totals.get("amount_in_words")
    )

    invoice = CanonicalInvoice(
        invoice_number=raw_dict.get("invoice_number"),
        invoice_date=raw_dict.get("invoice_date"),
        place_of_supply=raw_dict.get("place_of_supply") or supplier.state_code,
        supplier=supplier,
        buyer=buyer,
        line_items=line_items,
        totals=totals
    )

    # 4. Build FieldValue dictionary with Provenance and Tier
    fields: Dict[str, FieldValue] = {}
    
    def add_field(path: str, val: Any, tier: str, bbox: Optional[BBox] = None):
        val_str = str(val) if val is not None else None
        candidates = [Candidate(value=val_str or "", reader=reader_name)] if val_str else []
        fields[path] = FieldValue(
            path=path,
            value=val_str,
            tier=tier,
            confidence=0.95 if tier in ["A", "B"] and val_str else 0.70,
            provenance=Provenance.READ,
            bbox=bbox,
            candidates=candidates
        )

    # Header / Meta fields
    add_field("invoice_number", invoice.invoice_number, tier="B", bbox=BBox(page=1, x0=0.55, y0=0.18, x1=0.85, y1=0.23))
    add_field("invoice_date", invoice.invoice_date, tier="B", bbox=BBox(page=1, x0=0.55, y0=0.23, x1=0.85, y1=0.28))
    add_field("supplier.name", supplier.name, tier="C", bbox=BBox(page=1, x0=0.05, y0=0.05, x1=0.60, y1=0.12))
    add_field("supplier.gstin", supplier.gstin, tier="A", bbox=BBox(page=1, x0=0.05, y0=0.12, x1=0.45, y1=0.18))
    add_field("buyer.name", buyer.name, tier="C", bbox=BBox(page=1, x0=0.05, y0=0.20, x1=0.50, y1=0.26))
    add_field("buyer.gstin", buyer.gstin, tier="A", bbox=BBox(page=1, x0=0.05, y0=0.26, x1=0.45, y1=0.32))
    
    # Totals
    add_field("totals.taxable_amount", totals.taxable_amount, tier="A", bbox=BBox(page=1, x0=0.70, y0=0.78, x1=0.95, y1=0.82))
    add_field("totals.cgst_amount", totals.cgst_amount, tier="A", bbox=BBox(page=1, x0=0.70, y0=0.82, x1=0.95, y1=0.86))
    add_field("totals.sgst_amount", totals.sgst_amount, tier="A", bbox=BBox(page=1, x0=0.70, y0=0.86, x1=0.95, y1=0.90))
    add_field("totals.igst_amount", totals.igst_amount, tier="A", bbox=BBox(page=1, x0=0.70, y0=0.90, x1=0.95, y1=0.94))
    add_field("totals.grand_total", totals.grand_total, tier="A", bbox=BBox(page=1, x0=0.70, y0=0.94, x1=0.95, y1=0.98))
    add_field("totals.amount_in_words", totals.amount_in_words, tier="B", bbox=BBox(page=1, x0=0.05, y0=0.88, x1=0.65, y1=0.95))

    # Line item fields
    for i, li in enumerate(invoice.line_items):
        prefix = f"line_items[{i}]"
        add_field(f"{prefix}.qty", li.qty, tier="B")
        add_field(f"{prefix}.rate", li.rate, tier="B")
        add_field(f"{prefix}.taxable_value", li.taxable_value, tier="A")
        add_field(f"{prefix}.cgst_amt", li.cgst_amt, tier="A")
        add_field(f"{prefix}.sgst_amt", li.sgst_amt, tier="A")
        add_field(f"{prefix}.igst_amt", li.igst_amt, tier="A")
        add_field(f"{prefix}.line_total", li.line_total, tier="A")

    return InvoiceRecord(
        document_id=doc_id,
        filename=filename,
        source_type=source_type,
        status="verified",
        quality_score=quality_score,
        invoice=invoice,
        fields=fields
    )
