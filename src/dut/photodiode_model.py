"""Transparent simplified photodiode model for software verification only."""
from dataclasses import dataclass, replace
import math
import random

@dataclass(frozen=True)
class Photodiode:
    dut_id: str
    profile: str = "normal"
    saturation_current_a: float = 8e-10
    responsivity_a_per_w: float = 0.55
    shunt_resistance_ohm: float = 2e11
    ideality_factor: float = 1.5
    temperature_k: float = 298.15
    noise_std_a: float = 2e-14
    nonlinearity: float = 0.0
    peak_wavelength_nm: float = 900.0
    spectral_width_nm: float = 230.0
    drift_per_second: float = 2e-7
    dark_current_temp_coefficient_per_c: float = 0.07
    responsivity_temp_coefficient_per_c: float = 0.001

    @classmethod
    def from_profile(cls, dut_id: str, profile: str) -> "Photodiode":
        base = cls(dut_id=dut_id, profile=profile)
        profiles = {
            "normal": {},
            "high_dark_current": {"saturation_current_a": 8e-8},
            "low_responsivity": {"responsivity_a_per_w": 0.20},
            "noisy": {"noise_std_a": 5e-6},
            "nonlinear": {"nonlinearity": 6000.0},
            "open_circuit": {"responsivity_a_per_w": 0.0, "saturation_current_a": 0.0, "shunt_resistance_ohm": 1e18, "noise_std_a": 1e-13},
            "short_circuit": {"shunt_resistance_ohm": 100.0},
            "communication_error": {},
            "unstable": {"drift_per_second": 8e-4},
            "spectral_mismatch": {"peak_wavelength_nm": 1080.0, "spectral_width_nm": 100.0},
        }
        if profile not in profiles:
            raise ValueError(f"unknown DUT profile: {profile}")
        return replace(base, **profiles[profile])

    def with_manufacturing_variation(self, seed: int, settings: dict, nominal_temperature_c: float = 25.0) -> "Photodiode":
        """Apply realistic lot/device spread while keeping a recorded seed reproducible."""
        rng = random.Random(seed)
        temperature_c = rng.gauss(nominal_temperature_c, float(settings.get("temperature_sigma_c", 0.0)))
        return replace(
            self,
            saturation_current_a=self.saturation_current_a * rng.lognormvariate(0.0, float(settings.get("dark_current_log_sigma", 0.0))),
            responsivity_a_per_w=max(0.0, self.responsivity_a_per_w * rng.gauss(1.0, float(settings.get("responsivity_relative_sigma", 0.0)))),
            shunt_resistance_ohm=max(1.0, self.shunt_resistance_ohm * rng.lognormvariate(0.0, float(settings.get("shunt_resistance_log_sigma", 0.0)))),
            noise_std_a=max(0.0, self.noise_std_a * rng.gauss(1.0, float(settings.get("intrinsic_noise_relative_sigma", 0.0)))),
            peak_wavelength_nm=self.peak_wavelength_nm + rng.gauss(0.0, float(settings.get("peak_wavelength_sigma_nm", 0.0))),
            temperature_k=temperature_c + 273.15,
        )

    def current(
        self,
        voltage_v: float,
        optical_power_w: float,
        rng: random.Random,
        wavelength_nm: float = 850.0,
        elapsed_s: float = 0.0,
    ) -> float:
        if optical_power_w < 0:
            raise ValueError("optical power cannot be negative")
        thermal_voltage = 8.617333262e-5 * self.temperature_k
        exponent = max(-80.0, min(40.0, voltage_v / (self.ideality_factor * thermal_voltage)))
        temperature_delta_c = self.temperature_k - 298.15
        effective_saturation = self.saturation_current_a * math.exp(self.dark_current_temp_coefficient_per_c * temperature_delta_c)
        diode_current = effective_saturation * (math.exp(exponent) - 1.0)
        shunt_current = voltage_v / self.shunt_resistance_ohm
        optical_gain = max(0.0, 1.0 - self.nonlinearity * optical_power_w)
        spectral_gain = math.exp(-0.5 * ((wavelength_nm - self.peak_wavelength_nm) / self.spectral_width_nm) ** 2)
        drift_gain = max(0.0, 1.0 + self.drift_per_second * elapsed_s)
        temperature_response = max(0.0, 1.0 + self.responsivity_temp_coefficient_per_c * temperature_delta_c)
        photocurrent = self.responsivity_a_per_w * temperature_response * spectral_gain * optical_power_w * optical_gain * drift_gain
        # Dark noise is held near the nominal floor so the "noisy" profile can
        # isolate an illuminated repeatability failure instead of masquerading
        # as a dark-leakage failure.
        noise_std = self.noise_std_a if optical_power_w > 0 else min(self.noise_std_a, 2e-11)
        return diode_current + shunt_current - photocurrent + rng.gauss(0.0, noise_std)
