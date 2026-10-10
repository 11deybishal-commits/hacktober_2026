"""
Vision-Language / OCR Reader with Local Hugging Face / API and Optical Character Heuristics.
Handles printed and handwritten image parsing and targeted cell-crop re-reading.
"""
import os
import re
import json
import base64
import requests
import numpy as np
import cv2
from PIL import Image
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from gstlens.readers.base import BaseReader
from gstlens.contracts import Candidate, BBox

load_dotenv()

class VisionReader(BaseReader):
    def __init__(self, name: str = "vlm_paddle"):
        super().__init__(name=name)
        self.hf_token = os.getenv("HF_TOKEN", "")

    def read_document(self, image_input: Any) -> Dict[str, Any]:
        """Extracts invoice fields from an image using OCR heuristics and patterns."""
        # Convert to numpy image
        if isinstance(image_input, str):
            img = cv2.imread(image_input)
        elif isinstance(image_input, np.ndarray):
            img = image_input
        else:
            img = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)

        text = self._extract_text_from_image(img)
        return self._parse_text_to_fields(text)

    def read_crop(
        self,
        crop_image: np.ndarray,
        field_type: str,
        prompt_override: Optional[str] = None
    ) -> Candidate:
        """
        Reads a single cell crop. If HF_TOKEN is present and active, attempts VLM inference;
        otherwise runs OCR / digit pattern recognition.
        """
        if crop_image is None or crop_image.size == 0:
            return Candidate(value="", reader=self.name, legible=False)

        # Try Hugging Face Serverless API if configured
        if self.hf_token and len(self.hf_token) > 10:
            vlm_val = self._query_hf_vision(crop_image, field_type, prompt_override)
            if vlm_val:
                return Candidate(
                    value=vlm_val,
                    reader=f"{self.name}_hf",
                    view="crop",
                    logprob=-0.05,
                    legible=True
                )

        # Fallback to OCR / Image processing
        raw_text = self._extract_text_from_image(crop_image)
        cleaned = self._clean_crop_value(raw_text, field_type)

        return Candidate(
            value=cleaned,
            reader=self.name,
            view="crop",
            logprob=-0.15,
            legible=len(cleaned) > 0
        )

    def _extract_text_from_image(self, img: np.ndarray) -> str:
        """Attempts Tesseract OCR if installed, else returns extracted text."""
        try:
            import pytesseract
            # Convert BGR to RGB
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else img
            text = pytesseract.image_to_string(rgb)
            return text
        except Exception:
            # If tesseract executable is not on PATH, return empty
            return ""

    def _clean_crop_value(self, raw_text: str, field_type: str) -> str:
        raw = raw_text.strip()
        if field_type in ["numeric", "qty", "rate", "taxable_value", "amount", "tax"]:
            # Extract digits and decimal point
            match = re.search(r"[0-9]+(?:\.[0-9]+)?", raw.replace(",", ""))
            return match.group(0) if match else raw
        elif field_type == "gstin":
            # Match 15 uppercase alphanumeric chars
            cleaned = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
            return cleaned[:15] if len(cleaned) >= 15 else cleaned
        return raw

    def _query_hf_vision(self, crop_image: np.ndarray, field_type: str, prompt: Optional[str]) -> Optional[str]:
        """Sends crop to HF Vision Model."""
        try:
            _, buffer = cv2.imencode(".png", crop_image)
            base64_img = base64.b64encode(buffer).decode("utf-8")
            # Minimal prompt
            p = prompt or f"Read the exact text of this {field_type}."
            # We can use Hugging Face router if reachable
            # For resilience and offline operation, gracefully timeout
            url = "https://api-inference.huggingface.co/models/Qwen/Qwen2-VL-7B-Instruct"
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            payload = {"inputs": f"data:image/png;base64,{base64_img}", "parameters": {"prompt": p, "max_new_tokens": 30}}
            res = requests.post(url, headers=headers, json=payload, timeout=2.5)
            if res.status_code == 200:
                resp_json = res.json()
                if isinstance(resp_json, list) and len(resp_json) > 0:
                    text = resp_json[0].get("generated_text", "")
                    return self._clean_crop_value(text, field_type)
        except Exception:
            pass
        return None

    def _parse_text_to_fields(self, text: str) -> Dict[str, Any]:
        """Heuristic parser for full page OCR text."""
        result: Dict[str, Any] = {
            "supplier": {},
            "buyer": {},
            "line_items": [],
            "totals": {}
        }
        
        # GSTIN matches
        gstins = re.findall(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text)
        if len(gstins) >= 1:
            result["supplier"]["gstin"] = gstins[0]
            result["supplier"]["state_code"] = gstins[0][:2]
        if len(gstins) >= 2:
            result["buyer"]["gstin"] = gstins[1]
            result["buyer"]["state_code"] = gstins[1][:2]

        # Invoice No
        inv_no = re.search(r"(?:Inv|Invoice|Bill)\s*(?:No|Number|#)?[:\s]*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
        if inv_no:
            result["invoice_number"] = inv_no.group(1).strip()

        # Date
        inv_date = re.search(r"(?:Date|Dated)[:\s]*([0-9]{2}[\/\-\.][0-9]{2}[\/\-\.][0-9]{2,4}|[0-9]{4}[\/\-\.][0-9]{2}[\/\-\.][0-9]{2})", text, re.IGNORECASE)
        if inv_date:
            result["invoice_date"] = inv_date.group(1).strip()

        # Grand Total
        gt = re.search(r"(?:Grand\s*Total|Total\s*Amount|Total)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)", text, re.IGNORECASE)
        if gt:
            result["totals"]["grand_total"] = gt.group(1).replace(",", "")

        return result
