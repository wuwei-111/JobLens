"""Seed the database from the current real dataset when it is empty.

Called by the one-command dev launcher before uvicorn starts. The SQLite file
is gitignored, so a fresh clone needs a bootstrap dataset. Prefer the current
real dataset; fall back to the 10-record fictional sample only when the real
file is absent. It never overwrites existing data: once any records have been
imported, this script does nothing.
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import JobPosting
from app.services.importer import import_dataset

DATA_RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
REAL_PATH = DATA_RAW / "shanghai_graduate_jobs_2026-11-13.json"
SAMPLE_PATH = DATA_RAW / "sample_jobs.json"


def main() -> None:
    init_db()
    with SessionLocal() as db:
        existing = db.scalar(select(func.count(JobPosting.id))) or 0
        if existing:
            return

        dataset_path = REAL_PATH if REAL_PATH.is_file() else SAMPLE_PATH
        payload = json.loads(dataset_path.read_text(encoding="utf-8-sig"))
        result = import_dataset(db, payload, source_file=str(dataset_path))
        kind = "真实数据" if dataset_path == REAL_PATH else "虚构演示数据"
        print(
            f"[seed] 数据库为空，已导入 {result.imported} 条{kind}"
            f"（{dataset_path.name}）"
        )


if __name__ == "__main__":
    main()
