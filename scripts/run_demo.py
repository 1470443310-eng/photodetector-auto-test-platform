#!/usr/bin/env python3
"""Command-line entry point that works without the web dashboard."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pipeline import execute

if __name__ == "__main__":
    outcome = execute(ROOT / "configs/default_test_plan.yaml", ROOT / "artifacts")
    s = outcome["summary"]
    print(f"Run: {outcome['run_id']}")
    print(f"PASS={s['pass']} FAIL={s['fail']} ERROR={s['error']} Yield={s['yield_excluding_errors']:.1%}")
    print(f"Report: {outcome['report']}")
