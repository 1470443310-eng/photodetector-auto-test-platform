from src.analysis.batch_statistics import summarize
from src.analysis.data_cleaning import clean_measurements
from src.domain import DutResult, MeasurementPoint


def test_cleaning_removes_invalid_and_duplicate_points():
    point = MeasurementPoint("dark_iv", -2.0, 0.0, 1e-9)
    invalid = MeasurementPoint("dark_iv", -2.0, 0.0, float("nan"))
    cleaned, audit = clean_measurements([point, point, invalid])
    assert cleaned == [point]
    assert audit == {"raw_point_count": 3, "clean_point_count": 1, "invalid_point_count": 1, "duplicate_point_count": 1}


def test_batch_anomaly_detection_marks_outlier():
    results = [
        DutResult(f"N{i}", "normal", "PASS", {"responsivity_a_per_w": value})
        for i, value in enumerate((0.50, 0.51, 0.49, 0.505), 1)
    ]
    results.append(DutResult("OUT", "low", "FAIL", {"responsivity_a_per_w": 0.05}, ["responsivity below minimum"]))
    summary = summarize(results)
    assert summary["anomaly_count"] == 1
    assert summary["anomaly_duts"][0]["dut_id"] == "OUT"
