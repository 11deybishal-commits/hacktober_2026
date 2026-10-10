"""
Structuring: Item Table Reconstruction.
Parses table row strips or OCR text lines into structured LineItem models.
"""
from typing import List, Dict, Any, Optional
import re
from decimal import Decimal
from gstlens.contracts import LineItem

def parse_row_text_to_item(row_text: str, index: int) -> Optional[LineItem]:
    """Parses a single row text string into a LineItem."""
    tokens = [t.strip() for t in row_text.split() if t.strip()]
    if not tokens:
        return None

    # Search for numbers in tokens
    numbers = []
    text_parts = []
    for token in tokens:
        clean_num = token.replace(",", "").replace("/-", "")
        if re.match(r"^[0-9]+(?:\.[0-9]+)?$", clean_num):
            numbers.append(float(clean_num))
        else:
            text_parts.append(token)

    desc = " ".join(text_parts) if text_parts else f"Item {index}"
    
    qty = None
    rate = None
    taxable = None
    
    if len(numbers) >= 3:
        # Typically: Qty, Rate, Taxable or Rate, Taxable, Total
        qty = numbers[0]
        rate = numbers[1]
        taxable = numbers[2]
    elif len(numbers) == 2:
        qty = numbers[0]
        rate = numbers[1]
        taxable = qty * rate
    elif len(numbers) == 1:
        taxable = numbers[0]

    dec_qty = Decimal(str(round(qty, 2))) if qty is not None else None
    dec_rate = Decimal(str(round(rate, 2))) if rate is not None else None
    dec_taxable = Decimal(str(round(taxable, 2))) if taxable is not None else Decimal("0.00")

    return LineItem(
        item_index=index,
        description=desc,
        qty=dec_qty,
        rate=dec_rate,
        taxable_value=dec_taxable,
        line_total=dec_taxable
    )
