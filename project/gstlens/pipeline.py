"""
GSTLens Main Pipeline Orchestrator.
Manages the end-to-end flow from file routing to final validated InvoiceRecords.
"""
from typing import List, Dict, Any
import os

from gstlens.router import route_file, PipelineRoute, RoutingDecision
from gstlens.contracts import InvoiceRecord
from gstlens.structure.normalize import normalize_to_record
from gstlens.validate.engine import run_validation_rules
from gstlens.repair.controller import run_repair_loop
from gstlens.tabular.detect_header import load_and_clean_tabular
from gstlens.tabular.group_invoices import parse_tabular_to_invoices
from gstlens.readers.text_layer import DigitalPdfReader
from gstlens.readers.mock import MockReader

class PipelineManager:
    """Orchestrates the entire GSTLens pipeline based on the routing decision."""
    
    def __init__(self):
        self.digital_pdf_reader = DigitalPdfReader()
        self.mock_reader = MockReader()  # Pluggable backend reader

    def process_file(self, file_path: str) -> List[InvoiceRecord]:
        """Entry point for processing any supported file format."""
        decision = route_file(file_path)
        filename = os.path.basename(file_path)
        
        if decision.route == PipelineRoute.REJECTED:
            raise ValueError(f"File rejected: {decision.reason}")
            
        elif decision.route == PipelineRoute.TABULAR:
            return self._process_tabular(file_path, filename)
            
        elif decision.route == PipelineRoute.DIGITAL_PDF:
            return self._process_digital_pdf(file_path, filename)
            
        else: # SCANNED_IMAGE or HANDWRITTEN_IMAGE
            return self._process_image(file_path, decision, filename)

    def _process_tabular(self, file_path: str, filename: str) -> List[InvoiceRecord]:
        df = load_and_clean_tabular(file_path)
        canonical_invoices = parse_tabular_to_invoices(df, filename)
        
        records = []
        for inv in canonical_invoices:
            # Reconstruct raw dict to pass through normalizer for uniform fields/provenance
            raw_dict = inv.model_dump(mode="json")
            record = normalize_to_record(raw_dict, source_type="tabular", filename=filename, reader_name="tabular_mapper")
            record = run_validation_rules(record)
            # Repair loop skipped for tabular as it's exact; if it fails, it needs human review
            records.append(record)
        return records

    def _process_digital_pdf(self, file_path: str, filename: str) -> List[InvoiceRecord]:
        raw_dict = self.digital_pdf_reader.read_document(file_path)
        record = normalize_to_record(raw_dict, source_type="digital_pdf", filename=filename, reader_name="digital_pdf_extractor")
        record = run_validation_rules(record)
        return [record]

    def _process_image(self, file_path: str, decision: RoutingDecision, filename: str) -> List[InvoiceRecord]:
        # For this prototype/hackathon slice, we use the MockReader.
        # In full production, this would invoke VisionReader with HF_TOKEN and Layout mapping.
        
        # We can dynamically set the mock mode based on filename to show off the system capabilities
        mode = "perfect"
        if "handwritten" in filename.lower() or "repair" in filename.lower():
            mode = "misread_taxable"
        elif "gstin" in filename.lower():
            mode = "gstin_confusion"
            
        self.mock_reader.mode = mode
        raw_dict = self.mock_reader.read_document(file_path)
        
        source_t = "handwritten_image" if decision.route == PipelineRoute.HANDWRITTEN_IMAGE else "scanned_image"
        
        record = normalize_to_record(raw_dict, source_type=source_t, filename=filename, reader_name="vlm_paddle")
        record = run_validation_rules(record)
        
        # If rules fail, invoke the constraint-guided repair loop
        if record.status == "needs_review":
            record = run_repair_loop(record)
            
        return [record]

# Singleton orchestrator
pipeline = PipelineManager()
