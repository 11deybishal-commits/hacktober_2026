"""
Vision-Language / OCR Reader.
Handles scanned invoice images and handwritten bill-books using:
  - Tesseract OCR (free, offline, installed via apt/brew/choco)
  - Hugging Face Serverless Inference API (Qwen2-VL via chat completions format)
  - Pillow/OpenCV preprocessing for contrast + deskew before OCR

Graceful degradation: if Tesseract is not installed or HF token is absent,
returns an empty-but-valid structured dict that the repair pipeline will handle.
"""
import os
import re
import json
import base64
import logging
from typing import Dict, Any, List, Optional

import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter
from dotenv import load_dotenv

from gstlens.readers.base import BaseReader
from gstlens.contracts import Candidate, BBox

load_dotenv()
logger = logging.getLogger(__name__)


# ── Preprocessing helpers ────────────────────────────────────────────────────

def _preprocess_for_ocr(img_bgr: np.ndarray) -> np.ndarray:
    """
    Apply contrast enhancement, deskew, and binarization to improve OCR accuracy.
    Returns a BGR image ready for Tesseract or VLM.
    """
    # Upscale if too small (Tesseract likes >= 300dpi equivalent)
    h, w = img_bgr.shape[:2]
    if max(h, w) < 1500:
        scale = 1500 / max(h, w)
        img_bgr = cv2.resize(img_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Convert to grayscale
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Adaptive thresholding for clean binarization
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 8
    )

    # Convert back to BGR for consistency
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


def _ndarray_to_base64_png(img: np.ndarray) -> str:
    """Encode a NumPy BGR image to base64 PNG string."""
    _, buffer = cv2.imencode(".png", img)
    return base64.b64encode(buffer).decode("utf-8")


# ── VisionReader class ───────────────────────────────────────────────────────

