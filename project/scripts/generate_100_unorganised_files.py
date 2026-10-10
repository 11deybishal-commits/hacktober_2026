"""
Generator for 100 Unorganised .xlsx and .csv GST Invoice Datasets.
Simulates real-world chaotic ERP dumps, Tally exports, handwritten-style digital sheets,
merged banners, missing column headers, currency formatting, multi-invoice files,
and trailing summary footers.
"""
import os
import random
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

OUTPUT_DIR = "c:/Users/wrich/Documents/Hacktober/hacktober_2026/benchmark_100"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SUPPLIERS = [
    ("NATH TRADERS", "07AAGPN2913H1ZU", "Delhi"),
    ("BHARAT ASSOCIATES", "09GBVPS8212J1ZP", "Uttar Pradesh"),
    ("KAILASH TRADERS", "07ABOPK0909P1Z6", "Delhi"),
    ("SEENU TRANSPORTS PVT LTD", "33ACUPCE9T2D1ZH", "Tamil Nadu"),
    ("SHREE SHYAM ENTERPRISES", "27AASCS9921M1Z3", "Maharashtra"),
    ("GLOBAL LOGISTICS CORP", "29AAACG1234K1Z2", "Karnataka"),
    ("METRO STEEL & HARDWARE", "24AABCM5678P1ZQ", "Gujarat"),
    ("APEX TECH SOLUTIONS", "06AAACT9876R1Z4", "Haryana"),
]

BUYERS = [
    ("Educrafter Legal Solutions Pvt Ltd", "07AAAFC3342M1ZK", "Delhi"),
    ("SOG Enterprises", "33AAECN3422C1Z4", "Tamil Nadu"),
    ("Rishabh & Co.", "07AABCR1234L1Z8", "Delhi"),
    ("Zenith Industrial Parts", "27AAACZ4321Q1Z9", "Maharashtra"),
    ("Delta Electro Components", "29AABCD9876S1Z7", "Karnataka"),
    ("Surat Textile Mills", "24AABCS5555T1Z5", "Gujarat"),
    ("Prime Retail Distribution", "06AAACP1111N1Z3", "Haryana"),
]

ITEMS = [
    ("Single Phase Energy Meter", "9028", 1200.0, 1500.0),
    ("Chakor Room Heater Blower", "8516", 2500.0, 3200.0),
    ("Industrial Fasteners & Bolts", "7318", 450.0, 800.0),
    ("Stamp Paper & Legal Documentation", "9982", 2000.0, 5000.0),
    ("Logistics Freight Transport", "9965", 1000.0, 3000.0),
    ("Computer Peripheral Monitors", "8471", 5000.0, 9500.0),
    ("Packaging Corrugated Boxes", "4819", 150.0, 350.0),
    ("Stainless Steel Pipes & Rods", "7306", 1800.0, 4200.0),
    ("Electrical Copper Wiring 1.5mm", "8544", 850.0, 1600.0),
    ("Network Routing Hardware Hub", "8517", 3200.0, 7500.0),
]

def format_currency_val(val, style_idx):
    if style_idx == 0:
        return round(val, 2)
    elif style_idx == 1:
        return f"₹ {val:,.2f}"
    elif style_idx == 2:
        return f"Rs. {val:,.2f}/-"
    elif style_idx == 3:
        return f"INR {val:,.2f}"
    elif style_idx == 4:
        return f"{val:,.2f}"
    else:
        return round(val, 2)

