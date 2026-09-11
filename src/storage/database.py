"""SQLite persistence for traceable test runs."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from src.domain import DutResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, created_at TEXT, config_json TEXT);
CREATE TABLE IF NOT EXISTS dut_results (run_id TEXT, dut_id TEXT, profile TEXT, status TEXT, metrics_json TEXT, reasons_json TEXT, error TEXT, PRIMARY KEY(run_id, dut_id));
CREATE TABLE IF NOT EXISTS measurements (run_id TEXT, dut_id TEXT, mode TEXT, voltage_v REAL, optical_power_w REAL, current_a REAL, wavelength_nm REAL, elapsed_s REAL);
"""

def save_run(db_path: str | Path, run_id: str, created_at: str, plan: dict, results: list[DutResult]) -> None:
    path = Path(db_path); path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(measurements)")}
        if "wavelength_nm" not in existing_columns:
            conn.execute("ALTER TABLE measurements ADD COLUMN wavelength_nm REAL")
        if "elapsed_s" not in existing_columns:
            conn.execute("ALTER TABLE measurements ADD COLUMN elapsed_s REAL")
        conn.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?)", (run_id, created_at, json.dumps(plan, ensure_ascii=False)))
        conn.execute("DELETE FROM dut_results WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM measurements WHERE run_id = ?", (run_id,))
        for result in results:
            conn.execute("INSERT INTO dut_results VALUES (?, ?, ?, ?, ?, ?, ?)", (run_id, result.dut_id, result.profile, result.status, json.dumps(result.metrics), json.dumps(result.reasons), result.error))
            conn.executemany(
                "INSERT INTO measurements (run_id, dut_id, mode, voltage_v, optical_power_w, current_a, wavelength_nm, elapsed_s) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(run_id, result.dut_id, p.mode, p.voltage_v, p.optical_power_w, p.current_a, p.wavelength_nm, p.elapsed_s) for p in result.measurements],
            )
