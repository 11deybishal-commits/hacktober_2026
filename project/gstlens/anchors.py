"""
GSTLens Anchor Detector.
Fuzzy matching of printed invoice headers and labels to anchor handwritten and printed value cells.
"""
from typing import List, Dict, Tuple, Optional
try:
    from rapidfuzz import fuzz
except ImportError:
    import difflib
    class _FuzzFallback:
        @staticmethod
        def ratio(s1, s2):
            return difflib.SequenceMatcher(None, str(s1).lower(), str(s2).lower()).ratio() * 100
        @staticmethod
        def partial_ratio(s1, s2):
            s1, s2 = str(s1).lower(), str(s2).lower()
            if s1 in s2 or s2 in s1:
                return 100.0
            return difflib.SequenceMatcher(None, s1, s2).ratio() * 100
    fuzz = _FuzzFallback()

# Key anchor patterns
DEFAULT_ANCHORS = {
    "invoice_number": ["Invoice No", "Inv No", "Bill No", "Invoice #", "Cash Memo"],
    "invoice_date": ["Invoice Date", "Date", "Dated", "Bill Date"],
    "supplier_gstin": ["GSTIN", "GST No", "GSTIN / UIN", "Supplier GSTIN"],
    "buyer_gstin": ["Party GST", "Buyer GSTIN", "Customer GST", "Consignee GSTIN"],
    "supplier_name": ["M/s", "Messrs", "Supplier", "Sold By"],
    "buyer_name": ["Buyer", "Billed To", "Customer", "M/s"],
    "taxable_amount": ["Taxable Value", "Taxable Amount", "Taxable Amt", "Sub Total", "Total Taxable"],
    "cgst_amount": ["CGST", "Central Tax", "CGST Amount", "CGST @"],
    "sgst_amount": ["SGST", "State Tax", "SGST Amount", "SGST @", "UTGST"],
    "igst_amount": ["IGST", "Integrated Tax", "IGST Amount", "IGST @"],
    "grand_total": ["Grand Total", "Total Amount", "Net Payable", "Total Invoice Value", "Net Total"],
    "amount_in_words": ["Amount in Words", "Rupees in Words", "Total in Words"]
}

def match_anchor(text: str, score_cutoff: float = 75.0) -> Optional[str]:
    """
    Checks if a detected text string matches any known GST invoice anchor.
    Returns the canonical anchor field name or None.
    """
    if not text or len(text.strip()) < 2:
        return None
        
    cleaned = text.strip()
    best_field = None
    best_score = 0.0
    
    for field, synonyms in DEFAULT_ANCHORS.items():
        for syn in synonyms:
            score = fuzz.partial_ratio(syn.lower(), cleaned.lower())
            if score > best_score and score >= score_cutoff:
                best_score = score
                best_field = field
                
    return best_field
