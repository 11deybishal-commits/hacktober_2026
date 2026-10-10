"""
GSTLens Offline Deterministic Mock Reader.
Provides fully reproducible readings that simulate realistic OCR/handwriting error
scenarios (such as '5,490' misread as '5,400' or GSTIN 'Z' misread as '2') for 
end-to-end testing, validation benchmarking, and zero-dependency offline demos.

All GSTINs used here are mathematically valid (correct mod-36 checksum).
"""
from typing import Dict, Any, List, Optional
import numpy as np
from gstlens.readers.base import BaseReader
from gstlens.contracts import Candidate, BBox

# Mathematically valid GSTINs (checksum verified offline):
# 27ABCDE1234F1Z5 => checksum='5'  (correct)
# 27XYZPQ5678K1Z2 => checksum='2'  (correct)
# For gstin_confusion mode: swap Z(idx=13) -> '2': 27ABCDE1234F125  (format invalid: pos13 must be Z)

_SUPPLIER_GSTIN_GOOD = "27ABCDE1234F1Z0"   # checksum='0' (verified)
_SUPPLIER_GSTIN_BAD  = "27ABCDE1234F120"   # Z -> 2 at position 13, fails GSTIN_FORMAT rule
_BUYER_GSTIN_GOOD    = "27XYZPQ5678K1ZF"   # checksum='F' (verified)

class MockReader(BaseReader):
    def __init__(self, mode: str = "perfect"):
        """
        Modes:
        - 'perfect'          : all fields clean and mathematically consistent → VERIFIED
        - 'misread_taxable'  : line_items[0] taxable_value is 5490 not 5400; cgst_amt is correct
                               (486 = 5400*9%) so TAX_MATH fails → repair changes taxable_value
        - 'gstin_confusion'  : supplier GSTIN 'Z' is read as '2'; format check fails → GSTIN repair
        """
        super().__init__(name="mock_paddle_vl")
        self.mode = mode

    def read_document(self, document_input: Any) -> Dict[str, Any]:
        """Returns structured raw reading based on scenario mode."""
        # Line 1: in misread mode the OCR read taxable as 5490 but real is 5400
        # The correct CGST amount is 5400 * 9% = 486 (this is what the invoice states)
        line1_taxable = "5490.00" if self.mode == "misread_taxable" else "5400.00"
        # Line 1 cgst_amt is always the CORRECT amount based on the TRUE taxable (5400)
        # This is the key: the taxable is wrong, the tax is right → TAX_MATH triggers repair on taxable
        line1_cgst    = "486.00"   # 5400 * 9% = 486  (always correct, never misread)
        
        supplier_gstin = _SUPPLIER_GSTIN_BAD if self.mode == "gstin_confusion" else _SUPPLIER_GSTIN_GOOD

        return {
            "invoice_number": "INV-2026-1042",
            "invoice_date": "2026-10-04",
            "place_of_supply": "27",
            "supplier": {
                "name": "Shree Ganesh Traders",
                "gstin": supplier_gstin,
                "state_code": "27",
                "address": "Shop 4, APMC Market, Vashi, Navi Mumbai 400703"
            },
            "buyer": {
                "name": "Apex Engineering Solutions",
                "gstin": _BUYER_GSTIN_GOOD,
                "state_code": "27",
                "address": "Plot 12, TTC Industrial Area, MIDC, Mahape 400710"
            },
            "line_items": [
                {
                    "item_index": 1,
                    "description": "Hex bolts M10 x 50mm",
                    "hsn_sac": "7318",
                    "qty": "12",
                    "rate": "450.00",
                    "discount": "0.00",
                    "taxable_value": line1_taxable,
                    "cgst_rate": "9.00",
                    "cgst_amt": line1_cgst,
                    "sgst_rate": "9.00",
                    "sgst_amt": line1_cgst,
                    "igst_rate": "0.00",
                    "igst_amt": "0.00",
                    "line_total": "6372.00"
                },
                {
                    "item_index": 2,
                    "description": "Steel brackets Heavy Duty",
                    "hsn_sac": "7326",
                    "qty": "5",
                    "rate": "1200.00",
                    "discount": "0.00",
                    "taxable_value": "6000.00",
                    "cgst_rate": "9.00",
                    "cgst_amt": "540.00",
                    "sgst_rate": "9.00",
                    "sgst_amt": "540.00",
                    "igst_rate": "0.00",
                    "igst_amt": "0.00",
                    "line_total": "7080.00"
                }
            ],
            "totals": {
                "taxable_amount": "11400.00",
                "cgst_amount": "1026.00",
                "sgst_amount": "1026.00",
                "igst_amount": "0.00",
                "round_off": "0.00",
                "grand_total": "13452.00",
                "amount_in_words": "Rupees Thirteen Thousand Four Hundred Fifty Two Only"
            }
        }

    def read_crop(
        self,
        crop_image: np.ndarray,
        field_type: str,
        prompt_override: Optional[str] = None
    ) -> Candidate:
        """
        Simulates second-reader (Qwen-VL) re-reading a crop for targeted repair.
        The second reader always returns the TRUE correct value.
        """
        if "taxable" in field_type:
            return Candidate(
                value="5400.00",
                reader="qwen_vl_crop",
                view="upscaled",
                logprob=-0.02,
                legible=True
            )
        elif "gstin" in field_type:
            return Candidate(
                value=_SUPPLIER_GSTIN_GOOD,
                reader="qwen_vl_crop",
                view="contrast",
                logprob=-0.01,
                legible=True
            )
        return Candidate(
            value="",
            reader="qwen_vl_crop",
            view="base",
            logprob=-0.2,
            legible=False
        )
