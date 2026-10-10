# GSTLens — Frontend Architecture & Development Context Guide

> **Context Prompt for LLMs (ChatGPT / Claude / Antigravity)**  
> *This document provides a comprehensive technical overview of the GSTLens frontend application, including architecture, API endpoints, design tokens, data models, UI components, and guidelines for adding features or building external web applications (e.g. Next.js / Vite / Vanilla).*

---

## 1. Project Overview & Product Vision

**GSTLens** is an intelligent GST Invoice Audit & Verification platform designed to ingest multi-source invoice documents (digital PDFs, scanned images, camera snapshots, handwritten billbooks, and spreadsheets), extract structured data via OCR/VLMs, and validate tax arithmetic against statutory GST rules.

### Core Frontend Responsibilities
1. **Multi-Format Upload Dropzone**: Drag-and-drop ingestion of `.pdf`, `.jpg`, `.jpeg`, `.png`, `.svg`, `.csv`, `.xls`, `.xlsx`.
2. **Batch Audit Queue & Dashboard**: Real-time summary statistics (Total Processing Queue, Verified, Repaired, Flagged for Review).
3. **Interactive Side-by-Side Verification Panel**:
   - **Document Viewer**: High-resolution image/PDF preview.
   - **Metadata & Party Inspection**: Supplier GSTIN, Buyer GSTIN, Invoice Number, Invoice Date, Place of Supply.
   - **Dynamic Line Items & Tax Calculation**: Description, HSN/SAC, Qty, Rate, Taxable Value, CGST, SGST, IGST, Line Totals.
   - **Validation Rules & Audit Trail**: Visual rule breakdown showing which statutory checks passed or failed (Rule 1: GSTIN Format, Rule 3: State Match, Rule 4: Tax Symmetry, Rule 6: Tax Math, Rule 8: Grand Total).
   - **Repair Log**: Interactive history showing auto-repaired fields.
4. **Data Export**: One-click download as structured `JSON` or `CSV`.

---

## 2. Technology Stack & Design Tokens

### Current Implementation
- **Architecture**: Embedded Single Page Application (SPA) served directly by FastAPI via `HTMLResponse`.
- **Core**: Vanilla HTML5 + ES6 JavaScript + Modern CSS3.
- **Typography**: Inter (Google Fonts) (`400`, `500`, `600`, `700`).
- **Icons / Badges**: Native GFM-style status pills and SVG indicators.

### Design Tokens & Color Palette
The interface uses a modern, sleek dark mode theme with glassmorphism and semantic status highlights.

```css
:root {
  /* Background & Structure */
  --bg: #0f172a;            /* Slate 900 */
  --card-bg: #1e293b;       /* Slate 800 */
  --card-border: #334155;   /* Slate 700 */

  /* Typography */
  --text: #f8fafc;          /* Slate 50 */
  --text-muted: #94a3b8;    /* Slate 400 */

  /* Actions & Accents */
  --primary: #3b82f6;       /* Blue 500 */
  --primary-hover: #2563eb; /* Blue 600 */

  /* Status Badges */
  --verified-bg: #064e3b;   /* Emerald 900 */
  --verified-text: #34d399; /* Emerald 400 */

  --repaired-bg: #78350f;   /* Amber 900 */
  --repaired-text: #fbbf24; /* Amber 400 */

  --review-bg: #7f1d1d;     /* Red 900 */
  --review-text: #f87171;   /* Red 400 */
}
```

---

## 3. Backend API Contract Integration

The frontend communicates with a FastAPI backend running at `http://127.0.0.1:8000`.

### Endpoints Reference

#### 1. System Health
- **`GET /api/health`**
  - **Response**: `{"status": "ok", "records_count": 5}`

#### 2. File Ingestion
- **`POST /api/upload`**
  - **Request**: `multipart/form-data` with key `files` (accepts multiple files).
  - **Response**:
    ```json
    {
      "status": "success",
      "processed_count": 1,
      "records": [ /* Array of InvoiceRecord objects */ ]
    }
    ```

#### 3. Invoice Records Management
- **`GET /api/records`**
  - Returns an array of all processed `InvoiceRecord` objects.
- **`GET /api/records/{doc_id}`**
  - Returns a single `InvoiceRecord` by ID.

#### 4. Document File Streaming
- **`GET /api/files/{doc_id}`**
  - Returns raw document image (`image/jpeg`, `image/png`) or binary file for side-by-side preview.

#### 5. Data Export
- **`GET /api/export/{doc_id}?format=json`** -> JSON File Download
- **`GET /api/export/{doc_id}?format=csv`** -> CSV File Download

