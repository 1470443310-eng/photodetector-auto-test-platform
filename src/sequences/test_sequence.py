"""End-to-end dark, illuminated and repeatability sequence for one DUT."""
from __future__ import annotations
from typing import Any
from src.analysis.parameter_extraction import extract_metrics
from src.analysis.pass_fail import evaluate
from src.config import voltage_points
from src.domain import DutResult, MeasurementPoint
from src.dut.photodiode_model import Photodiode
from src.instruments.base import InstrumentError
from src.instruments.simulated_light_source import SimulatedLightSource
from src.instruments.simulated_smu import SimulatedSMU

def run_dut(dut_id: str, profile: str, plan: dict[str, Any], seed: int) -> DutResult:
    points: list[MeasurementPoint] = []
    smu = SimulatedSMU(Photodiode.from_profile(dut_id, profile), seed, float(plan["voltage_sweep"]["compliance_a"]))
    light = SimulatedLightSource()
    try:
        smu.connect(); light.connect(); smu.reset()
        for voltage in voltage_points(plan):
            points.append(MeasurementPoint("dark_iv", voltage, 0.0, smu.measure_current(voltage, 0.0)))
        power = float(plan["illumination"]["optical_power_w"])
        light.set_power(power); light.output(True)
        for voltage in voltage_points(plan):
            points.append(MeasurementPoint("light_iv", voltage, power, smu.measure_current(voltage, power)))
        bias = float(plan["measurement"].get("reference_bias_v", -2.0))
        samples = int(plan["measurement"]["samples_per_point"])
        for _ in range(samples):
            points.append(MeasurementPoint("repeatability", bias, power, smu.measure_current(bias, power)))
        metrics = extract_metrics(points, bias, power, smu.compliance_tripped)
        status, reasons = evaluate(metrics, plan["limits"])
        return DutResult(dut_id, profile, status, metrics, reasons, points)
    except InstrumentError as exc:
        return DutResult(dut_id, profile, "ERROR", reasons=[str(exc)], measurements=points, error=str(exc))
    finally:
        smu.disconnect(); light.disconnect()

def run_batch(plan: dict[str, Any], profiles: list[str] | None = None) -> list[DutResult]:
    default = ["normal"] * 12 + ["high_dark_current", "low_responsivity", "noisy", "nonlinear", "open_circuit", "short_circuit", "communication_error", "normal"]
    selected = profiles or default[: int(plan.get("batch_size", 20))]
    base_seed = int(plan.get("random_seed", 0))
    return [run_dut(f"PD-{index:03d}", profile, plan, base_seed + index) for index, profile in enumerate(selected, 1)]
