"""
GSTLens Test Suite: API & UI Smoke Tests.
Tests FastAPI endpoints: health, UI render, list records, and mock file processing.
"""
import sys
import os
import io

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from starlette.testclient import TestClient
from gstlens.api.main import app, RECORDS_STORE


client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_ui_render():
    res = client.get("/")
    assert res.status_code == 200
    assert "GSTLens" in res.text
    assert "Batch Queue" in res.text


def test_api_upload_csv():
    csv_content = (
        "Inv No,Date,Party GST No,Item,Qty,Rate,Taxable Amt,CGST Amt,SGST Amt\n"
        "INV-999,2026-10-04,27XYZPQ5678K1ZF,Hex Bolts,10,100,1000,90,90\n"
    )
    files = [
        ("files", ("test_inv.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"))
    ]
    res = client.post("/api/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["processed_count"] >= 1
    
    # Verify records endpoint returns the record
    records_res = client.get("/api/records")
    assert records_res.status_code == 200
    records = records_res.json()
    assert len(records) >= 1
    
    doc_id = records[0]["document_id"]
    detail_res = client.get(f"/api/records/{doc_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["document_id"] == doc_id
    
    # Test JSON and CSV export
    export_json = client.get(f"/api/export/{doc_id}?format=json")
    assert export_json.status_code == 200
    export_csv = client.get(f"/api/export/{doc_id}?format=csv")
    assert export_csv.status_code == 200


if __name__ == "__main__":
    test_api_health()
    test_ui_render()
    test_api_upload_csv()
    print("All API smoke tests passed successfully.")