---

## 4. Frontend Data Models (TypeScript / JSDoc)

When extending the UI in React/Next.js/TypeScript, use these canonical types:

```typescript
export type ProcessingStatus = 'verified' | 'repaired' | 'needs_review';

export interface SupplierBuyer {
  name?: string;
  gstin?: string;
  state_code?: string;
  address?: string;
}

export interface LineItem {
  item_index: number;
  description?: string;
  hsn_sac?: string;
  qty?: number;
  rate?: number;
  discount?: number;
  taxable_value?: number;
  cgst_rate?: number;
  cgst_amt?: number;
  sgst_rate?: number;
  sgst_amt?: number;
  igst_rate?: number;
  igst_amt?: number;
  line_total?: number;
}

export interface Totals {
  taxable_amount?: number;
  cgst_amount?: number;
  sgst_amount?: number;
  igst_amount?: number;
  round_off?: number;
  grand_total?: number;
  amount_in_words?: string;
}

export interface CanonicalInvoice {
  invoice_number?: string;
  invoice_date?: string;
  place_of_supply?: string;
  is_reverse_charge: boolean;
  supplier: SupplierBuyer;
  buyer: SupplierBuyer;
  line_items: LineItem[];
  totals: Totals;
}

export interface RuleResult {
  rule_id: number;
  rule_name: string;
  passed: boolean;
  severity: 'hard' | 'soft';
  implicated_fields: string[];
  message: string;
  expected_values: Record<string, string>;
}

export interface InvoiceRecord {
  document_id: string;
  filename: string;
  source_type: 'tabular' | 'digital_pdf' | 'scanned_image' | 'handwritten_image';
  status: ProcessingStatus;
  quality_score: number;
  invoice: CanonicalInvoice;
  rules: RuleResult[];
  needs_review: string[];
  repair_log: Array<{
    field: string;
    old_val: any;
    new_val: any;
    reason: string;
  }>;
}
```

---

## 5. Key UI Component Layout & Architecture

The single-page review dashboard layout is structured as follows:

```
+-----------------------------------------------------------------------------------+
|  GSTLens — GST Invoice Intelligence System                       [System Ready]   |
+-----------------------------------------------------------------------------------+
|  [ STATS BAR ]  Total: 12  |  Verified: 8  |  Repaired: 3  |  Needs Review: 1   |
+------------------------------------+----------------------------------------------+
|  LEFT PANEL (Upload & Queue)       |  RIGHT PANEL (Side-by-Side Review Inspector) |
|                                    |                                              |
|  +------------------------------+  |  +-------------------+ +------------------+  |
|  | Drag & Drop Ingestion Zone   |  |  | Document Source   | | Invoice Metadata |  |
|  | [ Select / Drag Files ]      |  |  | Image/PDF Preview | | Supplier & Buyer |  |
|  +------------------------------+  |  +-------------------+ +------------------+  |
|                                    |                                              |
|  +------------------------------+  |  +----------------------------------------+  |
|  | Batch Document Queue Table   |  |  | Dynamic Line Items Table (HSN, Tax, Tot) |  |
|  | (File, Inv #, Status, Action)|  |  +----------------------------------------+  |
|  +------------------------------+  |                                              |
|                                    |  +--------------------+ +-----------------+  |
|                                    |  | Validation Rules   | | Repair Trail    |  |
|                                    |  | (Passed/Failed)    | | Auto-Fix History|  |
|                                    |  +--------------------+ +-----------------+  |
+------------------------------------+----------------------------------------------+
```

---

## 6. Guidelines for ChatGPT / AI Developers

When requesting ChatGPT or AI assistants to generate new UI components or refactor frontend code for GSTLens, ensure the following constraints are respected:

1. **Strict Field Alignment**: Always bind invoice fields strictly to `record.invoice.supplier.name`, `record.invoice.totals.grand_total`, etc. Do not fabricate placeholder field names.
2. **Currency & Tax Formatting**: Format financial numbers in Indian numbering system format (e.g. `₹32,345.00` or `₹1,600.08`).
3. **Status Pill Conventions**:
   - `verified`: Emerald badge (`#064e3b` / `#34d399`).
   - `repaired`: Amber badge (`#78350f` / `#fbbf24`).
   - `needs_review`: Red badge (`#7f1d1d` / `#f87171`).
4. **Interactive Responsiveness**: The dashboard uses a responsive two-column grid (`grid-template-columns: 380px 1fr` on desktop, stacked on mobile).
5. **No Blind Stubs**: Ensure API errors during file upload are explicitly displayed in a red banner toast.
