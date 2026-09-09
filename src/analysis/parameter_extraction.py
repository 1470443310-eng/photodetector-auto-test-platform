"""Extract engineering metrics from raw measurement points."""
from __future__ import annotations
import statistics
from src.domain import MeasurementPoint

def _nearest(points: list[MeasurementPoint], mode: str, bias_v: float) -> MeasurementPoint:
    candidates = [p for p in points if p.mode == mode]
    if not candidates:
        raise ValueError(f"no points for mode {mode}")
    return min(candidates, key=lambda p: abs(p.voltage_v - bias_v))

def extract_metrics(points: list[MeasurementPoint], reference_bias_v: float, optical_power_w: float, compliance_tripped: bool) -> dict[str, float | bool]:
    dark = _nearest(points, "dark_iv", reference_bias_v)
    light = _nearest(points, "light_iv", reference_bias_v)
    photocurrent = abs(light.current_a - dark.current_a)
    repeats = [abs(p.current_a) for p in points if p.mode == "repeatability"]
    repeat_mean = statistics.fmean(repeats)
    repeatability_cv = statistics.stdev(repeats) / repeat_mean if len(repeats) > 1 and repeat_mean else 0.0
    noise_std_a = statistics.stdev(repeats) if len(repeats) > 1 else 0.0
    return {
        "reference_bias_v": reference_bias_v,
        "dark_current_a": abs(dark.current_a),
        "light_current_a": abs(light.current_a),
        "photocurrent_a": photocurrent,
        "responsivity_a_per_w": photocurrent / optical_power_w,
        "repeatability_cv": repeatability_cv,
        "repeatability_noise_std_a": noise_std_a,
        "compliance_tripped": compliance_tripped,
    }
