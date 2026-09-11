"""Migrate anonymous feedback from local SQLite into the configured cloud database."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.storage.feedback import import_feedback_rows, list_feedback


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=str(ROOT / "artifacts/test_results.sqlite3"),
        help="Local SQLite feedback database",
    )
    args = parser.parse_args()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("请先通过环境变量 DATABASE_URL 提供云端 PostgreSQL 连接串。")

    source = Path(args.source)
    rows = list_feedback(source)
    inserted = import_feedback_rows(database_url, rows)
    print(f"迁移完成：读取 {len(rows)} 条，新增 {inserted} 条。")


if __name__ == "__main__":
    main()
