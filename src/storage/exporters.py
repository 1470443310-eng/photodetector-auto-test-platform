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
    metric_fields = sorted({key for result in results for key in result.metrics})
    fields = ["dut_id", "profile", "status", *metric_fields, "reasons", "error"]
    with summary_csv.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for r in results:
            writer.writerow({"dut_id": r.dut_id, "profile": r.profile, "status": r.status, **r.metrics, "reasons": "; ".join(r.reasons), "error": r.error})
    with raw_csv.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle); writer.writerow(["dut_id", "profile", "mode", "voltage_v", "optical_power_w", "current_a", "wavelength_nm", "elapsed_s"])
        for r in results:
            for p in r.measurements: writer.writerow([r.dut_id, r.profile, p.mode, p.voltage_v, p.optical_power_w, p.current_a, p.wavelength_nm, p.elapsed_s])
    payload = {"run_id": run_id, "summary": summary, "results": [r.to_dict() for r in results], "simulation_notice": "SIMULATED DATA — NOT A PHYSICAL DEVICE MEASUREMENT"}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"summary_csv": summary_csv, "measurements_csv": raw_csv, "json": json_path}
