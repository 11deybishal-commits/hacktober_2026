"""
GSTLens Test Suite: GSTIN Utilities.
Tests GSTIN structural regex, mod-36 checksum calculation, and OCR confusion candidate generation.
"""
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gstlens.validate.gstin import (
    char_to_val,
    val_to_char,
    calculate_checksum,
    is_valid_gstin_format,
    is_valid_gstin_checksum,
    generate_gstin_confusion_candidates,
)


def test_char_val_mapping():
    assert char_to_val("0") == 0
    assert char_to_val("9") == 9
    assert char_to_val("A") == 10
    assert char_to_val("Z") == 35
    assert val_to_char(0) == "0"
    assert val_to_char(35) == "Z"


def test_valid_gstin_checksum_calculation():
    # 27ABCDE1234F1Z0 -> check digit 0
    prefix_14 = "27ABCDE1234F1Z"
    expected_char = calculate_checksum(prefix_14)
    assert expected_char == "0"

    # 27XYZPQ5678K1Z -> check digit F
    prefix_buyer = "27XYZPQ5678K1Z"
    assert calculate_checksum(prefix_buyer) == "F"


def test_is_valid_gstin_format():
    # Valid 15-character structural format
    assert is_valid_gstin_format("27ABCDE1234F1Z0") is True
    assert is_valid_gstin_format("27XYZPQ5678K1ZF") is True
    
    # Invalid length
    assert is_valid_gstin_format("27ABCDE1234F1Z") is False
    assert is_valid_gstin_format("27ABCDE1234F1Z00") is False

    # Invalid characters (lowercase or symbols)
    assert is_valid_gstin_format("27abcde1234f1z0") is True  # handled via upper()
    assert is_valid_gstin_format("27ABCDE1234F1!0") is False

    # Position 13 must be 'Z'
    assert is_valid_gstin_format("27ABCDE1234F120") is False  # '2' at pos 13 fails


def test_is_valid_gstin_checksum():
    assert is_valid_gstin_checksum("27ABCDE1234F1Z0") is True
    assert is_valid_gstin_checksum("27XYZPQ5678K1ZF") is True

    # Corrupted check character
    assert is_valid_gstin_checksum("27ABCDE1234F1Z9") is False
    assert is_valid_gstin_checksum("27XYZPQ5678K1Z1") is False


def test_generate_gstin_confusion_candidates():
    # Bad GSTIN where Z was misread as 2 at pos 13: 27ABCDE1234F120
    bad_gstin = "27ABCDE1234F120"
    candidates = generate_gstin_confusion_candidates(bad_gstin)
    
    assert len(candidates) > 0
    # The valid GSTIN "27ABCDE1234F1Z0" must be among the generated candidates
    assert "27ABCDE1234F1Z0" in candidates
    
    # All returned candidates must be 15 chars and pass checksum
    for cand in candidates:
        assert len(cand) == 15
        assert is_valid_gstin_checksum(cand) is True


if __name__ == "__main__":
    test_char_val_mapping()
    test_valid_gstin_checksum_calculation()
    test_is_valid_gstin_format()
    test_is_valid_gstin_checksum()
    test_generate_gstin_confusion_candidates()
    print("All GSTIN tests passed successfully.")
