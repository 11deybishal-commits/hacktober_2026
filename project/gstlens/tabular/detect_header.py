"""
Tabular Pipeline: Header Detection and Pre-processing.
Finds the true header row in complex Excel sheets and CSVs with merged cells or title banners.
"""
from typing import List, Tuple, Optional
import pandas as pd
from rapidfuzz import fuzz

HEADER_KEYWORDS = [
    "invoice", "inv", "bill", "date", "gstin", "party", "item", "description",
    "particulars", "hsn", "qty", "quantity", "rate", "price", "taxable", "cgst",
    "sgst", "igst", "total", "amount", "tax"
]

def detect_header_row(df_raw: pd.DataFrame, max_search_rows: int = 15) -> int:
    """
    Scans the first N rows of a dataframe and returns the index of the row
    with the highest density of invoice table header keywords.
    """
    best_row = 0
    best_score = 0

    for idx in range(min(len(df_raw), max_search_rows)):
        row_values = [str(val).strip().lower() for val in df_raw.iloc[idx].dropna()]
        if not row_values:
            continue

        match_count = 0
        for val in row_values:
            if any(k in val for k in HEADER_KEYWORDS):
                match_count += 1
            elif any(fuzz.partial_ratio(k, val) > 80 for k in HEADER_KEYWORDS):
                match_count += 1

        if match_count > best_score:
            best_score = match_count
            best_row = idx

    return best_row

def load_and_clean_tabular(file_path: str) -> pd.DataFrame:
    """Loads CSV or Excel, detects header row, and unmerges/forward-fills headers."""
    ext = file_path.lower().split(".")[-1]
    
    if ext == "csv":
        # Try common encodings and separators
        for enc in ["utf-8", "latin1", "cp1252"]:
            for sep in [",", ";", "\t"]:
                try:
                    df = pd.read_csv(file_path, encoding=enc, sep=sep, header=None)
                    if len(df.columns) > 1:
                        break
                except Exception:
                    continue
            else:
                continue
            break
    else:
        df = pd.read_excel(file_path, header=None)

    header_idx = detect_header_row(df)
    
    # Set detected header row
    headers = [str(col).strip() if pd.notna(col) else f"col_{i}" for i, col in enumerate(df.iloc[header_idx])]
    clean_df = df.iloc[header_idx + 1:].copy()
    clean_df.columns = headers
    clean_df.reset_index(drop=True, inplace=True)
    
    # Drop rows that are completely empty
    clean_df.dropna(how="all", inplace=True)
    return clean_df
