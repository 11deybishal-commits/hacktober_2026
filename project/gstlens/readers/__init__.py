from gstlens.readers.base import BaseReader
from gstlens.readers.mock import MockReader
from gstlens.readers.text_layer import DigitalPdfReader
try:
    from gstlens.readers.vlm_reader import VisionReader
except ImportError:
    VisionReader = None

__all__ = ["BaseReader", "MockReader", "DigitalPdfReader", "VisionReader"]
