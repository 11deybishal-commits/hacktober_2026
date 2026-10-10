"""
Digital PDF Text-Layer Reader.
Extracts structured text directly from PDF text-stream without running OCR.
"""
from typing import Dict, Any, List, Optional
import os
import re
from decimal import Decimal
import numpy as np

from gstlens.readers.base import BaseReader
from gstlens.contracts import Candidate, BBox

class DigitalPdfReader(BaseReader):
    def __init__(self):
        super().__init__(name="pdf_text_layer")

    def read_document(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts text and table rows directly from PDF pages."""
        text = ""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text() + "\n"
        except Exception:
            try:
                import pypdf
                reader = pypdf.PdfReader(pdf_path)
                for page in reader.pages:
                    text += (page.extract_text() or "") + "\n"
            except Exception:
                text = ""

        return self._parse_pdf_text(text)

    def read_crop(self, crop_image: np.ndarray, field_type: str, prompt_override: Optional[str] = None) -> Candidate:
        return Candidate(
            value="",
            reader=self.name,
            legible=False
        )

    def _parse_pdf_text(self, text: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "supplier": {},
            "buyer": {},
            "line_items": [],
            "totals": {}
        }
        
        # 1. GSTIN Regex Extraction: 2 digits + 5 chars + 4 digits + 1 char + 1 char + 'Z' + 1 char
        gstin_matches = re.findall(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text)
        if len(gstin_matches) >= 1:
            result["supplier"]["gstin"] = gstin_matches[0]
            result["supplier"]["state_code"] = gstin_matches[0][:2]
        if len(gstin_matches) >= 2:
            result["buyer"]["gstin"] = gstin_matches[1]
            result["buyer"]["state_code"] = gstin_matches[1][:2]

        # 2. Invoice Number
        inv_no_match = re.search(r"(?:Invoice\s*(?:No|Number|#)|Inv\s*No|Bill\s*No)[:\s]*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
        if inv_no_match:
            result["invoice_number"] = inv_no_match.group(1).strip()

        # 3. Invoice Date
        inv_date_match = re.search(r"(?:Invoice\s*Date|Date|Dated)[:\s]*([0-9]{2}[\/\-\.][0-9]{2}[\/\-\.][0-9]{2,4}|[0-9]{4}[\/\-\.][0-9]{2}[\/\-\.][0-9]{2})", text, re.IGNORECASE)
        if inv_date_match:
            result["invoice_date"] = inv_date_match.group(1).strip()

        # 4. Supplier & Buyer Names
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for i, line in enumerate(lines[:15]):
            if any(k in line.lower() for k in ["ltd", "pvt", "enterprises", "traders", "services", "corporation", "industries", "m/s"]):
                if not result["supplier"].get("name"):
                    result["supplier"]["name"] = line
                    break

        for i, line in enumerate(lines):
            if any(k in line.lower() for k in ["billed to", "buyer", "customer", "consignee"]) and i + 1 < len(lines):
                result["buyer"]["name"] = lines[i + 1]
                break

        # 5. Totals
        grand_total_match = re.search(r"(?:Grand\s*Total|Total\s*Amount|Net\s*Payable|Invoice\s*Total)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)", text, re.IGNORECASE)
        if grand_total_match:
            val_str = grand_total_match.group(1).replace(",", "")
            result["totals"]["grand_total"] = val_str

        taxable_match = re.search(r"(?:Total\s*Taxable|Taxable\s*Amount|Taxable\s*Value|Sub\s*Total)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)", text, re.IGNORECASE)
        if taxable_match:
            val_str = taxable_match.group(1).replace(",", "")
            result["totals"]["taxable_amount"] = val_str

        cgst_match = re.search(r"(?:CGST|Central\s*Tax)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)", text, re.IGNORECASE)
        if cgst_match:
            result["totals"]["cgst_amount"] = cgst_match.group(1).replace(",", "")

        sgst_match = re.search(r"(?:SGST|State\s*Tax)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)", text, re.IGNORECASE)
        if sgst_match:
            result["totals"]["sgst_amount"] = sgst_match.group(1).replace(",", "")

        igst_match = re.search(r"(?:IGST|Integrated\s*Tax)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)", text, re.IGNORECASE)
        if igst_match:
            result["totals"]["igst_amount"] = igst_match.group(1).replace(",", "")

        return result
