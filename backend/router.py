import os
import magic
from enum import Enum
from pydantic import BaseModel

class PipelineRoute(str, Enum):
    TABULAR = "tabular"
    DIGITAL_PDF = "digital_pdf"
    SCANNED_IMAGE = "scanned_image"
    REJECTED = "rejected"

class RoutingDecision(BaseModel):
    file_path: str
    route: PipelineRoute
    mime_type: str
    reason: str

def detect_text_layer(pdf_path: str) -> bool:
    """
    Check if a PDF has a genuine text layer vs being a scanned image.
    Uses pdfplumber or pypdfium2. Here we mock the behavior for skeleton setup.
    """
    # TODO: Implement real pdfplumber text extraction heuristic
    # return len(text) > 50 and not image_dominated
    return True

def route_file(file_path: str) -> RoutingDecision:
    """
    Determine the correct processing pipeline for an incoming file
    based on magic bytes, not just the file extension.
    """
    if not os.path.exists(file_path):
        return RoutingDecision(file_path=file_path, route=PipelineRoute.REJECTED, mime_type="unknown", reason="File not found")
        
    mime_type = magic.from_file(file_path, mime=True)
    
    if mime_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        return RoutingDecision(file_path=file_path, route=PipelineRoute.TABULAR, mime_type=mime_type, reason="Excel spreadsheet detected")
        
    if mime_type in ["text/csv", "text/plain"]:
        return RoutingDecision(file_path=file_path, route=PipelineRoute.TABULAR, mime_type=mime_type, reason="CSV/Text data detected")
        
    if mime_type == "application/pdf":
        if detect_text_layer(file_path):
            return RoutingDecision(file_path=file_path, route=PipelineRoute.DIGITAL_PDF, mime_type=mime_type, reason="PDF with text layer detected")
        else:
            return RoutingDecision(file_path=file_path, route=PipelineRoute.SCANNED_IMAGE, mime_type=mime_type, reason="Scanned PDF without text layer")
            
    if mime_type.startswith("image/"):
        return RoutingDecision(file_path=file_path, route=PipelineRoute.SCANNED_IMAGE, mime_type=mime_type, reason="Image file detected")
        
    return RoutingDecision(file_path=file_path, route=PipelineRoute.REJECTED, mime_type=mime_type, reason="Unsupported file type")