def generate_benchmark_file(file_index: int):
    # Determine format: 60 xlsx, 40 csv
    is_xlsx = file_index <= 60
    ext = "xlsx" if is_xlsx else "csv"
    
    # Random scenario archetype
    archetype = (file_index % 7) + 1
    
    supp_name, supp_gstin, supp_state = random.choice(SUPPLIERS)
    buyer_name, buyer_gstin, buyer_state = random.choice(BUYERS)
    
    is_inter = supp_gstin[:2] != buyer_gstin[:2]
    
    # Generate 1 to 4 invoices in this file
    num_invoices = 1 if archetype in [1, 2, 3, 4] else (2 if archetype in [5, 6] else 3)
    
    all_rows = []
    
    for inv_i in range(num_invoices):
        inv_no = f"INV-2026-{file_index:03d}-{inv_i+1}"
        inv_date = f"{random.randint(1, 28):02d}/{random.randint(1, 10):02d}/2026"
        
        num_items = random.randint(1, 4)
        for itm_i in range(num_items):
            desc, hsn, min_r, max_r = random.choice(ITEMS)
            qty = random.randint(1, 10)
            rate = round(random.uniform(min_r, max_r), 2)
            taxable = round(qty * rate, 2)
            
            if is_inter:
                cgst = 0.0
                sgst = 0.0
                igst = round(taxable * 0.18, 2)
            else:
                cgst = round(taxable * 0.09, 2)
                sgst = round(taxable * 0.09, 2)
                igst = 0.0
            
            total = round(taxable + cgst + sgst + igst, 2)
            
            # Sparse formatting (Tally / SAP style): only row 0 has invoice level fields
            show_meta = (itm_i == 0) or (archetype not in [4])
            
            curr_style = file_index % 5
            
            row = {
                "inv_no": inv_no if show_meta else None,
                "inv_date": inv_date if show_meta else None,
                "supp_name": supp_name if show_meta else None,
                "supp_gstin": supp_gstin if show_meta else None,
                "buyer_name": buyer_name if show_meta else None,
                "buyer_gstin": buyer_gstin if show_meta else None,
                "desc": desc,
                "hsn": hsn,
                "qty": qty,
                "rate": format_currency_val(rate, curr_style),
                "taxable": format_currency_val(taxable, curr_style),
                "cgst": format_currency_val(cgst, curr_style),
                "sgst": format_currency_val(sgst, curr_style),
                "igst": format_currency_val(igst, curr_style),
                "total": format_currency_val(total, curr_style),
            }
            all_rows.append(row)

    # Column header variations (Unorthodox names)
    col_headers = [
        ("inv_no", random.choice(["Invoice No", "Inv #", "Bill Ref", "Vch No", "Tax Inv No", "Doc No"])),
        ("inv_date", random.choice(["Invoice Date", "Date", "Bill Date", "Dated", "Doc Date"])),
        ("supp_name", random.choice(["Supplier Name", "Seller", "Vendor", "From Company", "Billing Party"])),
        ("supp_gstin", random.choice(["Supplier GSTIN", "Seller GST", "Own GSTIN", "Vendor GST No"])),
        ("buyer_name", random.choice(["Customer Name", "Buyer", "Client", "Party Name", "Billed To"])),
        ("buyer_gstin", random.choice(["Buyer GSTIN", "Party GSTIN", "GSTIN / UIN", "Customer GST", "TIN/GST"])),
        ("desc", random.choice(["Item Description", "Particulars", "Product Name", "Goods Description", "Item"])),
        ("hsn", random.choice(["HSN Code", "Tariff Head", "HSN/SAC", "Commodity Code"])),
        ("qty", random.choice(["Qty", "Quantity", "Nos", "Pcs", "Billing Qty"])),
        ("rate", random.choice(["Unit Price", "Rate (INR)", "Basic Rate", "Price / Item", "Rate"])),
        ("taxable", random.choice(["Taxable Value", "Assessable Value", "Basic Amount", "Net Taxable", "Taxable Amt"])),
        ("cgst", random.choice(["CGST Amount", "Central Tax", "CGST (9%)", "CGST Amt"])),
        ("sgst", random.choice(["SGST Amount", "State Tax", "SGST (9%)", "SGST Amt"])),
        ("igst", random.choice(["IGST Amount", "Integrated Tax", "IGST (18%)", "IGST Amt"])),
        ("total", random.choice(["Total Amount", "Gross Total", "Line Total", "Invoice Total", "Net Amount"])),
    ]

    # Convert to matrix
    header_row = [lbl for _, lbl in col_headers]
    data_rows = []
    for r in all_rows:
        row_vals = [r[k] for k, _ in col_headers]
        data_rows.append(row_vals)

    filename = f"sample_{file_index:03d}_{'xlsx' if is_xlsx else 'csv'}.{ext}"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Construct chaotic banner headers
    banner_rows = []
    num_banner_rows = random.choice([0, 1, 2, 3, 4, 5]) if archetype in [1, 2, 5] else 1
    
    if num_banner_rows >= 1:
        banner_rows.append([f"*** {supp_name.upper()} - TAX INVOICE REPORT ***"])
    if num_banner_rows >= 2:
        banner_rows.append([f"GSTIN: {supp_gstin} | State: {supp_state}"])
    if num_banner_rows >= 3:
        banner_rows.append([f"Period: 01-Oct-2026 to 31-Oct-2026 | ERP Version 9.4"])
    if num_banner_rows >= 4:
        banner_rows.append([])  # blank spacer row
    if num_banner_rows >= 5:
        banner_rows.append([f"Printed by Operator on: {random.randint(1, 28)}/10/2026"])

    # Trailing summary footer rows
    footer_rows = []
    if archetype in [3, 6]:
        footer_rows.append(["Sub Total", "", "", "", "", "", "", "", "", "", "Sum Taxable", "Sum CGST", "Sum SGST", "Sum IGST", "Grand Total"])
        footer_rows.append(["E. & O. E.", "Goods once sold cannot be taken back", "", "", "", "", "", "", "", "", "", "", "", "", ""])
        footer_rows.append(["For " + supp_name, "Authorized Signatory", "", "", "", "", "", "", "", "", "", "", "", "", ""])

    if is_xlsx:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sales Register"
        
        # Write banners
        cur_row = 1
        for b in banner_rows:
            if b:
                ws.cell(row=cur_row, column=1, value=b[0])
            cur_row += 1
            
        # Write table header
        for col_idx, col_name in enumerate(header_row, start=1):
            cell = ws.cell(row=cur_row, column=col_idx, value=col_name)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="DDEEFF", end_color="DDEEFF", fill_type="solid")
        cur_row += 1
        
        # Write data rows
        for d_row in data_rows:
            for col_idx, val in enumerate(d_row, start=1):
                ws.cell(row=cur_row, column=col_idx, value=val)
            cur_row += 1
            
        # Write footers
        for f_row in footer_rows:
            for col_idx, val in enumerate(f_row, start=1):
                ws.cell(row=cur_row, column=col_idx, value=val)
            cur_row += 1
            
        wb.save(filepath)
    else:
        # CSV with varied delimiter and encoding
        delim = random.choice([",", ";", "\t"]) if file_index % 4 == 0 else ","
        enc = "utf-8" if file_index % 3 != 0 else "latin1"
        
        with open(filepath, "w", encoding=enc, newline="", errors="ignore") as f:
            # write banners
            for b in banner_rows:
                if b:
                    f.write(b[0] + "\n")
                else:
                    f.write("\n")
            # write header
            f.write(delim.join(f'"{h}"' if delim in h or " " in h else h for h in header_row) + "\n")
            # write data
            for d in data_rows:
                line_str = delim.join("" if v is None else f'"{v}"' if delim in str(v) or " " in str(v) else str(v) for v in d)
                f.write(line_str + "\n")
            # write footers
            for ft in footer_rows:
                line_str = delim.join(f'"{v}"' if delim in str(v) or " " in str(v) else str(v) for v in ft)
                f.write(line_str + "\n")

    return filepath

if __name__ == "__main__":
    print("Generating 100 benchmark unorganised files...")
    created = []
    for i in range(1, 101):
        fp = generate_benchmark_file(i)
        created.append(fp)
    print(f"Successfully generated {len(created)} files in {OUTPUT_DIR}")
    print(f"XLSX files: {sum(1 for f in created if f.endswith('.xlsx'))}")
    print(f"CSV files: {sum(1 for f in created if f.endswith('.csv'))}")
