"""
GSTLens Layout and Zone Analyzer.
Divides document page into semantic zones:
- Header (Supplier info, Title)
- Metadata & Party (Invoice No, Date, Buyer info, Place of Supply)
- Table (Line items, quantities, rates, amounts)
- Totals (Subtotal, CGST, SGST, IGST, Round-off, Grand Total, Words)
"""
from typing import Dict, List, Tuple
from gstlens.contracts import BBox

class PageZone:
    HEADER = "header"
    METADATA = "metadata"
    TABLE = "table"
    TOTALS = "totals"
    FOOTER = "footer"

DEFAULT_ZONE_BOXES = {
    PageZone.HEADER: BBox(page=1, x0=0.0, y0=0.0, x1=1.0, y1=0.20),
    PageZone.METADATA: BBox(page=1, x0=0.0, y0=0.18, x1=1.0, y1=0.35),
    PageZone.TABLE: BBox(page=1, x0=0.0, y0=0.32, x1=1.0, y1=0.76),
    PageZone.TOTALS: BBox(page=1, x0=0.0, y0=0.74, x1=1.0, y1=0.94),
    PageZone.FOOTER: BBox(page=1, x0=0.0, y0=0.92, x1=1.0, y1=1.00),
}

def classify_zone(y_mid: float) -> str:
    """Classifies a vertical normalized position into a semantic zone."""
    if y_mid < 0.20:
        return PageZone.HEADER
    elif y_mid < 0.35:
        return PageZone.METADATA
    elif y_mid < 0.76:
        return PageZone.TABLE
    elif y_mid < 0.94:
        return PageZone.TOTALS
    else:
        return PageZone.FOOTER
