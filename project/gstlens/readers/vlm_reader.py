"""
Vision-Language / OCR Reader for Camera Photos, Scans, and Handwritten Bill-Books.
Supports:
  - Hugging Face Multimodal VLM (Qwen2-VL / Qwen2.5-VL) via Serverless Inference API
  - Local Tesseract OCR / OpenCV parsing
  - Crop-level re-reading for targeted constraint adjudication
  - Automatic fallback for offline testing
"""
import os
import re
import json
import base64
import logging
from typing import Dict, Any, List, Optional

import numpy as np
import cv2
from PIL import Image
from dotenv import load_dotenv

from gstlens.readers.base import BaseReader
from gstlens.contracts import Candidate, BBox
from gstlens.preprocess import preprocess_camera_photo, extract_field_crop

# Load environment variables from all possible locations
load_dotenv()
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, "..", ".."))
load_dotenv(os.path.join(_project_root, ".env"))
load_dotenv(os.path.join(_project_root, "backend", ".env"))
load_dotenv(os.path.join(_project_root, "..", "backend", ".env"))

logger = logging.getLogger(__name__)


def _ndarray_to_base64_png(img: np.ndarray) -> str:
    """Encodes a NumPy BGR image to base64 PNG string."""
    _, buffer = cv2.imencode(".png", img)
    return base64.b64encode(buffer).decode("utf-8")


