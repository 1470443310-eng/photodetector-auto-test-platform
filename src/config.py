"""YAML configuration loading and safety-oriented validation."""
from pathlib import Path
from typing import Any
import yaml

REQUIRED = ("voltage_sweep", "measurement", "illumination", "detector", "environment", "simulation", "noise", "linearity", "stability", "spectral_response", "limits")

def load_test_plan(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        plan = yaml.safe_load(handle)
    missing = [key for key in REQUIRED if key not in plan]
    if missing:
        raise ValueError(f"test plan missing sections: {', '.join(missing)}")
    sweep = plan["voltage_sweep"]
    if sweep["step_v"] <= 0 or sweep["start_v"] >= sweep["stop_v"]:
        raise ValueError("voltage sweep requires start < stop and positive step")
    if sweep["compliance_a"] <= 0:
        raise ValueError("current compliance must be positive")
    if plan["illumination"]["optical_power_w"] <= 0:
        raise ValueError("optical power must be positive")
    if plan["detector"]["active_area_cm2"] <= 0:
        raise ValueError("detector active area must be positive")
    if plan["noise"]["samples"] < 2 or plan["noise"]["bandwidth_hz"] <= 0:
        raise ValueError("noise test requires at least two samples and positive bandwidth")
    powers = plan["linearity"]["optical_powers_w"]
    if len(powers) < 3 or any(float(power) <= 0 for power in powers):
        raise ValueError("linearity test requires at least three positive optical powers")
    if plan["stability"]["samples"] < 2 or plan["stability"]["sample_interval_s"] <= 0:
        raise ValueError("stability test requires at least two samples and positive interval")
    wavelengths = plan["spectral_response"]["wavelengths_nm"]
    if len(wavelengths) < 3 or any(float(wavelength) <= 0 for wavelength in wavelengths):
        raise ValueError("spectral response requires at least three positive wavelengths")
    return plan

def voltage_points(plan: dict[str, Any]) -> list[float]:
    sweep = plan["voltage_sweep"]
    start, stop, step = float(sweep["start_v"]), float(sweep["stop_v"]), float(sweep["step_v"])
    count = int(round((stop - start) / step))
    return [round(start + i * step, 12) for i in range(count + 1)]
