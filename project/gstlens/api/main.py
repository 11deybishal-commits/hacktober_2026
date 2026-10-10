"""
GSTLens FastAPI Backend & Web Interface.
Provides REST endpoints and serves a clean, zero-dependency HTML/JS/CSS frontend.
"""
import os
import sys
import uuid
import json
import logging
from typing import List, Dict, Any, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from gstlens.pipeline import pipeline
from gstlens.contracts import InvoiceRecord
from gstlens.export.json_csv import export_to_json, export_to_csv

logger = logging.getLogger(__name__)

app = FastAPI(
    title="GSTLens API",
    description="End-to-End AI-Powered GST Invoice Intelligence System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
RECORDS_STORE: Dict[str, InvoiceRecord] = {}
DOCUMENT_FILES: Dict[str, str] = {}
TEMP_UPLOAD_DIR = os.path.join(PROJECT_ROOT, "temp_uploads")
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


@app.get("/api/health")
def health():
    return {"status": "ok", "records_count": len(RECORDS_STORE)}


@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Accepts multiple invoice files, runs the GSTLens pipeline, and stores results."""
    uploaded_records = []
    
    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in [".xlsx", ".xls", ".csv", ".pdf", ".jpg", ".jpeg", ".png", ".svg"]:
            continue
            
        saved_path = os.path.join(TEMP_UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(saved_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        try:
            records = pipeline.process_file(saved_path)
            for rec in records:
                rec.filename = file.filename
                RECORDS_STORE[rec.document_id] = rec
                DOCUMENT_FILES[rec.document_id] = saved_path
                uploaded_records.append(rec.model_dump(mode="json"))
        except Exception as e:
            logger.exception("Failed to process %s", file.filename)
            return JSONResponse(
                status_code=400,
                content={"error": f"Failed to process {file.filename}: {str(e)}"}
            )
            
    return {"status": "success", "processed_count": len(uploaded_records), "records": uploaded_records}


@app.get("/api/files/{doc_id}")
def get_document_file(doc_id: str):
    from fastapi.responses import FileResponse
    if doc_id not in DOCUMENT_FILES or not os.path.exists(DOCUMENT_FILES[doc_id]):
        raise HTTPException(status_code=404, detail="Document file not found")
    return FileResponse(DOCUMENT_FILES[doc_id])


@app.get("/api/records")
def list_records():
    return [rec.model_dump(mode="json") for rec in RECORDS_STORE.values()]


@app.get("/api/records/{doc_id}")
def get_record(doc_id: str):
    if doc_id not in RECORDS_STORE:
        raise HTTPException(status_code=404, detail="Record not found")
    return RECORDS_STORE[doc_id].model_dump(mode="json")


@app.get("/api/export/{doc_id}")
def export_record(doc_id: str, format: str = Query("json", pattern="^(json|csv)$")):
    if doc_id not in RECORDS_STORE:
        raise HTTPException(status_code=404, detail="Record not found")
    record = RECORDS_STORE[doc_id]
    if format == "json":
        return JSONResponse(content=json.loads(export_to_json(record)))
    else:
        return PlainTextResponse(content=export_to_csv(record), media_type="text/csv")


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serves the complete single-page interactive review UI."""
    return HTML_CONTENT


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>GSTLens — GST Invoice Intelligence System</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --verified-bg: #064e3b;
      --verified-text: #34d399;
      --repaired-bg: #78350f;
      --repaired-text: #fbbf24;
      --review-bg: #7f1d1d;
      --review-text: #f87171;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
    .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--card-border); padding-bottom: 16px; margin-bottom: 24px; }
    .header h1 { font-size: 1.75rem; font-weight: 700; color: #fff; }
    .header p { color: var(--text-muted); font-size: 0.9rem; font-style: italic; margin-top: 4px; }
    .badge-offline { background: #334155; color: #38bdf8; font-size: 0.8rem; font-weight: 600; padding: 6px 14px; border-radius: 9999px; display: inline-flex; align-items: center; gap: 6px; }
    .badge-offline::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #38bdf8; }

    .grid-layout { display: grid; grid-template-columns: 1fr; gap: 24px; }
    @media (min-width: 1024px) {
      .grid-layout { grid-template-columns: 380px 1fr; }
    }

    .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; }
    .card-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }

    /* Upload Area */
    .dropzone { border: 2px dashed #475569; border-radius: 8px; padding: 28px 16px; text-align: center; cursor: pointer; transition: 0.2s; background: #0f172a55; }
    .dropzone:hover { border-color: var(--primary); background: #1e293b; }
    .dropzone input { display: none; }
    .dropzone-icon { font-size: 2rem; margin-bottom: 8px; }
    .btn { background: var(--primary); color: white; border: none; border-radius: 6px; padding: 10px 18px; font-weight: 500; font-size: 0.9rem; cursor: pointer; width: 100%; margin-top: 14px; transition: 0.2s; }
    .btn:hover { background: var(--primary-hover); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }

    /* Stats bar */
    .stats-bar { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
    .stat-chip { background: #0f172a; border: 1px solid var(--card-border); border-radius: 8px; padding: 10px; text-align: center; }
    .stat-val { font-size: 1.25rem; font-weight: 700; }
    .stat-lbl { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

    /* Queue Table */
    .table-container { overflow-x: auto; max-height: 480px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    th { text-align: left; padding: 10px; color: var(--text-muted); border-bottom: 1px solid var(--card-border); font-weight: 600; }
    td { padding: 12px 10px; border-bottom: 1px solid #33415555; }
    tr.selected { background: #33415577; }
    tr:hover { background: #33415544; cursor: pointer; }

    .chip { padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .chip-verified { background: var(--verified-bg); color: var(--verified-text); }
    .chip-repaired { background: var(--repaired-bg); color: var(--repaired-text); }
    .chip-needs_review { background: var(--review-bg); color: var(--review-text); }

    /* Review Panel */
    .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
    .field-group { background: #0f172a; border: 1px solid var(--card-border); border-radius: 8px; padding: 14px; }
    .field-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }
    .field-value { font-size: 0.95rem; font-weight: 500; word-break: break-all; }

    .item-table { margin-top: 14px; width: 100%; font-size: 0.82rem; }
    .item-table th { background: #0f172a; padding: 8px; }
    .item-table td { padding: 8px; }

    .alert { padding: 10px 14px; border-radius: 6px; font-size: 0.85rem; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; }
    .alert-pass { background: #064e3b33; border-left: 4px solid #34d399; color: #34d399; }
    .alert-fail { background: #7f1d1d33; border-left: 4px solid #f87171; color: #f87171; }
    .alert-repair { background: #78350f33; border-left: 4px solid #fbbf24; color: #fbbf24; }

    .export-btns { display: flex; gap: 10px; margin-top: 16px; }
    .btn-secondary { background: #334155; color: white; border: 1px solid #475569; border-radius: 6px; padding: 8px 14px; font-size: 0.85rem; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; }
    .btn-secondary:hover { background: #475569; }
  </style>
</head>
<body>

  <div class="header">
    <div>
      <h1>GSTLens</h1>
      <p>Perception proposes. Arithmetic disposes. · Track 3 VYOM+ System</p>
    </div>
    <div class="badge-offline">Local &amp; Offline Mode</div>
  </div>

  <div class="grid-layout">
    
    <!-- LEFT COLUMN: Upload & Queue -->
    <div>
      <!-- Upload Card -->
      <div class="card" style="margin-bottom: 24px;">
        <div class="card-title">Upload Invoices</div>
        <div class="dropzone" id="dropzone" onclick="document.getElementById('fileInput').click()">
          <div class="dropzone-icon">📁</div>
          <div style="font-weight: 500; font-size: 0.95rem;">Click or drag invoices here</div>
          <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 4px;">.xlsx, .csv, .pdf, .jpg, .png</div>
          <input type="file" id="fileInput" multiple accept=".xlsx,.xls,.csv,.pdf,.jpg,.jpeg,.png" onchange="handleFileSelect(event)" />
        </div>
        <div id="fileListText" style="font-size: 0.8rem; color: var(--text-muted); margin-top: 8px;"></div>
        <button class="btn" id="uploadBtn" onclick="submitFiles()" disabled>Process Documents</button>
      </div>

      <!-- Batch Queue Card -->
      <div class="card">
        <div class="card-title">
          <span>Batch Queue</span>
          <span id="queueCount" style="font-size: 0.85rem; color: var(--text-muted);">0 items</span>
        </div>

        <div class="stats-bar">
          <div class="stat-chip">
            <div class="stat-val" id="statTotal">0</div>
            <div class="stat-lbl">Total</div>
          </div>
          <div class="stat-chip">
            <div class="stat-val" style="color: var(--verified-text);" id="statVerified">0</div>
            <div class="stat-lbl">Verified</div>
          </div>
          <div class="stat-chip">
            <div class="stat-val" style="color: var(--repaired-text);" id="statRepaired">0</div>
            <div class="stat-lbl">Repaired</div>
          </div>
          <div class="stat-chip">
            <div class="stat-val" style="color: var(--review-text);" id="statReview">0</div>
            <div class="stat-lbl">Review</div>
          </div>
        </div>

        <div class="table-container">
          <table id="queueTable">
            <thead>
              <tr>
                <th>File</th>
                <th>Type</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id="queueTbody">
              <tr><td colspan="3" style="text-align: center; color: var(--text-muted); padding: 24px;">No documents processed yet.</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- RIGHT COLUMN: Inspection & Review Panel -->
    <div>
      <div class="card" id="detailCard">
        <div class="card-title">
          <span id="detailTitle">Invoice Details &amp; Verification</span>
          <div id="exportBtnGroup" class="export-btns" style="display: none; margin-top: 0;">
            <a id="exportJsonLink" class="btn-secondary" target="_blank">Export JSON</a>
            <a id="exportCsvLink" class="btn-secondary" target="_blank">Export CSV</a>
          </div>
        </div>

        <div id="noSelectionMsg" style="text-align: center; color: var(--text-muted); padding: 80px 20px;">
          Select an invoice from the queue on the left to inspect its validation report, repair trail, and line items.
        </div>

        <div id="detailContent" style="display: none;">
          
          <!-- Status Banner -->
          <div id="statusBanner" style="margin-bottom: 16px;"></div>

          <!-- Repair Trail (if any) -->
          <div id="repairTrailSection" style="display: none; margin-bottom: 20px;">
            <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 8px; color: var(--repaired-text);">🛠️ Constraint-Guided Repair Trail</div>
            <div id="repairTrailList"></div>
          </div>

          <!-- Source Document Image Preview -->
          <div id="imagePreviewCard" style="margin-bottom: 20px; background: #0f172a; border: 1px solid var(--card-border); border-radius: 8px; padding: 14px;">
            <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
              <span>📷 Source Invoice Image</span>
              <a id="openFullImgLink" href="" target="_blank" class="btn-secondary" style="padding: 3px 10px; font-size: 0.75rem;">Open Full Image ↗</a>
            </div>
            <div id="imgViewerWrapper" style="max-height: 420px; overflow: auto; border-radius: 6px; background: #0b0f19; border: 1px solid #1e293b; text-align: center; padding: 8px;">
              <img id="sourceDocImg" src="" style="max-width: 100%; height: auto; display: inline-block; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);" alt="Source Invoice" />
            </div>
            <div id="noImgNotice" style="display: none; padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
              📊 Tabular spreadsheet / digital data. Directly extracted without rasterization.
            </div>
          </div>

          <!-- Header & Parties -->
          <div class="detail-grid">
            <div class="field-group">
              <div class="field-label">Invoice Number</div>
              <div class="field-value" id="f_inv_no">-</div>
            </div>
            <div class="field-group">
              <div class="field-label">Invoice Date</div>
              <div class="field-value" id="f_inv_date">-</div>
            </div>
            <div class="field-group">
              <div class="field-label">Supplier GSTIN</div>
              <div class="field-value" id="f_sup_gstin">-</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;" id="f_sup_name"></div>
            </div>
            <div class="field-group">
              <div class="field-label">Buyer GSTIN</div>
              <div class="field-value" id="f_buy_gstin">-</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;" id="f_buy_name"></div>
            </div>
          </div>

          <!-- Line Items Table -->
          <div style="margin-top: 20px;">
            <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 8px;">Line Items &amp; Tax Calculation</div>
            <div style="overflow-x: auto; border: 1px solid var(--card-border); border-radius: 8px;">
              <table class="item-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Description</th>
                    <th>HSN</th>
                    <th>Qty</th>
                    <th>Rate</th>
                    <th>Taxable</th>
                    <th>CGST</th>
                    <th>SGST</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody id="lineItemsTbody"></tbody>
              </table>
            </div>
          </div>

          <!-- Totals -->
          <div class="detail-grid" style="margin-top: 20px;">
            <div class="field-group">
              <div class="field-label">Taxable Amount</div>
              <div class="field-value" id="f_tot_taxable">₹0.00</div>
            </div>
            <div class="field-group">
              <div class="field-label">Grand Total</div>
              <div class="field-value" style="font-size: 1.15rem; font-weight: 700; color: #38bdf8;" id="f_grand_total">₹0.00</div>
            </div>
          </div>

          <!-- Rules Diagnostics -->
          <div style="margin-top: 24px;">
            <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 10px;">⚖️ GST Deterministic Rule Diagnostics</div>
            <div id="rulesList"></div>
          </div>

        </div>
      </div>
    </div>

  </div>

  <script>
    let selectedFiles = [];
    let currentRecords = [];
    let selectedRecordId = null;

    function handleFileSelect(event) {
      selectedFiles = Array.from(event.target.files);
      const btn = document.getElementById('uploadBtn');
      const text = document.getElementById('fileListText');
      if (selectedFiles.length > 0) {
        text.innerText = `${selectedFiles.length} file(s) selected: ` + selectedFiles.map(f => f.name).join(', ');
        btn.disabled = false;
      } else {
        text.innerText = '';
        btn.disabled = true;
      }
    }

    async function submitFiles() {
      const btn = document.getElementById('uploadBtn');
      btn.disabled = true;
      btn.innerText = "Processing...";

      const formData = new FormData();
      for (const file of selectedFiles) {
        formData.append("files", file);
      }

      try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        const data = await res.json();
        if (res.ok) {
          loadQueue();
          document.getElementById('fileInput').value = "";
          document.getElementById('fileListText').innerText = "";
        } else {
          alert("Upload error: " + (data.error || "Unknown"));
        }
      } catch (err) {
        alert("Server error: " + err);
      } finally {
        btn.disabled = false;
        btn.innerText = "Process Documents";
      }
    }

    async function loadQueue() {
      try {
        const res = await fetch("/api/records");
        currentRecords = await res.json();
        renderQueue();
      } catch (err) {
        console.error(err);
      }
    }

    function renderQueue() {
      const tbody = document.getElementById('queueTbody');
      const total = currentRecords.length;
      let verified = 0, repaired = 0, review = 0;

      document.getElementById('queueCount').innerText = `${total} items`;

      if (total === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--text-muted); padding: 24px;">No documents processed yet.</td></tr>';
        return;
      }

      tbody.innerHTML = "";
      currentRecords.forEach(rec => {
        if (rec.status === 'verified') verified++;
        else if (rec.status === 'repaired') repaired++;
        else review++;

        const tr = document.createElement('tr');
        if (rec.document_id === selectedRecordId) tr.className = 'selected';
        tr.onclick = () => selectRecord(rec.document_id);

        const statusClass = `chip-${rec.status}`;
        const statusLabel = rec.status === 'verified' ? '✓ Verified' : (rec.status === 'repaired' ? '~ Repaired' : '! Review');

        tr.innerHTML = `
          <td><strong>${rec.filename || 'Invoice'}</strong><br><span style="font-size:0.75rem; color:var(--text-muted)">${rec.document_id.slice(0,8)}</span></td>
          <td><span style="font-size:0.8rem; color:var(--text-muted);">${rec.source_type}</span></td>
          <td><span class="chip ${statusClass}">${statusLabel}</span></td>
        `;
        tbody.appendChild(tr);
      });

      document.getElementById('statTotal').innerText = total;
      document.getElementById('statVerified').innerText = verified;
      document.getElementById('statRepaired').innerText = repaired;
      document.getElementById('statReview').innerText = review;

      if (selectedRecordId) {
        const rec = currentRecords.find(r => r.document_id === selectedRecordId);
        if (rec) renderDetail(rec);
      }
    }

    function selectRecord(docId) {
      selectedRecordId = docId;
      renderQueue();
      const rec = currentRecords.find(r => r.document_id === docId);
      if (rec) renderDetail(rec);
    }

    function renderDetail(rec) {
      document.getElementById('noSelectionMsg').style.display = 'none';
      document.getElementById('detailContent').style.display = 'block';
      document.getElementById('exportBtnGroup').style.display = 'flex';

      document.getElementById('exportJsonLink').href = `/api/export/${rec.document_id}?format=json`;
      document.getElementById('exportCsvLink').href = `/api/export/${rec.document_id}?format=csv`;

      // Image Preview Handling
      const imgCard = document.getElementById('imagePreviewCard');
      const imgElem = document.getElementById('sourceDocImg');
      const imgWrapper = document.getElementById('imgViewerWrapper');
      const noImgNotice = document.getElementById('noImgNotice');
      const openFullLink = document.getElementById('openFullImgLink');
      const fileUrl = `/api/files/${rec.document_id}`;

      const ext = (rec.filename || '').split('.').pop().toLowerCase();
      const isImg = ['jpg', 'jpeg', 'png', 'svg', 'webp'].includes(ext) || (rec.source_type && rec.source_type.includes('image'));
      
      imgCard.style.display = 'block';
      if (isImg) {
        imgWrapper.style.display = 'block';
        noImgNotice.style.display = 'none';
        openFullLink.style.display = 'inline-flex';
        openFullLink.href = fileUrl;
        imgElem.src = fileUrl;
      } else {
        imgWrapper.style.display = 'none';
        noImgNotice.style.display = 'block';
        openFullLink.style.display = 'none';
        imgElem.src = '';
      }

      // Status Banner & Quality Metric
      const banner = document.getElementById('statusBanner');
      let statusHtml = '';
      if (rec.status === 'verified') {
        statusHtml = '<div class="alert alert-pass"><strong>✓ VERIFIED</strong> — All 12 deterministic GST mathematical and statutory rules passed without modifications.</div>';
      } else if (rec.status === 'repaired') {
        statusHtml = '<div class="alert alert-repair"><strong>~ REPAIRED</strong> — Values were corrected via closed constraint-guided repair loop & arithmetic backsolve.</div>';
      } else {
        statusHtml = '<div class="alert alert-fail"><strong>! NEEDS REVIEW</strong> — Hard rule violations unresolved after repair iterations. Human review required.</div>';
      }

      const qScore = rec.quality_score != null ? rec.quality_score : 1.0;
      const qPct = Math.round(qScore * 100);
      const qClass = qScore >= 0.7 ? 'alert-pass' : (qScore >= 0.4 ? 'alert-repair' : 'alert-fail');
      const qText = qScore >= 0.7 ? 'Sharp & High Contrast' : (qScore >= 0.4 ? 'Moderate Sharpness' : 'Low Sharpness / Blurry Camera Shot');
      statusHtml += `<div class="alert ${qClass}" style="font-size:0.8rem; margin-top:4px;">
        <span><strong>📷 Image Quality Score:</strong> ${qPct}% (${qText})</span>
        <span>Route: <code>${rec.source_type}</code></span>
      </div>`;
      banner.innerHTML = statusHtml;

      // Repair Trail
      const repairSec = document.getElementById('repairTrailSection');
      const repairList = document.getElementById('repairTrailList');
      if (rec.repair_log && rec.repair_log.length > 0) {
        repairSec.style.display = 'block';
        repairList.innerHTML = rec.repair_log.map(l => `
          <div class="alert alert-repair" style="font-size:0.8rem; margin-bottom:4px;">
            <span><strong>Loop ${l.loop} [${l.field}]:</strong> ${l.old_value || 'None'} → <strong>${l.applied}</strong></span>
            <span style="opacity:0.8;">via ${l.reader}</span>
          </div>
        `).join('');
      } else {
        repairSec.style.display = 'none';
      }

      // Headers
      const inv = rec.invoice || {};
      document.getElementById('f_inv_no').innerText = inv.invoice_number || '-';
      document.getElementById('f_inv_date').innerText = inv.invoice_date || '-';
      document.getElementById('f_sup_gstin').innerText = (inv.supplier && inv.supplier.gstin) || '-';
      document.getElementById('f_sup_name').innerText = (inv.supplier && inv.supplier.name) || '';
      document.getElementById('f_buy_gstin').innerText = (inv.buyer && inv.buyer.gstin) || '-';
      document.getElementById('f_buy_name').innerText = (inv.buyer && inv.buyer.name) || '';

      // Line items
      const itemTbody = document.getElementById('lineItemsTbody');
      itemTbody.innerHTML = '';
      (inv.line_items || []).forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${item.item_index}</td>
          <td><strong>${item.description || 'Item'}</strong></td>
          <td>${item.hsn_sac || '-'}</td>
          <td>${item.qty != null ? item.qty : '-'}</td>
          <td>₹${item.rate != null ? item.rate : '-'}</td>
          <td><strong>₹${item.taxable_value != null ? item.taxable_value : '-'}</strong></td>
          <td>₹${item.cgst_amt != null ? item.cgst_amt : '0'}</td>
          <td>₹${item.sgst_amt != null ? item.sgst_amt : '0'}</td>
          <td>₹${item.line_total != null ? item.line_total : '-'}</td>
        `;
        itemTbody.appendChild(row);
      });

      // Totals
      const totals = inv.totals || {};
      document.getElementById('f_tot_taxable').innerText = totals.taxable_amount != null ? `₹${totals.taxable_amount}` : '₹0.00';
      document.getElementById('f_grand_total').innerText = totals.grand_total != null ? `₹${totals.grand_total}` : '₹0.00';

      // Rules List
      const rulesList = document.getElementById('rulesList');
      rulesList.innerHTML = (rec.rules || []).map(r => {
        const alertClass = r.passed ? 'alert-pass' : (r.severity === 'hard' ? 'alert-fail' : 'alert-repair');
        const icon = r.passed ? '✓' : (r.severity === 'hard' ? '✗' : '⚠');
        return `
          <div class="alert ${alertClass}">
            <div><strong>${icon} ${r.rule_name}</strong>: ${r.message}</div>
            <div style="font-size:0.75rem; text-transform:uppercase; opacity:0.8;">${r.severity}</div>
          </div>
        `;
      }).join('');
    }

    // Initial load
    loadQueue();
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run("gstlens.api.main:app", host="127.0.0.1", port=8000, reload=False)
