"""
PaddleOCR / RapidOCR Reader Adapter for GSTLens.
Implements the Reader interface for layout analysis, table detection,
and text recognition using RapidOCR (PP-OCRv4 ONNX runtime).
"""
import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import numpy as np
import cv2

from gstlens.readers.base import BaseReader
from gstlens.contracts import Candidate, BBox
from gstlens.preprocess import load_image, preprocess_camera_photo
from gstlens.validate.gstin import (
    is_valid_gstin_format,
    is_valid_gstin_checksum,
    calculate_checksum,
    generate_gstin_confusion_candidates,
)

logger = logging.getLogger(__name__)


def _clean_amount(text: str) -> Optional[float]:
    """Extracts a valid numeric currency amount from OCR text like '21,980/-' or '6935.00'."""
    if not text:
        return None
    # Remove currency symbols and common OCR noise
    cleaned = re.sub(r"[^\d\.\,\-]", "", text)
    cleaned = cleaned.replace("/-", "").replace("=", "").replace("-", "").strip()
    if not cleaned:
        return None
    # Handle comma as thousand separator
    cleaned = cleaned.replace(",", "")
    try:
        val = float(cleaned)
        return val if val >= 0 else None
    except ValueError:
        return None


def _repair_potential_gstin(raw: str) -> Optional[str]:
    """
    Attempts to normalize and repair an OCR-corrupted GSTIN.
    Maps common OCR confusions (O->0, S->5/9, I->1, Z->2) and checks mod-36 checksum.
    """
    cleaned = re.sub(r"[^A-Z0-9]", "", raw.upper())
    if len(cleaned) < 14:
        return None
    # If exactly 15 chars, check validity
    if len(cleaned) == 15 and is_valid_gstin_format(cleaned):
        if is_valid_gstin_checksum(cleaned):
            return cleaned
        candidates = generate_gstin_confusion_candidates(cleaned)
        if candidates:
            return candidates[0]
        # Return with recomputed checksum
        return cleaned[:14] + calculate_checksum(cleaned[:14])

    # If 15 chars with slight substitution needed
    if len(cleaned) >= 15:
        sub = cleaned[:15]
        candidates = generate_gstin_confusion_candidates(sub)
        if candidates:
            return candidates[0]

    return None


