"""
GSTIN Utilities: Checksum validation and OCR confusion repair logic.

The GSTIN mod-36 check digit algorithm:
  1. Map each of the 14 prefix characters to a value (0='0', ..., 9='9', 10='A', ..., 35='Z')
  2. Multiply even-indexed (0-based) values by 1, odd-indexed by 2
  3. For each product p: digit_sum = (p // 36) + (p % 36)
  4. Sum all digit_sums → hash_val
  5. check_value = (36 - (hash_val % 36)) % 36
  6. check_char = GSTIN_ALPHABET[check_value]
"""
import re
from typing import List, Optional

# GSTIN Checksum Alphabet (0-9, A-Z)
GSTIN_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Regex pattern for GSTIN structural format
_GSTIN_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
)

# Common OCR confusion pairs (both directions)
_OCR_CONFUSIONS = {
    "0": ["O", "Q"],
    "O": ["0", "Q"],
    "Q": ["O", "0"],
    "1": ["I", "L"],
    "I": ["1", "L"],
    "L": ["I", "1"],
    "2": ["Z"],
    "Z": ["2"],
    "5": ["S"],
    "S": ["5"],
    "8": ["B"],
    "B": ["8"],
    "6": ["G"],
    "G": ["6"],
}


def char_to_val(c: str) -> int:
    """Map a GSTIN alphabet character to its numeric value (0-35)."""
    return GSTIN_ALPHABET.index(c.upper())


def val_to_char(v: int) -> str:
    """Map a numeric value (0-35) back to its GSTIN alphabet character."""
    return GSTIN_ALPHABET[v % 36]


def calculate_checksum(gstin_14: str) -> str:
    """
    Calculates the 15th check character for a 14-character GSTIN prefix.
    Uses the official mod-36 GST checksum algorithm.
    """
    if len(gstin_14) != 14:
        raise ValueError(f"GSTIN prefix must be exactly 14 characters, got {len(gstin_14)}: {gstin_14!r}")

    hash_val = 0
    for i, char in enumerate(gstin_14.upper()):
        val = char_to_val(char)
        weight = 1 if (i % 2 == 0) else 2
        product = val * weight
        hash_val += (product // 36) + (product % 36)

    check_val = (36 - (hash_val % 36)) % 36
    return val_to_char(check_val)


def is_valid_gstin_format(gstin: str) -> bool:
    """
    Validates GSTIN structural format:
    2 digits + 5 uppercase letters + 4 digits + 1 uppercase letter +
    1 alphanumeric (not 0) + 'Z' + 1 alphanumeric
    """
    if not gstin or len(gstin) != 15:
        return False
    return bool(_GSTIN_PATTERN.match(gstin.upper()))


def is_valid_gstin_checksum(gstin: str) -> bool:
    """Validates GSTIN checksum (15th character) using mod-36 algorithm."""
    if not is_valid_gstin_format(gstin):
        return False
    try:
        expected = calculate_checksum(gstin[:14].upper())
        return gstin[14].upper() == expected
    except (ValueError, IndexError):
        return False


def generate_gstin_confusion_candidates(bad_gstin: str) -> List[str]:
    """
    Given a GSTIN that fails format or checksum validation, generate a list
    of candidate corrections using common OCR confusion substitutions.
    
    Strategy:
    1. Fix structural issues first (position 13 must be 'Z')
    2. Try single-character substitutions at each position using _OCR_CONFUSIONS
    3. Return only candidates that pass BOTH format and checksum
    """
    if not bad_gstin:
        return []

    gstin = bad_gstin.upper()
    candidates: List[str] = []
    seen = set()

    def try_add(candidate: str):
        if candidate not in seen and is_valid_gstin_format(candidate) and is_valid_gstin_checksum(candidate):
            seen.add(candidate)
            candidates.append(candidate)

    # Pass 1: Fix position 13 (must be 'Z') — covers the most common confusion (2↔Z)
    if len(gstin) == 15 and gstin[13] != 'Z':
        fixed = gstin[:13] + 'Z' + gstin[14]
        try_add(fixed)

    # Pass 2: Fix the check character (position 14) — recompute correct checksum
    if len(gstin) == 15 and is_valid_gstin_format(gstin):
        try:
            correct_check = calculate_checksum(gstin[:14])
            fixed = gstin[:14] + correct_check
            try_add(fixed)
        except ValueError:
            pass

    # Pass 3: Single-char substitution sweep across all 15 positions
    if len(gstin) == 15:
        for pos in range(15):
            char = gstin[pos]
            for replacement in _OCR_CONFUSIONS.get(char, []):
                candidate = gstin[:pos] + replacement + gstin[pos + 1:]
                try_add(candidate)

    # Pass 4: Fix position 13 AND recompute checksum together
    if len(gstin) == 15 and gstin[13] != 'Z':
        prefix14 = gstin[:13] + 'Z' + gstin[14]
        # The above is still 15 chars if we just replace pos 13; need prefix of 14
        prefix14_only = gstin[:13] + 'Z'  # only 14 chars... but we already have 15
        # Correct approach: fix pos 13 to Z, then fix pos 14 to correct check
        try:
            prefix = gstin[:13] + 'Z'
            correct_check = calculate_checksum(prefix)
            fixed = prefix + correct_check
            try_add(fixed)
        except ValueError:
            pass

    return candidates
