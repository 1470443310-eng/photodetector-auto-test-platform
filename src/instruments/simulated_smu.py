"""Deterministic virtual SMU backed by a simplified photodiode model."""
import random
from .base import CommunicationError, SafetyInterlockError, SourceMeasureUnit
from src.dut.photodiode_model import Photodiode

class SimulatedSMU(SourceMeasureUnit):
    def __init__(self, dut: Photodiode, seed: int, compliance_a: float, max_abs_voltage_v: float = 10.0):
        self.dut, self.rng = dut, random.Random(seed)
        self.compliance_a, self.max_abs_voltage_v = compliance_a, max_abs_voltage_v
        self.connected = False
        self.compliance_tripped = False
    def connect(self) -> None:
        if self.dut.profile == "communication_error":
            raise CommunicationError("simulated VISA timeout during connect")
        self.connected = True
    def reset(self) -> None:
        self.compliance_tripped = False
    def measure_current(self, voltage_v: float, optical_power_w: float) -> float:
        if not self.connected:
            raise CommunicationError("SMU is not connected")
        if abs(voltage_v) > self.max_abs_voltage_v:
            raise SafetyInterlockError(f"requested voltage {voltage_v} V exceeds safe limit")
        value = self.dut.current(voltage_v, optical_power_w, self.rng)
        if abs(value) > self.compliance_a:
            self.compliance_tripped = True
            return self.compliance_a if value >= 0 else -self.compliance_a
        return value
    def disconnect(self) -> None:
        self.connected = False
