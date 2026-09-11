"""Deterministic validation and cleaning for acquired measurement records."""
from __future__ import annotations

import math
from src.domain import MeasurementPoint


def clean_measurements(points: list[MeasurementPoint]) -> tuple[list[MeasurementPoint], dict[str, int]]:
    """Remove unusable numeric records and exact duplicates without hiding the audit count."""
    cleaned: list[MeasurementPoint] = []
    seen: set[tuple] = set()
    invalid = duplicates = 0
    for point in points:
        numeric = (point.voltage_v, point.optical_power_w, point.current_a)
        if not all(math.isfinite(float(value)) for value in numeric):
            invalid += 1
            continue
        key = (
            point.mode,
            point.voltage_v,
            point.optical_power_w,
            point.current_a,
            point.wavelength_nm,
            point.elapsed_s,
        )
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        cleaned.append(point)
    return cleaned, {
        "raw_point_count": len(points),
        "clean_point_count": len(cleaned),
        "invalid_point_count": invalid,
        "duplicate_point_count": duplicates,
    }
