"""
Abstract Base Class for all GSTLens Perception Readers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np
from gstlens.contracts import Candidate, BBox

class BaseReader(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def read_document(self, document_path_or_bytes: Any) -> Dict[str, Any]:
        """
        Parses an entire document and returns dictionary of extracted raw fields.
        """
        pass

    @abstractmethod
    def read_crop(
        self,
        crop_image: np.ndarray,
        field_type: str,
        prompt_override: Optional[str] = None
    ) -> Candidate:
        """
        Reads a cropped region of an image for a targeted field type.
        """
        pass
