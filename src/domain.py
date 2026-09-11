"""Data contracts shared by test, storage and reporting layers."""
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class MeasurementPoint:
    mode: str
    voltage_v: float
    optical_power_w: float
    current_a: float
    wavelength_nm: float | None = None
    elapsed_s: float | None = None

@dataclass
class DutResult:
    dut_id: str
    profile: str
    status: str
    metrics: dict[str, float | bool | None] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    measurements: list[MeasurementPoint] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
