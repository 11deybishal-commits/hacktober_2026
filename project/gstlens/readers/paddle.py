"""
PaddleOCR Reader Adapter for GSTLens.
Implements the Reader interface for layout analysis, table detection,
and printed text recognition using PaddleOCR / PaddleOCR-VL.
Supports:
  1. Direct PaddleOCR Python library (if installed in local environment)
  2. HTTP microservice on localhost:8100 (Dockerized Paddle service from ARCHITECTURE.md §3)
  3. OpenCV morphological table-line and anchor spotter fallback
"""
import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import cv2

from gstlens.readers.base import BaseReader
from gstlens.contracts import Candidate, BBox
from gstlens.preprocess import load_image, extract_field_crop

logger = logging.getLogger(__name__)


class PaddleReader(BaseReader):
    """
    PaddleOCR reader specializing in:
    - Printed text and anchor spotting (GSTIN, Qty, Rate, Taxable, etc.)
    - Ruled line table grid detection and cell bounding boxes
    - First-pass document reading
    """

    def __init__(self, endpoint: Optional[str] = None):
        super().__init__(name="paddle_vl")
        self.endpoint = endpoint or os.getenv("PADDLE_ENDPOINT", "http://localhost:8100/parse")
        self._paddle_lib = self._init_paddle_lib()

    @staticmethod
    def _init_paddle_lib():
        """Attempts to load local paddleocr Python library if available."""
        try:
            from paddleocr import PaddleOCR
            return PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        except Exception:
            return None

    def read_document(self, document_input: Any) -> Dict[str, Any]:
        """
        Parses full document layout, tables, and printed text.
        """
        img_bgr = load_image(document_input)
        if img_bgr is None or img_bgr.size == 0:
            return {"supplier": {}, "buyer": {}, "line_items": [], "totals": {}}

        # Path 1: Local PaddleOCR library
        if self._paddle_lib is not None:
            try:
                results = self._paddle_lib.ocr(img_bgr, cls=True)
                return self._parse_paddle_raw(results)
            except Exception as e:
                logger.warning("Local PaddleOCR execution failed: %s", e)

        # Path 2: HTTP Microservice on localhost:8100
        http_res = self._query_http_service(img_bgr)
        if http_res:
            return http_res

        # Path 3: Morphological layout + table geometry extractor
        return self._detect_table_geometry(img_bgr)

    def read_crop(
        self,
        crop_image: np.ndarray,
        field_type: str,
        prompt_override: Optional[str] = None
    ) -> Candidate:
        """
        Reads an isolated cell crop using PaddleOCR.
        """
        if crop_image is None or crop_image.size == 0:
            return Candidate(value="", reader=self.name, legible=False)

        if self._paddle_lib is not None:
            try:
                res = self._paddle_lib.ocr(crop_image, cls=False)
                if res and res[0]:
                    lines = [line[1][0] for line in res[0]]
                    raw = " ".join(lines).strip()
                    clean = self._clean_numeric(raw) if field_type in ("numeric", "taxable_value", "amount") else raw
                    return Candidate(value=clean, reader=self.name, view="crop", legible=bool(clean))
            except Exception as e:
                logger.debug("Paddle crop OCR failed: %s", e)

        return Candidate(value="", reader=self.name, legible=False)

    def detect_table_grid(self, img_bgr: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Uses OpenCV morphological operations to detect horizontal and vertical
        ruled lines of invoice tables and extract cell boxes.
        """
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        bw = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)

        # Horizontal lines
        h_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (int(bw.shape[1] / 30), 1))
        h_lines = cv2.erode(bw, h_structure)
        h_lines = cv2.dilate(h_lines, h_structure)

        # Vertical lines
        v_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(bw.shape[0] / 30)))
        v_lines = cv2.erode(bw, v_structure)
        v_lines = cv2.dilate(v_lines, v_structure)

        # Grid mask
        grid = cv2.add(h_lines, v_lines)
        contours, _ = cv2.findContours(grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        cells = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            # Filter reasonable cell sizes (width > 30px, height > 15px)
            if w > 30 and h > 15 and w < img_bgr.shape[1] * 0.95 and h < img_bgr.shape[0] * 0.5:
                cells.append((x, y, w, h))

        # Sort top-to-bottom, left-to-right
        cells = sorted(cells, key=lambda b: (b[1] // 20, b[0]))
        return cells

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

    def _detect_table_geometry(self, img_bgr: np.ndarray) -> Dict[str, Any]:
        """Fallback geometry detector when running without active Paddle binary."""
        cells = self.detect_table_grid(img_bgr)
        return {
            "supplier": {},
            "buyer": {},
            "line_items": [],
            "totals": {},
            "detected_cells_count": len(cells)
        }

    def _parse_paddle_raw(self, ocr_results) -> Dict[str, Any]:
        """Converts raw PaddleOCR bounding-box outputs into structured dictionary."""
        extracted_text = []
        if ocr_results and ocr_results[0]:
            for line in ocr_results[0]:
                text = line[1][0]
                extracted_text.append(text)

        full_text = "\n".join(extracted_text)
        from gstlens.readers.vlm_reader import VisionReader
        # Re-use the structural regex parser on extracted text
        vr = VisionReader()
        return vr._parse_full_text(full_text)

    @staticmethod
    def _clean_numeric(raw: str) -> str:
        m = re.search(r"[\d,]+\.?\d*", raw.replace(" ", ""))
        return m.group(0).replace(",", "") if m else ""
