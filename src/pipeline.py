"""Application service that runs a batch and creates all evidence artifacts."""
from __future__ import annotations
from datetime import datetime, timezone
from copy import deepcopy
import logging
from pathlib import Path
import secrets
from src.analysis.batch_statistics import summarize
from src.config import load_test_plan
from src.reporting.report_generator import generate_html_report
from src.sequences.test_sequence import run_batch
from src.storage.database import save_run
from src.storage.exporters import export_results

def execute(
    config_path: str | Path, output_root: str | Path = "artifacts",
    profiles: list[str] | None = None, randomize_seed: bool = False,
) -> dict:
    plan = deepcopy(load_test_plan(config_path))
    configured_seed = int(plan.get("random_seed", 0))
    effective_seed = secrets.randbits(32) if randomize_seed else configured_seed
    plan["configured_random_seed"] = configured_seed
    plan["random_seed"] = effective_seed
    plan["simulation_run_mode"] = "realistic_variation" if randomize_seed else "reproducible"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"SIM-{stamp}"
    run_dir = Path(output_root) / run_id; run_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=run_dir / "run.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    logging.info("starting simulation run %s", run_id)
    results = run_batch(plan, profiles)
    summary = summarize(results)
    paths = export_results(run_dir, run_id, results, summary)
    save_run(Path(output_root) / "test_results.sqlite3", run_id, stamp, plan, results)
    report = generate_html_report(run_dir / f"{run_id}_report.html", run_id, results, summary, plan)
    logging.info("completed run: %s", summary)
    return {"run_id": run_id, "run_dir": run_dir, "results": results, "summary": summary, "paths": paths, "report": report, "plan": plan, "effective_seed": effective_seed, "simulation_run_mode": plan["simulation_run_mode"]}
