"""
Structuring: Free Text Parser.
Parses non-tabular header and metadata blocks for supplier/buyer details.
"""
from typing import Dict, Any
import re

def parse_header_text(text: str) -> Dict[str, Any]:
    """Parses text chunks from Header and Metadata zones."""
    result: Dict[str, Any] = {
        "supplier": {},
        "buyer": {}
    }
    
    # 1. GSTIN Regex Extraction
    gstins = re.findall(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text)
    if len(gstins) >= 1:
        result["supplier"]["gstin"] = gstins[0]
        result["supplier"]["state_code"] = gstins[0][:2]
    if len(gstins) >= 2:
        result["buyer"]["gstin"] = gstins[1]
        result["buyer"]["state_code"] = gstins[1][:2]

    # 2. Invoice Number
    inv_no_match = re.search(r"(?:Invoice\s*(?:No|Number|#)|Inv\s*No|Bill\s*No)[:\s]*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    if inv_no_match:
        result["invoice_number"] = inv_no_match.group(1).strip()

    # 3. Invoice Date
    inv_date_match = re.search(r"(?:Invoice\s*Date|Date|Dated)[:\s]*([0-9]{2}[\/\-\.][0-9]{2}[\/\-\.][0-9]{2,4}|[0-9]{4}[\/\-\.][0-9]{2}[\/\-\.][0-9]{2})", text, re.IGNORECASE)
    if inv_date_match:
        result["invoice_date"] = inv_date_match.group(1).strip()

    return result
