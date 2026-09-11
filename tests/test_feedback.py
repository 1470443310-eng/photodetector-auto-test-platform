import sqlite3
from src.storage.feedback import feedback_summary, import_feedback_rows, list_feedback, save_feedback


def test_feedback_is_saved_and_aggregated(tmp_path):
    db = tmp_path / "feedback.sqlite3"
    feedback_id = save_feedback(
        db, "anonymous-1", 4,
        {"completed_run": True, "found_fail_reason": True, "understood_report": False, "found_anomaly": False},
        "NEP", "希望增加指标说明",
    )
    summary = feedback_summary(db)
    assert feedback_id
    assert summary["total"] == 1
    assert summary["average_rating"] == 4
    assert summary["task_completion_rates"]["completed_run"] == 1.0
    assert summary["task_completion_rates"]["understood_report"] == 0.0
    assert summary["difficult_metrics"] == {"NEP": 1}

    with sqlite3.connect(db) as connection:
        row = connection.execute("SELECT anonymous_session_id, comments FROM user_feedback").fetchone()
    assert row == ("anonymous-1", "希望增加指标说明")


def test_feedback_validation_and_length_limits(tmp_path):
    db = tmp_path / "feedback.sqlite3"
    try:
        save_feedback(db, "x", 6, {}, "", "")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid rating was accepted")

    save_feedback(db, "x", 5, {}, "N" * 300, "C" * 3000)
    summary = feedback_summary(db)
    assert len(summary["rows"][0]["difficult_metric"]) == 200
    assert len(summary["rows"][0]["comments"]) == 2000


def test_feedback_migration_is_idempotent(tmp_path):
    source = tmp_path / "source.sqlite3"
    target = tmp_path / "target.sqlite3"
    save_feedback(source, "anonymous-migrate", 5, {"completed_run": True}, "", "很好用")

    rows = list_feedback(source)
    assert import_feedback_rows(target, rows) == 1
    assert import_feedback_rows(target, rows) == 0
    assert feedback_summary(target)["total"] == 1
