"""
GSTLens Test Suite: Tabular Pipeline.
Tests header detection, fuzzy column mapping, and invoice grouping.
"""
import sys
import os
import pandas as pd
from decimal import Decimal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gstlens.tabular.detect_header import detect_header_row
from gstlens.tabular.map_columns import map_column_name, clean_numeric_value
from gstlens.tabular.group_invoices import parse_tabular_to_invoices


def test_detect_header_row_with_banner():
    # Messy spreadsheet with 2 rows of banner/title before the real table headers
    data = [
        ["Shree Ganesh Traders", None, None, None, None],
        ["Monthly Sales Register - Sep 2026", None, None, None, None],
        ["Inv No", "Date", "Item Description", "Qty", "Taxable Amt"],
        ["INV-001", "2026-09-01", "Hex Bolt M10", 10, 500.0],
        ["INV-002", "2026-09-02", "Steel Bracket", 5, 1200.0],
    ]
    df = pd.DataFrame(data)
    header_idx = detect_header_row(df)
    assert header_idx == 2  # The 3rd row (index 2) is the true header row


def test_map_column_name_synonyms():
    # Test fuzzy column synonym mapping
    assert map_column_name("Inv No") == "invoice_number"
    assert map_column_name("Bill Date") == "invoice_date"
    assert map_column_name("Party GST No") == "buyer_gstin"
    assert map_column_name("Item Description") == "description"
    assert map_column_name("Taxable Amt") == "taxable_value"
    assert map_column_name("Quantity") == "qty"
    assert map_column_name("Rate/Unit") == "rate"
    assert map_column_name("Central Tax") == "cgst_amt"
    assert map_column_name("State Tax") == "sgst_amt"


def test_clean_numeric_value():
    assert clean_numeric_value("5,400.00/-") == 5400.0
    assert clean_numeric_value("₹ 1,00,000") == 100000.0
    assert clean_numeric_value(450) == 450.0
    assert clean_numeric_value(None) is None
    assert clean_numeric_value("(500.50)") == -500.50


def test_parse_tabular_to_invoices():
    # Construct a sample dataframe simulating an extracted table
    df = pd.DataFrame({
        "Inv No": ["INV-101", "INV-101", "INV-102"],
        "Inv Date": ["2026-10-04", "2026-10-04", "2026-10-05"],
        "Party GSTIN": ["27XYZPQ5678K1ZF", "27XYZPQ5678K1ZF", "27XYZPQ5678K1ZF"],
        "Item": ["Hex Bolts", "Washers", "Steel Plate"],
        "Qty": [12, 50, 2],
        "Rate": [450, 10, 2500],
        "Taxable Amt": [5400, 500, 5000],
        "CGST Amt": [486, 45, 450],
        "SGST Amt": [486, 45, 450]
    })
    
    invoices = parse_tabular_to_invoices(df, "test_sales.xlsx")
    assert len(invoices) == 2  # INV-101 and INV-102
    
    inv_101 = next(inv for inv in invoices if inv.invoice_number == "INV-101")
    assert len(inv_101.line_items) == 2
    assert inv_101.buyer.gstin == "27XYZPQ5678K1ZF"
    assert inv_101.totals.taxable_amount == Decimal("5900.00")  # 5400 + 500


if __name__ == "__main__":
    test_detect_header_row_with_banner()
    test_map_column_name_synonyms()
    test_clean_numeric_value()
    test_parse_tabular_to_invoices()
    print("All tabular pipeline tests passed successfully.")
