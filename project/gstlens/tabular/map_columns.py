"""
Tabular Pipeline: Column Mapping and Type Coercion.
Maps source spreadsheet column headers to canonical GST invoice fields.
"""
from typing import Dict, Any, List, Optional
import re
import pandas as pd
from rapidfuzz import fuzz, process

CANONICAL_SYNONYMS = {
    "invoice_number": ["inv no", "invoice no", "inv #", "bill no", "invoice number", "invoice_no"],
    "invoice_date": ["date", "inv date", "invoice date", "bill date", "dated", "bill dt"],
    "supplier_name": ["supplier", "seller", "vendor", "supplier name", "party name"],
    "supplier_gstin": ["supplier gstin", "seller gstin", "vendor gstin"],
    "buyer_name": ["buyer", "customer", "client", "billed to", "buyer name", "party"],
    "buyer_gstin": ["buyer gstin", "party gstin", "customer gstin", "gstin", "gst no", "party gst no"],
    "place_of_supply": ["place of supply", "pos", "state", "supply state"],
    "description": ["item", "description", "particulars", "item name", "product", "goods"],
    "hsn_sac": ["hsn", "sac", "hsn/sac", "hsn code", "tariff"],
    "qty": ["qty", "quantity", "nos", "pcs", "units"],
    "rate": ["rate", "price", "unit price", "rate/unit"],
    "discount": ["disc", "discount", "less disc"],
    "taxable_value": ["taxable", "taxable amt", "taxable amount", "taxable value", "basic amount"],
    "cgst_rate": ["cgst %", "cgst rate", "cgst_rate"],
    "cgst_amt": ["cgst", "cgst amt", "cgst amount", "central tax"],
    "sgst_rate": ["sgst %", "sgst rate", "sgst_rate"],
    "sgst_amt": ["sgst", "sgst amt", "sgst amount", "state tax", "utgst"],
    "igst_rate": ["igst %", "igst rate", "igst_rate"],
    "igst_amt": ["igst", "igst amt", "igst amount", "integrated tax"],
    "line_total": ["total", "total amt", "line total", "amount", "net amount"]
}

def map_column_name(col_name: str, sample_values: Optional[List[Any]] = None) -> Optional[str]:
    """Maps a column name to a canonical field using synonyms and value profiling."""
    clean = str(col_name).strip().lower()
    
    # 1. Exact or partial synonym matching
    best_field = None
    best_score = 0.0

    for field, synonyms in CANONICAL_SYNONYMS.items():
        for syn in synonyms:
            score = fuzz.ratio(clean, syn)
            if score > best_score and score >= 75:
                best_score = score
                best_field = field

    if best_field:
        return best_field

    # 2. Value profiling fallback
    if sample_values:
        str_samples = [str(v).strip() for v in sample_values if pd.notna(v) and str(v).strip()]
        if str_samples:
            # Check GSTIN pattern
            gstin_count = sum(1 for s in str_samples if re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", s.upper()))
            if gstin_count >= len(str_samples) * 0.5:
                return "buyer_gstin"

    return None

def clean_numeric_value(val: Any) -> Optional[float]:
    """Coerces strings like '₹ 5,400/-' or '(500)' into clean float."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).strip()
    # Strip currency symbols, commas, and trailing / -
    cleaned = re.sub(r"[₹$Rs.,\/\-\s]", "", val_str)
    try:
        return float(cleaned)
    except ValueError:
        return None
