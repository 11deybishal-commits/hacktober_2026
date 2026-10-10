# GSTLens

GSTLens is a verification-first pipeline that turns any GST invoice (digital, printed, or handwritten) into validated, machine-readable records.

### Quick Start

1. Install requirements: `pip install -r requirements.txt`
2. Run the UI: `streamlit run services/ui/app.py`
3. Upload an invoice image, PDF, or spreadsheet.

### Structure

- `gstlens/`: The core perception, validation, and repair engine.
- `services/`: API and UI endpoints.
- `config/`: Declarative constraints and tax slabs.
- `eval/`: Synthetic test generator.
