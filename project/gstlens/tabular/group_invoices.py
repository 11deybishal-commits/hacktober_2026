"""
Tabular Pipeline: Grouping Rows into Invoices.
Converts clean, mapped tabular rows into CanonicalInvoice records.
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
import pandas as pd

from gstlens.contracts import (
    CanonicalInvoice,
    Supplier,
    Buyer,
    LineItem,
    Totals,
    InvoiceRecord,
    FieldValue,
    Provenance
)
from gstlens.tabular.map_columns import map_column_name, clean_numeric_value

def parse_tabular_to_invoices(df: pd.DataFrame, source_filename: str = "") -> List[CanonicalInvoice]:
    """
    Groups tabular data rows by invoice_number and maps into CanonicalInvoice models.
    """
    # 1. Map columns uniquely (avoid duplicate renamed columns)
    column_mapping = {}
    used_canonical_keys = set()
    for col in df.columns:
        samples = df[col].dropna().head(5).tolist()
        canonical_key = map_column_name(col, samples)
        if canonical_key and canonical_key not in used_canonical_keys:
            column_mapping[col] = canonical_key
            used_canonical_keys.add(canonical_key)

    # Rename mapped columns
    renamed_df = df.rename(columns=column_mapping)

    # 1.5. Filter summary and total rows that are not line items
    summary_words = ["total", "grand total", "subtotal", "sub total", "totals", "summary", "amount in words", "signatory", "e.&o.e", "e&oe"]
    for check_col in ["description", "invoice_number", "hsn_sac"]:
        if check_col in renamed_df.columns:
            renamed_df = renamed_df[~renamed_df[check_col].astype(str).str.strip().str.lower().isin(summary_words)]

    # Forward-fill sparse header metadata across multi-item invoice rows
    for meta_col in ["invoice_number", "invoice_date", "buyer_name", "buyer_gstin", "supplier_name", "supplier_gstin", "place_of_supply"]:
        if meta_col in renamed_df.columns:
            renamed_df[meta_col] = renamed_df[meta_col].ffill()

    # 2. Group by invoice_number (or single group if no invoice_number column)
    invoices: List[CanonicalInvoice] = []
    
    if "invoice_number" in renamed_df.columns and renamed_df["invoice_number"].dropna().nunique() > 1:
        groups = renamed_df.groupby("invoice_number", sort=False)
    else:
        groups = [("default_inv", renamed_df)]

    for group_key, group_df in groups:
        if group_df.empty:
            continue
        first_row = group_df.iloc[0]
        
        # Build Supplier & Buyer
        supplier = Supplier(
            name=str(first_row.get("supplier_name", "Supplier")) if pd.notna(first_row.get("supplier_name")) else None,
            gstin=str(first_row.get("supplier_gstin", "")).strip().upper() if pd.notna(first_row.get("supplier_gstin")) else None,
            state_code=str(first_row.get("supplier_gstin", ""))[:2] if pd.notna(first_row.get("supplier_gstin")) and len(str(first_row.get("supplier_gstin"))) >= 2 else None
        )
        
        buyer_gstin = str(first_row.get("buyer_gstin", "")).strip().upper() if pd.notna(first_row.get("buyer_gstin")) else None
        buyer = Buyer(
            name=str(first_row.get("buyer_name", "Customer")) if pd.notna(first_row.get("buyer_name")) else None,
            gstin=buyer_gstin,
            state_code=buyer_gstin[:2] if buyer_gstin and len(buyer_gstin) >= 2 else None
        )

        inv_number = str(first_row.get("invoice_number", "INV-TABULAR-01")) if pd.notna(first_row.get("invoice_number")) else "INV-TABULAR-01"
        inv_date = str(first_row.get("invoice_date", "2026-10-01")) if pd.notna(first_row.get("invoice_date")) else "2026-10-01"

        # Build Line Items
        line_items: List[LineItem] = []
        tot_taxable = Decimal("0.00")
        tot_cgst = Decimal("0.00")
        tot_sgst = Decimal("0.00")
        tot_igst = Decimal("0.00")

        for idx, (_, row) in enumerate(group_df.iterrows(), start=1):
            qty = clean_numeric_value(row.get("qty"))
            rate = clean_numeric_value(row.get("rate"))
            taxable = clean_numeric_value(row.get("taxable_value"))
            
            # If taxable missing but qty and rate exist
            if taxable is None and qty is not None and rate is not None:
                taxable = qty * rate

            cgst_amt = clean_numeric_value(row.get("cgst_amt")) or 0.0
            sgst_amt = clean_numeric_value(row.get("sgst_amt")) or 0.0
            igst_amt = clean_numeric_value(row.get("igst_amt")) or 0.0
            
            line_tot = clean_numeric_value(row.get("line_total"))
            if line_tot is None and taxable is not None:
                line_tot = taxable + cgst_amt + sgst_amt + igst_amt

            dec_taxable = Decimal(str(round(taxable, 2))) if taxable is not None else Decimal("0.00")
            dec_cgst = Decimal(str(round(cgst_amt, 2)))
            dec_sgst = Decimal(str(round(sgst_amt, 2)))
            dec_igst = Decimal(str(round(igst_amt, 2)))
            dec_tot = Decimal(str(round(line_tot, 2))) if line_tot is not None else Decimal("0.00")

            item = LineItem(
                item_index=idx,
                description=str(row.get("description", f"Item {idx}")) if pd.notna(row.get("description")) else f"Item {idx}",
                hsn_sac=str(row.get("hsn_sac", "")).strip() if pd.notna(row.get("hsn_sac")) else None,
                qty=Decimal(str(round(qty, 2))) if qty is not None else None,
                rate=Decimal(str(round(rate, 2))) if rate is not None else None,
                taxable_value=dec_taxable,
                cgst_amt=dec_cgst,
                sgst_amt=dec_sgst,
                igst_amt=dec_igst,
                line_total=dec_tot
            )
            line_items.append(item)
            tot_taxable += dec_taxable
            tot_cgst += dec_cgst
            tot_sgst += dec_sgst
            tot_igst += dec_igst

        totals = Totals(
            taxable_amount=tot_taxable,
            cgst_amount=tot_cgst,
            sgst_amount=tot_sgst,
            igst_amount=tot_igst,
            grand_total=tot_taxable + tot_cgst + tot_sgst + tot_igst
        )

        inv = CanonicalInvoice(
            invoice_number=inv_number,
            invoice_date=inv_date,
            supplier=supplier,
            buyer=buyer,
            line_items=line_items,
            totals=totals
        )
        invoices.append(inv)

    return invoices
