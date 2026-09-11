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
    assert {key: result["summary"][key] for key in ("total", "pass", "fail", "error", "yield_excluding_errors", "first_pass_yield")} == {
        "total": 3, "pass": 1, "fail": 1, "error": 1,
        "yield_excluding_errors": .5, "first_pass_yield": 1/3,
    }
    assert result["summary"]["failure_reasons"] == {"响应度低于下限": 1, "模拟VISA仪器连接超时": 1}
    assert "anomaly_duts" in result["summary"]
    assert result["report"].exists()
    assert (tmp_path / "test_results.sqlite3").exists()

def test_complete_chain_produces_engineering_metrics():
    result = run_dut("N", "normal", PLAN, 1)
    expected = {
        "dark_current_a", "responsivity_a_per_w", "noise_rms_a",
        "nep_w_per_sqrt_hz", "detectivity_jones", "linearity_r_squared",
        "repeatability_cv", "stability_drift_fraction",
        "spectral_peak_wavelength_nm", "estimated_shunt_resistance_ohm",
        "raw_point_count", "clean_point_count",
    }
    assert result.status == "PASS"
    assert expected <= result.metrics.keys()
    assert {point.mode for point in result.measurements} >= {
        "dark_iv", "light_iv", "noise_dark", "linearity",
        "repeatability", "stability", "spectral_response",
    }

def test_seed_controls_realistic_device_variation():
    first = run_dut("N", "normal", PLAN, 101)
    repeated = run_dut("N", "normal", PLAN, 101)
    different = run_dut("N", "normal", PLAN, 102)
    assert first.metrics["responsivity_a_per_w"] == repeated.metrics["responsivity_a_per_w"]
    assert first.metrics["simulated_temperature_c"] == repeated.metrics["simulated_temperature_c"]
    assert first.metrics["responsivity_a_per_w"] != different.metrics["responsivity_a_per_w"]

def test_randomized_pipeline_records_new_seed(tmp_path):
    first = execute(Path(__file__).parents[1] / "configs/default_test_plan.yaml", tmp_path, ["normal"], randomize_seed=True)
    second = execute(Path(__file__).parents[1] / "configs/default_test_plan.yaml", tmp_path, ["normal"], randomize_seed=True)
    assert first["effective_seed"] != second["effective_seed"]
    assert first["simulation_run_mode"] == "realistic_variation"
    assert first["results"][0].metrics["responsivity_a_per_w"] != second["results"][0].metrics["responsivity_a_per_w"]

def test_teaching_fault_profiles_are_not_hidden_by_normal_variation():
    fault_profiles = ("high_dark_current", "low_responsivity", "noisy", "nonlinear", "open_circuit", "short_circuit")
    for index, profile in enumerate(fault_profiles, 1):
        assert run_dut(f"F{index}", profile, PLAN, 20260909 + index).status == "FAIL"

def test_realistic_batches_vary_profile_and_quality_counts(tmp_path):
    counts = set()
    profile_sets = set()
    for seed in range(100, 110):
        varied_plan = load_test_plan(Path(__file__).parents[1] / "configs/default_test_plan.yaml")
        varied_plan["random_seed"] = seed
        varied_plan["simulation_run_mode"] = "realistic_variation"
        from src.sequences.test_sequence import run_batch
        results = run_batch(varied_plan)
        counts.add(tuple(sum(result.status == status for result in results) for status in ("PASS", "FAIL", "ERROR")))
        profile_sets.add(tuple(result.profile for result in results))
    assert len(profile_sets) > 1
    assert len(counts) > 1
