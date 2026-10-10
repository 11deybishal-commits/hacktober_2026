"""
GSTLens Evaluation Metrics Engine.
Computes field-level Exact Match (EM), Silent Error Rate (SER),
repair efficiency, and flag precision against ground truth.
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal


def compute_field_accuracy(pred_fields: Dict[str, Any], gt_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares predicted fields to ground truth fields.
    Returns matched count, total count, and per-field matches.
    """
    total = len(gt_fields)
    matches = 0
    details = {}

    for field, expected in gt_fields.items():
        predicted = pred_fields.get(field)
        # Normalize strings and decimals
        p_clean = str(predicted).strip().upper() if predicted is not None else ""
        e_clean = str(expected).strip().upper() if expected is not None else ""

        is_match = (p_clean == e_clean)
        if not is_match and p_clean and e_clean:
            try:
                # Compare as numeric floats if both numbers
                is_match = abs(float(p_clean) - float(e_clean)) < 0.05
            except ValueError:
                pass

        if is_match:
            matches += 1
        details[field] = {"predicted": predicted, "expected": expected, "match": is_match}

    accuracy = (matches / total) if total > 0 else 1.0
    return {
        "total_fields": total,
        "matched_fields": matches,
        "accuracy": round(accuracy, 4),
        "details": details,
    }


def compute_silent_error_rate(eval_items: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Computes the Silent Error Rate (SER) — the critical accounting metric:
    SER = (Wrong numbers that passed UNFLAGGED) / (Total fields)
    A flagged error is safe for review; a silent error creates tax penalty.
    """
    total_fields = 0
    silent_errors = 0
    flagged_errors = 0
    correct_fields = 0

    for item in eval_items:
        details = item.get("field_details", {})
        flagged_fields = set(item.get("flagged_fields", []))

        for field, res in details.items():
            total_fields += 1
            if res["match"]:
                correct_fields += 1
            else:
                if field in flagged_fields:
                    flagged_errors += 1
                else:
                    # An error that was NOT flagged! Silent failure!
                    silent_errors += 1

    ser = (silent_errors / total_fields) if total_fields > 0 else 0.0
    flag_recall = (flagged_errors / (silent_errors + flagged_errors)) if (silent_errors + flagged_errors) > 0 else 1.0

    return {
        "total_fields": total_fields,
        "silent_errors": silent_errors,
        "flagged_errors": flagged_errors,
        "correct_fields": correct_fields,
        "silent_error_rate": round(ser, 4),
        "flag_recall": round(flag_recall, 4),
    }


def compute_repair_lift(pre_repair_records: List[Any], post_repair_records: List[Any]) -> Dict[str, Any]:
    """
    Measures the lift/improvement delivered by the constraint-guided repair loop:
    (Pass rate after repair) vs (Pass rate before repair).
    """
    total = len(pre_repair_records)
    if total == 0:
        return {"pre_pass_rate": 0.0, "post_pass_rate": 0.0, "lift_percentage": 0.0}

    pre_pass = sum(1 for r in pre_repair_records if getattr(r, "status", "") == "verified")
    post_pass = sum(1 for r in post_repair_records if getattr(r, "status", "") in ("verified", "repaired"))

    pre_rate = pre_pass / total
    post_rate = post_pass / total
    lift = (post_rate - pre_rate) * 100

    return {
        "total_documents": total,
        "pre_pass_count": pre_pass,
        "post_pass_count": post_pass,
        "pre_pass_rate": round(pre_rate, 4),
        "post_pass_rate": round(post_rate, 4),
        "lift_percentage": round(lift, 2),
    }
