# GSTLens Performance & Evaluation Report

**Generated:** Automatic Benchmark Harness  
**Track:** VYOM+ Track 3 — End-to-End AI-Powered GST Invoice Intelligence System

---

## 1. Executive Summary

| Metric | Target | Benchmark Result | Status |
|---|---|---|---|
| **Silent Error Rate (SER)** | $< 1.0\%$ | **0.00%** | 🟢 **OPTIMAL** |
| **Post-Repair Pass Rate** | $> 70\%$ | **75.0%** | 🟢 **OPTIMAL** |
| **Repair Accuracy Lift** | $> +20\%$ | **+50.0%** | 🟢 **OPTIMAL** |
| **Flag Precision** | $> 90\%$ | **100.0%** | 🟢 **OPTIMAL** |

> **Key Takeaway:** Raw perception produced initial failures due to optical ink confusion ($5,490$ for $5,400$, and $Z \to 2$). The constraint-guided repair loop completely eliminated silent failures, delivering **0.00% Silent Error Rate** and boosting document pass rate by **+50.0%**, while safely escalating irreconcilable paper errors to human review.

---

## 2. Category-Wise Performance Breakdown

| Document Scenario | Category | Pre-Repair Accuracy | Post-Repair Accuracy | Repairs Made | Final Verdict |
|---|---|---|---|---|---|
| **Clean Printed Tax Invoice** | Printed | 100.0% | **100.0%** | 0 | 🟢 VERIFIED |
| **Handwritten Bill-Book (Ink Misread 5,490)** | Handwritten | 87.5% | **100.0%** | 3 | 🟡 REPAIRED |
| **Camera Shot Bill (GSTIN Z->2 Confusion)** | Camera Photo | 87.5% | **100.0%** | 1 | 🟡 REPAIRED |
| **Adversarial Bill-Book (Writer Arithmetic Slip on Paper)** | Adversarial | 100.0% | **100.0%** | 0 | 🔴 NEEDS REVIEW |

---

## 3. Four-Tier Ablation Study

| Ablation Level | Pipeline Description | Document Pass Rate | Silent Error Rate |
|---|---|---|---|
| **Level A** | Raw Single-Pass OCR | 25.0% | 25.0% |
| **Level B** | OCR + Schema-Constrained Pydantic | 25.0% | 25.0% |
| **Level C** | Level B + 12 GST Validation Rules (Flagging Only) | 25.0% | 0.0% (Flagged) |
| **Level D (Full)** | **Level C + Constraint-Guided Repair Loop (GSTLens)** | **75.0% (+50% lift)** | **0.0% (Zero Silent Errors)** |

*Note on Honest Scoping:* 100% pass rate on adversarial data is an anti-pattern (indicating unchecked hallucinations). In GSTLens, 75.0% represents verified clean & auto-repaired invoices, while the remaining 25.0% represents contradictory paper errors safely escalated for accountant audit with zero silent errors.

---

## 4. Arithmetic Proof of Auto-Repairs

1. **Taxable Value Ink Misread ($5,490 \to 5,400$):**
   * **Rule Failures:** Line Math ($12 \times 450 \neq 5490$) and Tax Math ($5490 \times 9\% \neq 486$).
   * **Backsolve:** $486 / 0.09 = 5,400.00$ agrees with $12 \times 450 = 5,400.00$.
   * **Outcome:** Repaired to **$5,400.00$**; all 12 rules passed.

2. **GSTIN Character Confusion ($Z \to 2$ at pos 13):**
   * **Rule Failure:** Mod-36 Checksum and Positional regex violation on `27ABCDE1234F120`.
   * **Confusion Solver:** Tested substitution pair $2 \leftrightarrow Z \implies `27ABCDE1234F1Z0`$.
   * **Outcome:** Checksum verified; repaired to **`27ABCDE1234F1Z0`**.
