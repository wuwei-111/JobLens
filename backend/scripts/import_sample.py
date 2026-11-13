"""Import a JSON dataset from the command line.

Usage (run from ``backend/``)::

    python -m scripts.import_sample
    python -m scripts.import_sample data/raw/jobs.json --on-conflict update
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.importer import import_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="导入 JobLens JSON 数据集")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/raw/sample_jobs.json",
        help="JSON 文件路径（默认 data/raw/sample_jobs.json）",
    )
    parser.add_argument(
        "--on-conflict",
        choices=("skip", "update", "fail"),
        default="skip",
        help="重复 id 的处理方式（默认 skip）",
    )
    args = parser.parse_args()

    file_path = Path(args.path)
    if not file_path.is_file():
        raise SystemExit(f"文件不存在：{file_path}")

    payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
    init_db()
    with SessionLocal() as db:
        result = import_dataset(
            db,
            payload,
            on_conflict=args.on_conflict,
            source_file=str(file_path),
        )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
