"""Deterministic virtual SMU backed by a simplified photodiode model."""
import random
from .base import CommunicationError, SafetyInterlockError, SourceMeasureUnit
from src.dut.photodiode_model import Photodiode

class SimulatedSMU(SourceMeasureUnit):
    def __init__(
        self, dut: Photodiode, seed: int, compliance_a: float,
        max_abs_voltage_v: float = 10.0, gain_error: float = 0.0,
        zero_offset_a: float = 0.0, instrument_noise_a: float = 0.0,
    ):
        self.dut, self.rng = dut, random.Random(seed)
        self.compliance_a, self.max_abs_voltage_v = compliance_a, max_abs_voltage_v
        self.gain_error, self.zero_offset_a = gain_error, zero_offset_a
        self.instrument_noise_a = instrument_noise_a
        self.connected = False
        self.compliance_tripped = False
    def connect(self) -> None:
        if self.dut.profile == "communication_error":
            raise CommunicationError("模拟VISA仪器连接超时")
        self.connected = True
    def reset(self) -> None:
        self.compliance_tripped = False
    def measure_current(self, voltage_v: float, optical_power_w: float, wavelength_nm: float = 850.0, elapsed_s: float = 0.0) -> float:
        if not self.connected:
            raise CommunicationError("源测量单元尚未连接")
        if abs(voltage_v) > self.max_abs_voltage_v:
            raise SafetyInterlockError(f"请求电压 {voltage_v} V 超过安全限值")
        ideal_value = self.dut.current(voltage_v, optical_power_w, self.rng, wavelength_nm, elapsed_s)
        value = ideal_value * (1.0 + self.gain_error) + self.zero_offset_a + self.rng.gauss(0.0, self.instrument_noise_a)
        if abs(value) > self.compliance_a:
            self.compliance_tripped = True
            return self.compliance_a if value >= 0 else -self.compliance_a
        return value
    def disconnect(self) -> None:
        self.connected = False
