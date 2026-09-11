"""Instrument interfaces and domain-specific exceptions."""
from abc import ABC, abstractmethod

class InstrumentError(RuntimeError):
    """Base error raised when an instrument cannot provide a measurement."""

class CommunicationError(InstrumentError):
    """Communication timeout or transport failure."""

class SafetyInterlockError(InstrumentError):
    """Unsafe source settings were rejected before a measurement."""

class SourceMeasureUnit(ABC):
    @abstractmethod
    def connect(self) -> None: ...
    @abstractmethod
    def reset(self) -> None: ...
    @abstractmethod
    def measure_current(self, voltage_v: float, optical_power_w: float, wavelength_nm: float = 850.0, elapsed_s: float = 0.0) -> float: ...
    @abstractmethod
    def disconnect(self) -> None: ...

class LightSource(ABC):
    @abstractmethod
    def connect(self) -> None: ...
    @abstractmethod
    def set_power(self, power_w: float) -> None: ...
    @abstractmethod
    def output(self, enabled: bool) -> None: ...
    @abstractmethod
    def disconnect(self) -> None: ...
