"""
GSTIN Utilities: Checksum validation and OCR confusion repair logic.
"""
from typing import List

# GSTIN Checksum Alphabet (0-9, A-Z)
GSTIN_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def char_to_val(c: str) -> int:
    return GSTIN_ALPHABET.index(c.upper())

def val_to_char(v: int) -> str:
    return GSTIN_ALPHABET[v]

def calculate_checksum(gstin_14: str) -> str:
    """Calculates the 15th checksum character of a 14-char GSTIN prefix."""
    if len(gstin_14) != 14:
        raise ValueError("GSTIN prefix must be exactly 14 characters.")
        
    hash_val = 0
    for i, char in enumerate(gstin_14):
        val = char_to_val(char)
        weight = 2 if (i % 2 == 0) else 1
        product = val * weight
        hash_val += (product // 36) + (product % 36)
        
    check_val = (36 - (hash_val % 36)) % 36
    return val_to_char(check_val)

def is_valid_gstin_format(gstin: str) -> bool:
    import re
    if not gstin or len(gstin) != 15:
        return False
    return bool(re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", gstin))

def is_valid_gstin_checksum(gstin: str) -> bool:
    if not is_valid_gstin_format(gstin):
        return False
    expected = calculate_checksum(gstin[:14])
    return gstin[14].upper() == expected

def generate_gstin_confusion_candidates(bad_gstin: str) -> List[str]:
    """
    If a GSTIN fails checksum, generate candidate fixes using common OCR confusions.
    Confusions: 0↔O, 1↔I, 2↔Z, 5↔S, 8↔B
    """
    if len(bad_gstin) != 15:
        return []
        
    confusions = {
        "0": ["O"], "O": ["0"],
        "1": ["I"], "I": ["1"],
        "2": ["Z"], "Z": ["2"],
        "5": ["S"], "S": ["5"],
        "8": ["B"], "B": ["8"]
    }
    
    candidates = []
    # Try fixing the 14th character (usually 'Z' misread as '2')
    if bad_gstin[13] != 'Z':
        test_gstin = bad_gstin[:13] + 'Z' + bad_gstin[14]
        if is_valid_gstin_checksum(test_gstin):
            candidates.append(test_gstin)
            
    # Try fixing the check character itself
    try:
        correct_check = calculate_checksum(bad_gstin[:14])
        if bad_gstin[14] in confusions.get(correct_check, []):
            candidates.append(bad_gstin[:14] + correct_check)
    except Exception:
        pass
        
    return candidates
