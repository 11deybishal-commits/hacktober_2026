"""
Tabular Pipeline: Header Detection and Pre-processing.
Finds the true header row in complex Excel sheets and CSVs with merged cells or title banners.
"""
from typing import List, Tuple, Optional
import pandas as pd
try:
    from rapidfuzz import fuzz
except ImportError:
    import difflib
    class _FuzzFallback:
        @staticmethod
        def ratio(s1, s2):
            return difflib.SequenceMatcher(None, str(s1).lower(), str(s2).lower()).ratio() * 100
        @staticmethod
        def partial_ratio(s1, s2):
            s1, s2 = str(s1).lower(), str(s2).lower()
            if s1 in s2 or s2 in s1:
                return 100.0
            return difflib.SequenceMatcher(None, s1, s2).ratio() * 100
    fuzz = _FuzzFallback()

HEADER_KEYWORDS = [
    "invoice", "inv", "bill", "date", "gstin", "party", "item", "description",
    "particulars", "hsn", "qty", "quantity", "rate", "price", "taxable", "cgst",
    "sgst", "igst", "total", "amount", "tax", "customer", "buyer", "vendor",
    "seller", "product", "goods", "disc", "discount", "net", "gross", "vch",
    "voucher", "sno", "s.no", "sl"
]

def detect_header_row(df_raw: pd.DataFrame, max_search_rows: int = 25) -> int:
    """
    Scans the first N rows of a dataframe and returns the index of the row
    with the highest density of invoice table header keywords.
    Requires at least 2 non-empty cells to avoid matching single-cell banner titles.
    """
    best_row = 0
    best_score = 0

    for idx in range(min(len(df_raw), max_search_rows)):
        row_values = [str(val).strip().lower() for val in df_raw.iloc[idx].dropna()]
        if len(row_values) < 2:
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
    """Loads CSV or Excel, detects header row, handles ragged lines, and unmerges/forward-fills headers."""
    ext = file_path.lower().split(".")[-1]
    
    if ext == "csv":
        best_df = None
        best_col_count = 0

        # Try common encodings and separators, selecting the one that maximizes column count
        for enc in ["utf-8", "latin1", "cp1252", "utf-8-sig"]:
            for sep in [",", ";", "\t", "|"]:
                try:
                    with open(file_path, "r", encoding=enc, errors="ignore") as f:
                        sample_lines = [f.readline() for _ in range(50)]
                    sample_lines = [l for l in sample_lines if l.strip()]
                    if not sample_lines:
                        continue
                    import csv
                    max_cols = 1
                    for line in sample_lines:
                        try:
                            cols_in_line = len(next(csv.reader([line], delimiter=sep)))
                            if cols_in_line > max_cols:
                                max_cols = cols_in_line
                        except Exception:
                            continue
                    
                    if max_cols > best_col_count:
                        candidate_df = pd.read_csv(
                            file_path,
                            encoding=enc,
                            sep=sep,
                            header=None,
                            names=list(range(max_cols)),
                            engine="python",
                            on_bad_lines="skip"
                        )
                        if len(candidate_df.columns) > best_col_count and len(candidate_df) > 0:
                            best_col_count = len(candidate_df.columns)
                            best_df = candidate_df
                except Exception:
                    continue

        df = best_df if best_df is not None else pd.read_csv(file_path, header=None, engine="python", on_bad_lines="skip")
    else:
        # Excel: read first available sheet
        df = pd.read_excel(file_path, header=None)

    # Drop entirely blank rows and columns from margins
    df.dropna(how="all", inplace=True)
    df.dropna(how="all", axis=1, inplace=True)
    df.reset_index(drop=True, inplace=True)

    header_idx = detect_header_row(df)
    
    # Set detected header row
    header_series = df.iloc[header_idx].copy()
    headers = []
    for i, col in enumerate(header_series):
        if pd.notna(col) and str(col).strip():
            headers.append(str(col).strip())
        else:
            headers.append(f"col_{i}")

    # Deduplicate column names to guarantee 1D Series access
    seen_counts = {}
    unique_headers = []
    for h in headers:
        if h in seen_counts:
            seen_counts[h] += 1
            unique_headers.append(f"{h}_{seen_counts[h]}")
        else:
            seen_counts[h] = 0
            unique_headers.append(h)

    clean_df = df.iloc[header_idx + 1:].copy()
    clean_df.columns = unique_headers
    clean_df.reset_index(drop=True, inplace=True)
    
    # Drop rows that are completely empty
    clean_df.dropna(how="all", inplace=True)
    return clean_df
