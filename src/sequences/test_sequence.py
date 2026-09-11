"""End-to-end dark, illuminated and repeatability sequence for one DUT."""
from __future__ import annotations
import random
from typing import Any
from src.analysis.data_cleaning import clean_measurements
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
    variation = plan["simulation"]["manufacturing_variation"]
    nominal_temperature_c = float(plan["environment"]["nominal_temperature_c"])
    dut = Photodiode.from_profile(dut_id, profile).with_manufacturing_variation(seed, variation, nominal_temperature_c)
    instrument_rng = random.Random(seed ^ 0x5A17)
    instrument_settings = plan["simulation"]["instrument"]
    gain_error = instrument_rng.gauss(0.0, float(instrument_settings["gain_error_sigma"]))
    zero_offset_a = instrument_rng.gauss(0.0, float(instrument_settings["zero_offset_sigma_a"]))
    smu = SimulatedSMU(
        dut, seed, float(plan["voltage_sweep"]["compliance_a"]),
        gain_error=gain_error, zero_offset_a=zero_offset_a,
        instrument_noise_a=float(instrument_settings["noise_floor_a"]),
    )
    light = SimulatedLightSource()
    try:
        smu.connect(); light.connect(); smu.reset()
        for voltage in voltage_points(plan):
            points.append(MeasurementPoint("dark_iv", voltage, 0.0, smu.measure_current(voltage, 0.0)))
        power = float(plan["illumination"]["optical_power_w"])
        wavelength = float(plan["illumination"]["wavelength_nm"])
        light.set_power(power); light.output(True)
        for voltage in voltage_points(plan):
            points.append(MeasurementPoint("light_iv", voltage, power, smu.measure_current(voltage, power, wavelength), wavelength))
        bias = float(plan["measurement"].get("reference_bias_v", -2.0))
        samples = int(plan["measurement"]["samples_per_point"])
        for _ in range(samples):
            points.append(MeasurementPoint("repeatability", bias, power, smu.measure_current(bias, power, wavelength), wavelength))

        light.output(False)
        for _ in range(int(plan["noise"]["samples"])):
            points.append(MeasurementPoint("noise_dark", bias, 0.0, smu.measure_current(bias, 0.0, wavelength), wavelength))

        light.output(True)
        for test_power in plan["linearity"]["optical_powers_w"]:
            value = float(test_power); light.set_power(value)
            points.append(MeasurementPoint("linearity", bias, value, smu.measure_current(bias, value, wavelength), wavelength))

        light.set_power(power)
        stability_samples = int(plan["stability"]["samples"])
        interval_s = float(plan["stability"]["sample_interval_s"])
        for index in range(stability_samples):
            elapsed_s = index * interval_s
            points.append(MeasurementPoint("stability", bias, power, smu.measure_current(bias, power, wavelength, elapsed_s), wavelength, elapsed_s))

        for spectral_wavelength in plan["spectral_response"]["wavelengths_nm"]:
            wl = float(spectral_wavelength)
            points.append(MeasurementPoint("spectral_response", bias, power, smu.measure_current(bias, power, wl), wl))

        cleaned, data_quality = clean_measurements(points)
        metrics = extract_metrics(
            cleaned, bias, power, smu.compliance_tripped,
            float(plan["detector"]["active_area_cm2"]),
            float(plan["noise"]["bandwidth_hz"]), wavelength,
        )
        metrics.update(data_quality)
        metrics.update({
            "measurement_seed": seed,
            "simulated_temperature_c": dut.temperature_k - 273.15,
            "simulated_nominal_responsivity_a_per_w": dut.responsivity_a_per_w,
            "simulated_dark_saturation_current_a": dut.saturation_current_a,
            "simulated_instrument_gain_error": gain_error,
            "simulated_instrument_zero_offset_a": zero_offset_a,
        })
        status, reasons = evaluate(metrics, plan["limits"])
        return DutResult(dut_id, profile, status, metrics, reasons, cleaned)
    except InstrumentError as exc:
        return DutResult(dut_id, profile, "ERROR", reasons=[str(exc)], measurements=points, error=str(exc))
    finally:
        smu.disconnect(); light.disconnect()

def run_batch(plan: dict[str, Any], profiles: list[str] | None = None) -> list[DutResult]:
    default = ["normal"] * 12 + ["high_dark_current", "low_responsivity", "noisy", "nonlinear", "open_circuit", "short_circuit", "communication_error", "normal"]
    base_seed = int(plan.get("random_seed", 0))
    batch_size = int(plan.get("batch_size", 20))
    if profiles is not None:
        selected = profiles
    elif plan.get("simulation_run_mode") == "realistic_variation":
        distribution = plan.get("simulation", {}).get("batch_profile_distribution", {"normal": 1.0})
        names = list(distribution)
        weights = [float(distribution[name]) for name in names]
        if not names or any(weight < 0 for weight in weights) or sum(weights) <= 0:
            raise ValueError("simulation.batch_profile_distribution must contain non-negative weights with a positive sum")
        # Separate RNG stream keeps profile selection reproducible from the recorded
        # batch seed without coupling it to any individual measurement sequence.
        batch_rng = random.Random(base_seed ^ 0xB47C_2026)
        selected = batch_rng.choices(names, weights=weights, k=batch_size)
    else:
        selected = default[:batch_size]
    return [run_dut(f"PD-{index:03d}", profile, plan, base_seed + index) for index, profile in enumerate(selected, 1)]
