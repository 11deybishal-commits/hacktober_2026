import os
import sys
import streamlit as st
import pandas as pd
from typing import List, Dict

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from gstlens.pipeline import pipeline
from gstlens.contracts import InvoiceRecord
from gstlens.export.json_csv import export_to_json, export_to_csv

st.set_page_config(page_title="GSTLens | Perception proposes. Arithmetic disposes.", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .verified { color: #0f766e; font-weight: bold; background-color: #ccfbf1; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; }
    .repaired { color: #b45309; font-weight: bold; background-color: #fef3c7; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; }
    .needs_review { color: #b91c1c; font-weight: bold; background-color: #fee2e2; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; }
    .header-box { border-bottom: 2px solid #e5e7eb; padding-bottom: 1rem; margin-bottom: 1.5rem; }
    .title-text { font-family: 'Inter', sans-serif; }
    .offline-badge { float: right; background-color: #374151; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8em; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "records" not in st.session_state:
    st.session_state.records = {}
if "selected_record_id" not in st.session_state:
    st.session_state.selected_record_id = None

# --- HEADER ---
st.markdown('<div class="header-box"><span class="offline-badge">● Local · Offline</span><h1 class="title-text">GSTLens</h1><p style="color: #6b7280; font-style: italic;">Perception proposes. Arithmetic disposes.</p></div>', unsafe_allow_html=True)

# --- UPLOAD SECTION ---
st.markdown("### 📤 Upload Invoices")
st.markdown("Accepts `.xlsx`, `.csv`, `.pdf`, `.jpg`, `.png`")

uploaded_files = st.file_uploader("Drop invoices here", accept_multiple_files=True, type=["xlsx", "csv", "pdf", "jpg", "jpeg", "png"])

if st.button("Process Invoices", type="primary") and uploaded_files:
    # Processing block
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Save files to temp and process
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    for idx, file in enumerate(uploaded_files):
        status_text.text(f"Routing and Reading: {file.name}...")
        file_path = os.path.join(temp_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
            
        try:
            results = pipeline.process_file(file_path)
            for record in results:
                st.session_state.records[record.document_id] = record
        except Exception as e:
            st.error(f"Error processing {file.name}: {str(e)}")
            
        progress_bar.progress((idx + 1) / len(uploaded_files))
        
    status_text.text("Processing complete.")
    progress_bar.empty()
    status_text.empty()

# --- BATCH QUEUE VIEW ---
if st.session_state.records:
    st.markdown("### 📋 Batch Queue")
    
    # Summary stats
    stats_cols = st.columns(5)
    records_list = list(st.session_state.records.values())
    verified = len([r for r in records_list if r.status == "verified"])
    repaired = len([r for r in records_list if r.status == "repaired"])
    needs_review = len([r for r in records_list if r.status == "needs_review"])
    
    stats_cols[0].metric("Total", len(records_list))
    stats_cols[1].metric("✓ Verified", verified)
    stats_cols[2].metric("~ Repaired", repaired)
    stats_cols[3].metric("! Needs Review", needs_review)
    
    # Build Table
    table_data = []
    for r in records_list:
        status_html = ""
        if r.status == "verified":
            status_html = "✓ Verified"
        elif r.status == "repaired":
            status_html = "~ Repaired"
        else:
            status_html = "! Needs review"
            
        flags = len(r.needs_review) if r.needs_review else "-"
        table_data.append({
            "ID": r.document_id[:8],
            "File": r.filename,
            "Type": r.source_type,
            "Status": r.status.upper(),
            "Flags": flags
        })
        
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Selection
    selected_id_prefix = st.selectbox("Select Invoice ID to Review", ["-- Select --"] + [r["ID"] for r in table_data])
    if selected_id_prefix != "-- Select --":
        full_id = next(r.document_id for r in records_list if r.document_id.startswith(selected_id_prefix))
        st.session_state.selected_record_id = full_id

# --- REVIEW VIEW ---
if st.session_state.selected_record_id:
    record: InvoiceRecord = st.session_state.records[st.session_state.selected_record_id]
    st.markdown("---")
    
    status_class = record.status
    if status_class == "needs_review":
        status_class_label = "needs_review"
        icon = "!"
    elif status_class == "repaired":
        status_class_label = "repaired"
        icon = "~"
    else:
        status_class_label = "verified"
        icon = "✓"
        
    st.markdown(f"### Review: {record.filename} <span class='{status_class_label}'>{icon} {record.status.upper()}</span>", unsafe_allow_html=True)
    
    # Export buttons
    dl_cols = st.columns([1, 1, 8])
    with dl_cols[0]:
        st.download_button("Export JSON", export_to_json(record), file_name=f"{record.filename}.json", mime="application/json")
    with dl_cols[1]:
        st.download_button("Export CSV", export_to_csv(record), file_name=f"{record.filename}.csv", mime="text/csv")
        
    # Split View
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown("#### Source Document")
        st.info("Image viewer with bounding boxes would render here. (For Hackathon demo, image overlay implemented via OpenCV/Pillow)")
        
        if record.repair_log:
            st.markdown("#### 🛠️ Repair Trail")
            for log in record.repair_log:
                st.warning(f"**Loop {log['loop']} | {log['field']}**: {log['reason']} -> Applied {log['applied']}")
                
        if record.rules:
            st.markdown("#### ⚖️ Rule Diagnostics")
            for rule in record.rules:
                if rule.passed:
                    st.success(f"{rule.rule_name}: {rule.message}")
                else:
                    st.error(f"{rule.rule_name}: {rule.message}")
                    
    with col2:
        st.markdown("#### Extracted Record")
        
        with st.expander("Header & Parties", expanded=True):
            h_col1, h_col2 = st.columns(2)
            h_col1.text_input("Invoice Number", value=record.invoice.invoice_number or "")
            h_col2.text_input("Invoice Date", value=record.invoice.invoice_date or "")
            
            st.markdown("**Supplier**")
            h_col1.text_input("Name", value=record.invoice.supplier.name or "", key="s_name")
            h_col2.text_input("GSTIN", value=record.invoice.supplier.gstin or "", key="s_gstin")
            
            st.markdown("**Buyer**")
            h_col1.text_input("Name", value=record.invoice.buyer.name or "", key="b_name")
            h_col2.text_input("GSTIN", value=record.invoice.buyer.gstin or "", key="b_gstin")
            
        with st.expander("Line Items", expanded=True):
            items_data = []
            for item in record.invoice.line_items:
                items_data.append({
                    "Desc": item.description,
                    "HSN": item.hsn_sac,
                    "Qty": float(item.qty) if item.qty else None,
                    "Rate": float(item.rate) if item.rate else None,
                    "Taxable": float(item.taxable_value) if item.taxable_value else None,
                    "CGST": float(item.cgst_amt) if item.cgst_amt else None,
                    "SGST": float(item.sgst_amt) if item.sgst_amt else None,
                    "Total": float(item.line_total) if item.line_total else None,
                })
            st.data_editor(pd.DataFrame(items_data), num_rows="dynamic", use_container_width=True)
            
        with st.expander("Totals", expanded=True):
            t_col1, t_col2 = st.columns(2)
            t_col1.text_input("Taxable Amount", value=str(record.invoice.totals.taxable_amount) or "")
            t_col2.text_input("Total Tax", value=str((record.invoice.totals.cgst_amount or 0) + (record.invoice.totals.sgst_amount or 0) + (record.invoice.totals.igst_amount or 0)))
            st.text_input("Grand Total", value=str(record.invoice.totals.grand_total) or "")
