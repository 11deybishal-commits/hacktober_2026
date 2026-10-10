import urllib.request
import json

def make_invoice_svg(title, inv_no, date, sup_name, sup_gstin, buy_name, buy_gstin, item1_name, item1_val, item1_tax, total_val, is_handwritten=False):
    font_family = "'Comic Sans MS', cursive, sans-serif" if is_handwritten else "'Inter', Arial, sans-serif"
    header_color = "#92400e" if is_handwritten else "#1e40af"
    bg_color = "#fffbeb" if is_handwritten else "#ffffff"
    border_style = "2px dashed #b45309" if is_handwritten else "2px solid #3b82f6"
    
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 650 500" width="650" height="500">
  <rect width="650" height="500" fill="{bg_color}" rx="8" />
  <rect x="15" y="15" width="620" height="470" fill="none" stroke="{header_color}" stroke-width="2" rx="6" />
  
  <!-- Header Title -->
  <text x="325" y="45" font-family="{font_family}" font-size="20" font-weight="bold" fill="{header_color}" text-anchor="middle">{title}</text>
  <line x1="15" y1="60" x2="635" y2="60" stroke="#cbd5e1" stroke-width="1" />
  
  <!-- Invoice Details -->
  <text x="30" y="85" font-family="Arial" font-size="11" font-weight="bold" fill="#64748b">INVOICE NO:</text>
  <text x="120" y="85" font-family="{font_family}" font-size="12" font-weight="bold" fill="#0f172a">{inv_no}</text>
  
  <text x="440" y="85" font-family="Arial" font-size="11" font-weight="bold" fill="#64748b">DATE:</text>
  <text x="490" y="85" font-family="{font_family}" font-size="12" font-weight="bold" fill="#0f172a">{date}</text>
  
  <!-- Parties Box -->
  <rect x="30" y="105" width="280" height="85" fill="#f8fafc" stroke="#e2e8f0" rx="4" />
  <text x="40" y="125" font-family="Arial" font-size="10" font-weight="bold" fill="#64748b">SUPPLIER (M/s):</text>
  <text x="40" y="145" font-family="{font_family}" font-size="13" font-weight="bold" fill="#0f172a">{sup_name}</text>
  <text x="40" y="165" font-family="Arial" font-size="10" fill="#64748b">GSTIN: <tspan font-family="{font_family}" font-size="12" font-weight="bold" fill="#1e3a8a">{sup_gstin}</tspan></text>
  
  <rect x="340" y="105" width="280" height="85" fill="#f8fafc" stroke="#e2e8f0" rx="4" />
  <text x="350" y="125" font-family="Arial" font-size="10" font-weight="bold" fill="#64748b">BUYER / BILLED TO:</text>
  <text x="350" y="145" font-family="{font_family}" font-size="13" font-weight="bold" fill="#0f172a">{buy_name}</text>
  <text x="350" y="165" font-family="Arial" font-size="10" fill="#64748b">GSTIN: <tspan font-family="{font_family}" font-size="12" font-weight="bold" fill="#1e3a8a">{buy_gstin}</tspan></text>

  <!-- Line Item Table -->
  <rect x="30" y="210" width="590" height="26" fill="{header_color}" rx="3" />
  <text x="45" y="227" font-family="Arial" font-size="11" font-weight="bold" fill="#ffffff">#</text>
  <text x="80" y="227" font-family="Arial" font-size="11" font-weight="bold" fill="#ffffff">Description</text>
  <text x="260" y="227" font-family="Arial" font-size="11" font-weight="bold" fill="#ffffff">HSN</text>
  <text x="320" y="227" font-family="Arial" font-size="11" font-weight="bold" fill="#ffffff">Qty</text>
  <text x="370" y="227" font-family="Arial" font-size="11" font-weight="bold" fill="#ffffff">Rate</text>
  <text x="430" y="227" font-family="Arial" font-size="11" font-weight="bold" fill="#ffffff">Taxable</text>
  <text x="500" y="227" font-family="Arial" font-size="11" font-weight="bold" fill="#ffffff">CGST 9%</text>
  <text x="570" y="227" font-family="Arial" font-size="11" font-weight="bold" fill="#ffffff">SGST 9%</text>

  <!-- Row 1 -->
  <text x="45" y="260" font-family="{font_family}" font-size="12" fill="#0f172a">1</text>
  <text x="80" y="260" font-family="{font_family}" font-size="12" font-weight="bold" fill="#0f172a">{item1_name}</text>
  <text x="260" y="260" font-family="{font_family}" font-size="12" fill="#0f172a">7318</text>
  <text x="320" y="260" font-family="{font_family}" font-size="12" fill="#0f172a">12</text>
  <text x="370" y="260" font-family="{font_family}" font-size="12" fill="#0f172a">450.00</text>
  <text x="430" y="260" font-family="{font_family}" font-size="13" font-weight="bold" fill="{('#b91c1c' if is_handwritten else '#0f172a')}">{item1_val}</text>
  <text x="500" y="260" font-family="{font_family}" font-size="12" fill="#0f172a">{item1_tax}</text>
  <text x="570" y="260" font-family="{font_family}" font-size="12" fill="#0f172a">{item1_tax}</text>
  <line x1="30" y1="275" x2="620" y2="275" stroke="#e2e8f0" stroke-width="1" />

  <!-- Row 2 -->
  <text x="45" y="300" font-family="{font_family}" font-size="12" fill="#0f172a">2</text>
  <text x="80" y="300" font-family="{font_family}" font-size="12" font-weight="bold" fill="#0f172a">Steel Brackets</text>
  <text x="260" y="300" font-family="{font_family}" font-size="12" fill="#0f172a">7326</text>
  <text x="320" y="300" font-family="{font_family}" font-size="12" fill="#0f172a">5</text>
  <text x="370" y="300" font-family="{font_family}" font-size="12" fill="#0f172a">1200.00</text>
  <text x="430" y="300" font-family="{font_family}" font-size="12" fill="#0f172a">6,000.00</text>
  <text x="500" y="300" font-family="{font_family}" font-size="12" fill="#0f172a">540.00</text>
  <text x="570" y="300" font-family="{font_family}" font-size="12" fill="#0f172a">540.00</text>
  <line x1="30" y1="315" x2="620" y2="315" stroke="#cbd5e1" stroke-width="1" />

  <!-- Totals Area -->
  <rect x="360" y="335" width="260" height="85" fill="#f1f5f9" rx="4" />
  <text x="375" y="360" font-family="Arial" font-size="11" fill="#475569">Total Taxable Value:</text>
  <text x="540" y="360" font-family="{font_family}" font-size="12" font-weight="bold" fill="#0f172a">11,400.00</text>
  
  <text x="375" y="380" font-family="Arial" font-size="11" fill="#475569">CGST + SGST (18%):</text>
  <text x="540" y="380" font-family="{font_family}" font-size="12" font-weight="bold" fill="#0f172a">2,052.00</text>
  
  <line x1="375" y1="390" x2="610" y2="390" stroke="#cbd5e1" stroke-width="1" />
  <text x="375" y="410" font-family="Arial" font-size="12" font-weight="bold" fill="{header_color}">GRAND TOTAL:</text>
  <text x="530" y="410" font-family="{font_family}" font-size="14" font-weight="bold" fill="{header_color}">₹{total_val}</text>
  
  <!-- Stamp / Signature -->
  <rect x="40" y="395" width="160" height="55" fill="none" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="3,2" rx="4" />
  <text x="120" y="425" font-family="'Courier New', monospace" font-size="12" font-weight="bold" fill="#dc2626" text-anchor="middle">AUTHORIZED SIGN</text>
