"""Seed the database from all real datasets when it is empty.

Called by the one-command dev launcher before uvicorn starts. The SQLite file
is gitignored, so a fresh clone needs a bootstrap dataset. Every real dataset
under ``data/raw/`` (``*_graduate_jobs_*.json``) is imported in filename order;
the 10-record fictional sample is used only when no real dataset is present.
It never overwrites existing data: once any records have been imported, this
script does nothing.
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
REAL_GLOB = "*_graduate_jobs_*.json"
SAMPLE_PATH = DATA_RAW / "sample_jobs.json"


def _real_paths() -> list[Path]:
    return sorted(DATA_RAW.glob(REAL_GLOB))


def main() -> None:
    init_db()
    with SessionLocal() as db:
        existing = db.scalar(select(func.count(JobPosting.id))) or 0
        if existing:
            return

        dataset_paths = _real_paths()
        if not dataset_paths:
            dataset_paths = [SAMPLE_PATH]

        imported = failed = skipped = 0
        for dataset_path in dataset_paths:
            payload = json.loads(dataset_path.read_text(encoding="utf-8-sig"))
            result = import_dataset(db, payload, source_file=str(dataset_path))
            imported += result.imported
            failed += result.failed
            skipped += result.skipped
            print(
                f"[seed] {dataset_path.name}: 导入 {result.imported} 条，"
                f"跳过 {result.skipped} 条，失败 {result.failed} 条"
            )

        kind = "真实数据" if dataset_paths != [SAMPLE_PATH] else "虚构演示数据"
        print(
            f"[seed] 数据库为空，已从 {len(dataset_paths)} 个文件导入 "
            f"{imported} 条{kind}（跳过 {skipped}，失败 {failed}）"
        )


if __name__ == "__main__":
    main()
