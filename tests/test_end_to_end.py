from pathlib import Path
from src.config import load_test_plan
from src.sequences.test_sequence import run_dut
from src.pipeline import execute

PLAN = load_test_plan(Path(__file__).parents[1] / "configs/default_test_plan.yaml")

def test_three_state_decision():
    assert run_dut("N", "normal", PLAN, 1).status == "PASS"
    assert run_dut("F", "low_responsivity", PLAN, 1).status == "FAIL"
    assert run_dut("E", "communication_error", PLAN, 1).status == "ERROR"

def test_pipeline_generates_traceable_artifacts(tmp_path):
    result = execute(Path(__file__).parents[1] / "configs/default_test_plan.yaml", tmp_path, ["normal", "low_responsivity", "communication_error"])
    assert result["summary"] == {"total": 3, "pass": 1, "fail": 1, "error": 1, "yield_excluding_errors": .5, "first_pass_yield": 1/3, "failure_reasons": {"responsivity below minimum": 1, "simulated VISA timeout during connect": 1}}
    assert result["report"].exists()
    assert (tmp_path / "test_results.sqlite3").exists()
