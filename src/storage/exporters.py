"""Human-readable CSV/JSON export."""
from __future__ import annotations
import csv
import json
from pathlib import Path
from src.domain import DutResult

def export_results(output_dir: str | Path, run_id: str, results: list[DutResult], summary: dict) -> dict[str, Path]:
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    summary_csv = out / f"{run_id}_dut_summary.csv"
    raw_csv = out / f"{run_id}_measurements.csv"
    json_path = out / f"{run_id}_results.json"
    fields = ["dut_id", "profile", "status", "dark_current_a", "responsivity_a_per_w", "repeatability_cv", "compliance_tripped", "reasons"]
    with summary_csv.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for r in results:
            writer.writerow({"dut_id": r.dut_id, "profile": r.profile, "status": r.status, "dark_current_a": r.metrics.get("dark_current_a"), "responsivity_a_per_w": r.metrics.get("responsivity_a_per_w"), "repeatability_cv": r.metrics.get("repeatability_cv"), "compliance_tripped": r.metrics.get("compliance_tripped"), "reasons": "; ".join(r.reasons)})
    with raw_csv.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle); writer.writerow(["dut_id", "profile", "mode", "voltage_v", "optical_power_w", "current_a"])
        for r in results:
            for p in r.measurements: writer.writerow([r.dut_id, r.profile, p.mode, p.voltage_v, p.optical_power_w, p.current_a])
    payload = {"run_id": run_id, "summary": summary, "results": [r.to_dict() for r in results], "simulation_notice": "SIMULATED DATA — NOT A PHYSICAL DEVICE MEASUREMENT"}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"summary_csv": summary_csv, "measurements_csv": raw_csv, "json": json_path}
