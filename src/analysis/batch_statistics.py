"""Batch yield, Pareto statistics and robust multivariate anomaly screening."""
from __future__ import annotations

from collections import Counter
import math
import statistics
from src.domain import DutResult

ANOMALY_METRICS = (
    "dark_current_a", "responsivity_a_per_w", "noise_rms_a",
    "nep_w_per_sqrt_hz", "detectivity_jones",
    "linearity_max_error_fraction", "repeatability_cv",
    "stability_drift_fraction", "target_spectral_ratio",
)


def _transform(value: float) -> float:
    return math.log10(value) if value > 0 else value


def detect_anomalies(results: list[DutResult], threshold: float = 3.5) -> list[dict]:
    completed = [result for result in results if result.status != "ERROR"]
    centers: dict[str, tuple[float, float]] = {}
    for metric in ANOMALY_METRICS:
        values = [_transform(float(r.metrics[metric])) for r in completed if metric in r.metrics and math.isfinite(float(r.metrics[metric]))]
        if not values:
            continue
        median = statistics.median(values)
        mad = statistics.median(abs(value - median) for value in values)
        centers[metric] = (median, mad)

    anomalies: list[dict] = []
    for result in results:
        metric_scores: dict[str, float] = {}
        for metric, (median, mad) in centers.items():
            raw = result.metrics.get(metric)
            if raw is None or not math.isfinite(float(raw)):
                continue
            distance = abs(_transform(float(raw)) - median)
            score = 0.6745 * distance / mad if mad > 1e-12 else (threshold + 1.0 if distance > 1e-12 else 0.0)
            if score >= threshold:
                metric_scores[metric] = score
        anomaly_score = min(999.0, max(metric_scores.values(), default=0.0))
        result.metrics["batch_anomaly_score"] = anomaly_score
        result.metrics["batch_anomaly"] = bool(metric_scores)
        if metric_scores:
            anomalies.append({
                "dut_id": result.dut_id,
                "status": result.status,
                "score": anomaly_score,
                "metrics": sorted(metric_scores, key=metric_scores.get, reverse=True),
            })
    return sorted(anomalies, key=lambda item: item["score"], reverse=True)


def summarize(results: list[DutResult]) -> dict:
    anomalies = detect_anomalies(results)
    counts = Counter(r.status for r in results)
    completed = counts["PASS"] + counts["FAIL"]
    reason_counts = Counter(reason for r in results for reason in r.reasons)
    profile_counts = Counter(r.profile for r in results)
    return {
        "total": len(results), "pass": counts["PASS"], "fail": counts["FAIL"], "error": counts["ERROR"],
        "yield_excluding_errors": counts["PASS"] / completed if completed else 0.0,
        "first_pass_yield": counts["PASS"] / len(results) if results else 0.0,
        "failure_reasons": dict(reason_counts.most_common()),
        "profile_counts": dict(profile_counts),
        "anomaly_count": len(anomalies),
        "anomaly_duts": anomalies,
    }
