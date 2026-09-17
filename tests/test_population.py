import math
from src.domain import DutResult
from src.reporting.population import histogram, metric_population, population_html
from src.config import load_test_plan


def test_population_excludes_errors_and_invalid_without_zero_imputation():
    results = [DutResult(str(i), "normal", status, {"dark_current_a": value})
               for i, (status, value) in enumerate([
                   ("PASS", 0), ("FAIL", 4), ("ERROR", 100), ("PASS", math.nan), ("FAIL", math.inf)])]
    pop = metric_population(results, "dark_current_a")
    assert (pop['n'], pop['excluded'], pop['mean'], pop['median']) == (2, 3, 2, 2)
    assert math.isclose(pop['stdev'], math.sqrt(8))


def test_histogram_preserves_all_samples_and_upper_endpoint():
    for values in [[1]*20, [0, 1, 2, 3, 1000], [-5, 0, 5]]:
        edges, counts = histogram(values)
        assert sum(counts) == len(values)
        assert edges[0] <= min(values) <= max(values) <= edges[-1]


def test_empty_and_single_sample_reports_are_defined():
    plan = load_test_plan("configs/default_test_plan.yaml")
    html = population_html([], plan, "empty")
    assert "无有效分母" in html
    assert html.count("无有效测量数据") == 8
    html = population_html([DutResult("<DUT>", "normal", "FAIL", {"dark_current_a": 0})], plan, "<run>")
    assert "不可估计" in html
    assert "&lt;DUT&gt;" in html and "&lt;run&gt;" in html
    assert "nan" not in html.lower()
