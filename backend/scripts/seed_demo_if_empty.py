"""Seed the 10-record demo dataset only when the database is empty.

Called by the one-command dev launcher before uvicorn starts. It never
overwrites existing data: once real records have been imported, this script
does nothing. The dataset is fictional and clearly labelled in every row.
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import JobPosting
from app.services.importer import import_dataset

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "sample_jobs.json"


def main() -> None:
    init_db()
    with SessionLocal() as db:
        existing = db.scalar(select(func.count(JobPosting.id))) or 0
        if existing:
            return

        payload = json.loads(SAMPLE_PATH.read_text(encoding="utf-8-sig"))
        result = import_dataset(db, payload, source_file=str(SAMPLE_PATH))
        print(
            f"[demo] 数据库为空，已导入 {result.imported} 条虚构演示数据 "
            f"（{SAMPLE_PATH.name}）"
        )


if __name__ == "__main__":
    main()
