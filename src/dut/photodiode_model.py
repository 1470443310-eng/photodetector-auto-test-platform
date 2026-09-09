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
    temperature_k: float = 300.0
    noise_std_a: float = 2e-11
    nonlinearity: float = 0.0

    @classmethod
    def from_profile(cls, dut_id: str, profile: str) -> "Photodiode":
        base = cls(dut_id=dut_id, profile=profile)
        profiles = {
            "normal": {},
            "high_dark_current": {"saturation_current_a": 2.5e-8},
            "low_responsivity": {"responsivity_a_per_w": 0.20},
            "noisy": {"noise_std_a": 6e-5},
            "nonlinear": {"nonlinearity": 450.0},
            "open_circuit": {"responsivity_a_per_w": 0.0, "saturation_current_a": 0.0, "shunt_resistance_ohm": 1e18, "noise_std_a": 1e-13},
            "short_circuit": {"shunt_resistance_ohm": 100.0},
            "communication_error": {},
        }
        if profile not in profiles:
            raise ValueError(f"unknown DUT profile: {profile}")
        return replace(base, **profiles[profile])

    def current(self, voltage_v: float, optical_power_w: float, rng: random.Random) -> float:
        if optical_power_w < 0:
            raise ValueError("optical power cannot be negative")
        thermal_voltage = 8.617333262e-5 * self.temperature_k
        exponent = max(-80.0, min(40.0, voltage_v / (self.ideality_factor * thermal_voltage)))
        diode_current = self.saturation_current_a * (math.exp(exponent) - 1.0)
        shunt_current = voltage_v / self.shunt_resistance_ohm
        optical_gain = max(0.0, 1.0 - self.nonlinearity * optical_power_w)
        photocurrent = self.responsivity_a_per_w * optical_power_w * optical_gain
        # Dark noise is held near the nominal floor so the "noisy" profile can
        # isolate an illuminated repeatability failure instead of masquerading
        # as a dark-leakage failure.
        noise_std = self.noise_std_a if optical_power_w > 0 else min(self.noise_std_a, 2e-11)
        return diode_current + shunt_current - photocurrent + rng.gauss(0.0, noise_std)