class VisionReader(BaseReader):
    """
    Advanced Multimodal Vision Reader for GST Invoices.
    Handles raw phone camera photos, deskews, unwarps perspective,
    extracts structured fields via VLM / OCR, and provides cell crops for repair.
    """

    def __init__(self, name: str = "vlm_paddle"):
        super().__init__(name=name)
        self.hf_token = self._resolve_hf_token()
        self._tesseract_available = self._check_tesseract()
        self.last_quality_score: float = 1.0

    @staticmethod
    def _resolve_hf_token() -> str:
        token = os.getenv("HF_TOKEN", "").strip()
        # Clean quotes if present
        if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
            token = token[1:-1].strip()
        return token if token and token != "your_hugging_face_token_here" else ""

    @staticmethod
    def _check_tesseract() -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def read_document(self, image_input: Any) -> Dict[str, Any]:
        """
        Full invoice extraction for camera photos or scans.
        1. Camera preprocessing (EXIF, 4-corner perspective unwarp, CLAHE de-shadow)
        2. Quality score computation
        3. Multimodal VLM extraction (if HF_TOKEN is valid)
        4. Local OCR extraction (if Tesseract available)
        5. Returns canonical structured dictionary
        """
        try:
            enhanced_img, quality, meta = preprocess_camera_photo(image_input)
            self.last_quality_score = quality
        except Exception as e:
            logger.warning("Preprocessing failed: %s, falling back to raw load", e)
            enhanced_img = None
            self.last_quality_score = 0.5

        if enhanced_img is None or enhanced_img.size == 0:
            return self._empty_result()

        # ── Path 1: Multimodal VLM via Hugging Face Serverless API ───────────
        if self.hf_token and len(self.hf_token) > 15:
            logger.info("Querying Qwen2-VL via Hugging Face API for invoice document...")
            vlm_dict = self._query_qwen_vl_full_page(enhanced_img)
            if vlm_dict and (vlm_dict.get("invoice_number") or vlm_dict.get("supplier", {}).get("gstin") or vlm_dict.get("totals", {}).get("grand_total")):
                logger.info("Qwen2-VL successfully parsed camera invoice")
                return vlm_dict

        # ── Path 2: Local OCR Extraction ─────────────────────────────────────
        if self._tesseract_available:
            logger.info("Extracting text via local Tesseract OCR...")
            text = self._extract_full_text(enhanced_img)
            parsed_dict = self._parse_full_text(text)
            if parsed_dict and (parsed_dict.get("supplier", {}).get("gstin") or parsed_dict.get("totals", {}).get("grand_total")):
                return parsed_dict

        # If no active OCR returned data, return empty dict so downstream router handles fallback
        return self._empty_result()

    def read_crop(
        self,
        crop_image: np.ndarray,
        field_type: str,
        prompt_override: Optional[str] = None,
    ) -> Candidate:
        """
        Targeted re-read of an isolated bounding-box crop for repair adjudication.
        """
        if crop_image is None or crop_image.size == 0:
            return Candidate(value="", reader=self.name, legible=False)

        # ── Path 1: Qwen2-VL via HF Serverless API ───────────────────────────
        if self.hf_token and len(self.hf_token) > 15:
            vlm_result = self._query_qwen_vl_crop(crop_image, field_type, prompt_override)
            if vlm_result:
                cleaned = self._clean_value(vlm_result, field_type)
                return Candidate(
                    value=cleaned,
                    reader=f"{self.name}_hf_qwen2vl",
                    view="crop",
                    logprob=-0.02,
                    legible=bool(cleaned),
                )

        # ── Path 2: Local OCR ────────────────────────────────────────────────
        if self._tesseract_available:
            raw_text = self._extract_full_text(crop_image)
            cleaned = self._clean_value(raw_text, field_type)
            return Candidate(
                value=cleaned,
                reader=f"{self.name}_tesseract",
                view="crop",
                logprob=-0.15,
                legible=len(cleaned) > 0,
            )

        return Candidate(value="", reader=self.name, legible=False)

    # ── Internal VLM Helpers ─────────────────────────────────────────────────

    def _query_qwen_vl_full_page(self, img_bgr: np.ndarray) -> Optional[Dict[str, Any]]:
        """Queries Qwen2-VL for full-page Indian GST invoice structured JSON."""
        try:
            import requests

            # Resize if very large for fast inference (< 1200 px)
            h, w = img_bgr.shape[:2]
            if max(h, w) > 1200:
                scale = 1200.0 / max(h, w)
                img_to_send = cv2.resize(img_bgr, (0, 0), fx=scale, fy=scale)
            else:
                img_to_send = img_bgr

            b64 = _ndarray_to_base64_png(img_to_send)
            prompt = (
                "You are an expert Indian GST Invoice Intelligence engine. Analyze this invoice image.\n"
                "Extract the information in valid JSON strictly following this schema:\n"
                "{\n"
                '  "invoice_number": "string",\n'
                '  "invoice_date": "YYYY-MM-DD or DD/MM/YYYY",\n'
                '  "place_of_supply": "2-digit state code",\n'
                '  "supplier": {"name": "string", "gstin": "15-char string", "state_code": "2-digit string"},\n'
                '  "buyer": {"name": "string", "gstin": "15-char string", "state_code": "2-digit string"},\n'
                '  "line_items": [\n'
                '    {\n'
                '      "item_index": 1,\n'
                '      "description": "string",\n'
                '      "hsn_sac": "string",\n'
                '      "qty": 10.0,\n'
                '      "rate": 100.0,\n'
                '      "taxable_value": 1000.0,\n'
                '      "cgst_rate": 9.0,\n'
                '      "cgst_amt": 90.0,\n'
                '      "sgst_rate": 9.0,\n'
                '      "sgst_amt": 90.0,\n'
                '      "igst_rate": 0.0,\n'
                '      "igst_amt": 0.0,\n'
                '      "line_total": 1180.0\n'
                '    }\n'
                '  ],\n'
                '  "totals": {\n'
                '    "taxable_amount": 1000.0,\n'
                '    "cgst_amount": 90.0,\n'
                '    "sgst_amount": 90.0,\n'
                '    "igst_amount": 0.0,\n'
                '    "grand_total": 1180.0\n'
                '  }\n'
                "}\n"
                "Return ONLY the JSON string. Do not include markdown code block formatting or explanation."
            )

            url = "https://api-inference.huggingface.co/models/Qwen/Qwen2-VL-7B-Instruct/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "Qwen/Qwen2-VL-7B-Instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.0,
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                # Clean code blocks if present
                clean_json = re.sub(r"^```(?:json)?\s*", "", content)
                clean_json = re.sub(r"\s*```$", "", clean_json)
                return json.loads(clean_json)
            else:
                logger.warning("HF API error: status %d - %s", resp.status_code, resp.text[:200])
                return None

        except Exception as exc:
            logger.warning("VLM full page query failed: %s", exc)
            return None

    def _query_qwen_vl_crop(
        self, crop_bgr: np.ndarray, field_type: str, prompt_override: Optional[str]
    ) -> Optional[str]:
        """Queries Qwen2-VL on an isolated cell crop with typed prompt."""
        try:
            import requests

            b64 = _ndarray_to_base64_png(crop_bgr)
            prompt = prompt_override or _build_field_prompt(field_type)

            url = "https://api-inference.huggingface.co/models/Qwen/Qwen2-VL-7B-Instruct/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "Qwen/Qwen2-VL-7B-Instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                "max_tokens": 64,
                "temperature": 0.0,
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            return None

        except Exception as exc:
            logger.debug("VLM crop query failed: %s", exc)
            return None

    # ── Text Parsing & Cleansing ─────────────────────────────────────────────

    def _extract_full_text(self, img_bgr: np.ndarray) -> str:
        """Extract text using Tesseract OCR if installed."""
        if not self._tesseract_available:
            return ""
        try:
            import pytesseract
            rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            return pytesseract.image_to_string(rgb, config="--psm 6 -l eng")
        except Exception:
            return ""

    def _clean_value(self, raw: str, field_type: str) -> str:
        """Sanitizes model output according to statutory field formats."""
        text = raw.strip()
        if field_type in {"numeric", "qty", "rate", "taxable_value", "amount", "tax", "cgst_amt", "sgst_amt"}:
            match = re.search(r"[\d,]+\.?\d*", text.replace(" ", ""))
            return match.group(0).replace(",", "") if match else ""
        elif field_type == "gstin":
            cleaned = re.sub(r"[^A-Za-z0-9]", "", text).upper()
            return cleaned[:15] if len(cleaned) >= 15 else cleaned
        elif field_type == "date":
            match = re.search(
                r"\d{2}[\/\-\.]\d{2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2}", text
            )
            return match.group(0) if match else text
        return text

    def _parse_full_text(self, text: str) -> Dict[str, Any]:
        """
        Parses raw OCR text into a structured dictionary.
        Extracts parties, GSTINs, invoice numbers, dates, line items, and totals.
        """
        result: Dict[str, Any] = {
            "supplier": {},
            "buyer": {},
            "line_items": [],
            "totals": {},
        }

        if not text:
            return result

        # 1. GSTINs: 15-char regex
        gstins = re.findall(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b", text)
        if len(gstins) >= 1:
            result["supplier"]["gstin"] = gstins[0]
            result["supplier"]["state_code"] = gstins[0][:2]
        if len(gstins) >= 2:
            result["buyer"]["gstin"] = gstins[1]
            result["buyer"]["state_code"] = gstins[1][:2]

        # 2. Invoice Number
        inv_m = re.search(r"(?:Invoice|Inv|Bill)\s*(?:No|Number|#)?[:\s]*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
        if inv_m:
            result["invoice_number"] = inv_m.group(1).strip()

        # 3. Invoice Date
        date_m = re.search(r"(?:Invoice\s*Date|Date|Dated)[:\s]*(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2})", text, re.IGNORECASE)
        if date_m:
            result["invoice_date"] = date_m.group(1).strip()

        # 4. Totals
        gt_m = re.search(r"(?:Grand\s*Total|Total\s*Amount|Net\s*Payable|Invoice\s*Total)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)", text, re.IGNORECASE)
        if gt_m:
            result["totals"]["grand_total"] = gt_m.group(1).replace(",", "")

        tax_m = re.search(r"(?:Total\s*Taxable|Taxable\s*(?:Amount|Value)|Sub\s*Total)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)", text, re.IGNORECASE)
        if tax_m:
            result["totals"]["taxable_amount"] = tax_m.group(1).replace(",", "")

        for key, pattern in [
            ("cgst_amount", r"(?:CGST|Central\s*Tax)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)"),
            ("sgst_amount", r"(?:SGST|State\s*Tax)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)"),
            ("igst_amount", r"(?:IGST|Integrated\s*Tax)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)"),
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                result["totals"][key] = m.group(1).replace(",", "")

        # 5. Table Line Items Parser
        # Scan lines matching: Description Qty Rate Taxable CGST SGST Total
        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            numbers = re.findall(r"\b\d+(?:\.\d{1,2})?\b", line)
            # A line item typically has at least 3-4 numbers (e.g. qty, rate, taxable, total)
            if len(numbers) >= 3 and len(line.split()) >= 4:
                desc = re.sub(r"\b\d+(?:\.\d{1,2})?\b", "", line).strip()
                result["line_items"].append({
                    "item_index": len(result["line_items"]) + 1,
                    "description": desc or f"Item {len(result['line_items']) + 1}",
                    "qty": float(numbers[0]) if len(numbers) > 0 else 1.0,
                    "rate": float(numbers[1]) if len(numbers) > 1 else 0.0,
                    "taxable_value": float(numbers[2]) if len(numbers) > 2 else 0.0,
                    "line_total": float(numbers[-1]) if len(numbers) > 3 else 0.0,
                })

        return result

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        return {"supplier": {}, "buyer": {}, "line_items": [], "totals": {}}


def _build_field_prompt(field_type: str) -> str:
    """Returns a tight, task-specific prompt to minimise VLM hallucination."""
    prompts = {
        "gstin": (
            "Read the GSTIN in this image. A GSTIN is exactly 15 characters: "
            "2 digits, 5 uppercase letters, 4 digits, 1 letter, 1 alphanumeric, "
            "the letter Z, 1 alphanumeric. Reply with ONLY the 15-character GSTIN."
        ),
        "taxable_value": "Read the taxable value amount. Reply with ONLY the numeric value.",
        "cgst_amt": "Read the CGST amount. Reply with ONLY the numeric value.",
        "sgst_amt": "Read the SGST amount. Reply with ONLY the numeric value.",
        "qty": "Read the quantity. Reply with ONLY the numeric digits.",
        "rate": "Read the unit price/rate. Reply with ONLY the numeric digits.",
        "date": "Read the date. Reply with ONLY the date string (DD/MM/YYYY or YYYY-MM-DD).",
        "invoice_number": "Read the invoice number string. Reply with ONLY the invoice number.",
    }
    return prompts.get(field_type, f"Read the exact text for field '{field_type}'. Reply with ONLY the value.")
