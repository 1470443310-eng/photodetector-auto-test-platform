"""Three-state quality decision: PASS, FAIL and ERROR."""
from typing import Any

def evaluate(metrics: dict[str, float | bool], limits: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if bool(metrics["compliance_tripped"]):
        reasons.append("current compliance tripped")
    if float(metrics["dark_current_a"]) > float(limits["dark_current_max_a"]):
        reasons.append("dark current above maximum")
    response = float(metrics["responsivity_a_per_w"])
    if response < float(limits["responsivity_min_a_per_w"]):
        reasons.append("responsivity below minimum")
    if response > float(limits["responsivity_max_a_per_w"]):
        reasons.append("responsivity above maximum")
    if float(metrics["repeatability_cv"]) > float(limits["repeatability_cv_max"]):
        reasons.append("repeatability CV above maximum")
    return ("FAIL", reasons) if reasons else ("PASS", [])

def error_decision(message: str) -> tuple[str, list[str]]:
    return "ERROR", [message]
