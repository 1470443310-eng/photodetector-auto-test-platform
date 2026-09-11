"""Extract traceable electrical, optical, noise and stability metrics."""
from __future__ import annotations

import math
import statistics
from src.domain import MeasurementPoint


def _nearest(points: list[MeasurementPoint], mode: str, bias_v: float) -> MeasurementPoint:
    candidates = [p for p in points if p.mode == mode]
    if not candidates:
        raise ValueError(f"no points for mode {mode}")
    return min(candidates, key=lambda p: abs(p.voltage_v - bias_v))


def _linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0, 0.0, 0.0
    x_mean, y_mean = statistics.fmean(xs), statistics.fmean(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator if denominator else 0.0
    intercept = y_mean - slope * x_mean
    fitted = [slope * x + intercept for x in xs]
    ss_total = sum((y - y_mean) ** 2 for y in ys)
    ss_residual = sum((y - fit) ** 2 for y, fit in zip(ys, fitted))
    r_squared = 1.0 - ss_residual / ss_total if ss_total else 1.0
    full_scale = max(ys) - min(ys)
    max_error = max((abs(y - fit) for y, fit in zip(ys, fitted)), default=0.0)
    return slope, max(0.0, min(1.0, r_squared)), max_error / full_scale if full_scale else 0.0


def extract_metrics(
    points: list[MeasurementPoint], reference_bias_v: float, optical_power_w: float,
    compliance_tripped: bool, detector_area_cm2: float = 0.01,
    noise_bandwidth_hz: float = 1.0, target_wavelength_nm: float = 850.0,
) -> dict[str, float | bool | int]:
    dark = _nearest(points, "dark_iv", reference_bias_v)
    light = _nearest(points, "light_iv", reference_bias_v)
    photocurrent = abs(light.current_a - dark.current_a)
    responsivity = photocurrent / optical_power_w

    repeats = [abs(p.current_a) for p in points if p.mode == "repeatability"]
    repeat_mean = statistics.fmean(repeats)
    repeat_std = statistics.stdev(repeats) if len(repeats) > 1 else 0.0
    repeatability_cv = repeat_std / repeat_mean if repeat_mean else 0.0

    dark_noise = [p.current_a for p in points if p.mode == "noise_dark"]
    noise_rms = statistics.stdev(dark_noise) if len(dark_noise) > 1 else 0.0
    noise_density = noise_rms / math.sqrt(noise_bandwidth_hz)
    nep = noise_density / responsivity if responsivity > 0 else math.inf
    detectivity = math.sqrt(detector_area_cm2) / nep if nep > 0 and math.isfinite(nep) else 0.0

    linearity = sorted((p for p in points if p.mode == "linearity"), key=lambda p: p.optical_power_w)
    linearity_power = [p.optical_power_w for p in linearity]
    linearity_photo = [abs(p.current_a - dark.current_a) for p in linearity]
    linearity_slope, linearity_r2, linearity_error = _linear_fit(linearity_power, linearity_photo)

    stability = sorted((p for p in points if p.mode == "stability"), key=lambda p: p.elapsed_s or 0.0)
    stability_photo = [abs(p.current_a - dark.current_a) for p in stability]
    stability_mean = statistics.fmean(stability_photo) if stability_photo else 0.0
    stability_drift = abs(stability_photo[-1] - stability_photo[0]) / stability_mean if len(stability_photo) > 1 and stability_mean else 0.0
    stability_range = (max(stability_photo) - min(stability_photo)) / stability_mean if stability_photo and stability_mean else 0.0

    spectral = [p for p in points if p.mode == "spectral_response" and p.wavelength_nm is not None]
    spectral_responses = [(float(p.wavelength_nm), abs(p.current_a - dark.current_a) / p.optical_power_w) for p in spectral if p.optical_power_w > 0]
    peak_wavelength, peak_response = max(spectral_responses, key=lambda item: item[1]) if spectral_responses else (target_wavelength_nm, responsivity)
    target_response = min(spectral_responses, key=lambda item: abs(item[0] - target_wavelength_nm))[1] if spectral_responses else responsivity
    target_spectral_ratio = target_response / peak_response if peak_response else 0.0

    dark_iv = [p for p in points if p.mode == "dark_iv"]
    dark_slope, _, _ = _linear_fit([p.voltage_v for p in dark_iv], [p.current_a for p in dark_iv])
    estimated_shunt = abs(1.0 / dark_slope) if dark_slope else math.inf

    return {
        "reference_bias_v": reference_bias_v,
        "dark_current_a": abs(dark.current_a), "light_current_a": abs(light.current_a),
        "photocurrent_a": photocurrent, "responsivity_a_per_w": responsivity,
        "noise_rms_a": noise_rms, "noise_density_a_per_sqrt_hz": noise_density,
        "nep_w_per_sqrt_hz": nep, "detectivity_jones": detectivity,
        "linearity_slope_a_per_w": linearity_slope, "linearity_r_squared": linearity_r2,
        "linearity_max_error_fraction": linearity_error,
        "repeatability_cv": repeatability_cv, "repeatability_noise_std_a": repeat_std,
        "stability_drift_fraction": stability_drift, "stability_range_fraction": stability_range,
        "spectral_peak_wavelength_nm": peak_wavelength,
        "spectral_peak_responsivity_a_per_w": peak_response,
        "target_spectral_ratio": target_spectral_ratio,
        "estimated_shunt_resistance_ohm": estimated_shunt,
        "dark_iv_point_count": len(dark_iv),
        "light_iv_point_count": len([p for p in points if p.mode == "light_iv"]),
        "compliance_tripped": compliance_tripped,
    }
