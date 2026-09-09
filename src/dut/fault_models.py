"""Named fault profiles exposed by the simulator."""
PROFILES = ("normal", "high_dark_current", "low_responsivity", "noisy", "nonlinear", "open_circuit", "short_circuit", "communication_error")
PROFILE_DESCRIPTIONS = {
    "normal": "Nominal device",
    "high_dark_current": "Reverse dark current exceeds specification",
    "low_responsivity": "Optical responsivity is below specification",
    "noisy": "Repeatability is degraded by measurement noise",
    "nonlinear": "Responsivity drops at the configured optical power",
    "open_circuit": "Near-zero electrical and optical response",
    "short_circuit": "Excess current trips the compliance limit",
    "communication_error": "Virtual instrument raises a timeout",
}
