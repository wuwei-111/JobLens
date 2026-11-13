"""Rebuild the local SQLite database from a JSON dataset.

The course project intentionally does not use Alembic. When the schema changes
(indexes, columns), stop the API, rebuild, and re-import:

    python -m scripts.reset_db --yes
    python -m scripts.reset_db data/raw/jobs_hangzhou_2026-11.json --yes

Only file-backed SQLite URLs are supported. The script refuses to run without
``--yes`` and refuses to touch a non-SQLite database.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy.engine import make_url

from app.core import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="重建 JobLens SQLite 数据库并导入数据集")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/raw/sample_jobs.json",
        help="要导入的 JSON 文件（默认演示数据）",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="确认删除现有数据库；这是不可恢复操作",
    )
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit(
            "这会删除现有 SQLite 数据库，确认后请加 --yes。\n"
            "建议先停止 API 服务，避免 Windows 文件占用。"
        )

    file_path = Path(args.path)
    if not file_path.is_file():
        raise SystemExit(f"文件不存在：{file_path}")

    url = make_url(settings.database_url)
    if (
        url.get_backend_name() != "sqlite"
        or not url.database
        or url.database == ":memory:"
    ):
        raise SystemExit("仅支持文件型 SQLite 数据库（JOBLENS_DATABASE_URL）")

    db_path = Path(url.database)
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError as exc:
            raise SystemExit(
                f"无法删除数据库 {db_path}：{exc}\n请先停止 API 服务再重试。"
            ) from exc
        print(f"已删除数据库：{db_path}")

    # Import after the file is removed so the engine creates a fresh schema.
    from app.db.init_db import init_db
    from app.db.session import SessionLocal
    from app.services.importer import import_dataset

    init_db()
    payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
    with SessionLocal() as db:
        result = import_dataset(db, payload, source_file=str(file_path))

    print(result.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
