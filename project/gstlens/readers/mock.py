"""
GSTLens Offline Deterministic Mock Reader.
Provides reproducible readings and simulates realistic OCR/handwriting error scenarios
(such as '5,400' misread as '5,490' or GSTIN 'Z' misread as '2') for end-to-end testing,
validation benchmarking, and zero-dependency offline demos.
"""
from typing import Dict, Any, List, Optional
import numpy as np
from gstlens.readers.base import BaseReader
from gstlens.contracts import Candidate, BBox

class MockReader(BaseReader):
    def __init__(self, mode: str = "misread_taxable"):
        """
        Modes:
        - 'perfect': all fields clean and passing
        - 'misread_taxable': line 1 taxable is 5,490 instead of 5,400 (triggers arithmetic repair)
        - 'gstin_confusion': GSTIN character 'Z' is read as '2' (triggers mod-36 checksum repair)
        """
        super().__init__(name="mock_paddle_vl")
        self.mode = mode

    def read_document(self, document_input: Any) -> Dict[str, Any]:
        """Returns structured raw reading based on scenario mode."""
        line1_taxable = "5490.00" if self.mode == "misread_taxable" else "5400.00"
        supplier_gstin = "27ABCPD0234F12E" if self.mode == "gstin_confusion" else "27ABCPD0234F1ZE"

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
                "gstin": "27XYZPQ5678K1ZF",
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
                    "cgst_amt": "486.00",
                    "sgst_rate": "9.00",
                    "sgst_amt": "486.00",
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
        Simulates second-reader (Qwen-VL) re-reading a crop.
        When re-reading line1 taxable with digit-only prompt, the second reader discovers '5400'.
        When re-reading GSTIN with mod-36 confusion prompt, it confirms '27ABCPD0234F1ZE'.
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
                value="27ABCPD0234F1ZE",
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
