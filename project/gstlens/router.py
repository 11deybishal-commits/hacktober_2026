"""
GSTLens Input Router.
Classifies incoming documents by file signature and structure:
- Tabular (.xlsx, .csv)
- Digital PDF (text-layer extractable without OCR)
- Scanned / photographed PDF (needs OCR/VLM vision pipeline)
- Image (.jpg, .jpeg, .png)
"""
import os
import mimetypes
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class PipelineRoute(str, Enum):
    TABULAR = "tabular"
    DIGITAL_PDF = "digital_pdf"
    SCANNED_IMAGE = "scanned_image"
    HANDWRITTEN_IMAGE = "handwritten_image"
    REJECTED = "rejected"

class RoutingDecision(BaseModel):
    file_path: str
    route: PipelineRoute
    mime_type: str
    reason: str
    has_text_layer: bool = False
    estimated_quality: float = 1.0

def sniff_mime_type(file_path: str) -> str:
    """Detect MIME type safely via magic bytes inspection, falling back to mimetypes."""
    if not os.path.exists(file_path):
        return "application/octet-stream"

    try:
        with open(file_path, "rb") as f:
            header = f.read(32)
            
        if header.startswith(b"%PDF"):
            return "application/pdf"
        elif header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif header.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif header.startswith(b"PK\x03\x04"):
            # ZIP container - check if it's an xlsx
            ext = os.path.splitext(file_path)[1].lower()
            if ext in [".xlsx", ".xlsm"]:
                return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            return "application/zip"
        elif header.startswith(b"\xd0\xcf\x11\xe0"): # OLE compound doc (old .xls)
            return "application/vnd.ms-excel"
    except Exception:
        pass

    guessed, _ = mimetypes.guess_type(file_path)
    if guessed:
        return guessed
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return "text/csv"
    elif ext in [".xlsx", ".xlsm"]:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    elif ext == ".png":
        return "image/png"
    elif ext == ".pdf":
        return "application/pdf"
        
    return "application/octet-stream"

def detect_pdf_text_layer(pdf_path: str) -> bool:
    """
    Examines if a PDF contains a selectable text layer (digital invoice)
    rather than purely embedded raster images.
    """
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        total_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            total_text += text
            if len(total_text) > 100:
                return True
        return len(total_text.strip()) > 50
    except Exception:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            total_text = ""
            for page in doc:
                total_text += page.get_text()
                if len(total_text) > 100:
                    return True
            return len(total_text.strip()) > 50
        except Exception:
            return False

def route_file(file_path: str) -> RoutingDecision:
    """
    Determine the optimal processing pipeline for an incoming document.
    """
    if not os.path.exists(file_path):
        return RoutingDecision(
            file_path=file_path,
            route=PipelineRoute.REJECTED,
            mime_type="unknown",
            reason="File not found on filesystem"
        )
        
    mime_type = sniff_mime_type(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    
    # 1. Spreadsheets and CSVs
    if mime_type in [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
    ] or ext in [".xlsx", ".xls", ".csv"]:
        return RoutingDecision(
            file_path=file_path,
            route=PipelineRoute.TABULAR,
            mime_type=mime_type,
            reason="Spreadsheet/Tabular data detected: routed to deterministic Tabular Pipeline"
        )
        
    # 2. PDF Documents
    if mime_type == "application/pdf" or ext == ".pdf":
        has_text = detect_pdf_text_layer(file_path)
        if has_text:
            return RoutingDecision(
                file_path=file_path,
                route=PipelineRoute.DIGITAL_PDF,
                mime_type=mime_type,
                has_text_layer=True,
                reason="Digital PDF with extractable text layer detected: routed to Digital PDF Pipeline (no OCR required)"
            )
        else:
            return RoutingDecision(
                file_path=file_path,
                route=PipelineRoute.SCANNED_IMAGE,
                mime_type=mime_type,
                has_text_layer=False,
                reason="Scanned/Image-dominated PDF detected: routed to Vision OCR Pipeline"
            )
            
    # 3. Raster Images
    if mime_type.startswith("image/") or ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"]:
        # Check if filename hints handwriting or route to SCANNED_IMAGE
        is_handwritten_hint = any(keyword in os.path.basename(file_path).lower() for keyword in ["handwritten", "billbook", "manual_bill"])
        route = PipelineRoute.HANDWRITTEN_IMAGE if is_handwritten_hint else PipelineRoute.SCANNED_IMAGE
        return RoutingDecision(
            file_path=file_path,
            route=route,
            mime_type=mime_type,
            reason=f"Raster image detected ({ext}): routed to Vision Perception Pipeline"
        )
        
    return RoutingDecision(
        file_path=file_path,
        route=PipelineRoute.REJECTED,
        mime_type=mime_type,
        reason=f"Unsupported file format '{ext}' (MIME: {mime_type})"
    )