class VisionReader(BaseReader):
    """
    Pluggable vision reader. Uses Tesseract for free offline OCR and
    optionally calls Qwen2-VL via HF Serverless Inference for targeted crop re-reads.
    """

    def __init__(self, name: str = "vlm_paddle"):
        super().__init__(name=name)
        self.hf_token = os.getenv("HF_TOKEN", "").strip()
        self._tesseract_available = self._check_tesseract()

    @staticmethod
    def _check_tesseract() -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    # ── Public API ───────────────────────────────────────────────────────────

    def read_document(self, image_input: Any) -> Dict[str, Any]:
        """
        Full-page invoice extraction.
        Loads image → preprocesses → extracts text → parses into structured dict.
        """
        img_bgr = self._load_image(image_input)
        if img_bgr is None:
            logger.warning("VisionReader.read_document: could not load image from %s", image_input)
            return self._empty_result()

        preprocessed = _preprocess_for_ocr(img_bgr)
        text = self._extract_full_text(preprocessed)
        return self._parse_full_text(text)

    def read_crop(
        self,
        crop_image: np.ndarray,
        field_type: str,
        prompt_override: Optional[str] = None,
    ) -> Candidate:
        """
        Targeted re-read of a single bounding-box crop.
        Tries HF Qwen2-VL first (if token available), falls back to Tesseract.
        """
        if crop_image is None or crop_image.size == 0:
            return Candidate(value="", reader=self.name, legible=False)

        preprocessed = _preprocess_for_ocr(crop_image)

        # ── Path 1: Qwen2-VL via HF Serverless API ───────────────────────────
        if self.hf_token and len(self.hf_token) > 20:
            vlm_result = self._query_qwen_vl(preprocessed, field_type, prompt_override)
            if vlm_result:
                cleaned = self._clean_value(vlm_result, field_type)
                return Candidate(
                    value=cleaned,
                    reader=f"{self.name}_hf_qwen2vl",
                    view="crop",
                    logprob=-0.03,
                    legible=True
                )

        # ── Path 2: Tesseract ────────────────────────────────────────────────
        raw_text = self._extract_full_text(preprocessed)
        cleaned  = self._clean_value(raw_text, field_type)
        return Candidate(
            value=cleaned,
            reader=f"{self.name}_tesseract",
            view="crop",
            logprob=-0.15,
            legible=len(cleaned) > 0
        )

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _load_image(self, image_input: Any) -> Optional[np.ndarray]:
        """Load image from file path, numpy array, or PIL Image."""
        if isinstance(image_input, str):
            if not os.path.exists(image_input):
                return None
            return cv2.imread(image_input)
        elif isinstance(image_input, np.ndarray):
            return image_input
        elif isinstance(image_input, Image.Image):
            return cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        return None

    def _extract_full_text(self, img_bgr: np.ndarray) -> str:
        """Extract text using Tesseract OCR (if available)."""
        if not self._tesseract_available:
            return ""
        try:
            import pytesseract
            rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            # Config: PSM 6 = assume a single uniform block of text
            text = pytesseract.image_to_string(rgb, config="--psm 6 -l eng")
            return text
        except Exception as exc:
            logger.debug("Tesseract OCR failed: %s", exc)
            return ""

    def _query_qwen_vl(
        self, img_bgr: np.ndarray, field_type: str, prompt_override: Optional[str]
    ) -> Optional[str]:
        """
        Query Qwen2-VL-7B-Instruct via HF Serverless Inference (chat-completions format).
        Uses a field-type-specific prompt to reduce hallucination.
        """
        try:
            import requests

            b64 = _ndarray_to_base64_png(img_bgr)
            prompt = prompt_override or _build_field_prompt(field_type)

            # HF Serverless uses the OpenAI-compatible /v1/chat/completions endpoint
            url = (
                "https://api-inference.huggingface.co/models/"
                "Qwen/Qwen2-VL-7B-Instruct/v1/chat/completions"
            )
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
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                "max_tokens": 64,
                "temperature": 0.0,
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
            return text

        except Exception as exc:
            logger.debug("Qwen2-VL HF query failed: %s", exc)
            return None

    def _clean_value(self, raw: str, field_type: str) -> str:
        """Post-process OCR/VLM output to extract the canonical field value."""
        text = raw.strip()
        if field_type in {"numeric", "qty", "rate", "taxable_value", "amount", "tax", "cgst_amt", "sgst_amt"}:
            match = re.search(r"[\d,]+\.?\d*", text.replace(" ", ""))
            if match:
                return match.group(0).replace(",", "")
            return ""
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
        Parse full-page OCR text into a structured invoice dict.
        All fields are optional — downstream normalizer + validator handles missing values.
        """
        result: Dict[str, Any] = {
            "supplier": {},
            "buyer": {},
            "line_items": [],
            "totals": {},
        }

        if not text:
            return result

        # GSTINs: first match → supplier, second → buyer
        gstins = re.findall(
            r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b", text
        )
        if len(gstins) >= 1:
            result["supplier"]["gstin"] = gstins[0]
            result["supplier"]["state_code"] = gstins[0][:2]
        if len(gstins) >= 2:
            result["buyer"]["gstin"] = gstins[1]
            result["buyer"]["state_code"] = gstins[1][:2]

        # Invoice number
        inv_m = re.search(
            r"(?:Invoice|Inv|Bill)\s*(?:No|Number|#)?[:\s]*([A-Za-z0-9\-\/]+)",
            text, re.IGNORECASE
        )
        if inv_m:
            result["invoice_number"] = inv_m.group(1).strip()

        # Invoice date
        date_m = re.search(
            r"(?:Invoice\s*Date|Date|Dated)[:\s]*"
            r"(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2})",
            text, re.IGNORECASE
        )
        if date_m:
            result["invoice_date"] = date_m.group(1).strip()

        # Grand total
        gt_m = re.search(
            r"(?:Grand\s*Total|Total\s*Amount|Net\s*Payable|Invoice\s*Total)"
            r"[:\s₹Rs.]*([0-9,]+\.?[0-9]*)",
            text, re.IGNORECASE
        )
        if gt_m:
            result["totals"]["grand_total"] = gt_m.group(1).replace(",", "")

        # Taxable total
        tax_m = re.search(
            r"(?:Total\s*Taxable|Taxable\s*(?:Amount|Value)|Sub\s*Total)"
            r"[:\s₹Rs.]*([0-9,]+\.?[0-9]*)",
            text, re.IGNORECASE
        )
        if tax_m:
            result["totals"]["taxable_amount"] = tax_m.group(1).replace(",", "")

        # CGST / SGST / IGST
        for key, pattern in [
            ("cgst_amount", r"(?:CGST|Central\s*Tax)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)"),
            ("sgst_amount", r"(?:SGST|State\s*Tax)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)"),
            ("igst_amount", r"(?:IGST|Integrated\s*Tax)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)"),
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                result["totals"][key] = m.group(1).replace(",", "")

        return result

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        return {"supplier": {}, "buyer": {}, "line_items": [], "totals": {}}


# ── Prompt templates ─────────────────────────────────────────────────────────

def _build_field_prompt(field_type: str) -> str:
    """Returns a tight, task-specific prompt to minimise VLM hallucination."""
    prompts = {
        "gstin": (
            "Read the GSTIN in this image. A GSTIN is exactly 15 characters: "
            "2 digits, 5 uppercase letters, 4 digits, 1 letter, 1 alphanumeric, "
            "the letter Z, 1 alphanumeric. Reply with ONLY the 15-character GSTIN, nothing else."
        ),
        "taxable_value": (
            "Read the taxable value amount in this image. "
            "Reply with ONLY the numeric value (digits and decimal point), nothing else."
        ),
        "cgst_amt": (
            "Read the CGST amount in this image. "
            "Reply with ONLY the numeric value, nothing else."
        ),
        "sgst_amt": (
            "Read the SGST amount in this image. "
            "Reply with ONLY the numeric value, nothing else."
        ),
        "qty": "Read the quantity number. Reply with ONLY the numeric value.",
        "rate": "Read the unit rate/price. Reply with ONLY the numeric value.",
        "date": "Read the date in this image. Reply with ONLY the date (DD/MM/YYYY or YYYY-MM-DD).",
        "invoice_number": "Read the invoice number. Reply with ONLY the invoice number string.",
    }
    return prompts.get(field_type, f"Read the exact text in this image for field '{field_type}'. Reply with ONLY the value.")
