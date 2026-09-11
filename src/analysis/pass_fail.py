"""Three-state quality decision: PASS, FAIL and ERROR."""
from typing import Any

def evaluate(metrics: dict[str, float | bool], limits: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if bool(metrics["compliance_tripped"]):
        reasons.append("电流达到保护限值")
    if float(metrics["dark_current_a"]) > float(limits["dark_current_max_a"]):
        reasons.append("暗电流超过上限")
    response = float(metrics["responsivity_a_per_w"])
    if response < float(limits["responsivity_min_a_per_w"]):
        reasons.append("响应度低于下限")
    if response > float(limits["responsivity_max_a_per_w"]):
        reasons.append("响应度高于上限")
    if float(metrics["repeatability_cv"]) > float(limits["repeatability_cv_max"]):
        reasons.append("重复性CV超过上限")
    checks = (
        ("noise_rms_a", "noise_rms_max_a", lambda value, limit: value > limit, "暗噪声RMS超过上限"),
        ("nep_w_per_sqrt_hz", "nep_max_w_per_sqrt_hz", lambda value, limit: value > limit, "NEP超过上限"),
        ("detectivity_jones", "detectivity_min_jones", lambda value, limit: value < limit, "比探测率D*低于下限"),
        ("linearity_r_squared", "linearity_r_squared_min", lambda value, limit: value < limit, "线性拟合R²低于下限"),
        ("linearity_max_error_fraction", "linearity_max_error_fraction", lambda value, limit: value > limit, "线性最大偏差超过上限"),
        ("stability_drift_fraction", "stability_drift_max_fraction", lambda value, limit: value > limit, "稳定性漂移超过上限"),
        ("stability_range_fraction", "stability_range_max_fraction", lambda value, limit: value > limit, "稳定性极差超过上限"),
        ("target_spectral_ratio", "target_spectral_ratio_min", lambda value, limit: value < limit, "目标波长相对响应低于下限"),
    )
    for metric_key, limit_key, predicate, message in checks:
        if metric_key in metrics and limit_key in limits and predicate(float(metrics[metric_key]), float(limits[limit_key])):
            reasons.append(message)
    if int(metrics.get("invalid_point_count", 0)) > 0:
        reasons.append("数据清洗剔除了无效测量点")
    return ("FAIL", reasons) if reasons else ("PASS", [])

def error_decision(message: str) -> tuple[str, list[str]]:
    return "ERROR", [message]