</svg>"""


def upload_file(filename, content_bytes, content_type="image/svg+xml"):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + content_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request("http://127.0.0.1:8000/api/upload", data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

# 1. Clean Printed Invoice SVG
svg_printed = make_invoice_svg(
    title="TAX INVOICE — APEX DISTRIBUTORS",
    inv_no="INV-2026-1042",
    date="04/10/2026",
    sup_name="Shree Ganesh Traders",
    sup_gstin="27ABCDE1234F1Z0",
    buy_name="Apex Engineering Solutions",
    buy_gstin="27XYZPQ5678K1ZF",
    item1_name="Hex Bolts M10",
    item1_val="5,400.00",
    item1_tax="486.00",
    total_val="13,452.00",
    is_handwritten=False
).encode("utf-8")
res1 = upload_file("inv_0381_printed.svg", svg_printed)
print("Uploaded Printed Invoice:", res1.get("status"))

# 2. Handwritten Bill-Book Invoice (with 5,490 misread in ink)
svg_handwritten = make_invoice_svg(
    title="CASH / CREDIT BILL BOOK",
    inv_no="INV-2026-1042",
    date="04/10/2026",
    sup_name="Shree Ganesh Traders (Bill-Book)",
    sup_gstin="27ABCDE1234F1Z0",
    buy_name="Apex Engineering Solutions",
    buy_gstin="27XYZPQ5678K1ZF",
    item1_name="Hex Bolts M10",
    item1_val="5,490.00",  # Raw handwritten read with OCR confusion
    item1_tax="486.00",
    total_val="13,452.00",
    is_handwritten=True
).encode("utf-8")
res2 = upload_file("hand_0042_billbook.svg", svg_handwritten)
print("Uploaded Handwritten Bill-book Invoice:", res2.get("status"))

# 3. Scanned Invoice with GSTIN OCR Error (Z -> 2)
svg_gstin_error = make_invoice_svg(
    title="TAX INVOICE — OCR CHALLENGE",
    inv_no="INV-2026-1042",
    date="04/10/2026",
    sup_name="Shree Ganesh Traders",
    sup_gstin="27ABCDE1234F120",  # Z misread as 2
    buy_name="Apex Engineering Solutions",
    buy_gstin="27XYZPQ5678K1ZF",
    item1_name="Hex Bolts M10",
    item1_val="5,400.00",
    item1_tax="486.00",
    total_val="13,452.00",
    is_handwritten=False
).encode("utf-8")
res3 = upload_file("gstin_error_scan.svg", svg_gstin_error)
print("Uploaded GSTIN Error Invoice:", res3.get("status"))

# 4. Upload CSV
csv_data = (
    "Inv No,Bill Dt,Party GST No,Item,HSN,Qty,Rate,Taxable Amt,CGST Amt,SGST Amt\n"
    "INV/26/118,2026-10-04,27XYZPQ5678K1ZF,Hex Bolts M10,7318,12,450,5400.00,486.00,486.00\n"
    "INV/26/119,2026-10-04,27XYZPQ5678K1ZF,Steel Brackets,7326,5,1200,6000.00,540.00,540.00\n"
).encode("utf-8")
res4 = upload_file("sales_september.csv", csv_data, "text/csv")
print("Uploaded CSV:", res4.get("status"))

print("\nLive demo refreshed with real document image previews!")
