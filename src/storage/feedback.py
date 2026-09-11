"""Anonymous usability-feedback persistence and aggregate queries."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS user_feedback (
    feedback_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    anonymous_session_id TEXT NOT NULL,
    overall_rating INTEGER NOT NULL CHECK(overall_rating BETWEEN 1 AND 5),
    completed_run INTEGER NOT NULL,
    found_fail_reason INTEGER NOT NULL,
    understood_report INTEGER NOT NULL,
    found_anomaly INTEGER NOT NULL,
    difficult_metric TEXT NOT NULL,
    comments TEXT NOT NULL,
    app_version TEXT NOT NULL
);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_feedback (
    feedback_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    anonymous_session_id TEXT NOT NULL,
    overall_rating INTEGER NOT NULL CHECK(overall_rating BETWEEN 1 AND 5),
    completed_run INTEGER NOT NULL,
    found_fail_reason INTEGER NOT NULL,
    understood_report INTEGER NOT NULL,
    found_anomaly INTEGER NOT NULL,
    difficult_metric TEXT NOT NULL,
    comments TEXT NOT NULL,
    app_version TEXT NOT NULL
)
"""

FeedbackTarget = str | Path


def _is_postgres(target: FeedbackTarget) -> bool:
    return str(target).startswith(("postgresql://", "postgres://"))


def _connect(path: FeedbackTarget):
    if _is_postgres(path):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "云端反馈数据库需要安装 psycopg；请安装 requirements.txt。"
            ) from exc
        connection = psycopg.connect(str(path), row_factory=dict_row)
        connection.execute(POSTGRES_SCHEMA)
        connection.commit()
        return connection

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=5000")
    connection.executescript(SCHEMA)
    return connection


def save_feedback(
    db_path: FeedbackTarget, anonymous_session_id: str, overall_rating: int,
    tasks: dict[str, bool], difficult_metric: str, comments: str,
    app_version: str = "0.3.0",
) -> str:
    if not 1 <= int(overall_rating) <= 5:
        raise ValueError("overall rating must be between 1 and 5")
    feedback_id = str(uuid.uuid4())
    values = (
        feedback_id, datetime.now(timezone.utc).isoformat(), anonymous_session_id,
        int(overall_rating), int(bool(tasks.get("completed_run"))),
        int(bool(tasks.get("found_fail_reason"))), int(bool(tasks.get("understood_report"))),
        int(bool(tasks.get("found_anomaly"))), difficult_metric.strip()[:200],
        comments.strip()[:2000], app_version,
    )
    placeholder = "%s" if _is_postgres(db_path) else "?"
    placeholders = ", ".join([placeholder] * len(values))
    with _connect(db_path) as connection:
        connection.execute(f"INSERT INTO user_feedback VALUES ({placeholders})", values)
    return feedback_id


def list_feedback(db_path: FeedbackTarget) -> list[dict]:
    with _connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM user_feedback ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def feedback_summary(db_path: FeedbackTarget) -> dict:
    rows = list_feedback(db_path)
    total = len(rows)
    task_keys = ("completed_run", "found_fail_reason", "understood_report", "found_anomaly")
    return {
        "total": total,
        "average_rating": sum(row["overall_rating"] for row in rows) / total if total else 0.0,
        "rating_distribution": {rating: sum(row["overall_rating"] == rating for row in rows) for rating in range(1, 6)},
        "task_completion_rates": {key: sum(row[key] for row in rows) / total if total else 0.0 for key in task_keys},
        "difficult_metrics": _counts(row["difficult_metric"] for row in rows if row["difficult_metric"]),
        "rows": rows,
    }


def export_feedback_json(db_path: FeedbackTarget) -> str:
    return json.dumps(list_feedback(db_path), ensure_ascii=False, indent=2)


def import_feedback_rows(db_path: FeedbackTarget, rows: list[dict[str, Any]]) -> int:
    """Insert exported feedback without duplicating existing feedback IDs."""
    if not rows:
        return 0
    columns = (
        "feedback_id", "created_at", "anonymous_session_id", "overall_rating",
        "completed_run", "found_fail_reason", "understood_report", "found_anomaly",
        "difficult_metric", "comments", "app_version",
    )
    placeholder = "%s" if _is_postgres(db_path) else "?"
    placeholders = ", ".join([placeholder] * len(columns))
    conflict_clause = " ON CONFLICT (feedback_id) DO NOTHING" if _is_postgres(db_path) else " OR IGNORE"
    if _is_postgres(db_path):
        statement = f"INSERT INTO user_feedback ({', '.join(columns)}) VALUES ({placeholders}){conflict_clause}"
    else:
        statement = f"INSERT{conflict_clause} INTO user_feedback ({', '.join(columns)}) VALUES ({placeholders})"
    inserted = 0
    with _connect(db_path) as connection:
        for row in rows:
            cursor = connection.execute(statement, tuple(row[column] for column in columns))
            inserted += max(cursor.rowcount, 0)
    return inserted


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
