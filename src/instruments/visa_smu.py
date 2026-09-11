"""Generic VISA/SCPI adapter scaffold; commands require model-specific review."""
from __future__ import annotations
from .base import CommunicationError, SafetyInterlockError, SourceMeasureUnit

class VisaSMU(SourceMeasureUnit):
    def __init__(self, resource_name: str, compliance_a: float, max_abs_voltage_v: float = 10.0, timeout_ms: int = 5000):
        self.resource_name, self.compliance_a = resource_name, compliance_a
        self.max_abs_voltage_v, self.timeout_ms = max_abs_voltage_v, timeout_ms
        self._rm = None
        self._instrument = None
    def connect(self) -> None:
        try:
            import pyvisa
            self._rm = pyvisa.ResourceManager()
            self._instrument = self._rm.open_resource(self.resource_name)
            self._instrument.timeout = self.timeout_ms
        except Exception as exc:
            raise CommunicationError(f"VISA connection failed: {exc}") from exc
    def reset(self) -> None:
        self._write("*RST")
        self._write(f":SENS:CURR:PROT {self.compliance_a}")
    def measure_current(self, voltage_v: float, optical_power_w: float = 0.0, wavelength_nm: float = 850.0, elapsed_s: float = 0.0) -> float:
        del optical_power_w, wavelength_nm, elapsed_s
        if abs(voltage_v) > self.max_abs_voltage_v:
            raise SafetyInterlockError("requested voltage exceeds configured safe limit")
        self._write(f":SOUR:VOLT {voltage_v}")
        try:
            return float(self._instrument.query(":MEAS:CURR?"))
        except Exception as exc:
            raise CommunicationError(f"VISA measurement failed: {exc}") from exc
    def disconnect(self) -> None:
        if self._instrument is not None:
            try: self._instrument.write(":OUTP OFF")
            finally: self._instrument.close()
        if self._rm is not None: self._rm.close()
        self._instrument = self._rm = None
    def _write(self, command: str) -> None:
        if self._instrument is None:
            raise CommunicationError("SMU is not connected")
        try: self._instrument.write(command)
        except Exception as exc: raise CommunicationError(f"VISA write failed: {exc}") from exc
