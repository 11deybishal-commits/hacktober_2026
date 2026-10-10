"""
Export: JSON and CSV formatters.
Converts CanonicalInvoice and InvoiceRecord into standard outputs.
"""
import json
import csv
import io
from typing import Dict, Any, List
from gstlens.contracts import InvoiceRecord

def export_to_json(record: InvoiceRecord) -> str:
    """Exports the full InvoiceRecord, including validation status, to JSON."""
    return record.model_dump_json(indent=2)

def export_to_csv(record: InvoiceRecord) -> str:
    """Exports Line Items with Header/Totals context to CSV string."""
    inv = record.invoice
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Invoice No", "Date", "Supplier GSTIN", "Buyer GSTIN", "POS",
        "Item Index", "Description", "HSN/SAC", "Qty", "Rate", "Taxable Value",
        "CGST Rate", "CGST Amt", "SGST Rate", "SGST Amt", "IGST Rate", "IGST Amt", "Line Total"
    ])
    
    # Line items
    for item in inv.line_items:
        writer.writerow([
            inv.invoice_number,
            inv.invoice_date,
            inv.supplier.gstin,
            inv.buyer.gstin,
            inv.place_of_supply,
            item.item_index,
            item.description,
            item.hsn_sac,
            item.qty,
            item.rate,
            item.taxable_value,
            item.cgst_rate,
            item.cgst_amt,
            item.sgst_rate,
            item.sgst_amt,
            item.igst_rate,
            item.igst_amt,
            item.line_total
        ])
        
    return output.getvalue()
