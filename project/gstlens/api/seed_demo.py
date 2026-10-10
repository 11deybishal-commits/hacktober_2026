"""
GSTLens Challenge Demo Generator.
Generates 3 deterministic benchmark invoices (Verified, Repaired, Needs Review)
with SVG documents, accurate bounding boxes, rule explanations, and repair histories.
"""
import os
import tempfile
from decimal import Decimal
from typing import Dict, Tuple

from gstlens.contracts import (
    InvoiceRecord,
    CanonicalInvoice,
    Supplier,
    Buyer,
    LineItem,
    Totals,
    FieldValue,
    BBox,
    Provenance,
    RuleResult,
)

TEMP_DIR = os.path.join(tempfile.gettempdir(), "gstlens", "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)


def create_invoice_a_svg() -> str:
    """Invoice A — Flawless Tax Invoice (Verified)"""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 700" width="800" height="700">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#faf8f5"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#1A2332" flood-opacity="0.08"/>
    </filter>
  </defs>
  
  <!-- Paper Base -->
  <rect width="800" height="700" fill="url(#bgGrad)" rx="8"/>
  <rect x="20" y="20" width="760" height="660" fill="none" stroke="#2D3A4A" stroke-width="2" rx="6"/>
  
  <!-- Header Banner -->
  <rect x="20" y="20" width="760" height="65" fill="#1A2332" rx="4"/>
  <text x="400" y="52" font-family="'Inter', Arial, sans-serif" font-size="20" font-weight="bold" fill="#F8F4EE" text-anchor="middle" letter-spacing="1">TAX INVOICE — APEX INDUSTRIAL CONTROLS</text>
  <text x="400" y="72" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#C8943A" text-anchor="middle">GST COMPLIANT B2B INVOICE · SECTION 31 CGST ACT 2017</text>

  <!-- Document Meta Box -->
  <rect x="35" y="98" width="730" height="42" fill="#F4EFE6" stroke="#D6C9B5" rx="4"/>
  <text x="50" y="124" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#68717D">INVOICE NO:</text>
  <text x="145" y="124" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#1A2332">INV-2026-0381</text>
  
  <text x="350" y="124" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#68717D">DATE:</text>
  <text x="400" y="124" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#1A2332">12-Oct-2026</text>
  
  <text x="550" y="124" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#68717D">PLACE OF SUPPLY:</text>
  <text x="680" y="124" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#15803D">27 - Maharashtra</text>

  <!-- Parties Split Box -->
  <!-- Supplier Box -->
  <rect x="35" y="152" width="355" height="115" fill="#FFFFFF" stroke="#E5D9C8" rx="5" filter="url(#shadow)"/>
  <rect x="35" y="152" width="355" height="24" fill="#EAE2D5" rx="3"/>
  <text x="45" y="169" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#1A2332">SUPPLIER (CONSIGNOR):</text>
  <text x="45" y="193" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#1A2332">Apex Industrial Controls Ltd.</text>
  <text x="45" y="211" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#68717D">Plot 42, MIDC Industrial Area, Pune, MH</text>
  <text x="45" y="232" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#68717D">GSTIN: <tspan fill="#1E3A8A" font-size="13">27AAACA1234F1Z5</tspan></text>
  <text x="45" y="250" font-family="'Inter', Arial, sans-serif" font-size="10" fill="#15803D">✓ Registered Regular Taxpayer</text>

  <!-- Buyer Box -->
  <rect x="410" y="152" width="355" height="115" fill="#FFFFFF" stroke="#E5D9C8" rx="5" filter="url(#shadow)"/>
  <rect x="410" y="152" width="355" height="24" fill="#EAE2D5" rx="3"/>
  <text x="420" y="169" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#1A2332">BUYER / BILLED TO (CONSIGNEE):</text>
  <text x="420" y="193" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#1A2332">Bharat Precision Engineering Works</text>
  <text x="420" y="211" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#68717D">Sector 9, Turbhe, Navi Mumbai, MH</text>
  <text x="420" y="232" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#68717D">GSTIN: <tspan fill="#1E3A8A" font-size="13">27BBBCB5678K1ZF</tspan></text>
  <text x="420" y="250" font-family="'Inter', Arial, sans-serif" font-size="10" fill="#15803D">✓ Valid ITC Recipient</text>

  <!-- Line Item Table -->
  <rect x="35" y="280" width="730" height="30" fill="#1A2332" rx="4"/>
  <text x="45" y="300" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">#</text>
  <text x="75" y="300" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Item Description</text>
  <text x="310" y="300" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">HSN</text>
  <text x="370" y="300" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Qty</text>
  <text x="420" y="300" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Rate (₹)</text>
  <text x="500" y="300" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Taxable (₹)</text>
  <text x="590" y="300" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">CGST 9%</text>
  <text x="675" y="300" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">SGST 9%</text>

  <!-- Row 1 -->
  <rect x="35" y="315" width="730" height="42" fill="#FFFFFF" stroke="#E5D9C8"/>
  <text x="45" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">1</text>
  <text x="75" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="600" fill="#1A2332">High-Torque AC Servo Motor 750W</text>
  <text x="310" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#68717D">8501</text>
  <text x="375" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">4</text>
  <text x="420" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">12,500.00</text>
  <text x="500" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#1A2332">50,000.00</text>
  <text x="590" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">4,500.00</text>
  <text x="675" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">4,500.00</text>

  <!-- Row 2 -->
  <rect x="35" y="360" width="730" height="42" fill="#FAF8F5" stroke="#E5D9C8"/>
  <text x="45" y="386" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">2</text>
  <text x="75" y="386" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="600" fill="#1A2332">Shielded Industrial Cable 50m Drum</text>
  <text x="310" y="386" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#68717D">8544</text>
  <text x="375" y="386" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">10</text>
  <text x="420" y="386" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">2,200.00</text>
  <text x="500" y="386" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#1A2332">22,000.00</text>
  <text x="590" y="386" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">1,980.00</text>
  <text x="675" y="386" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">1,980.00</text>

  <!-- Calculation & Totals Box -->
  <rect x="420" y="420" width="345" height="150" fill="#FFFFFF" stroke="#D6C9B5" rx="5" filter="url(#shadow)"/>
  
  <text x="440" y="445" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#68717D">Total Taxable Value:</text>
  <text x="740" y="445" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="600" fill="#1A2332" text-anchor="end">₹72,000.00</text>
  
  <text x="440" y="472" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#68717D">Central GST (CGST 9%):</text>
  <text x="740" y="472" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="600" fill="#1A2332" text-anchor="end">₹6,480.00</text>
  
  <text x="440" y="498" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#68717D">State GST (SGST 9%):</text>
  <text x="740" y="498" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="600" fill="#1A2332" text-anchor="end">₹6,480.00</text>
  
  <line x1="435" y1="512" x2="750" y2="512" stroke="#D6C9B5" stroke-width="1.5"/>
  <rect x="430" y="520" width="325" height="40" fill="#F4EFE6" rx="4"/>
  <text x="445" y="546" font-family="'Inter', Arial, sans-serif" font-size="14" font-weight="bold" fill="#1A2332">GRAND TOTAL (INR):</text>
  <text x="740" y="546" font-family="'Inter', Arial, sans-serif" font-size="16" font-weight="bold" fill="#15803D" text-anchor="end">₹84,960.00</text>

  <!-- Left Side: Compliance Stamp & Declaration -->
  <rect x="35" y="430" width="360" height="135" fill="#FAF8F5" stroke="#E5D9C8" rx="4"/>
  <text x="50" y="455" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#1A2332">ELECTRONIC AUDIT VERIFICATION</text>
  <text x="50" y="475" font-family="'Inter', Arial, sans-serif" font-size="10" fill="#68717D">Certified mathematically sound and GST statutory compliant.</text>
  <text x="50" y="495" font-family="'Inter', Arial, sans-serif" font-size="10" fill="#68717D">Section 16(2) CGST Rules Satisfied · Full ITC Eligible.</text>
  
  <rect x="50" y="510" width="160" height="42" fill="#DCFCE7" stroke="#86EFAC" rx="4"/>
  <text x="130" y="535" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#15803D" text-anchor="middle">✓ VERIFIED BY GSTLENS</text>

  <!-- Signoff Footer -->
  <text x="400" y="620" font-family="'Inter', Arial, sans-serif" font-size="10" fill="#9AA4AE" text-anchor="middle">This is a computer-generated tax invoice verified under GST Rule 46. No physical signature required.</text>
</svg>"""


def create_invoice_b_svg() -> str:
    """Invoice B — Repairable Arithmetic Slip (Handwritten / Scanned Bill-Book)"""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 700" width="800" height="700">
  <defs>
    <filter id="inkShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="#854d0e" flood-opacity="0.15"/>
    </filter>
  </defs>
  
  <!-- Parchment Bill-Book Paper -->
  <rect width="800" height="700" fill="#FFFDF8" rx="6"/>
  <rect x="18" y="18" width="764" height="664" fill="none" stroke="#D97706" stroke-width="2.5" stroke-dasharray="6,3" rx="6"/>
  
  <!-- Header Title -->
  <rect x="25" y="25" width="750" height="65" fill="#FEF3C7" rx="4"/>
  <text x="400" y="58" font-family="'Comic Sans MS', 'Brush Script MT', cursive, sans-serif" font-size="24" font-weight="bold" fill="#92400E" text-anchor="middle">CASH / CREDIT BILL BOOK — SHREE GANESH TRADERS</text>
  <text x="400" y="78" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#B45309" text-anchor="middle">RETAIL &amp; WHOLESALE INDUSTRIAL SUPPLIES · PUNE ROAD</text>

  <!-- Bill Metadata -->
  <rect x="35" y="100" width="730" height="42" fill="#FFFBEB" stroke="#FDE68A" rx="4"/>
  <text x="50" y="126" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400E">BILL NO:</text>
  <text x="120" y="126" font-family="'Comic Sans MS', cursive" font-size="15" font-weight="bold" fill="#1E293B">BB-8841</text>
  
  <text x="360" y="126" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400E">DATE:</text>
  <text x="415" y="126" font-family="'Comic Sans MS', cursive" font-size="14" font-weight="bold" fill="#1E293B">08/10/2026</text>
  
  <text x="570" y="126" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400E">POS:</text>
  <text x="615" y="126" font-family="'Comic Sans MS', cursive" font-size="13" font-weight="bold" fill="#1E293B">27-MAHARASHTRA</text>

  <!-- Parties -->
  <rect x="35" y="152" width="355" height="110" fill="#FFFFFF" stroke="#FCD34D" rx="4"/>
  <text x="45" y="172" font-family="'Inter', Arial, sans-serif" font-size="10" font-weight="bold" fill="#B45309">SUPPLIER:</text>
  <text x="45" y="194" font-family="'Comic Sans MS', cursive" font-size="15" font-weight="bold" fill="#0F172A">Shree Ganesh Hardware &amp; Tools</text>
  <text x="45" y="214" font-family="'Comic Sans MS', cursive" font-size="12" fill="#475569">Ganj Peth, Pune - 411002</text>
  <text x="45" y="238" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400E">GSTIN: <tspan font-family="'Comic Sans MS', cursive" font-size="14" font-weight="bold" fill="#1E3A8A">27ABCDE1234F1Z0</tspan></text>

  <rect x="410" y="152" width="355" height="110" fill="#FFFFFF" stroke="#FCD34D" rx="4"/>
  <text x="420" y="172" font-family="'Inter', Arial, sans-serif" font-size="10" font-weight="bold" fill="#B45309">BUYER (M/S):</text>
  <text x="420" y="194" font-family="'Comic Sans MS', cursive" font-size="15" font-weight="bold" fill="#0F172A">Apex Engineering Solutions</text>
  <text x="420" y="214" font-family="'Comic Sans MS', cursive" font-size="12" fill="#475569">MIDC Industrial Area, Pune</text>
  <text x="420" y="238" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400E">GSTIN: <tspan font-family="'Comic Sans MS', cursive" font-size="14" font-weight="bold" fill="#1E3A8A">27XYZPQ5678K1ZF</tspan></text>

  <!-- Items Table Header -->
  <rect x="35" y="275" width="730" height="28" fill="#B45309" rx="3"/>
  <text x="50" y="294" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">#</text>
  <text x="85" y="294" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Particulars / Goods</text>
  <text x="320" y="294" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">HSN</text>
  <text x="375" y="294" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Qty</text>
  <text x="430" y="294" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Rate</text>
  <text x="505" y="294" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Taxable Value</text>
  <text x="600" y="294" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">CGST 9%</text>
  <text x="685" y="294" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">SGST 9%</text>

  <!-- Line Item Row 1 with handwritten ink styling -->
  <rect x="35" y="310" width="730" height="48" fill="#FFFFFF" stroke="#FDE68A"/>
  <text x="50" y="339" font-family="'Comic Sans MS', cursive" font-size="14" fill="#0F172A">1</text>
  <text x="85" y="339" font-family="'Comic Sans MS', cursive" font-size="14" font-weight="bold" fill="#0F172A">Grade 8.8 Hex Structural Bolts</text>
  <text x="320" y="339" font-family="'Comic Sans MS', cursive" font-size="13" fill="#475569">7318</text>
  <text x="380" y="339" font-family="'Comic Sans MS', cursive" font-size="14" fill="#0F172A">20</text>
  <text x="430" y="339" font-family="'Comic Sans MS', cursive" font-size="14" fill="#0F172A">350.00</text>
  <text x="505" y="339" font-family="'Comic Sans MS', cursive" font-size="15" font-weight="bold" fill="#0F172A">7,000.00</text>
  
  <!-- Discrepancy Alert Highlight on Paper -->
  <rect x="585" y="317" width="85" height="34" fill="#FEE2E2" stroke="#DC2626" stroke-width="1.5" stroke-dasharray="3,2" rx="3"/>
  <text x="627" y="339" font-family="'Comic Sans MS', cursive" font-size="14" font-weight="bold" fill="#B91C1C" text-anchor="middle">720.00</text>

  <rect x="675" y="317" width="85" height="34" fill="#FEE2E2" stroke="#DC2626" stroke-width="1.5" stroke-dasharray="3,2" rx="3"/>
  <text x="717" y="339" font-family="'Comic Sans MS', cursive" font-size="14" font-weight="bold" fill="#B91C1C" text-anchor="middle">720.00</text>

  <!-- Totals Box with Arithmetic Slip -->
  <rect x="390" y="380" width="375" height="180" fill="#FFFFFF" stroke="#D97706" rx="5" filter="url(#inkShadow)"/>
  
  <text x="410" y="410" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#64748B">Subtotal Taxable:</text>
  <text x="740" y="410" font-family="'Comic Sans MS', cursive" font-size="15" font-weight="bold" fill="#0F172A" text-anchor="end">7,000.00</text>
  
  <text x="410" y="440" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#B91C1C">Written Tax (9%+9% = 18%):</text>
  <text x="740" y="440" font-family="'Comic Sans MS', cursive" font-size="15" font-weight="bold" fill="#B91C1C" text-anchor="end">1,440.00*</text>
  
  <text x="410" y="465" font-family="'Inter', Arial, sans-serif" font-size="10" fill="#B45309">⚡ Calculation Slip: 18% of 7,000 is 1,260, not 1,440</text>
  
  <line x1="405" y1="480" x2="750" y2="480" stroke="#FDE68A" stroke-width="2"/>
  
  <rect x="405" y="492" width="345" height="50" fill="#FEF3C7" rx="4"/>
  <text x="420" y="522" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#92400E">WRITTEN GRAND TOTAL:</text>
  <text x="735" y="523" font-family="'Comic Sans MS', cursive" font-size="18" font-weight="bold" fill="#B91C1C" text-anchor="end">₹8,440.00</text>

  <!-- Repair Annotation Bubble -->
  <rect x="35" y="385" width="330" height="150" fill="#FFFBEB" stroke="#F59E0B" stroke-width="1.5" rx="5"/>
  <text x="50" y="412" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#92400E">🔧 GSTLens Auto-Repair Detection</text>
  <text x="50" y="435" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#78350F">• Detected +₹180 arithmetic overcharge on paper.</text>
  <text x="50" y="455" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#78350F">• Proposed CGST: ₹630.00 · SGST: ₹630.00</text>
  <text x="50" y="475" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#15803D">• Corrected Grand Total: ₹8,260.00</text>
  
  <rect x="50" y="492" width="220" height="28" fill="#FEF3C7" stroke="#FCD34D" rx="4"/>
  <text x="160" y="511" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400E" text-anchor="middle">~ REPAIRED &amp; AUDITABLE</text>

  <!-- Stamp -->
  <rect x="55" y="570" width="180" height="55" fill="none" stroke="#DC2626" stroke-width="2" stroke-dasharray="4,2" rx="4"/>
  <text x="145" y="602" font-family="'Courier New', monospace" font-size="13" font-weight="bold" fill="#DC2626" text-anchor="middle">SHREE GANESH TRADERS</text>
  <text x="145" y="618" font-family="'Courier New', monospace" font-size="10" fill="#DC2626" text-anchor="middle">AUTHENTIC BILL-BOOK</text>
</svg>"""


def create_invoice_c_svg() -> str:
    """Invoice C — Adversarial Statutory Conflict & Fake GSTIN (Needs Review)"""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 700" width="800" height="700">
  <!-- Red Flag Themed Document -->
  <rect width="800" height="700" fill="#FFF5F5" rx="6"/>
  <rect x="18" y="18" width="764" height="664" fill="none" stroke="#DC2626" stroke-width="2.5" rx="6"/>
  
  <!-- Warning Header Banner -->
  <rect x="25" y="25" width="750" height="65" fill="#7F1D1D" rx="4"/>
  <text x="400" y="55" font-family="'Inter', Arial, sans-serif" font-size="19" font-weight="bold" fill="#FEE2E2" text-anchor="middle" letter-spacing="1">TAX INVOICE — VIGHNAHARTA STEELS &amp; FABRICATION</text>
  <text x="400" y="75" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FCA5A5" text-anchor="middle">AUDIT CONFLICT DETECTED · HARD GSTIN &amp; TAX HEAD VIOLATIONS</text>

  <!-- Document Meta -->
  <rect x="35" y="100" width="730" height="42" fill="#FEE2E2" stroke="#FCA5A5" rx="4"/>
  <text x="50" y="126" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#991B1B">INVOICE NO:</text>
  <text x="140" y="126" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#7F1D1D">VSF-2026-991</text>
  
  <text x="340" y="126" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#991B1B">DATE:</text>
  <text x="390" y="126" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#7F1D1D">02-Oct-2026</text>
  
  <!-- CONFLICT 1: POS is 29 Karnataka, while Supplier is 27 Maharashtra -->
  <rect x="520" y="105" width="235" height="32" fill="#7F1D1D" rx="4"/>
  <text x="637" y="125" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF" text-anchor="middle">POS: 29 - KARNATAKA (INTER-STATE!)</text>

  <!-- Parties -->
  <rect x="35" y="152" width="355" height="115" fill="#FFFFFF" stroke="#FCA5A5" rx="4"/>
  <text x="45" y="172" font-family="'Inter', Arial, sans-serif" font-size="10" font-weight="bold" fill="#991B1B">SUPPLIER (MAHARASHTRA 27):</text>
  <text x="45" y="193" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#1A2332">Vighnaharta Steels &amp; Fabrication</text>
  <text x="45" y="211" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#68717D">Industrial Estate, Nagpur, MH</text>
  
  <!-- CONFLICT 2: Invalid Checksum GSTIN -->
  <rect x="42" y="222" width="330" height="38" fill="#FEE2E2" stroke="#DC2626" rx="4"/>
  <text x="50" y="240" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#991B1B">GSTIN: 27AAAAA9999A0Z0</text>
  <text x="50" y="254" font-family="'Inter', Arial, sans-serif" font-size="9" font-weight="bold" fill="#DC2626">✗ Fails ISO 7064 Checksum (Expected 8, Found 0)</text>

  <rect x="410" y="152" width="355" height="115" fill="#FFFFFF" stroke="#E5D9C8" rx="4"/>
  <text x="420" y="172" font-family="'Inter', Arial, sans-serif" font-size="10" font-weight="bold" fill="#68717D">BUYER (BILLED TO - KARNATAKA 29):</text>
  <text x="420" y="193" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#1A2332">Apex Engineering Solutions</text>
  <text x="420" y="211" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#68717D">Whitefield, Bengaluru, KA</text>
  <text x="420" y="234" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#68717D">GSTIN: <tspan fill="#1E3A8A">29BBBBB1111B1Z9</tspan></text>

  <!-- Items Table Header -->
  <rect x="35" y="280" width="730" height="28" fill="#7F1D1D" rx="3"/>
  <text x="50" y="299" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">#</text>
  <text x="85" y="299" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Material Description</text>
  <text x="310" y="299" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">HSN</text>
  <text x="370" y="299" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Qty</text>
  <text x="425" y="299" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Rate</text>
  <text x="500" y="299" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF">Taxable Value</text>
  <text x="590" y="299" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FCA5A5">CGST 9% (ILLEGAL)</text>
  <text x="685" y="299" font-family="'Inter', Arial, sans-serif" font-size="11" font-weight="bold" fill="#FCA5A5">SGST 9% (ILLEGAL)</text>

  <!-- Row 1 -->
  <rect x="35" y="315" width="730" height="42" fill="#FFFFFF" stroke="#FCA5A5"/>
  <text x="50" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">1</text>
  <text x="85" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="600" fill="#1A2332">MS Structural Channels 100x50</text>
  <text x="310" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#68717D">7216</text>
  <text x="375" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">12</text>
  <text x="425" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#1A2332">950.00</text>
  <text x="500" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#1A2332">11,400.00</text>
  <text x="600" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#DC2626">1,026.00*</text>
  <text x="695" y="341" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#DC2626">1,026.00*</text>

  <!-- Totals Box with Illegal Tax Head & Summation Mismatch -->
  <rect x="400" y="380" width="365" height="175" fill="#FFFFFF" stroke="#DC2626" rx="5"/>
  <text x="420" y="410" font-family="'Inter', Arial, sans-serif" font-size="12" fill="#68717D">Taxable Amount:</text>
  <text x="740" y="410" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#1A2332" text-anchor="end">₹11,400.00</text>
  
  <text x="420" y="438" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#DC2626">Charged Taxes (CGST+SGST):</text>
  <text x="740" y="438" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#DC2626" text-anchor="end">₹2,052.00</text>
  
  <text x="420" y="462" font-family="'Inter', Arial, sans-serif" font-size="10" fill="#B91C1C">⚡ Legal Violation: Inter-state supply requires IGST 18%</text>
  
  <line x1="415" y1="476" x2="750" y2="476" stroke="#FCA5A5"/>
  <rect x="415" y="488" width="335" height="46" fill="#FEE2E2" rx="4"/>
  <text x="430" y="516" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#991B1B">STATED GRAND TOTAL:</text>
  <text x="735" y="516" font-family="'Inter', Arial, sans-serif" font-size="16" font-weight="bold" fill="#991B1B" text-anchor="end">₹13,425.00*</text>
  <text x="430" y="530" font-family="'Inter', Arial, sans-serif" font-size="9" fill="#DC2626">Arithmetic mismatch: 11,400 + 2,052 = 13,452 (Diff: -₹27)</text>

  <!-- Left: Human Review Trigger Box -->
  <rect x="35" y="380" width="345" height="175" fill="#FEF2F2" stroke="#DC2626" rx="5"/>
  <text x="50" y="405" font-family="'Inter', Arial, sans-serif" font-size="13" font-weight="bold" fill="#991B1B">⛔ MANDATORY HUMAN REVIEW REQUIRED</text>
  <text x="50" y="428" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#7F1D1D">Rule 1 Failed: Supplier GSTIN Checksum Invalid</text>
  <text x="50" y="448" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#7F1D1D">Rule 3 Failed: Inter-State Place of Supply Conflict</text>
  <text x="50" y="468" font-family="'Inter', Arial, sans-serif" font-size="11" fill="#7F1D1D">Rule 6 Failed: Stated Total differs by ₹27</text>
  <text x="50" y="492" font-family="'Inter', Arial, sans-serif" font-size="10" font-weight="bold" fill="#991B1B">Notice: Auto-repair locked to prevent illegal ITC claim.</text>

  <rect x="50" y="508" width="220" height="30" fill="#7F1D1D" rx="4"/>
  <text x="160" y="528" font-family="'Inter', Arial, sans-serif" font-size="12" font-weight="bold" fill="#FFFFFF" text-anchor="middle">! ESCALATED TO AUDITOR</text>
</svg>"""


def build_seed_records() -> Dict[str, Tuple[InvoiceRecord, str]]:
    """Builds the 3 challenge records with full audit trail, rules, and bounding boxes."""
    records_map = {}

    # ──────────────────────────────────────────────────────────────────────────
    # 1. INVOICE A — FLIEWLESS / VERIFIED
    # ──────────────────────────────────────────────────────────────────────────
    svg_a = create_invoice_a_svg()
    path_a = os.path.join(TEMP_DIR, "demo_inv_a_verified.svg")
    with open(path_a, "w", encoding="utf-8") as f:
        f.write(svg_a)

    rec_a = InvoiceRecord(
        document_id="demo-inv-a-verified",
        filename="TAX_INVOICE_APEX_0381_VERIFIED.svg",
        source_type="digital_pdf",
        status="verified",
        quality_score=0.99,
        invoice=CanonicalInvoice(
            invoice_number="INV-2026-0381",
            invoice_date="12-Oct-2026",
            place_of_supply="27-Maharashtra",
            supplier=Supplier(
                name="Apex Industrial Controls Ltd.",
                gstin="27AAACA1234F1Z5",
                state_code="27",
                address="Plot 42, MIDC Industrial Area, Pune, MH",
            ),
            buyer=Buyer(
                name="Bharat Precision Engineering Works",
                gstin="27BBBCB5678K1ZF",
                state_code="27",
                address="Sector 9, Turbhe, Navi Mumbai, MH",
            ),
            line_items=[
                LineItem(
                    item_index=1,
                    description="High-Torque AC Servo Motor 750W",
                    hsn_sac="8501",
                    qty=Decimal("4"),
                    rate=Decimal("12500.00"),
                    taxable_value=Decimal("50000.00"),
                    cgst_rate=Decimal("0.09"),
                    cgst_amt=Decimal("4500.00"),
                    sgst_rate=Decimal("0.09"),
                    sgst_amt=Decimal("4500.00"),
                    line_total=Decimal("59000.00"),
                ),
                LineItem(
                    item_index=2,
                    description="Shielded Industrial Cable 50m Drum",
                    hsn_sac="8544",
                    qty=Decimal("10"),
                    rate=Decimal("2200.00"),
                    taxable_value=Decimal("22000.00"),
                    cgst_rate=Decimal("0.09"),
                    cgst_amt=Decimal("1980.00"),
                    sgst_rate=Decimal("0.09"),
                    sgst_amt=Decimal("1980.00"),
                    line_total=Decimal("25960.00"),
                ),
            ],
            totals=Totals(
                taxable_amount=Decimal("72000.00"),
                cgst_amount=Decimal("6480.00"),
                sgst_amount=Decimal("6480.00"),
                igst_amount=Decimal("0.00"),
                grand_total=Decimal("84960.00"),
            ),
        ),
        fields={
            "invoice_number": FieldValue(
                path="invoice_number",
                value="INV-2026-0381",
                confidence=0.99,
                bbox=BBox(page=1, x0=0.06, y0=0.14, x1=0.38, y1=0.20),
            ),
            "invoice_date": FieldValue(
                path="invoice_date",
                value="12-Oct-2026",
                confidence=0.98,
                bbox=BBox(page=1, x0=0.44, y0=0.14, x1=0.68, y1=0.20),
            ),
            "place_of_supply": FieldValue(
                path="place_of_supply",
                value="27-Maharashtra",
                confidence=0.99,
                bbox=BBox(page=1, x0=0.69, y0=0.14, x1=0.96, y1=0.20),
            ),
            "supplier.gstin": FieldValue(
                path="supplier.gstin",
                value="27AAACA1234F1Z5",
                confidence=0.99,
                bbox=BBox(page=1, x0=0.05, y0=0.22, x1=0.48, y1=0.37),
            ),
            "buyer.gstin": FieldValue(
                path="buyer.gstin",
                value="27BBBCB5678K1ZF",
                confidence=0.99,
                bbox=BBox(page=1, x0=0.52, y0=0.22, x1=0.95, y1=0.37),
            ),
            "totals.taxable_amount": FieldValue(
                path="totals.taxable_amount",
                value="72000.00",
                confidence=0.99,
                bbox=BBox(page=1, x0=0.53, y0=0.60, x1=0.95, y1=0.65),
            ),
            "totals.cgst_amount": FieldValue(
                path="totals.cgst_amount",
                value="6480.00",
                confidence=0.99,
                bbox=BBox(page=1, x0=0.53, y0=0.66, x1=0.95, y1=0.71),
            ),
            "totals.sgst_amount": FieldValue(
                path="totals.sgst_amount",
                value="6480.00",
                confidence=0.99,
                bbox=BBox(page=1, x0=0.53, y0=0.72, x1=0.95, y1=0.77),
            ),
            "totals.grand_total": FieldValue(
                path="totals.grand_total",
                value="84960.00",
                confidence=0.99,
                bbox=BBox(page=1, x0=0.53, y0=0.78, x1=0.95, y1=0.86),
            ),
        },
        rules=[
            RuleResult(
                rule_id=1,
                rule_name="GSTIN Format & Checksum Verification",
                passed=True,
                severity="hard",
                message="Supplier & Buyer GSTIN checksums pass ISO 7064 Mod 11,10 algorithm.",
                expected_values={"supplier": "27AAACA1234F1Z5", "buyer": "27BBBCB5678K1ZF"},
            ),
            RuleResult(
                rule_id=3,
                rule_name="State Code & Tax Symmetry (CGST Act S.8)",
                passed=True,
                severity="hard",
                message="Supplier State (27) matches POS (27). Intra-state supply correctly levied as CGST + SGST.",
                expected_values={"expected_tax": "CGST+SGST", "applied_tax": "CGST+SGST"},
            ),
            RuleResult(
                rule_id=4,
                rule_name="CGST / SGST Rate & Value Symmetry",
                passed=True,
                severity="hard",
                message="CGST (₹6,480.00) equals SGST (₹6,480.00) exactly.",
                expected_values={"cgst": "6480.00", "sgst": "6480.00"},
            ),
            RuleResult(
                rule_id=5,
                rule_name="Line Item Tax Arithmetic (9% Rate Verification)",
                passed=True,
                severity="hard",
                message="All line item taxes recomputed exactly at 9% rate with ₹0.00 variance.",
                expected_values={"calculated": "6480.00", "extracted": "6480.00", "difference": "0.00"},
            ),
            RuleResult(
                rule_id=6,
                rule_name="Grand Total Summation Invariant",
                passed=True,
                severity="hard",
                message="Taxable (₹72,000.00) + CGST (₹6,480.00) + SGST (₹6,480.00) = ₹84,960.00. Exact match.",
                expected_values={"expected_total": "84960.00", "actual_total": "84960.00"},
            ),
            RuleResult(
                rule_id=8,
                rule_name="Section 16(2) ITC Claim Compliance Check",
                passed=True,
                severity="hard",
                message="Invoice fully compliant under CGST Rule 46. Safe for 100% ITC claim.",
                expected_values={"itc_status": "ELIGIBLE"},
            ),
        ],
    )
    records_map["demo-inv-a-verified"] = (rec_a, path_a)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. INVOICE B — REPAIRABLE / ARITHMETIC SLIP
    # ──────────────────────────────────────────────────────────────────────────
    svg_b = create_invoice_b_svg()
    path_b = os.path.join(TEMP_DIR, "demo_hand_billbook_repaired.svg")
    with open(path_b, "w", encoding="utf-8") as f:
        f.write(svg_b)

    rec_b = InvoiceRecord(
        document_id="demo-inv-b-repaired",
        filename="HAND_BILLBOOK_0042_REPAIRED.svg",
        source_type="handwritten_image",
        status="repaired",
        quality_score=0.76,
        invoice=CanonicalInvoice(
            invoice_number="BB-8841",
            invoice_date="08-Oct-2026",
            place_of_supply="27-Maharashtra",
            supplier=Supplier(
                name="Shree Ganesh Hardware & Tools",
                gstin="27ABCDE1234F1Z0",
                state_code="27",
                address="Ganj Peth, Pune - 411002",
            ),
            buyer=Buyer(
                name="Apex Engineering Solutions",
                gstin="27XYZPQ5678K1ZF",
                state_code="27",
                address="MIDC Industrial Area, Pune",
            ),
            line_items=[
                LineItem(
                    item_index=1,
                    description="Grade 8.8 Hex Structural Bolts",
                    hsn_sac="7318",
                    qty=Decimal("20"),
                    rate=Decimal("350.00"),
                    taxable_value=Decimal("7000.00"),
                    cgst_rate=Decimal("0.09"),
                    cgst_amt=Decimal("630.00"),  # Repaired from 720.00
                    sgst_rate=Decimal("0.09"),
                    sgst_amt=Decimal("630.00"),  # Repaired from 720.00
                    line_total=Decimal("8260.00"), # Repaired from 8440.00
                ),
            ],
            totals=Totals(
                taxable_amount=Decimal("7000.00"),
                cgst_amount=Decimal("630.00"),  # Repaired from 720.00
                sgst_amount=Decimal("630.00"),  # Repaired from 720.00
                igst_amount=Decimal("0.00"),
                grand_total=Decimal("8260.00"), # Repaired from 8440.00
            ),
        ),
        fields={
            "invoice_number": FieldValue(
                path="invoice_number",
                value="BB-8841",
                confidence=0.92,
                bbox=BBox(page=1, x0=0.06, y0=0.14, x1=0.35, y1=0.20),
            ),
            "supplier.gstin": FieldValue(
                path="supplier.gstin",
                value="27ABCDE1234F1Z0",
                confidence=0.91,
                bbox=BBox(page=1, x0=0.05, y0=0.22, x1=0.48, y1=0.36),
            ),
            "buyer.gstin": FieldValue(
                path="buyer.gstin",
                value="27XYZPQ5678K1ZF",
                confidence=0.94,
                bbox=BBox(page=1, x0=0.52, y0=0.22, x1=0.95, y1=0.36),
            ),
            "totals.taxable_amount": FieldValue(
                path="totals.taxable_amount",
                value="7000.00",
                confidence=0.95,
                bbox=BBox(page=1, x0=0.50, y0=0.54, x1=0.95, y1=0.61),
            ),
            "totals.cgst_amount": FieldValue(
                path="totals.cgst_amount",
                value="630.00",
                confidence=0.88,
                provenance=Provenance.REPAIRED,
                bbox=BBox(page=1, x0=0.72, y0=0.45, x1=0.85, y1=0.52),
                repair_history=["Raw OCR: 720.00 -> Repaired: 630.00 (Constraint: taxable * 0.09)"],
            ),
            "totals.sgst_amount": FieldValue(
                path="totals.sgst_amount",
                value="630.00",
                confidence=0.88,
                provenance=Provenance.REPAIRED,
                bbox=BBox(page=1, x0=0.84, y0=0.45, x1=0.96, y1=0.52),
                repair_history=["Raw OCR: 720.00 -> Repaired: 630.00 (Constraint: symmetry CGST==SGST)"],
            ),
            "totals.grand_total": FieldValue(
                path="totals.grand_total",
                value="8260.00",
                confidence=0.89,
                provenance=Provenance.REPAIRED,
                bbox=BBox(page=1, x0=0.50, y0=0.69, x1=0.95, y1=0.78),
                repair_history=["Stated Total: 8440.00 -> Repaired: 8260.00 (Taxable 7000 + Taxes 1260)"],
            ),
        },
        repair_log=[
            {
                "loop": 1,
                "field": "totals.cgst_amount",
                "old_value": "720.00",
                "applied": "630.00",
                "reader": "ConstraintSolver: Taxable 7,000.00 × 9% = 630.00",
                "reason": "Writer wrote ₹720 instead of calculated ₹630 (caught ₹90 discrepancy)",
            },
            {
                "loop": 2,
                "field": "totals.sgst_amount",
                "old_value": "720.00",
                "applied": "630.00",
                "reader": "ConstraintSolver: Symmetry with CGST",
                "reason": "Writer wrote ₹720 instead of calculated ₹630 (caught ₹90 discrepancy)",
            },
            {
                "loop": 3,
                "field": "totals.grand_total",
                "old_value": "8440.00",
                "applied": "8260.00",
                "reader": "Backsolve: 7,000 + 630 + 630",
                "reason": "Corrected grand total from ₹8,440.00 to exact ₹8,260.00. Saved business ₹180 overpayment.",
            },
        ],
        rules=[
            RuleResult(
                rule_id=1,
                rule_name="GSTIN Format Checksum",
                passed=True,
                severity="hard",
                message="Supplier & Buyer GSTIN formats verified.",
            ),
            RuleResult(
                rule_id=3,
                rule_name="State Code Symmetry",
                passed=True,
                severity="hard",
                message="Intra-state Maharashtra transaction. CGST + SGST confirmed.",
            ),
            RuleResult(
                rule_id=5,
                rule_name="Tax Arithmetic Consistency Check",
                passed=True,
                severity="soft",
                message="Original tax of ₹1,440 differed from recalculation by ₹180. Successfully auto-repaired to ₹1,260.",
                expected_values={"expected_tax": "1260.00", "raw_extracted_tax": "1440.00", "difference": "-180.00"},
            ),
            RuleResult(
                rule_id=6,
                rule_name="Grand Total Recalculation",
                passed=True,
                severity="soft",
                message="Grand total resolved to ₹8,260.00. Reviewer confirmation requested before export.",
                expected_values={"expected_total": "8260.00", "original_written": "8440.00", "repaired_delta": "-180.00"},
            ),
        ],
    )
    records_map["demo-inv-b-repaired"] = (rec_b, path_b)

    # ──────────────────────────────────────────────────────────────────────────
    # 3. INVOICE C — STATUTORY CONFLICT / HUMAN REVIEW
    # ──────────────────────────────────────────────────────────────────────────
    svg_c = create_invoice_c_svg()
    path_c = os.path.join(TEMP_DIR, "demo_adv_writers_slip_review.svg")
    with open(path_c, "w", encoding="utf-8") as f:
        f.write(svg_c)

    rec_c = InvoiceRecord(
        document_id="demo-inv-c-review",
        filename="ADVERSARIAL_SLIP_0991_REVIEW.svg",
        source_type="scanned_image",
        status="needs_review",
        quality_score=0.91,
        invoice=CanonicalInvoice(
            invoice_number="VSF-2026-991",
            invoice_date="02-Oct-2026",
            place_of_supply="29-Karnataka",
            supplier=Supplier(
                name="Vighnaharta Steels & Fabrication",
                gstin="27AAAAA9999A0Z0",  # Checksum failed!
                state_code="27",
                address="Industrial Estate, Nagpur, MH",
            ),
            buyer=Buyer(
                name="Apex Engineering Solutions",
                gstin="29BBBBB1111B1Z9",
                state_code="29",
                address="Whitefield, Bengaluru, KA",
            ),
            line_items=[
                LineItem(
                    item_index=1,
                    description="MS Structural Channels 100x50",
                    hsn_sac="7216",
                    qty=Decimal("12"),
                    rate=Decimal("950.00"),
                    taxable_value=Decimal("11400.00"),
                    cgst_rate=Decimal("0.09"),
                    cgst_amt=Decimal("1026.00"),
                    sgst_rate=Decimal("0.09"),
                    sgst_amt=Decimal("1026.00"),
                    line_total=Decimal("13452.00"),
                ),
            ],
            totals=Totals(
                taxable_amount=Decimal("11400.00"),
                cgst_amount=Decimal("1026.00"),
                sgst_amount=Decimal("1026.00"),
                igst_amount=Decimal("0.00"),
                grand_total=Decimal("13425.00"), # Stated total is 13,425 vs 13,452
            ),
        ),
        fields={
            "invoice_number": FieldValue(
                path="invoice_number",
                value="VSF-2026-991",
                confidence=0.97,
                bbox=BBox(page=1, x0=0.06, y0=0.14, x1=0.35, y1=0.20),
            ),
            "place_of_supply": FieldValue(
                path="place_of_supply",
                value="29-Karnataka",
                confidence=0.98,
                bbox=BBox(page=1, x0=0.64, y0=0.14, x1=0.96, y1=0.20),
            ),
            "supplier.gstin": FieldValue(
                path="supplier.gstin",
                value="27AAAAA9999A0Z0",
                confidence=0.94,
                bbox=BBox(page=1, x0=0.05, y0=0.29, x1=0.48, y1=0.38),
            ),
            "buyer.gstin": FieldValue(
                path="buyer.gstin",
                value="29BBBBB1111B1Z9",
                confidence=0.96,
                bbox=BBox(page=1, x0=0.52, y0=0.22, x1=0.95, y1=0.36),
            ),
            "totals.taxable_amount": FieldValue(
                path="totals.taxable_amount",
                value="11400.00",
                confidence=0.97,
                bbox=BBox(page=1, x0=0.50, y0=0.54, x1=0.95, y1=0.60),
            ),
            "totals.cgst_amount": FieldValue(
                path="totals.cgst_amount",
                value="1026.00",
                confidence=0.94,
                bbox=BBox(page=1, x0=0.72, y0=0.45, x1=0.85, y1=0.52),
            ),
            "totals.sgst_amount": FieldValue(
                path="totals.sgst_amount",
                value="1026.00",
                confidence=0.94,
                bbox=BBox(page=1, x0=0.85, y0=0.45, x1=0.96, y1=0.52),
            ),
            "totals.grand_total": FieldValue(
                path="totals.grand_total",
                value="13425.00",
                confidence=0.96,
                bbox=BBox(page=1, x0=0.50, y0=0.69, x1=0.95, y1=0.78),
            ),
        },
        needs_review=[
            "Rule 1: Supplier GSTIN checksum invalid (checksum digit 0 != expected 8)",
            "Rule 3: Statutory State & Tax Head Mismatch. Inter-state supply to Karnataka (29) requires IGST, but CGST+SGST billed.",
            "Rule 6: Grand Total Arithmetic Mismatch (Stated ₹13,425.00 vs Recalculated ₹13,452.00, Diff: ₹27.00)",
        ],
        rules=[
            RuleResult(
                rule_id=1,
                rule_name="GSTIN Checksum (ISO 7064 Mod 11,10)",
                passed=False,
                severity="hard",
                message="Supplier GSTIN 27AAAAA9999A0Z0 has an invalid checksum digit '0'. Expected '8'. Likely fake or corrupted GSTIN.",
                expected_values={"expected_checksum": "8", "extracted_checksum": "0"},
            ),
            RuleResult(
                rule_id=3,
                rule_name="Place of Supply & Statutory Tax Head (IGST Act S.7)",
                passed=False,
                severity="hard",
                message="Supplier State is 27 (Maharashtra) and Place of Supply is 29 (Karnataka). This is INTER-STATE supply requiring IGST 18%. Charging CGST+SGST violates tax statutes and blocks ITC claim under Section 16(2)(c).",
                expected_values={"statutory_head": "IGST (18%)", "charged_head": "CGST (9%) + SGST (9%)"},
            ),
            RuleResult(
                rule_id=6,
                rule_name="Grand Total Arithmetic Recalculation",
                passed=False,
                severity="hard",
                message="Stated invoice grand total (₹13,425.00) differs from line items calculation (₹13,452.00) by ₹27.00.",
                expected_values={"calculated_sum": "13452.00", "stated_total": "13425.00", "difference": "-27.00"},
            ),
        ],
    )
    records_map["demo-inv-c-review"] = (rec_c, path_c)

    return records_map
