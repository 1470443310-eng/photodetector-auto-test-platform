"""Batch-level yield and failure Pareto statistics."""
from collections import Counter
from src.domain import DutResult

def summarize(results: list[DutResult]) -> dict:
    counts = Counter(r.status for r in results)
    completed = counts["PASS"] + counts["FAIL"]
    reason_counts = Counter(reason for r in results for reason in r.reasons)
    return {
        "total": len(results),
        "pass": counts["PASS"],
        "fail": counts["FAIL"],
        "error": counts["ERROR"],
        "yield_excluding_errors": counts["PASS"] / completed if completed else 0.0,
        "first_pass_yield": counts["PASS"] / len(results) if results else 0.0,
        "failure_reasons": dict(reason_counts.most_common()),
    }