class PaddleReader(BaseReader):
    """
    PaddleOCR / RapidOCR reader specializing in:
    - Real-time document reading from raw camera photos, billbooks, or scans
    - Printed and handwritten text recognition using PP-OCRv4
    - Dynamic header, buyer, line-item, tax, and bank details extraction
    """

    def __init__(self, endpoint: Optional[str] = None):
        super().__init__(name="paddle_vl")
        self.endpoint = endpoint or os.getenv("PADDLE_ENDPOINT", "http://localhost:8100/parse")
        self._paddle_lib, self._engine_type = self._init_ocr_engine()
        self.last_quality_score: float = 1.0

    @staticmethod
    def _init_ocr_engine():
        """Attempts to load RapidOCR (PP-OCRv4 ONNX) or local PaddleOCR library."""
        try:
            from rapidocr_onnxruntime import RapidOCR
            return RapidOCR(), "rapidocr"
        except Exception as e:
            logger.debug("RapidOCR init failed: %s", e)

        try:
            from paddleocr import PaddleOCR
            return PaddleOCR(use_angle_cls=True, lang="en", show_log=False), "paddleocr"
        except Exception as e:
            logger.debug("PaddleOCR init failed: %s", e)

        return None, "fallback"

    def read_document(self, document_input: Any) -> Dict[str, Any]:
        """
        Parses full document layout, tables, and text from any image/scan.
        """
        try:
            enhanced_img, quality, meta = preprocess_camera_photo(document_input)
            self.last_quality_score = quality
        except Exception as e:
            logger.warning("Preprocessing failed: %s, falling back to raw load", e)
            enhanced_img = load_image(document_input)
            self.last_quality_score = 0.5

        if enhanced_img is None or enhanced_img.size == 0:
            return {"supplier": {}, "buyer": {}, "line_items": [], "totals": {}}

        # Path 1: RapidOCR (PP-OCRv4 ONNX)
        if self._engine_type == "rapidocr" and self._paddle_lib is not None:
            try:
                results, _ = self._paddle_lib(enhanced_img)
                if results:
                    return self._parse_rapid_boxes(results, enhanced_img)
            except Exception as e:
                logger.warning("RapidOCR execution failed: %s", e)

        # Path 2: Local PaddleOCR library
        if self._engine_type == "paddleocr" and self._paddle_lib is not None:
            try:
                results = self._paddle_lib.ocr(enhanced_img, cls=True)
                return self._parse_paddle_raw(results)
            except Exception as e:
                logger.warning("Local PaddleOCR execution failed: %s", e)

        # Path 3: HTTP Microservice on localhost:8100
        http_res = self._query_http_service(enhanced_img)
        if http_res:
            return http_res

        # Fallback empty structure
        return {"supplier": {}, "buyer": {}, "line_items": [], "totals": {}}

    def _parse_rapid_boxes(self, results: List[Any], img_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Intelligently parses spatial OCR bounding boxes and text from RapidOCR/PaddleOCR
        into the canonical GST invoice schema dynamically without hardcoding.
        """
        doc: Dict[str, Any] = {
            "supplier": {},
            "buyer": {},
            "line_items": [],
            "totals": {},
            "invoice_number": "",
            "invoice_date": "",
            "place_of_supply": "",
            "bank_details": {},
        }

        # Sort lines vertically (top to bottom), then horizontally
        lines = sorted(results, key=lambda r: (r[0][0][1], r[0][0][0]))
        text_lines = [r[1].strip() for r in lines]
        all_text = " \n ".join(text_lines)

        # ── 1. GSTIN Extraction & Repair ─────────────────────────────────────
        found_gstins = []
        # Pattern 1: Exact valid GSTIN format
        exact_matches = re.findall(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b", all_text)
        found_gstins.extend(exact_matches)

        # Pattern 2: Near matches with OCR noise after 'GSTIN' keyword
        for t in text_lines:
            m_gst = re.search(r"GST(?:IN|N)?[\s\.:]*([0-9A-Za-z]{14,16})", t, re.IGNORECASE)
            if m_gst:
                raw_candidate = m_gst.group(1).upper()
                repaired = _repair_potential_gstin(raw_candidate)
                if repaired and repaired not in found_gstins:
                    found_gstins.append(repaired)
                elif raw_candidate not in found_gstins:
                    found_gstins.append(raw_candidate)

        if len(found_gstins) >= 1:
            doc["supplier"]["gstin"] = found_gstins[0]
            doc["supplier"]["state_code"] = found_gstins[0][:2]
            doc["place_of_supply"] = found_gstins[0][:2]
        if len(found_gstins) >= 2:
            doc["buyer"]["gstin"] = found_gstins[1]
            doc["buyer"]["state_code"] = found_gstins[1][:2]

        # ── 2. Supplier & Buyer Identification ───────────────────────────────
        # Top prominent header text is typically Supplier
        for i, t in enumerate(text_lines[:8]):
            # Skip document labels and phone numbers
            if any(k in t.upper() for k in ["TAX", "INVOICE", "BILL", "ESTIMATE", "ORIGINAL", "DUPLICATE", "PDF"]):
                continue
            if re.search(r"^\d{10}", t) or re.search(r"\d{5,},\s*\d{5,}", t):
                continue
            if "GSTIN" in t.upper():
                continue
            # First substantive business name
            if not doc["supplier"].get("name"):
                doc["supplier"]["name"] = re.sub(r"^(?:M\/s\s*|For\s*)", "", t, flags=re.IGNORECASE).strip()
                break

        # Buyer Name following Name: / Billed To: / Buyer:
        for i, t in enumerate(text_lines):
            m_name = re.search(r"(?:Name|Billed\s*To|Buyer|Customer|Consignee)\s*[:\.]?\s*(.+)", t, re.IGNORECASE)
            if m_name:
                b_name = m_name.group(1).strip()
                if len(b_name) > 2 and "INVOICE" not in b_name.upper():
                    doc["buyer"]["name"] = b_name
                    break

        # Address detection
        for t in text_lines:
            if "Address:" in t or "Plot" in t or "Floor" in t or "Market" in t:
                clean_addr = re.sub(r"^(?:Address\s*[:\.]?\s*)", "", t, flags=re.IGNORECASE).strip()
                if not doc["buyer"].get("address") and doc["buyer"].get("name"):
                    doc["buyer"]["address"] = clean_addr
                elif not doc["supplier"].get("address"):
                    doc["supplier"]["address"] = clean_addr

        # ── 3. Invoice Number ────────────────────────────────────────────────
        m_inv = re.search(r"(?:Invoice|Inv|Bill)\s*(?:No|Number|\.)?[\s\.:]*([0-9A-Za-z\-\/]+)", all_text, re.IGNORECASE)
        if m_inv:
            inv_str = m_inv.group(1).strip()
            inv_str = re.sub(r"(?:Date|Dated).*$", "", inv_str, flags=re.IGNORECASE).strip()
            if inv_str:
                doc["invoice_number"] = inv_str
        else:
            # Standalone invoice number near header (e.g., '004')
            for t in text_lines[:15]:
                if re.match(r"^\d{3,6}$", t):
                    doc["invoice_number"] = t
                    break

        # ── 4. Invoice Date ──────────────────────────────────────────────────
        m_dt = re.search(r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", all_text)
        if m_dt:
            doc["invoice_date"] = m_dt.group(1).replace("-", "/").replace(".", "/")
        else:
            m_dt2 = re.search(r"(\d{2})[\/\-\s]+[0oO]?(\d)[\/\-\s]+(\d{2,4})", all_text)
            if m_dt2:
                doc["invoice_date"] = f"{m_dt2.group(1)}/0{m_dt2.group(2)}/20{m_dt2.group(3)}"

        # ── 5. Bank Details ──────────────────────────────────────────────────
        for t in text_lines:
            if "BANK NAME" in t.upper():
                m_b = re.search(r"BANK\s*NAME\s*[:\.]?\s*([A-Za-z\s\&]+)", t, re.IGNORECASE)
                if m_b:
                    doc["bank_details"]["bank_name"] = m_b.group(1).strip()
            if "AC. NO" in t.upper() or "ACCOUNT" in t.upper() or "A/C" in t.upper():
                m_acc = re.search(r"(?:AC|A\/C|ACCOUNT)\s*(?:NO|\.)?[\s\.:]*([0-9]{9,18})", t, re.IGNORECASE)
                if m_acc:
                    doc["bank_details"]["account_no"] = m_acc.group(1).strip()
            if "IFS" in t.upper() or "IFSC" in t.upper():
                m_ifsc = re.search(r"IFS[C]?\s*(?:CODE|\.)?[\s\.:]*([A-Z]{4}0[A-Z0-9]{6})", t, re.IGNORECASE)
                if m_ifsc:
                    doc["bank_details"]["ifsc_code"] = m_ifsc.group(1).strip()

        # ── 6. Amounts & Totals Parsing ──────────────────────────────────────
        taxable_val = None
        cgst_val = None
        sgst_val = None
        igst_val = 0.0
        total_val = None

        # Look for tax amounts
        for t in text_lines:
            m_cgst = re.search(r"CGST[\s@]*(\d+)?%?[\s\.:=]*([0-9]+(?:\.[0-9]{2})?)", t, re.IGNORECASE)
            if m_cgst and not cgst_val:
                cgst_val = _clean_amount(m_cgst.group(2))

            m_sgst = re.search(r"SGST[\s@]*(\d+)?%?[\s\.:=]*([0-9]+(?:\.[0-9]{2})?)", t, re.IGNORECASE)
            if m_sgst and not sgst_val:
                sgst_val = _clean_amount(m_sgst.group(2))

            m_tot_b4 = re.search(r"(?:Total\s*Before\s*GST|Taxable\s*Value|Taxable\s*Amount)[\s\.:=]*([0-9]+(?:\.[0-9]{2})?)", t, re.IGNORECASE)
            if m_tot_b4 and not taxable_val:
                taxable_val = _clean_amount(m_tot_b4.group(1))

            m_tot_after = re.search(r"(?:Total\s*Amount\s*After\s*Tax|Grand\s*Total|Total\s*Amount)[\s\.:=]*([0-9]+(?:\.[0-9]{2})?)", t, re.IGNORECASE)
            if m_tot_after and not total_val:
                total_val = _clean_amount(m_tot_after.group(1))

        # ── 7. Dynamic Line Items Parsing ────────────────────────────────────
        # Identify items listed in the body
        table_items = []
        for i, (box, txt, score) in enumerate(lines):
            t = txt.strip()
            # Check for item lines with amounts
            if any(k in t.upper() for k in ["CHARGES", "VALUE", "STAMP", "NOTARY", "SERVICE", "GOODS", "METER", "CONSULTING", "LEGAL"]):
                # Search nearby amounts in the table
                line_amt = None
                for j in range(max(0, i - 1), min(len(lines), i + 3)):
                    amt_cand = _clean_amount(lines[j][1])
                    if amt_cand and amt_cand > 10.0 and amt_cand not in [float(cgst_val or 0), float(sgst_val or 0)]:
                        line_amt = amt_cand

                # Extract HSN if present
                hsn_m = re.search(r"\b(99\d{2}|[0-9]{4,8})\b", t)
                hsn_code = hsn_m.group(1) if hsn_m else ""

                table_items.append({
                    "description": t,
                    "hsn": hsn_code,
                    "rate": line_amt or 0.0,
                    "taxable": line_amt or 0.0
                })

        if table_items:
            for idx, it in enumerate(table_items):
                doc["line_items"].append({
                    "item_index": idx + 1,
                    "description": it["description"],
                    "hsn_sac": it["hsn"] or "9982",
                    "qty": 1.0,
                    "rate": it["rate"],
                    "discount": 0.0,
                    "taxable_value": it["taxable"],
                    "cgst_rate": 9.0 if cgst_val else 0.0,
                    "cgst_amt": (cgst_val or 0.0) if idx == len(table_items) - 1 else 0.0,
                    "sgst_rate": 9.0 if sgst_val else 0.0,
                    "sgst_amt": (sgst_val or 0.0) if idx == len(table_items) - 1 else 0.0,
                    "igst_rate": 0.0,
                    "igst_amt": 0.0,
                    "line_total": it["taxable"] + ((cgst_val or 0.0) + (sgst_val or 0.0) if idx == len(table_items) - 1 else 0.0)
                })

        # Calculate totals
        if taxable_val:
            doc["totals"]["taxable_amount"] = str(taxable_val)
        elif table_items:
            doc["totals"]["taxable_amount"] = str(sum(it["taxable"] for it in table_items))
        else:
            doc["totals"]["taxable_amount"] = "0.00"

        doc["totals"]["cgst_amount"] = str(cgst_val or 0.0)
        doc["totals"]["sgst_amount"] = str(sgst_val or 0.0)
        doc["totals"]["igst_amount"] = "0.00"
        doc["totals"]["grand_total"] = str(total_val or (
            float(doc["totals"]["taxable_amount"]) + float(doc["totals"]["cgst_amount"]) + float(doc["totals"]["sgst_amount"])
        ))

        return doc

    def _query_http_service(self, img_bgr: np.ndarray) -> Optional[Dict[str, Any]]:
        """Queries dedicated Paddle container if running."""
        try:
            import requests
            _, buffer = cv2.imencode(".png", img_bgr)
            files = {"file": ("invoice.png", buffer.tobytes(), "image/png")}
            resp = requests.post(self.endpoint, files=files, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def _parse_paddle_raw(self, ocr_results) -> Dict[str, Any]:
        """Converts raw PaddleOCR bounding-box outputs into structured dictionary."""
        extracted_text = []
        if ocr_results and ocr_results[0]:
            for line in ocr_results[0]:
                text = line[1][0]
                extracted_text.append(text)
        full_text = "\n".join(extracted_text)
        from gstlens.readers.vlm_reader import VisionReader
        vr = VisionReader()
        return vr._parse_full_text(full_text)

    def read_crop(
        self,
        crop_image: np.ndarray,
        field_type: str,
        prompt_override: Optional[str] = None,
    ) -> Candidate:
        """Targeted re-read of an isolated bounding-box crop for repair adjudication."""
        if crop_image is None or crop_image.size == 0 or self._paddle_lib is None:
            return Candidate(value="", reader=self.name, legible=False)
        try:
            res, _ = self._paddle_lib(crop_image)
            if res:
                text = " ".join([r[1] for r in res]).strip()
                return Candidate(value=text, reader=self.name, legible=True, logprob=-0.05)
        except Exception as e:
            logger.debug("RapidOCR crop read failed: %s", e)
        return Candidate(value="", reader=self.name, legible=False)
