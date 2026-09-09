from src.analysis.pass_fail import evaluate

LIMITS = {"dark_current_max_a": 1e-8, "responsivity_min_a_per_w": 0.35, "responsivity_max_a_per_w": 0.75, "repeatability_cv_max": 0.05}

def test_nominal_metrics_pass():
    assert evaluate({"dark_current_a": 1e-9, "responsivity_a_per_w": .55, "repeatability_cv": .01, "compliance_tripped": False}, LIMITS)[0] == "PASS"

def test_multiple_failures_are_preserved():
    status, reasons = evaluate({"dark_current_a": 2e-8, "responsivity_a_per_w": .1, "repeatability_cv": .1, "compliance_tripped": False}, LIMITS)
    assert status == "FAIL" and len(reasons) == 3
