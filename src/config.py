"""YAML configuration loading and safety-oriented validation."""
from pathlib import Path
from typing import Any
import yaml

REQUIRED = ("voltage_sweep", "measurement", "illumination", "limits")

def load_test_plan(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        plan = yaml.safe_load(handle)
    missing = [key for key in REQUIRED if key not in plan]
    if missing:
        raise ValueError(f"test plan missing sections: {', '.join(missing)}")
    sweep = plan["voltage_sweep"]
    if sweep["step_v"] <= 0 or sweep["start_v"] >= sweep["stop_v"]:
        raise ValueError("voltage sweep requires start < stop and positive step")
    if sweep["compliance_a"] <= 0:
        raise ValueError("current compliance must be positive")
    if plan["illumination"]["optical_power_w"] <= 0:
        raise ValueError("optical power must be positive")
    return plan

def voltage_points(plan: dict[str, Any]) -> list[float]:
    sweep = plan["voltage_sweep"]
    start, stop, step = float(sweep["start_v"]), float(sweep["stop_v"]), float(sweep["step_v"])
    count = int(round((stop - start) / step))
    return [round(start + i * step, 12) for i in range(count + 1)]
