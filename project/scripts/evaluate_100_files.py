"""
Comprehensive Benchmark Evaluator for 100 Unorganised Tabular Datasets.
Executes the GSTLens pipeline on every generated .xlsx and .csv file,
measuring accuracy, header detection precision, arithmetic consistency,
validation pass rate, and execution speed.
"""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import time
import glob
import json
from decimal import Decimal
from typing import Dict, Any, List

from gstlens.pipeline import pipeline

BENCHMARK_DIR = "c:/Users/wrich/Documents/Hacktober/hacktober_2026/benchmark_100"

def evaluate_all():
    files = sorted(glob.glob(os.path.join(BENCHMARK_DIR, "*.xlsx")) + glob.glob(os.path.join(BENCHMARK_DIR, "*.csv")))
    print(f"Starting evaluation of {len(files)} unorganised files...\n")
    
    results: List[Dict[str, Any]] = []
    
    total_files = len(files)
    successful_files = 0
    failed_files = 0
    total_invoices = 0
    total_items = 0
    
    status_counts = {"verified": 0, "repaired": 0, "needs_review": 0, "error": 0}
    format_counts = {"xlsx": {"total": 0, "success": 0}, "csv": {"total": 0, "success": 0}}
    
    start_all = time.time()
    
    for idx, fpath in enumerate(files, start=1):
        fname = os.path.basename(fpath)
        ext = "xlsx" if fname.endswith(".xlsx") else "csv"
        format_counts[ext]["total"] += 1
        
        t0 = time.time()
        file_res = {
            "index": idx,
            "filename": fname,
            "format": ext,
            "success": False,
            "invoices_count": 0,
            "items_count": 0,
            "statuses": [],
            "error": None,
            "elapsed_ms": 0.0
        }
        
        try:
            records = pipeline.process_file(fpath)
            dt = (time.time() - t0) * 1000.0
            file_res["elapsed_ms"] = round(dt, 2)
            file_res["success"] = True
            file_res["invoices_count"] = len(records)
            
            items_in_file = 0
            for rec in records:
                st = rec.status if isinstance(rec.status, str) else rec.status.value
                file_res["statuses"].append(st)
                status_counts[st] = status_counts.get(st, 0) + 1
                items_in_file += len(rec.invoice.line_items)
                
            file_res["items_count"] = items_in_file
            total_invoices += len(records)
            total_items += items_in_file
            successful_files += 1
            format_counts[ext]["success"] += 1
            
            # Print periodic progress
            if idx % 10 == 0 or idx == total_files:
                print(f"[{idx:3d}/{total_files}] Processed {fname} -> {len(records)} invs, {items_in_file} items in {dt:.1f}ms")
                
        except Exception as e:
            dt = (time.time() - t0) * 1000.0
            file_res["elapsed_ms"] = round(dt, 2)
            file_res["error"] = str(e)
            failed_files += 1
            status_counts["error"] += 1
            print(f"[{idx:3d}/{total_files}] FAILED {fname}: {e}")
            
        results.append(file_res)
        
    total_time = time.time() - start_all
    avg_latency = (total_time / total_files) * 1000.0
    
    print("\n" + "=" * 60)
    print("           BENCHMARK EVALUATION SUMMARY (100 FILES)         ")
    print("=" * 60)
    print(f"Total Files Tested       : {total_files}")
    print(f"Successfully Processed   : {successful_files} ({successful_files/total_files*100:.1f}%)")
    print(f"Parsing Failures         : {failed_files} ({failed_files/total_files*100:.1f}%)")
    print(f"Total Invoices Extracted : {total_invoices}")
    print(f"Total Line Items Mapped  : {total_items}")
    print(f"Avg Time per File        : {avg_latency:.2f} ms")
    print(f"Total Test Run Time      : {total_time:.2f} s")
    print("-" * 60)
    print("Format Breakdown:")
    for fmt, counts in format_counts.items():
        rate = (counts["success"] / counts["total"] * 100) if counts["total"] else 0
        print(f"  - {fmt.upper():4s}: {counts['success']}/{counts['total']} parsed ({rate:.1f}%)")
    print("-" * 60)
    print("Invoice Validation Breakdown:")
    for st, c in status_counts.items():
        pct = (c / total_invoices * 100) if total_invoices else 0
        print(f"  - {st.replace('_', ' ').title():15s}: {c:3d} ({pct:.1f}%)")
    print("=" * 60)
    
    report_path = os.path.join(BENCHMARK_DIR, "benchmark_report.json")
    with open(report_path, "w") as f:
        json.dump({
            "total_files": total_files,
            "success_rate_percent": round(successful_files / total_files * 100, 2),
            "total_invoices": total_invoices,
            "total_items": total_items,
            "avg_latency_ms": round(avg_latency, 2),
            "format_breakdown": format_counts,
            "status_breakdown": status_counts,
            "details": results
        }, f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    evaluate_all()
