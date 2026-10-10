import sys
sys.path.insert(0, 'project')

from gstlens.validate.gstin import is_valid_gstin_format, is_valid_gstin_checksum, calculate_checksum
from gstlens.readers.mock import MockReader

# Test the GSTIN used in mock
test_gstins = ['27ABCPD0234F1ZE', '27XYZPQ5678K1ZF', '27ABCPD0234F12E']
for g in test_gstins:
    fmt = is_valid_gstin_format(g)
    chk = is_valid_gstin_checksum(g) if fmt else 'N/A (format fail)'
    print(f"GSTIN: {g!r:25} len={len(g)} format={fmt} checksum={chk}")

print()

# Test tax math in perfect mode
m = MockReader('perfect')
raw = m.read_document('x')
for idx, item in enumerate(raw['line_items']):
    taxable = float(item['taxable_value'])
    cgst_rate = float(item['cgst_rate'])
    cgst_amt = float(item['cgst_amt'])
    expected_cgst = taxable * cgst_rate / 100.0
    diff = abs(cgst_amt - expected_cgst)
    print(f"Item {idx}: taxable={taxable} rate={cgst_rate}% => expected={expected_cgst:.2f} got={cgst_amt} diff={diff:.2f}")

print()

# Also check repair solve logic — does it have correct field path keys?
from gstlens.structure.normalize import normalize_to_record
from gstlens.validate.engine import run_validation_rules
m2 = MockReader('misread_taxable')
raw2 = m2.read_document('x')
rec = normalize_to_record(raw2, 'scanned_image', filename='x.jpg')
rec = run_validation_rules(rec)
print("Post-validate status:", rec.status)
print("Failed rules:")
for r in rec.rules:
    if not r.passed:
        print(f"  {r.rule_name}: fields={r.implicated_fields}, expected={r.expected_values}")
print("Field keys in record (taxable fields):")
for k in rec.fields:
    if 'taxable' in k or 'cgst' in k:
        print(f"  {k!r} = {rec.fields[k].value}")
